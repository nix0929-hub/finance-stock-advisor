# engine/strategy.py  ─  Module C: Strategy Engine
"""
4개 레이어 점수를 통합 → Golden Bottom Score 산출
리스크 관리: 적정 매수가, 손절가, 권장 비중
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import (
    RSI_OVERSOLD, SCORE_BUY_STRONG, SCORE_BUY_WATCH, SCORE_NEUTRAL,
    STOP_LOSS_PCT, POSITION_MAX_PCT, WEIGHTS,
)
from engine.ai_analyzer import sentiment_to_layer_score


# ══════════════════════════════════════════════════════════════════════════════
#  Layer 1: Technical Score (0~100)
# ══════════════════════════════════════════════════════════════════════════════

def technical_score(price_df: pd.DataFrame) -> dict:
    """RSI, 볼린저밴드, 200일선 이격도 → 0~100 점수."""
    row   = price_df.iloc[-1]
    close = float(row["Close"].squeeze() if hasattr(row["Close"], "squeeze") else row["Close"])

    scores = {}

    # ── RSI ──────────────────────────────────────────────────────────────────
    rsi = float(row["RSI"]) if not pd.isna(row["RSI"]) else 50.0
    if rsi <= 20:
        scores["rsi"] = 100
    elif rsi <= RSI_OVERSOLD:      # 20~30
        scores["rsi"] = 80
    elif rsi <= 40:
        scores["rsi"] = 55
    elif rsi <= 50:
        scores["rsi"] = 40
    elif rsi <= 70:
        scores["rsi"] = 20
    else:
        scores["rsi"] = 5

    # ── 볼린저밴드 ────────────────────────────────────────────────────────────
    bb_lower = float(row["BB_lower"]) if not pd.isna(row["BB_lower"]) else close
    bb_mid   = float(row["BB_mid"])   if not pd.isna(row["BB_mid"])   else close
    bb_upper = float(row["BB_upper"]) if not pd.isna(row["BB_upper"]) else close

    if close < bb_lower:
        scores["bollinger"] = 100           # 하단 이탈 = 극단적 과매도
    elif close < bb_mid:
        bb_range = bb_mid - bb_lower if bb_mid != bb_lower else 1
        scores["bollinger"] = int(60 * (bb_mid - close) / bb_range)
    else:
        scores["bollinger"] = 10

    # ── 200일선 이격도 ────────────────────────────────────────────────────────
    ma200_dev = float(row["MA200_dev"]) if not pd.isna(row["MA200_dev"]) else 0.0
    if ma200_dev <= -30:
        scores["ma200_dev"] = 100
    elif ma200_dev <= -20:
        scores["ma200_dev"] = 80
    elif ma200_dev <= -10:
        scores["ma200_dev"] = 60
    elif ma200_dev <= 0:
        scores["ma200_dev"] = 40
    elif ma200_dev <= 10:
        scores["ma200_dev"] = 20
    else:
        scores["ma200_dev"] = 5

    total = (scores["rsi"] * 0.40 +
             scores["bollinger"] * 0.35 +
             scores["ma200_dev"] * 0.25)

    return {
        "score"     : round(total, 1),
        "rsi_val"   : rsi,
        "bb_lower"  : bb_lower,
        "bb_upper"  : bb_upper,
        "ma200_dev" : ma200_dev,
        "details"   : scores,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Layer 2: Fundamental Score (0~100)
# ══════════════════════════════════════════════════════════════════════════════

def fundamental_score(fundamentals: dict, price_df: pd.DataFrame) -> dict:
    """PBR, FCF, 부채비율, 52주 위치 → 0~100 점수."""
    scores = {}

    # ── PBR ──────────────────────────────────────────────────────────────────
    pbr = fundamentals.get("pbr")
    if pbr is not None:
        if pbr <= 0.5:      scores["pbr"] = 100
        elif pbr <= 1.0:    scores["pbr"] = 80
        elif pbr <= 1.5:    scores["pbr"] = 60
        elif pbr <= 2.5:    scores["pbr"] = 40
        elif pbr <= 4.0:    scores["pbr"] = 20
        else:               scores["pbr"] = 5
    else:
        scores["pbr"] = 50   # 데이터 없음 → 중립

    # ── FCF (현금흐름) ────────────────────────────────────────────────────────
    fcf = fundamentals.get("free_cashflow")
    if fcf is not None:
        if fcf > 0:         scores["fcf"] = 80
        elif fcf > -1e8:    scores["fcf"] = 40
        else:               scores["fcf"] = 10
    else:
        scores["fcf"] = 50

    # ── 부채비율 ──────────────────────────────────────────────────────────────
    dte = fundamentals.get("debt_to_equity")
    if dte is not None:
        if dte <= 30:       scores["debt"] = 100
        elif dte <= 80:     scores["debt"] = 75
        elif dte <= 150:    scores["debt"] = 50
        elif dte <= 300:    scores["debt"] = 25
        else:               scores["debt"] = 5
    else:
        scores["debt"] = 50

    # ── 52주 저점 근접도 ──────────────────────────────────────────────────────
    high_52 = fundamentals.get("52w_high")
    low_52  = fundamentals.get("52w_low")
    latest  = price_df["Close"].iloc[-1]
    if isinstance(latest, pd.Series):
        latest = latest.iloc[0]
    latest = float(latest)

    if high_52 and low_52 and high_52 != low_52:
        pct_from_low = (latest - low_52) / (high_52 - low_52)
        if pct_from_low <= 0.10:    scores["52w_pos"] = 100
        elif pct_from_low <= 0.25:  scores["52w_pos"] = 75
        elif pct_from_low <= 0.50:  scores["52w_pos"] = 50
        else:                       scores["52w_pos"] = 20
    else:
        scores["52w_pos"] = 50

    total = (scores["pbr"]    * 0.30 +
             scores["fcf"]    * 0.25 +
             scores["debt"]   * 0.25 +
             scores["52w_pos"]* 0.20)

    return {
        "score"   : round(total, 1),
        "pbr"     : pbr,
        "fcf"     : fcf,
        "debt_to_equity": dte,
        "details" : scores,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Layer 3: Sentiment Score (0~100)  ← ai_analyzer.py 연동
# ══════════════════════════════════════════════════════════════════════════════

def sentiment_score_layer(ai_result: dict) -> dict:
    raw_score = ai_result.get("sentiment_score", 0.0)
    layer_s   = sentiment_to_layer_score(raw_score)

    # 악재 선반영 보너스
    if ai_result.get("bad_news_priced_in"):
        layer_s = min(100, layer_s + 10)

    return {
        "score"            : round(layer_s, 1),
        "sentiment_raw"    : raw_score,
        "contrarian_signal": ai_result.get("contrarian_signal", "NEUTRAL"),
        "fear_greed_label" : ai_result.get("fear_greed_label", "중립"),
        "bad_news_priced"  : ai_result.get("bad_news_priced_in", False),
        "summary"          : ai_result.get("summary", ""),
        "opportunity"      : ai_result.get("opportunity", ""),
        "key_risks"        : ai_result.get("key_risks", []),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Layer 4: Flow Score (0~100)  ─ 수급 대리 지표
# ══════════════════════════════════════════════════════════════════════════════

def flow_score(price_df: pd.DataFrame, kis_flow: dict = None) -> dict:
    """
    거래량 급증 + 가격 반등 패턴 + KIS 수급 실데이터로 수급 전환 신호 포착.

    kis_flow: data_loader에서 전달된 KIS 수급 분석 결과 (한국주식)
    """
    scores = {}

    vol   = price_df["Volume"].squeeze()
    close = price_df["Close"].squeeze()

    # ── 거래량 이동평균 대비 ───────────────────────────────────────────────────
    vol_ma20 = vol.rolling(20).mean()
    latest_vol_ratio = float(vol.iloc[-1] / vol_ma20.iloc[-1]) if vol_ma20.iloc[-1] > 0 else 1.0

    if latest_vol_ratio >= 3.0:     scores["vol_surge"] = 100
    elif latest_vol_ratio >= 2.0:   scores["vol_surge"] = 75
    elif latest_vol_ratio >= 1.5:   scores["vol_surge"] = 55
    elif latest_vol_ratio >= 1.0:   scores["vol_surge"] = 40
    else:                           scores["vol_surge"] = 20

    # ── 최근 5일 내 거래량 증가 + 가격 반등 여부 ─────────────────────────────
    recent = price_df.tail(5)
    r_close = recent["Close"].squeeze()
    r_vol   = recent["Volume"].squeeze()

    price_rebound = float(r_close.iloc[-1]) > float(r_close.min())
    vol_building  = float(r_vol.iloc[-1]) > float(r_vol.mean())

    if price_rebound and vol_building:
        scores["accumulation"] = 80
    elif price_rebound or vol_building:
        scores["accumulation"] = 50
    else:
        scores["accumulation"] = 20

    # ── 52주 최저 거래량 대비 급증 여부 ──────────────────────────────────────
    vol_52w_max = float(vol.rolling(252).max().iloc[-1])
    vol_pct_max = float(vol.iloc[-1]) / vol_52w_max * 100 if vol_52w_max > 0 else 0.0

    if vol_pct_max >= 80:   scores["vol_historic"] = 100
    elif vol_pct_max >= 50: scores["vol_historic"] = 70
    elif vol_pct_max >= 30: scores["vol_historic"] = 45
    else:                   scores["vol_historic"] = 20

    # ── KIS 수급 실데이터 반영 (한국주식) ─────────────────────────────────────
    kis_summary = {}
    has_kis = False

    if kis_flow and kis_flow.get("available") and kis_flow.get("summary"):
        has_kis = True
        s = kis_flow["summary"]
        kis_summary = s

        # 외국인 순매수 전환 (역발상 핵심 신호)
        if s.get("foreign_turning"):
            scores["foreign"] = 95   # 외국인 순매도 → 순매수 전환 = 초강력 매수
        elif s.get("foreign_net_5d", 0) > 10000:
            scores["foreign"] = 85
        elif s.get("foreign_net_5d", 0) > 0:
            scores["foreign"] = 65
        elif s.get("foreign_net_5d", 0) > -5000:
            scores["foreign"] = 40
        else:
            scores["foreign"] = 15   # 외국인 대량 순매도

        # 기관 순매수 전환
        if s.get("inst_turning"):
            scores["institution"] = 90
        elif s.get("inst_net_5d", 0) > 10000:
            scores["institution"] = 80
        elif s.get("inst_net_5d", 0) > 0:
            scores["institution"] = 60
        elif s.get("inst_net_5d", 0) > -5000:
            scores["institution"] = 35
        else:
            scores["institution"] = 15

    # ── 최종 점수 산출 ───────────────────────────────────────────────────────
    if has_kis:
        # KIS 데이터 있을 때: 수급 실데이터 가중치 증가
        total = (
            scores["vol_surge"]     * 0.20 +
            scores["accumulation"]  * 0.15 +
            scores["vol_historic"]  * 0.10 +
            scores["foreign"]       * 0.30 +
            scores["institution"]   * 0.25
        )
    else:
        # KIS 데이터 없을 때: 기존 거래량 기반
        total = (
            scores["vol_surge"]    * 0.40 +
            scores["accumulation"] * 0.35 +
            scores["vol_historic"] * 0.25
        )

    return {
        "score"          : round(total, 1),
        "vol_ratio_20d"  : round(latest_vol_ratio, 2),
        "price_rebound"  : price_rebound,
        "vol_building"   : vol_building,
        "has_kis_data"   : has_kis,
        "kis_summary"    : kis_summary,
        "details"        : scores,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Golden Bottom Score 통합
# ══════════════════════════════════════════════════════════════════════════════

def calc_golden_bottom_score(
    tech: dict,
    fund: dict,
    sent: dict,
    flow: dict,
) -> float:
    """4개 레이어 가중치 합산 → 최종 Golden Bottom Score (0~100)."""
    w = WEIGHTS
    score = (
        tech["score"] * w["technical"]   +
        fund["score"] * w["fundamental"] +
        sent["score"] * w["sentiment"]   +
        flow["score"] * w["flow"]
    )
    return round(min(100, max(0, score)), 1)


# ══════════════════════════════════════════════════════════════════════════════
#  리스크 관리
# ══════════════════════════════════════════════════════════════════════════════

def risk_management(
    latest_price: float,
    price_df: pd.DataFrame,
    golden_score: float,
) -> dict:
    """
    적정 매수가, 손절가, 목표가, 권장 비중 계산.
    """
    stop_loss   = round(latest_price * (1 - STOP_LOSS_PCT), 2)

    # 볼린저 밴드 중선 / MA50 을 단기 목표가로 활용
    bb_mid = float(price_df["BB_mid"].iloc[-1])
    ma50   = float(price_df["MA50"].iloc[-1])  if not pd.isna(price_df["MA50"].iloc[-1]) else None
    ma200  = float(price_df["MA200"].iloc[-1]) if not pd.isna(price_df["MA200"].iloc[-1]) else None

    targets = [t for t in [bb_mid, ma50, ma200] if t and t > latest_price]
    target_price = round(min(targets), 2) if targets else round(latest_price * 1.15, 2)

    # 권장 비중: 점수 비례, 최대 POSITION_MAX_PCT
    if golden_score >= SCORE_BUY_STRONG:
        position_pct = POSITION_MAX_PCT
    elif golden_score >= SCORE_BUY_WATCH:
        position_pct = POSITION_MAX_PCT * 0.6
    elif golden_score >= SCORE_NEUTRAL:
        position_pct = POSITION_MAX_PCT * 0.3
    else:
        position_pct = 0.0

    risk_reward = round((target_price - latest_price) /
                        (latest_price - stop_loss), 2) if latest_price > stop_loss else 0.0

    return {
        "entry_price"   : latest_price,
        "stop_loss"     : stop_loss,
        "target_price"  : target_price,
        "position_pct"  : round(position_pct * 100, 1),   # %
        "risk_reward"   : risk_reward,
        "stop_loss_pct" : round(STOP_LOSS_PCT * 100, 1),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  신호 해석
# ══════════════════════════════════════════════════════════════════════════════

def interpret_score(score: float) -> tuple[str, str]:
    """(매수 신호 레이블, 색상) 반환."""
    if score >= 80:
        return "🔴 몰빵 (All-in)", "#DC2626"
    elif score >= SCORE_BUY_STRONG:        # 70
        return "🟠 본부대 투입 (Main Force)", "#F97316"
    elif score >= SCORE_BUY_WATCH:         # 50
        return "🟡 선발대 투입 (Scout)", "#EAB308"
    else:
        return "⚪ 관망 (Watch)", "#6B7280"


def interpret_sell_score(score: float) -> tuple[str, str]:
    """(매도 신호 레이블, 색상) 반환."""
    if score >= 80:
        return "🔴 무조건 매도 (Sell Now)", "#DC2626"
    elif score >= 65:
        return "🟠 강력 매도 (Strong Sell)", "#F97316"
    elif score >= 50:
        return "🟡 일부분 매도 (Partial Sell)", "#EAB308"
    else:
        return "⚪ 관망 (Hold)", "#6B7280"


# ══════════════════════════════════════════════════════════════════════════════
#  전체 파이프라인
# ══════════════════════════════════════════════════════════════════════════════

def run_full_analysis(data: dict, ai_result: dict) -> dict:
    """
    data_loader.load_all() 결과 + ai_analyzer.analyze_sentiment() 결과를
    받아 전체 분석 결과 dict 반환.
    """
    price_df     = data["price_df"]
    fundamentals = data["fundamentals"]
    latest_price = data["latest_price"]

    # 최근 30일 가격 변동률
    close_series = price_df["Close"].squeeze()
    price_30d_chg = float(
        (close_series.iloc[-1] / close_series.iloc[-min(30, len(close_series))] - 1) * 100
    )

    tech = technical_score(price_df)
    fund = fundamental_score(fundamentals, price_df)
    sent = sentiment_score_layer(ai_result)
    flow = flow_score(price_df, kis_flow=data.get("kis_flow"))

    golden = calc_golden_bottom_score(tech, fund, sent, flow)
    signal, color = interpret_score(golden)
    risk   = risk_management(latest_price, price_df, golden)

    return {
        "ticker"        : data["ticker"],
        "company_name"  : fundamentals.get("company_name", data["ticker"]),
        "sector"        : fundamentals.get("sector", "N/A"),
        "latest_price"  : latest_price,
        "price_30d_chg" : round(price_30d_chg, 2),
        "golden_score"  : golden,
        "signal"        : signal,
        "signal_color"  : color,
        "technical"     : tech,
        "fundamental"   : fund,
        "sentiment"     : sent,
        "flow"          : flow,
        "risk"          : risk,
        "price_df"      : price_df,
        "fundamentals"  : fundamentals,
        "ai_result"     : ai_result,
        "sell_analysis" : data.get("sell_analysis", {}),
        "kis_flow"      : data.get("kis_flow"),
    }
