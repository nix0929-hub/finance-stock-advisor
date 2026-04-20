# engine/kis_api.py  ─  한국투자증권 OpenAPI 클라이언트
"""
KIS Open Trading API 연동 모듈
- OAuth2 토큰 관리
- 투자자별 매매동향 (기관/외국인/개인)
- 공매도 일별 현황
- 국내 주식 현재가
- 매도 신호 분석

API 문서: https://apiportal.koreainvestment.com/
"""

from __future__ import annotations

import datetime
import json
import time
from typing import Optional

import requests
import pandas as pd

from config import KIS_APP_KEY, KIS_APP_SECRET, KIS_IS_PAPER

# ── 기본 URL ──────────────────────────────────────────────────────────────────
BASE_URL = (
    "https://openapivts.koreainvestment.com:29443"
    if KIS_IS_PAPER else
    "https://openapi.koreainvestment.com:9443"
)

# ── 토큰 캐시 ────────────────────────────────────────────────────────────────
_token_cache: dict = {}   # {"access_token": str, "expires_at": float}


# ══════════════════════════════════════════════════════════════════════════════
#  토큰 관리
# ══════════════════════════════════════════════════════════════════════════════

def _get_access_token() -> str:
    """OAuth2 접근 토큰 발급 (캐시 적용)."""
    global _token_cache

    now = time.time()
    if _token_cache.get("access_token") and _token_cache.get("expires_at", 0) > now:
        return _token_cache["access_token"]

    if not KIS_APP_KEY or not KIS_APP_SECRET:
        raise ValueError("한국투자증권 API 키가 설정되지 않았습니다. config.py를 확인하세요.")

    url = f"{BASE_URL}/oauth2/tokenP"
    body = {
        "grant_type": "client_credentials",
        "appkey":     KIS_APP_KEY,
        "appsecret":  KIS_APP_SECRET,
    }

    resp = requests.post(url, json=body, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    _token_cache = {
        "access_token": data["access_token"],
        "expires_at":   now + data.get("expires_in", 86400) - 600,  # 10분 여유
    }
    return _token_cache["access_token"]


def _headers(tr_id: str) -> dict:
    """API 호출 공통 헤더."""
    token = _get_access_token()
    return {
        "content-type":  "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey":        KIS_APP_KEY,
        "appsecret":     KIS_APP_SECRET,
        "tr_id":         tr_id,
        "custtype":      "P",
    }


# ══════════════════════════════════════════════════════════════════════════════
#  한국 종목코드 판별
# ══════════════════════════════════════════════════════════════════════════════

def is_korean_stock(ticker: str) -> bool:
    """한국 주식인지 판별 (.KS, .KQ, 6자리 숫자)."""
    ticker_up = ticker.upper()
    if ticker_up.endswith(".KS") or ticker_up.endswith(".KQ"):
        return True
    code = ticker_up.replace(".KS", "").replace(".KQ", "")
    return code.isdigit() and len(code) == 6


def _extract_stock_code(ticker: str) -> str:
    """yfinance 티커에서 순수 종목코드 추출 (예: 005930.KS → 005930)."""
    return ticker.upper().replace(".KS", "").replace(".KQ", "")


# ══════════════════════════════════════════════════════════════════════════════
#  투자자별 매매동향 (기관/외국인)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_investor_trend(ticker: str, days: int = 20) -> Optional[pd.DataFrame]:
    """
    투자자별 매매동향 조회 (최근 N일).

    반환 DataFrame 컬럼:
      date, 개인_순매수, 외국인_순매수, 기관_순매수
    """
    if not is_korean_stock(ticker):
        return None

    try:
        code = _extract_stock_code(ticker)
        end_date   = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days + 10)

        # FHKST01010900 = 국내주식 종목별 투자자 매매동향 (일별)
        tr_id = "FHKST01010900" if not KIS_IS_PAPER else "FHKST01010900"
        url   = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",         # J=주식
            "FID_INPUT_ISCD":          code,
            "FID_INPUT_DATE_1":        start_date.strftime("%Y%m%d"),
            "FID_INPUT_DATE_2":        end_date.strftime("%Y%m%d"),
        }

        resp = requests.get(url, headers=_headers(tr_id), params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("rt_cd") != "0":
            print(f"[KIS] 투자자 매매동향 실패: {data.get('msg1', '')}")
            return None

        records = data.get("output", [])
        if not records:
            return None

        rows = []
        for r in records[:days]:
            rows.append({
                "date":       pd.Timestamp(r.get("stck_bsop_date", "")),
                "개인_순매수":  int(r.get("prsn_ntby_qty", 0)),
                "외국인_순매수": int(r.get("frgn_ntby_qty", 0)),
                "기관_순매수":  int(r.get("orgn_ntby_qty", 0)),
            })

        df = pd.DataFrame(rows)
        df = df.sort_values("date").reset_index(drop=True)
        return df

    except Exception as e:
        print(f"[KIS] 투자자 매매동향 조회 실패: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  공매도 현황
# ══════════════════════════════════════════════════════════════════════════════

def fetch_short_selling(ticker: str, days: int = 20) -> Optional[pd.DataFrame]:
    """
    공매도 일별 현황 조회.

    반환 DataFrame 컬럼:
      date, 공매도량, 공매도_비율(%)
    """
    if not is_korean_stock(ticker):
        return None

    try:
        code = _extract_stock_code(ticker)
        end_date   = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days + 10)

        tr_id = "FHKST03060100"
        url   = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD":          code,
            "FID_INPUT_DATE_1":        start_date.strftime("%Y%m%d"),
            "FID_INPUT_DATE_2":        end_date.strftime("%Y%m%d"),
            "FID_PERIOD_DIV_CODE":     "D",
            "FID_ORG_ADJ_PRC":         "0",
        }

        resp = requests.get(url, headers=_headers(tr_id), params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("rt_cd") != "0":
            print(f"[KIS] 공매도 현황 실패: {data.get('msg1', '')}")
            return None

        records = data.get("output2", [])
        if not records:
            return None

        rows = []
        for r in records[:days]:
            total_vol = int(r.get("acml_vol", 1))
            rows.append({
                "date":       pd.Timestamp(r.get("stck_bsop_date", "")),
                "거래량":      total_vol,
                "시가":        int(r.get("stck_oprc", 0)),
                "고가":        int(r.get("stck_hgpr", 0)),
                "저가":        int(r.get("stck_lwpr", 0)),
                "종가":        int(r.get("stck_clpr", 0)),
            })

        df = pd.DataFrame(rows)
        df = df.sort_values("date").reset_index(drop=True)
        return df

    except Exception as e:
        print(f"[KIS] 공매도 현황 조회 실패: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  국내주식 현재가 조회
# ══════════════════════════════════════════════════════════════════════════════

def fetch_current_price(ticker: str) -> Optional[dict]:
    """
    국내주식 현재가 시세 조회.

    반환 dict:
      price, change, change_pct, volume,
      high_52w, low_52w, per, pbr, market_cap
    """
    if not is_korean_stock(ticker):
        return None

    try:
        code  = _extract_stock_code(ticker)
        tr_id = "FHKST01010100"
        url   = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD":          code,
        }

        resp = requests.get(url, headers=_headers(tr_id), params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("rt_cd") != "0":
            return None

        o = data.get("output", {})
        return {
            "price":       int(o.get("stck_prpr", 0)),
            "change":      int(o.get("prdy_vrss", 0)),
            "change_pct":  float(o.get("prdy_ctrt", 0)),
            "volume":      int(o.get("acml_vol", 0)),
            "high_52w":    int(o.get("stck_dryy_hgpr", 0)),
            "low_52w":     int(o.get("stck_dryy_lwpr", 0)),
            "per":         float(o.get("per", 0)),
            "pbr":         float(o.get("pbr", 0)),
            "market_cap":  int(o.get("hts_avls", 0)),  # 억원
            "foreign_rate": float(o.get("hts_frgn_ehrt", 0)),  # 외인 소진률 %
            "stock_name":  o.get("rprs_mrkt_kor_name", ""),
        }

    except Exception as e:
        print(f"[KIS] 현재가 조회 실패: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  수급 분석 종합 (전략 엔진 연동용)
# ══════════════════════════════════════════════════════════════════════════════

def analyze_flow(ticker: str) -> dict:
    """
    KIS API를 활용한 실시간 수급 분석 결과 반환.

    반환 dict:
      available:      bool (한국주식이고 API 정상이면 True)
      investor_trend: DataFrame or None
      short_selling:  DataFrame or None
      current_price:  dict or None
      summary: {
          foreign_net:     최근 5일 외국인 순매수 합계
          inst_net:        최근 5일 기관 순매수 합계
          foreign_turning: 외국인 순매수 전환 여부
          inst_turning:    기관 순매수 전환 여부
          foreign_rate:    외인 소진율
      }
    """
    if not is_korean_stock(ticker) or not KIS_APP_KEY:
        return {"available": False}

    inv_df = fetch_investor_trend(ticker)
    cur    = fetch_current_price(ticker)

    summary = {}

    if inv_df is not None and len(inv_df) >= 5:
        recent_5  = inv_df.tail(5)
        prev_5    = inv_df.iloc[-10:-5] if len(inv_df) >= 10 else inv_df.head(5)

        foreign_net_5d = int(recent_5["외국인_순매수"].sum())
        inst_net_5d    = int(recent_5["기관_순매수"].sum())
        indiv_net_5d   = int(recent_5["개인_순매수"].sum())

        # 순매수 전환 감지: 이전 5일 음수 → 최근 5일 양수
        prev_foreign = int(prev_5["외국인_순매수"].sum()) if len(prev_5) >= 3 else 0
        prev_inst    = int(prev_5["기관_순매수"].sum())    if len(prev_5) >= 3 else 0

        summary = {
            "foreign_net_5d":  foreign_net_5d,
            "inst_net_5d":     inst_net_5d,
            "indiv_net_5d":    indiv_net_5d,
            "foreign_turning": prev_foreign < 0 and foreign_net_5d > 0,
            "inst_turning":    prev_inst < 0 and inst_net_5d > 0,
            "foreign_rate":    cur.get("foreign_rate", 0) if cur else 0,
            "daily_data":      inv_df.to_dict("records"),
        }
    else:
        summary = {
            "foreign_net_5d": 0, "inst_net_5d": 0, "indiv_net_5d": 0,
            "foreign_turning": False, "inst_turning": False,
            "foreign_rate": cur.get("foreign_rate", 0) if cur else 0,
            "daily_data": [],
        }

    return {
        "available":      True,
        "investor_trend": inv_df,
        "current_price":  cur,
        "summary":        summary,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  매도 신호 분석
# ══════════════════════════════════════════════════════════════════════════════

def analyze_sell_signal(ticker: str, price_df: pd.DataFrame, kis_flow: dict = None) -> dict:
    """
    KIS 수급 데이터 + 기술적 지표를 결합한 매도 신호 분석.

    kis_flow: 이미 load_all()에서 수집한 KIS 수급 데이터 (있으면 재호출 방지)

    반환 dict:
      sell_score:     0~100 (높을수록 매도 권장)
      sell_signal:    str (신호 레이블)
      sell_reasons:   list[str]
      hold_reasons:   list[str]
    """
    sell_reasons = []
    hold_reasons = []
    score_parts  = []

    close = price_df["Close"].squeeze()
    rsi   = float(price_df["RSI"].iloc[-1]) if "RSI" in price_df.columns else 50

    # ── 기술적 매도 신호 ──────────────────────────────────────────────────────
    # RSI 과매수
    if rsi >= 80:
        score_parts.append(90)
        sell_reasons.append(f"RSI {rsi:.1f} — 극단적 과매수 구간")
    elif rsi >= 70:
        score_parts.append(70)
        sell_reasons.append(f"RSI {rsi:.1f} — 과매수 진입")
    elif rsi >= 50:
        score_parts.append(30)
    else:
        score_parts.append(10)
        hold_reasons.append(f"RSI {rsi:.1f} — 매도 시기 아님")

    # 볼린저 밴드 상단 이탈
    if "BB_upper" in price_df.columns:
        bb_upper = float(price_df["BB_upper"].iloc[-1])
        current  = float(close.iloc[-1])
        if current > bb_upper:
            score_parts.append(85)
            sell_reasons.append("볼린저밴드 상단 돌파 — 단기 과열")
        elif current > bb_upper * 0.97:
            score_parts.append(60)
            sell_reasons.append("볼린저밴드 상단 근접 — 주의")
        else:
            score_parts.append(20)

    # MA200 대비 +20% 이상 이격
    if "MA200_dev" in price_df.columns:
        dev = float(price_df["MA200_dev"].iloc[-1])
        if dev >= 30:
            score_parts.append(90)
            sell_reasons.append(f"200일선 대비 +{dev:.1f}% 과도 이격")
        elif dev >= 20:
            score_parts.append(70)
            sell_reasons.append(f"200일선 대비 +{dev:.1f}% 이격 확대")
        elif dev >= 10:
            score_parts.append(40)
        else:
            score_parts.append(10)
            hold_reasons.append(f"200일선 이격도 {dev:+.1f}% — 정상 범위")

    # ── KIS 수급 매도 신호 ────────────────────────────────────────────────────
    if is_korean_stock(ticker) and KIS_APP_KEY:
        # 이미 수집된 kis_flow가 있으면 재호출 방지 (중복 API 호출 제거)
        flow_data = kis_flow if (kis_flow and kis_flow.get("available")) else analyze_flow(ticker)
        if flow_data.get("available") and flow_data.get("summary"):
            s = flow_data["summary"]

            # 외국인 순매도 지속
            if s["foreign_net_5d"] < -10000:
                score_parts.append(85)
                sell_reasons.append(f"외국인 5일 순매도 {s['foreign_net_5d']:,}주 — 이탈 경고")
            elif s["foreign_net_5d"] < 0:
                score_parts.append(55)
                sell_reasons.append(f"외국인 5일 순매도 {s['foreign_net_5d']:,}주")
            else:
                score_parts.append(15)
                hold_reasons.append(f"외국인 5일 순매수 +{s['foreign_net_5d']:,}주 — 매수 유지")

            # 기관 순매도 지속
            if s["inst_net_5d"] < -10000:
                score_parts.append(80)
                sell_reasons.append(f"기관 5일 순매도 {s['inst_net_5d']:,}주 — 기관 이탈")
            elif s["inst_net_5d"] < 0:
                score_parts.append(50)
                sell_reasons.append(f"기관 5일 순매도 {s['inst_net_5d']:,}주")
            else:
                score_parts.append(15)
                hold_reasons.append(f"기관 5일 순매수 +{s['inst_net_5d']:,}주")

    # ── 최종 점수 ────────────────────────────────────────────────────────────
    sell_score = round(sum(score_parts) / max(len(score_parts), 1), 1) if score_parts else 50

    # 매도 신호 레이블 (관망 → 일부분 매도 → 강력 매도 → 무조건 매도)
    if sell_score >= 80:
        sell_signal = "🔴 무조건 매도 (Sell Now)"
    elif sell_score >= 65:
        sell_signal = "🟠 강력 매도 (Strong Sell)"
    elif sell_score >= 50:
        sell_signal = "🟡 일부분 매도 (Partial Sell)"
    else:
        sell_signal = "⚪ 관망 (Hold)"

    return {
        "sell_score":   sell_score,
        "sell_signal":  sell_signal,
        "sell_reasons": sell_reasons,
        "hold_reasons": hold_reasons,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  API 상태 확인
# ══════════════════════════════════════════════════════════════════════════════

def check_api_status() -> dict:
    """KIS API 연결 상태 확인."""
    if not KIS_APP_KEY or not KIS_APP_SECRET:
        return {"connected": False, "reason": "API 키 미설정"}

    try:
        token = _get_access_token()
        return {
            "connected": True,
            "base_url":  BASE_URL,
            "mode":      "모의투자" if KIS_IS_PAPER else "실거래",
            "token":     token[:20] + "...",
        }
    except Exception as e:
        return {"connected": False, "reason": str(e)}
