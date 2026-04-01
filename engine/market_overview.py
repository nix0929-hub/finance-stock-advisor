# engine/market_overview.py  ─  전체 시장 흐름 분석
"""
주요 지수, VIX, 섹터별 동향을 실시간 수집하여 시장 방향을 분석.
"""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")


def fetch_market_overview() -> dict:
    """주요 지수 + VIX + 섹터 ETF 실시간 데이터 수집."""

    # ── 주요 지수 ────────────────────────────────────────────────────
    indices = {
        "S&P 500":    "^GSPC",
        "NASDAQ":     "^IXIC",
        "DOW":        "^DJI",
        "Russell2000":"^RUT",
        "KOSPI":      "^KS11",
        "VIX":        "^VIX",
        "US 10Y":     "^TNX",
    }

    idx_data = {}
    for name, ticker in indices.items():
        try:
            df = yf.download(ticker, period="5d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 2:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            close = df["Close"].squeeze()
            price = float(close.iloc[-1])
            chg_1d = float((close.iloc[-1] / close.iloc[-2] - 1) * 100) if len(close) >= 2 else 0
            idx_data[name] = {"price": round(price, 2), "chg_1d": round(chg_1d, 2), "ticker": ticker}
        except Exception:
            pass

    # ── 섹터 ETF (S&P 섹터별) ─────────────────────────────────────────
    sector_etfs = {
        "Technology": "XLK", "Healthcare": "XLV", "Financials": "XLF",
        "Consumer Disc": "XLY", "Energy": "XLE", "Industrials": "XLI",
        "Communication": "XLC", "Utilities": "XLU", "Materials": "XLB",
        "Real Estate": "XLRE", "Staples": "XLP",
    }

    sector_data = {}
    for name, ticker in sector_etfs.items():
        try:
            df = yf.download(ticker, period="5d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 2:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            close = df["Close"].squeeze()
            chg = float((close.iloc[-1] / close.iloc[-2] - 1) * 100)
            sector_data[name] = round(chg, 2)
        except Exception:
            pass

    # ── 시장 방향 판단 ────────────────────────────────────────────────
    vix = idx_data.get("VIX", {}).get("price", 20)
    sp_chg = idx_data.get("S&P 500", {}).get("chg_1d", 0)
    nq_chg = idx_data.get("NASDAQ", {}).get("chg_1d", 0)
    kospi_chg = idx_data.get("KOSPI", {}).get("chg_1d", 0)

    # Fear & Greed 간이 판단
    fear_score = 50  # 중립 기본
    if vix >= 35:     fear_score = 15   # 극공포
    elif vix >= 25:   fear_score = 30   # 공포
    elif vix >= 20:   fear_score = 45   # 불안
    elif vix >= 15:   fear_score = 60   # 중립~낙관
    elif vix >= 12:   fear_score = 75   # 탐욕
    else:             fear_score = 90   # 극탐욕

    if sp_chg < -2:   fear_score -= 15
    elif sp_chg < -1: fear_score -= 8
    elif sp_chg > 2:  fear_score += 10
    elif sp_chg > 1:  fear_score += 5
    fear_score = max(0, min(100, fear_score))

    if fear_score <= 20:   fg_label = "극단적 공포 😱"
    elif fear_score <= 35: fg_label = "공포 😰"
    elif fear_score <= 50: fg_label = "불안 😟"
    elif fear_score <= 65: fg_label = "중립 😐"
    elif fear_score <= 80: fg_label = "낙관 😊"
    else:                  fg_label = "극단적 탐욕 🤑"

    # 시장 방향 요약
    up_sectors = sum(1 for v in sector_data.values() if v > 0)
    dn_sectors = sum(1 for v in sector_data.values() if v < 0)

    if sp_chg > 1 and up_sectors >= 8:
        direction = "🟢 강세 (Bullish)"
        direction_detail = "주요 지수 상승, 대부분의 섹터가 동반 상승 중"
    elif sp_chg > 0 and up_sectors >= 5:
        direction = "🟢 약세 상승 (Mild Bullish)"
        direction_detail = "소폭 상승세, 일부 섹터 차별화"
    elif sp_chg < -1 and dn_sectors >= 8:
        direction = "🔴 약세 (Bearish)"
        direction_detail = "주요 지수 하락, 대부분 섹터 동반 하락 — 저점 매수 기회 탐색"
    elif sp_chg < 0 and dn_sectors >= 5:
        direction = "🟠 약세 조정 (Mild Bearish)"
        direction_detail = "소폭 조정세, 방어주 강세 가능"
    else:
        direction = "🟡 혼조 (Mixed)"
        direction_detail = "방향성 불분명, 섹터별 차별화 장세"

    return {
        "indices":     idx_data,
        "sectors":     sector_data,
        "vix":         vix,
        "fear_score":  fear_score,
        "fear_label":  fg_label,
        "direction":   direction,
        "direction_detail": direction_detail,
        "up_sectors":  up_sectors,
        "dn_sectors":  dn_sectors,
    }
