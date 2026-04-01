"""
Earnings Calendar and Earnings Surprise Analysis
Fetches upcoming earnings dates and historical earnings surprise data
for major US and Korean stocks via yfinance.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tracked tickers and Korean name mapping
# ---------------------------------------------------------------------------

MAJOR_TICKERS: list[str] = [
    # US large-cap
    "AAPL", "MSFT", "NVDA", "GOOG", "AMZN",
    "META", "TSLA", "JPM", "BAC", "JNJ",
    "UNH", "V", "MA", "HD", "PG",
    "KO", "PEP", "MRK", "ABBV", "XOM",
    "CVX", "CRM", "AMD", "NFLX", "BA",
    "INTC",
    # Korean stocks
    "005930.KS", "000660.KS", "005380.KS", "035420.KS",
]

KOREAN_NAMES: dict[str, str] = {
    "005930.KS": "Samsung Electronics",
    "000660.KS": "SK Hynix",
    "005380.KS": "Hyundai Motor",
    "035420.KS": "Naver",
}

# Display-friendly names for all tracked tickers
TICKER_DISPLAY_NAMES: dict[str, str] = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "GOOG": "Alphabet (Google)",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "TSLA": "Tesla",
    "JPM": "JPMorgan Chase",
    "BAC": "Bank of America",
    "JNJ": "Johnson & Johnson",
    "UNH": "UnitedHealth",
    "V": "Visa",
    "MA": "Mastercard",
    "HD": "Home Depot",
    "PG": "Procter & Gamble",
    "KO": "Coca-Cola",
    "PEP": "PepsiCo",
    "MRK": "Merck",
    "ABBV": "AbbVie",
    "XOM": "ExxonMobil",
    "CVX": "Chevron",
    "CRM": "Salesforce",
    "AMD": "AMD",
    "NFLX": "Netflix",
    "BA": "Boeing",
    "INTC": "Intel",
    **KOREAN_NAMES,
}


# ---------------------------------------------------------------------------
# Upcoming earnings
# ---------------------------------------------------------------------------

def get_upcoming_earnings(
    days_ahead: int = 14,
    tickers: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Fetch upcoming earnings dates for major stocks.

    Checks each ticker's yfinance calendar for earnings dates within
    the specified window.

    Args:
        days_ahead: number of days into the future to look.
        tickers: list of tickers to check. Defaults to MAJOR_TICKERS.

    Returns:
        {
            "upcoming": [
                {
                    "ticker": str,
                    "company": str,
                    "earnings_date": str (YYYY-MM-DD),
                    "days_until": int,
                    "is_korean": bool,
                },
                ...
            ],
            "checked_tickers": int,
            "found_earnings": int,
            "window_start": str,
            "window_end": str,
        }
    """
    if tickers is None:
        tickers = MAJOR_TICKERS

    today = datetime.now().date()
    window_end = today + timedelta(days=days_ahead)

    upcoming: list[dict[str, Any]] = []
    checked = 0

    for symbol in tickers:
        checked += 1
        try:
            tk = yf.Ticker(symbol)
            earnings_date = _extract_earnings_date(tk, symbol)

            if earnings_date is None:
                continue

            if today <= earnings_date <= window_end:
                days_until = (earnings_date - today).days
                upcoming.append({
                    "ticker": symbol,
                    "company": TICKER_DISPLAY_NAMES.get(symbol, symbol),
                    "earnings_date": earnings_date.strftime("%Y-%m-%d"),
                    "days_until": days_until,
                    "is_korean": symbol.endswith(".KS"),
                })

        except Exception as exc:
            logger.debug("Error checking earnings for %s: %s", symbol, exc)

    # Sort by date ascending
    upcoming.sort(key=lambda x: x["earnings_date"])

    return {
        "upcoming": upcoming,
        "checked_tickers": checked,
        "found_earnings": len(upcoming),
        "window_start": today.strftime("%Y-%m-%d"),
        "window_end": window_end.strftime("%Y-%m-%d"),
    }


def _extract_earnings_date(tk: yf.Ticker, symbol: str) -> Optional[datetime]:
    """Try multiple methods to extract the next earnings date from a Ticker."""

    # Method 1: ticker.calendar
    try:
        cal = tk.calendar
        if cal is not None:
            if isinstance(cal, pd.DataFrame) and not cal.empty:
                # Some versions return a DataFrame with 'Earnings Date' row
                if "Earnings Date" in cal.index:
                    val = cal.loc["Earnings Date"].iloc[0]
                    return _parse_date(val)
                # Or columns might contain the date
                for col in cal.columns:
                    val = cal[col].iloc[0]
                    parsed = _parse_date(val)
                    if parsed:
                        return parsed
            elif isinstance(cal, dict):
                for key in ["Earnings Date", "earnings_date", "Earnings"]:
                    if key in cal:
                        val = cal[key]
                        if isinstance(val, list) and val:
                            return _parse_date(val[0])
                        return _parse_date(val)
    except Exception:
        pass

    # Method 2: ticker.earnings_dates
    try:
        earnings_dates = tk.earnings_dates
        if earnings_dates is not None and not earnings_dates.empty:
            today = datetime.now().date()
            for dt_idx in earnings_dates.index:
                d = _parse_date(dt_idx)
                if d and d >= today:
                    return d
    except Exception:
        pass

    # Method 3: info dict
    try:
        info = tk.info
        if info:
            for key in ["earningsTimestamp", "earningsTimestampStart",
                        "earningsTimestampEnd", "mostRecentQuarter"]:
                ts = info.get(key)
                if ts and isinstance(ts, (int, float)) and ts > 0:
                    d = datetime.fromtimestamp(ts).date()
                    if d >= datetime.now().date():
                        return d
    except Exception:
        pass

    return None


def _parse_date(val: Any) -> Optional[datetime]:
    """Convert various date representations to a date object."""
    if val is None:
        return None

    # pandas Timestamp
    if isinstance(val, pd.Timestamp):
        return val.date()

    # datetime
    if isinstance(val, datetime):
        return val.date()

    # date object already
    if hasattr(val, "year") and hasattr(val, "month") and hasattr(val, "day"):
        try:
            return val
        except Exception:
            pass

    # numeric timestamp
    if isinstance(val, (int, float)):
        try:
            return datetime.fromtimestamp(val).date()
        except (OSError, ValueError):
            pass

    # string
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%b %d, %Y"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue

    return None


# ---------------------------------------------------------------------------
# Earnings surprise
# ---------------------------------------------------------------------------

def get_earnings_surprise(ticker: str) -> dict[str, Any]:
    """Fetch historical earnings surprise data for a single ticker.

    Compares actual EPS vs estimate EPS across available quarters.

    Args:
        ticker: yfinance ticker symbol.

    Returns:
        {
            "ticker": str,
            "company": str,
            "is_korean": bool,
            "history": [
                {
                    "date": str,
                    "eps_actual": float | None,
                    "eps_estimate": float | None,
                    "surprise": float | None,
                    "surprise_pct": float | None,
                    "beat": bool | None,
                },
                ...
            ],
            "avg_surprise_pct": float | None,
            "beat_rate": float | None,
            "total_quarters": int,
        }
    """
    company = TICKER_DISPLAY_NAMES.get(ticker, ticker)
    is_korean = ticker.endswith(".KS")
    history: list[dict[str, Any]] = []

    # Method 1: earnings_dates (contains actual vs estimate in some yfinance versions)
    try:
        tk = yf.Ticker(ticker)
        ed = tk.earnings_dates
        if ed is not None and not ed.empty:
            history = _parse_earnings_dates_table(ed)
    except Exception as exc:
        logger.debug("earnings_dates failed for %s: %s", ticker, exc)

    # Method 2: earnings_history (older attribute)
    if not history:
        try:
            tk = yf.Ticker(ticker)
            eh = getattr(tk, "earnings_history", None)
            if eh is not None and not eh.empty:
                history = _parse_earnings_history_table(eh)
        except Exception as exc:
            logger.debug("earnings_history failed for %s: %s", ticker, exc)

    # Method 3: Reconstruct from quarterly_earnings
    if not history:
        try:
            tk = yf.Ticker(ticker)
            qe = tk.quarterly_earnings
            if qe is not None and not qe.empty:
                history = _parse_quarterly_earnings(qe)
        except Exception as exc:
            logger.debug("quarterly_earnings failed for %s: %s", ticker, exc)

    # Compute aggregate statistics
    surprises = [h["surprise_pct"] for h in history if h["surprise_pct"] is not None]
    beats = [h for h in history if h.get("beat") is True]
    total_quarters = len(history)

    avg_surprise_pct: Optional[float] = None
    beat_rate: Optional[float] = None

    if surprises:
        avg_surprise_pct = round(sum(surprises) / len(surprises), 2)
    if total_quarters > 0:
        beat_rate = round(len(beats) / total_quarters * 100, 1)

    return {
        "ticker": ticker,
        "company": company,
        "is_korean": is_korean,
        "history": history,
        "avg_surprise_pct": avg_surprise_pct,
        "beat_rate": beat_rate,
        "total_quarters": total_quarters,
    }


def _parse_earnings_dates_table(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Parse the earnings_dates DataFrame into a standardized list."""
    results: list[dict[str, Any]] = []

    # Typical columns: 'EPS Estimate', 'Reported EPS', 'Surprise(%)'
    estimate_col = _find_column(df, ["EPS Estimate", "epsEstimate", "eps_estimate"])
    actual_col = _find_column(df, ["Reported EPS", "epsActual", "eps_actual", "reportedEPS"])
    surprise_col = _find_column(df, ["Surprise(%)", "surprisePercent", "surprise_pct"])

    for idx in df.index:
        try:
            date_str = _parse_date(idx)
            date_out = date_str.strftime("%Y-%m-%d") if date_str else str(idx)

            eps_est = _safe_float(df.at[idx, estimate_col]) if estimate_col else None
            eps_act = _safe_float(df.at[idx, actual_col]) if actual_col else None

            surprise: Optional[float] = None
            surprise_pct: Optional[float] = None
            beat: Optional[bool] = None

            if surprise_col and surprise_col in df.columns:
                surprise_pct = _safe_float(df.at[idx, surprise_col])

            if eps_act is not None and eps_est is not None:
                surprise = round(eps_act - eps_est, 4)
                if eps_est != 0:
                    surprise_pct = round((surprise / abs(eps_est)) * 100, 2)
                beat = eps_act > eps_est

            results.append({
                "date": date_out,
                "eps_actual": eps_act,
                "eps_estimate": eps_est,
                "surprise": surprise,
                "surprise_pct": surprise_pct,
                "beat": beat,
            })
        except Exception:
            continue

    return results


def _parse_earnings_history_table(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Parse an earnings_history DataFrame."""
    results: list[dict[str, Any]] = []

    actual_col = _find_column(df, ["epsActual", "Actual", "eps_actual", "Reported EPS"])
    estimate_col = _find_column(df, ["epsEstimate", "Estimate", "eps_estimate", "EPS Estimate"])

    for idx in df.index:
        try:
            date_str = _parse_date(idx)
            date_out = date_str.strftime("%Y-%m-%d") if date_str else str(idx)

            eps_act = _safe_float(df.at[idx, actual_col]) if actual_col else None
            eps_est = _safe_float(df.at[idx, estimate_col]) if estimate_col else None

            surprise: Optional[float] = None
            surprise_pct: Optional[float] = None
            beat: Optional[bool] = None

            if eps_act is not None and eps_est is not None:
                surprise = round(eps_act - eps_est, 4)
                if eps_est != 0:
                    surprise_pct = round((surprise / abs(eps_est)) * 100, 2)
                beat = eps_act > eps_est

            results.append({
                "date": date_out,
                "eps_actual": eps_act,
                "eps_estimate": eps_est,
                "surprise": surprise,
                "surprise_pct": surprise_pct,
                "beat": beat,
            })
        except Exception:
            continue

    return results


def _parse_quarterly_earnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Parse quarterly_earnings DataFrame (Revenue + Earnings only, no estimate)."""
    results: list[dict[str, Any]] = []

    earnings_col = _find_column(df, ["Earnings", "earnings", "Net Income"])

    for idx in df.index:
        try:
            date_str = str(idx)
            earnings = _safe_float(df.at[idx, earnings_col]) if earnings_col else None

            results.append({
                "date": date_str,
                "eps_actual": earnings,
                "eps_estimate": None,
                "surprise": None,
                "surprise_pct": None,
                "beat": None,
            })
        except Exception:
            continue

    return results


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _find_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """Return the first matching column name from candidates."""
    for col_name in candidates:
        if col_name in df.columns:
            return col_name
    # Case-insensitive fallback
    lower_cols = {c.lower(): c for c in df.columns}
    for col_name in candidates:
        if col_name.lower() in lower_cols:
            return lower_cols[col_name.lower()]
    return None


def _safe_float(val: Any) -> Optional[float]:
    """Convert a value to float, returning None on failure or NaN."""
    if val is None:
        return None
    try:
        f = float(val)
        if pd.isna(f):
            return None
        return round(f, 4)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Convenience: combined earnings overview
# ---------------------------------------------------------------------------

def get_earnings_overview(
    days_ahead: int = 14,
    tickers: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Combined function returning upcoming earnings plus surprise data
    for tickers that have upcoming earnings.

    Returns:
        {
            "upcoming_earnings": <result from get_upcoming_earnings>,
            "surprise_data": {ticker: <result from get_earnings_surprise>, ...},
        }
    """
    upcoming = get_upcoming_earnings(days_ahead=days_ahead, tickers=tickers)

    surprise_data: dict[str, Any] = {}
    for entry in upcoming.get("upcoming", []):
        ticker = entry["ticker"]
        try:
            surprise_data[ticker] = get_earnings_surprise(ticker)
        except Exception as exc:
            logger.error("Failed to get surprise for %s: %s", ticker, exc)
            surprise_data[ticker] = {
                "ticker": ticker,
                "company": entry.get("company", ticker),
                "is_korean": entry.get("is_korean", False),
                "history": [],
                "avg_surprise_pct": None,
                "beat_rate": None,
                "total_quarters": 0,
            }

    return {
        "upcoming_earnings": upcoming,
        "surprise_data": surprise_data,
    }


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)

    print("=== Upcoming Earnings (14 days) ===")
    upcoming = get_upcoming_earnings(days_ahead=14)
    print(json.dumps(upcoming, ensure_ascii=False, indent=2))

    print("\n=== AAPL Earnings Surprise ===")
    surprise = get_earnings_surprise("AAPL")
    print(json.dumps(surprise, ensure_ascii=False, indent=2))
