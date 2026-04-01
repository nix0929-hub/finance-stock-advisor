"""
Insider and institutional trading activity tracker.

Uses yfinance to retrieve insider transactions and institutional holdings,
then produces actionable buy/sell signals based on net insider activity.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def _safe_scalar(value: Any) -> Any:
    """Convert numpy/pandas scalar types to native Python types."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _parse_timestamp(ts: Any) -> str | None:
    """Convert various timestamp formats to ISO date string."""
    if ts is None or pd.isna(ts):
        return None
    try:
        if isinstance(ts, (pd.Timestamp, datetime)):
            return ts.strftime("%Y-%m-%d")
        return str(ts)
    except Exception:
        return None


def get_insider_trades(ticker: str) -> dict:
    """
    Retrieve insider transactions and institutional holders for a ticker.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol (e.g. "AAPL").

    Returns
    -------
    dict
        {
            "ticker": str,
            "insider_trades": list[dict],
            "institutions": list[dict],
            "net_insider_buy": bool,
            "insider_buy_count": int,
            "insider_sell_count": int,
            "largest_buy": dict | None,
            "recent_institutional_holders": list[dict],
        }
    """
    result: dict[str, Any] = {
        "ticker": ticker.upper(),
        "insider_trades": [],
        "institutions": [],
        "net_insider_buy": False,
        "insider_buy_count": 0,
        "insider_sell_count": 0,
        "largest_buy": None,
        "recent_institutional_holders": [],
    }

    try:
        tk = yf.Ticker(ticker)
    except Exception as exc:
        logger.error("Failed to create yfinance Ticker for %s: %s", ticker, exc)
        return result

    # --- Insider Transactions ---
    try:
        insider_df = tk.insider_transactions
        if insider_df is not None and not insider_df.empty:
            cutoff = datetime.now() - timedelta(days=90)
            trades: list[dict] = []
            buy_count = 0
            sell_count = 0
            largest_buy_value = 0.0
            largest_buy_record: dict | None = None

            for _, row in insider_df.iterrows():
                raw_date = row.get("Start Date", row.get("Date", None))
                date_str = _parse_timestamp(raw_date)

                insider_name = str(row.get("Insider", row.get("Name", "Unknown")))
                position = str(row.get("Position", row.get("Relation", "")))

                # Determine transaction type
                text_col = str(row.get("Text", row.get("Transaction", ""))).lower()
                shares = _safe_scalar(row.get("Shares", row.get("Share", 0))) or 0
                value = _safe_scalar(row.get("Value", 0)) or 0

                if "purchase" in text_col or "buy" in text_col or "acquisition" in text_col:
                    tx_type = "Buy"
                elif "sale" in text_col or "sell" in text_col or "disposition" in text_col:
                    tx_type = "Sell"
                else:
                    # Fall back to sign of shares if available
                    if isinstance(shares, (int, float)) and shares > 0:
                        tx_type = "Buy"
                    elif isinstance(shares, (int, float)) and shares < 0:
                        tx_type = "Sell"
                    else:
                        tx_type = "Unknown"

                trade_record = {
                    "insider_name": insider_name,
                    "position": position,
                    "transaction_type": tx_type,
                    "shares": abs(int(shares)) if isinstance(shares, (int, float)) else 0,
                    "value": abs(float(value)) if isinstance(value, (int, float)) else 0.0,
                    "date": date_str,
                }
                trades.append(trade_record)

                # Count only transactions within the last 90 days
                is_recent = False
                if date_str:
                    try:
                        trade_date = datetime.strptime(date_str, "%Y-%m-%d")
                        is_recent = trade_date >= cutoff
                    except ValueError:
                        is_recent = False

                if is_recent:
                    if tx_type == "Buy":
                        buy_count += 1
                        if trade_record["value"] > largest_buy_value:
                            largest_buy_value = trade_record["value"]
                            largest_buy_record = trade_record
                    elif tx_type == "Sell":
                        sell_count += 1

            result["insider_trades"] = trades
            result["insider_buy_count"] = buy_count
            result["insider_sell_count"] = sell_count
            result["largest_buy"] = largest_buy_record
            result["net_insider_buy"] = buy_count > sell_count

    except Exception as exc:
        logger.warning("Could not retrieve insider transactions for %s: %s", ticker, exc)

    # --- Institutional Holders ---
    try:
        inst_df = tk.institutional_holders
        if inst_df is not None and not inst_df.empty:
            institutions: list[dict] = []
            for _, row in inst_df.iterrows():
                holder = {
                    "holder": str(row.get("Holder", row.get("Organization", "Unknown"))),
                    "shares": int(_safe_scalar(row.get("Shares", 0)) or 0),
                    "value": float(_safe_scalar(row.get("Value", 0)) or 0.0),
                    "date_reported": _parse_timestamp(
                        row.get("Date Reported", row.get("Date", None))
                    ),
                    "pct_held": float(_safe_scalar(row.get("% Out", row.get("pctHeld", 0))) or 0.0),
                }
                institutions.append(holder)

            result["institutions"] = institutions
            result["recent_institutional_holders"] = institutions[:5]

    except Exception as exc:
        logger.warning("Could not retrieve institutional holders for %s: %s", ticker, exc)

    return result


def insider_signal(ticker: str) -> dict:
    """
    Generate an insider-activity-based signal for a ticker.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol.

    Returns
    -------
    dict
        {
            "ticker": str,
            "insider_trades": list[dict],
            "institutions": list[dict],
            "signal": str,        -- "Strong Buy" / "Buy" / "Neutral" / "Sell" / "Strong Sell"
            "reasons": list[str],
            "net_insider_buy": bool,
            "insider_buy_count": int,
            "insider_sell_count": int,
            "largest_buy": dict | None,
            "recent_institutional_holders": list[dict],
        }
    """
    data = get_insider_trades(ticker)

    signal = "Neutral"
    reasons: list[str] = []

    buy_count = data["insider_buy_count"]
    sell_count = data["insider_sell_count"]
    net_buy = data["net_insider_buy"]

    # Strong buy: clear net insider buying in last 90 days
    if net_buy and buy_count >= 3:
        signal = "Strong Buy"
        reasons.append(
            f"Net insider buying: {buy_count} buys vs {sell_count} sells in last 90 days"
        )
    elif net_buy:
        signal = "Buy"
        reasons.append(
            f"Modest insider buying: {buy_count} buys vs {sell_count} sells in last 90 days"
        )
    elif sell_count > buy_count and sell_count >= 3:
        signal = "Sell"
        reasons.append(
            f"Heavy insider selling: {sell_count} sells vs {buy_count} buys in last 90 days"
        )
    elif sell_count > buy_count:
        signal = "Weak Sell"
        reasons.append(
            f"Modest insider selling: {sell_count} sells vs {buy_count} buys in last 90 days"
        )
    else:
        reasons.append("No significant insider trading trend in the last 90 days")

    # Large buy signal
    if data["largest_buy"] and data["largest_buy"]["value"] > 1_000_000:
        reasons.append(
            f"Large insider purchase: ${data['largest_buy']['value']:,.0f} "
            f"by {data['largest_buy']['insider_name']}"
        )
        if signal == "Buy":
            signal = "Strong Buy"

    # Institutional presence
    inst_count = len(data["institutions"])
    if inst_count >= 5:
        reasons.append(f"Strong institutional interest: {inst_count} institutional holders")
    elif inst_count == 0:
        reasons.append("No institutional holders found -- limited institutional interest")

    return {
        "ticker": data["ticker"],
        "insider_trades": data["insider_trades"],
        "institutions": data["institutions"],
        "signal": signal,
        "reasons": reasons,
        "net_insider_buy": net_buy,
        "insider_buy_count": buy_count,
        "insider_sell_count": sell_count,
        "largest_buy": data["largest_buy"],
        "recent_institutional_holders": data["recent_institutional_holders"],
    }
