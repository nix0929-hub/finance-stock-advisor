"""
Backtesting Engine for Golden Bottom Score Strategy
Tests a buy-low / sell-high strategy using RSI and Bollinger Band signals
on historical data fetched from yfinance.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Technical indicator calculations
# ---------------------------------------------------------------------------

def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate the Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def _compute_bollinger_bands(
    series: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands (middle, upper, lower)."""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return middle, upper, lower


# ---------------------------------------------------------------------------
# Core backtest logic
# ---------------------------------------------------------------------------

def run_backtest(
    ticker: str,
    lookback_years: int = 3,
    buy_threshold: int = 70,
    sell_threshold: int = 30,
    rsi_period: int = 14,
    bb_period: int = 20,
    bb_std: float = 2.0,
    rsi_buy_level: float = 30.0,
    rsi_sell_level: float = 70.0,
    profit_target_pct: float = 15.0,
) -> dict[str, Any]:
    """Run a backtest of the Golden Bottom Score strategy on a single ticker.

    Strategy rules:
      - BUY when RSI <= rsi_buy_level AND price <= Bollinger lower band
      - SELL when RSI >= rsi_sell_level OR profit >= profit_target_pct%

    Args:
        ticker: yfinance ticker symbol.
        lookback_years: how many years of historical data to use.
        buy_threshold: (reserved for extended scoring; not used in basic mode).
        sell_threshold: (reserved for extended scoring; not used in basic mode).
        rsi_period: RSI calculation period.
        bb_period: Bollinger Band moving-average period.
        bb_std: Bollinger Band standard-deviation multiplier.
        rsi_buy_level: RSI level at or below which a buy signal is generated.
        rsi_sell_level: RSI level at or above which a sell signal is generated.
        profit_target_pct: profit percentage that triggers a sell.

    Returns:
        {
            "ticker": str,
            "trades": [
                {
                    "entry_date": str,
                    "entry_price": float,
                    "exit_date": str | None,
                    "exit_price": float | None,
                    "return_pct": float | None,
                    "holding_days": int | None,
                    "exit_reason": str | None,
                },
                ...
            ],
            "summary": {
                "total_trades": int,
                "win_rate": float,
                "avg_return_pct": float,
                "max_return": float,
                "max_loss": float,
                "avg_holding_days": float,
                "total_return_pct": float,
                "max_drawdown_pct": float,
                "sharpe_ratio": float,
            },
            "price_df": pd.DataFrame,   # for charting
        }
    """
    # --- Fetch data --------------------------------------------------------
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_years * 365)

    try:
        df = yf.download(
            ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            progress=False,
        )
    except Exception as exc:
        logger.error("Failed to download data for %s: %s", ticker, exc)
        return _empty_result(ticker)

    if df.empty or len(df) < bb_period + 10:
        logger.warning("Insufficient data for %s (got %d rows).", ticker, len(df))
        return _empty_result(ticker)

    # Flatten MultiIndex columns if present (yfinance >= 0.2.x)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.copy()

    # --- Compute indicators -----------------------------------------------
    df["RSI"] = _compute_rsi(df["Close"], period=rsi_period)
    df["BB_mid"], df["BB_upper"], df["BB_lower"] = _compute_bollinger_bands(
        df["Close"], period=bb_period, num_std=bb_std,
    )

    # Drop rows with NaN indicators
    df.dropna(subset=["RSI", "BB_lower"], inplace=True)

    # --- Simulate trades ---------------------------------------------------
    trades: list[dict[str, Any]] = []
    in_position = False
    entry_price = 0.0
    entry_date: Optional[datetime] = None

    for i in range(len(df)):
        row = df.iloc[i]
        current_price = float(row["Close"])
        current_rsi = float(row["RSI"])
        current_bb_lower = float(row["BB_lower"])
        current_date = df.index[i]

        if not in_position:
            # Buy condition: RSI oversold AND price at/below lower Bollinger Band
            if current_rsi <= rsi_buy_level and current_price <= current_bb_lower:
                in_position = True
                entry_price = current_price
                entry_date = current_date
        else:
            # Sell conditions
            pct_gain = ((current_price - entry_price) / entry_price) * 100
            exit_reason: Optional[str] = None

            if current_rsi >= rsi_sell_level:
                exit_reason = "RSI overbought"
            elif pct_gain >= profit_target_pct:
                exit_reason = f"Profit target ({profit_target_pct}%)"

            if exit_reason is not None:
                holding = (current_date - entry_date).days if entry_date else 0
                trades.append({
                    "entry_date": entry_date.strftime("%Y-%m-%d") if entry_date else "",
                    "entry_price": round(entry_price, 2),
                    "exit_date": current_date.strftime("%Y-%m-%d"),
                    "exit_price": round(current_price, 2),
                    "return_pct": round(pct_gain, 2),
                    "holding_days": holding,
                    "exit_reason": exit_reason,
                })
                in_position = False
                entry_price = 0.0
                entry_date = None

    # Handle open position at end of data
    if in_position and entry_date is not None:
        last_price = float(df["Close"].iloc[-1])
        pct_gain = ((last_price - entry_price) / entry_price) * 100
        holding = (df.index[-1] - entry_date).days
        trades.append({
            "entry_date": entry_date.strftime("%Y-%m-%d"),
            "entry_price": round(entry_price, 2),
            "exit_date": None,
            "exit_price": round(last_price, 2),
            "return_pct": round(pct_gain, 2),
            "holding_days": holding,
            "exit_reason": "Open (not closed)",
        })

    # --- Compute summary statistics ----------------------------------------
    summary = _compute_summary(trades)

    return {
        "ticker": ticker,
        "trades": trades,
        "summary": summary,
        "price_df": df,
    }


def _empty_result(ticker: str) -> dict[str, Any]:
    """Return an empty result dict when data is unavailable."""
    return {
        "ticker": ticker,
        "trades": [],
        "summary": {
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_return_pct": 0.0,
            "max_return": 0.0,
            "max_loss": 0.0,
            "avg_holding_days": 0.0,
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe_ratio": 0.0,
        },
        "price_df": pd.DataFrame(),
    }


def _compute_summary(trades: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate aggregate statistics from a list of closed trades."""
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_return_pct": 0.0,
            "max_return": 0.0,
            "max_loss": 0.0,
            "avg_holding_days": 0.0,
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe_ratio": 0.0,
        }

    returns = [t["return_pct"] for t in trades if t["return_pct"] is not None]
    holding_days = [t["holding_days"] for t in trades if t["holding_days"] is not None]
    wins = [r for r in returns if r > 0]

    total_trades = len(trades)
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0
    avg_return = float(np.mean(returns)) if returns else 0.0
    max_return = float(max(returns)) if returns else 0.0
    max_loss = float(min(returns)) if returns else 0.0
    avg_holding = float(np.mean(holding_days)) if holding_days else 0.0

    # Compound total return
    total_return = 1.0
    for r in returns:
        total_return *= (1 + r / 100)
    total_return_pct = (total_return - 1) * 100

    # Max drawdown from trade sequence
    peak = 1.0
    max_dd = 0.0
    cumulative = 1.0
    for r in returns:
        cumulative *= (1 + r / 100)
        if cumulative > peak:
            peak = cumulative
        dd = (peak - cumulative) / peak * 100
        if dd > max_dd:
            max_dd = dd

    # Approximate Sharpe ratio (annualised, assuming 252 trading days)
    sharpe = 0.0
    if len(returns) >= 2:
        returns_arr = np.array(returns) / 100.0
        mean_ret = float(np.mean(returns_arr))
        std_ret = float(np.std(returns_arr, ddof=1))
        if std_ret > 0 and avg_holding > 0:
            trades_per_year = 252.0 / avg_holding
            sharpe = (mean_ret / std_ret) * np.sqrt(trades_per_year)
            sharpe = float(round(sharpe, 2))

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 1),
        "avg_return_pct": round(avg_return, 2),
        "max_return": round(max_return, 2),
        "max_loss": round(max_loss, 2),
        "avg_holding_days": round(avg_holding, 1),
        "total_return_pct": round(total_return_pct, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe_ratio": sharpe,
    }


# ---------------------------------------------------------------------------
# Plotly chart
# ---------------------------------------------------------------------------

def backtest_chart(
    trades: list[dict[str, Any]],
    price_df: pd.DataFrame,
    ticker: str = "",
) -> Optional[go.Figure]:
    """Create a Plotly chart showing price history with buy/sell markers.

    Args:
        trades: list of trade dicts from run_backtest.
        price_df: DataFrame with at least 'Close', 'BB_upper', 'BB_lower' columns.
        ticker: ticker symbol for the chart title.

    Returns:
        plotly Figure, or None if data is insufficient.
    """
    if price_df.empty:
        return None

    fig = go.Figure()

    # Price line
    fig.add_trace(go.Scatter(
        x=price_df.index,
        y=price_df["Close"],
        mode="lines",
        name="Close",
        line=dict(color="#2196F3", width=1.5),
    ))

    # Bollinger Bands
    if "BB_upper" in price_df.columns and "BB_lower" in price_df.columns:
        fig.add_trace(go.Scatter(
            x=price_df.index,
            y=price_df["BB_upper"],
            mode="lines",
            name="BB Upper",
            line=dict(color="rgba(150,150,150,0.4)", width=1, dash="dot"),
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=price_df.index,
            y=price_df["BB_lower"],
            mode="lines",
            name="BB Lower",
            line=dict(color="rgba(150,150,150,0.4)", width=1, dash="dot"),
            fill="tonexty",
            fillcolor="rgba(200,200,200,0.1)",
            showlegend=False,
        ))

    # Buy markers
    buy_dates = []
    buy_prices = []
    for t in trades:
        if t.get("entry_date"):
            buy_dates.append(pd.Timestamp(t["entry_date"]))
            buy_prices.append(t["entry_price"])

    if buy_dates:
        fig.add_trace(go.Scatter(
            x=buy_dates,
            y=buy_prices,
            mode="markers",
            name="BUY",
            marker=dict(
                symbol="triangle-up",
                size=12,
                color="#4CAF50",
                line=dict(width=1, color="white"),
            ),
        ))

    # Sell markers
    sell_dates = []
    sell_prices = []
    sell_colors = []
    for t in trades:
        if t.get("exit_date"):
            sell_dates.append(pd.Timestamp(t["exit_date"]))
            sell_prices.append(t["exit_price"])
            ret = t.get("return_pct", 0)
            sell_colors.append("#4CAF50" if ret and ret >= 0 else "#F44336")

    if sell_dates:
        fig.add_trace(go.Scatter(
            x=sell_dates,
            y=sell_prices,
            mode="markers",
            name="SELL",
            marker=dict(
                symbol="triangle-down",
                size=12,
                color=sell_colors,
                line=dict(width=1, color="white"),
            ),
        ))

    title_text = f"Backtest: {ticker}" if ticker else "Backtest Results"
    fig.update_layout(
        title=title_text,
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark",
        height=500,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)
    result = run_backtest("AAPL", lookback_years=3)
    # Remove price_df for JSON serialisation
    output = {k: v for k, v in result.items() if k != "price_df"}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\nTotal rows in price_df: {len(result['price_df'])}")
