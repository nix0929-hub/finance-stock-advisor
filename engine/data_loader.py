# engine/data_loader.py  ─  Module A: Data Engine
"""
yfinance  → OHLCV + 재무 지표
NewsAPI   → 최신 뉴스 헤드라인
"""

from __future__ import annotations

import datetime
import warnings
from typing import Optional

import numpy as np
import pandas as pd
import requests
import yfinance as yf

warnings.filterwarnings("ignore")

from config import (
    BB_PERIOD, BB_STD, LOOKBACK_DAYS, MA_LONG, MA_SHORT,
    NEWS_API_KEY, RSI_PERIOD,
)
from engine.kis_api import is_korean_stock, analyze_flow, analyze_sell_signal


# ══════════════════════════════════════════════════════════════════════════════
#  OHLCV + 기술적 지표
# ══════════════════════════════════════════════════════════════════════════════

def _rsi(series: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """RSI(Relative Strength Index) 계산."""
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _bollinger(series: pd.Series, period: int = BB_PERIOD, std: float = BB_STD):
    """볼린저 밴드 (mid, upper, lower) 반환."""
    mid   = series.rolling(period).mean()
    sigma = series.rolling(period).std()
    return mid, mid + std * sigma, mid - std * sigma


def fetch_price_data(ticker: str, days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """
    OHLCV + 기술적 지표 DataFrame 반환.

    추가 컬럼:
      RSI, BB_mid, BB_upper, BB_lower,
      MA50, MA200, MA200_deviation (현재가/MA200 - 1)
    """
    end   = datetime.date.today()
    start = end - datetime.timedelta(days=days + MA_LONG + 50)  # 이동평균 워밍업

    df = yf.download(ticker, start=str(start), end=str(end),
                     auto_adjust=True, progress=False)

    if df.empty:
        raise ValueError(f"'{ticker}' 에 대한 가격 데이터를 가져오지 못했습니다.")

    # 멀티인덱스 컬럼 정리
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df["Close"].squeeze()

    df["RSI"]           = _rsi(close)
    df["BB_mid"], df["BB_upper"], df["BB_lower"] = _bollinger(close)
    df["MA50"]          = close.rolling(MA_SHORT).mean()
    df["MA200"]         = close.rolling(MA_LONG).mean()
    df["MA200_dev"]     = (close / df["MA200"] - 1) * 100   # % 이격도

    # 최근 LOOKBACK_DAYS 만 반환
    cutoff = pd.Timestamp(end - datetime.timedelta(days=days))
    return df[df.index >= cutoff].copy()


# ══════════════════════════════════════════════════════════════════════════════
#  재무 지표
# ══════════════════════════════════════════════════════════════════════════════

def fetch_fundamentals(ticker: str) -> dict:
    """
    yfinance Ticker.info 에서 핵심 재무 지표를 추출.

    반환 키:
      pbr, per, roe, debt_to_equity,
      free_cashflow, current_ratio,
      market_cap, sector, company_name
    """
    info = yf.Ticker(ticker).info

    def _safe(key, default=None):
        v = info.get(key, default)
        return v if v not in (None, "N/A", float("inf"), float("-inf")) else default

    return {
        "company_name"    : _safe("longName", ticker),
        "sector"          : _safe("sector", "N/A"),
        "market_cap"      : _safe("marketCap"),
        "pbr"             : _safe("priceToBook"),
        "per"             : _safe("trailingPE"),
        "roe"             : _safe("returnOnEquity"),
        "debt_to_equity"  : _safe("debtToEquity"),
        "free_cashflow"   : _safe("freeCashflow"),
        "current_ratio"   : _safe("currentRatio"),
        "52w_high"        : _safe("fiftyTwoWeekHigh"),
        "52w_low"         : _safe("fiftyTwoWeekLow"),
        "currency"        : _safe("currency", "USD"),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  뉴스
# ══════════════════════════════════════════════════════════════════════════════

def fetch_news(query: str, max_articles: int = 10) -> list[dict]:
    """
    NewsAPI에서 최신 뉴스 수집.
    API 키가 없으면 빈 리스트 반환 (graceful degradation).

    반환 형식: [{"title": ..., "description": ..., "publishedAt": ...}, ...]
    """
    if not NEWS_API_KEY:
        return []

    url = "https://newsapi.org/v2/everything"
    params = {
        "q"          : query,
        "sortBy"     : "publishedAt",
        "pageSize"   : max_articles,
        "language"   : "en",
        "apiKey"     : NEWS_API_KEY,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            {
                "title"       : a.get("title", ""),
                "description" : a.get("description", ""),
                "publishedAt" : a.get("publishedAt", ""),
                "source"      : a.get("source", {}).get("name", ""),
            }
            for a in articles
            if a.get("title")
        ]
    except Exception as e:
        print(f"[NewsAPI] 뉴스 수집 실패: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
#  편의 함수: 전체 데이터 로드
# ══════════════════════════════════════════════════════════════════════════════

def load_all(ticker: str) -> dict:
    """
    가격·재무·뉴스·수급 데이터를 한 번에 로드하여 dict 반환.

    Keys: price_df, fundamentals, news, latest_price, ticker,
          kis_flow (한국주식인 경우), sell_analysis
    """
    price_df     = fetch_price_data(ticker)
    fundamentals = fetch_fundamentals(ticker)
    company_name = fundamentals.get("company_name", ticker)
    news         = fetch_news(f"{ticker} {company_name} stock")

    latest_close = price_df["Close"].iloc[-1]
    if hasattr(latest_close, "item"):
        latest_close = latest_close.item()

    # ── KIS 수급 데이터 (한국 주식) ──────────────────────────────────────────
    kis_flow = None
    if is_korean_stock(ticker):
        try:
            kis_flow = analyze_flow(ticker)
        except Exception as e:
            print(f"[KIS] 수급 데이터 로드 실패: {e}")
            kis_flow = {"available": False}

    # ── 매도 신호 분석 ───────────────────────────────────────────────────────
    try:
        sell_analysis = analyze_sell_signal(ticker, price_df)
    except Exception as e:
        print(f"[매도 분석] 실패: {e}")
        sell_analysis = {
            "sell_score": 50, "sell_signal": "🟡 분석 불가",
            "sell_reasons": [], "hold_reasons": [],
        }

    return {
        "ticker"       : ticker,
        "price_df"     : price_df,
        "fundamentals" : fundamentals,
        "news"         : news,
        "latest_price" : float(latest_close),
        "kis_flow"     : kis_flow,
        "sell_analysis": sell_analysis,
    }
