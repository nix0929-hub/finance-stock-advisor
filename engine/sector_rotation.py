"""
Sector rotation strategy -- track money flow between market sectors.

Downloads sector ETF data via yfinance, calculates multi-timeframe returns,
determines the current rotation phase, and ranks sectors by momentum.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

logger = logging.getLogger(__name__)

# Sector ETFs with descriptive names
SECTOR_ETFS: dict[str, str] = {
    "XLK": "Technology",
    "XLV": "Health Care",
    "XLF": "Financials",
    "XLY": "Consumer Discretionary",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLC": "Communication Services",
    "XLU": "Utilities",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "XLP": "Consumer Staples",
}

# Classification used for rotation phase detection
CYCLICAL_SECTORS = {"XLY", "XLK", "XLF", "XLI", "XLB"}
DEFENSIVE_SECTORS = {"XLU", "XLP", "XLV", "XLRE"}


def _calculate_returns(prices: pd.Series) -> dict[str, float | None]:
    """
    Calculate 1-week, 1-month, and 3-month returns from a daily price series.

    Returns
    -------
    dict with keys: return_1w, return_1m, return_3m (as percentages)
    """
    result: dict[str, float | None] = {
        "return_1w": None,
        "return_1m": None,
        "return_3m": None,
    }

    if prices is None or len(prices) < 2:
        return result

    current = float(prices.iloc[-1])
    if current == 0:
        return result

    # 1-week (5 trading days)
    if len(prices) >= 6:
        prev = float(prices.iloc[-6])
        if prev != 0:
            result["return_1w"] = round(((current - prev) / prev) * 100, 2)

    # 1-month (21 trading days)
    if len(prices) >= 22:
        prev = float(prices.iloc[-22])
        if prev != 0:
            result["return_1m"] = round(((current - prev) / prev) * 100, 2)

    # 3-month (63 trading days -- full series)
    prev = float(prices.iloc[0])
    if prev != 0:
        result["return_3m"] = round(((current - prev) / prev) * 100, 2)

    return result


def _determine_phase(sector_data: list[dict]) -> tuple[str, str]:
    """
    Determine the market rotation phase based on which sectors lead.

    Returns (phase_name, phase_description).
    """
    cyclical_momentum: list[float] = []
    defensive_momentum: list[float] = []

    for s in sector_data:
        ticker = s["ticker"]
        # Use 1-month return as the primary momentum metric
        ret = s.get("return_1m")
        if ret is None:
            continue

        if ticker in CYCLICAL_SECTORS:
            cyclical_momentum.append(ret)
        elif ticker in DEFENSIVE_SECTORS:
            defensive_momentum.append(ret)

    avg_cyc = np.mean(cyclical_momentum) if cyclical_momentum else 0.0
    avg_def = np.mean(defensive_momentum) if defensive_momentum else 0.0

    if avg_cyc > 0 and avg_cyc > avg_def:
        if avg_def > 0:
            phase = "Late Bull"
            desc = (
                "Both cyclical and defensive sectors are rising, but cyclicals "
                "still lead. The bull market may be maturing."
            )
        else:
            phase = "Early Bull"
            desc = (
                "Cyclical sectors are leading while defensives lag. This is "
                "typical of an early-stage recovery or new bull market."
            )
    elif avg_def > 0 and avg_def > avg_cyc:
        if avg_cyc > 0:
            phase = "Late Bull"
            desc = (
                "Defensive sectors are outperforming cyclicals. Investors are "
                "rotating toward safety, suggesting a late-cycle market."
            )
        else:
            phase = "Early Bear"
            desc = (
                "Cyclicals are falling while defensives hold up. Risk appetite "
                "is declining -- typical of an early bear market phase."
            )
    elif avg_cyc < 0 and avg_def < 0:
        if avg_cyc < avg_def:
            phase = "Early Bear"
            desc = (
                "Both sectors are declining with cyclicals falling faster. "
                "Broad weakness suggests an early bear market."
            )
        else:
            phase = "Late Bear"
            desc = (
                "Both sectors are declining but cyclicals are stabilizing. "
                "The market may be approaching a bottom."
            )
    else:
        phase = "Transition"
        desc = "No clear rotation signal -- the market is in a transitional phase."

    return phase, desc


def analyze_sector_rotation() -> dict:
    """
    Download sector ETF data, calculate returns, determine rotation phase,
    and rank sectors by momentum.

    Returns
    -------
    dict
        {
            "phase": str,
            "phase_description": str,
            "sectors_ranked": list[dict],
            "buy_sectors": list[dict],
            "sell_sectors": list[dict],
            "rotation_signal": str,
        }
    """
    result: dict[str, Any] = {
        "phase": "Unknown",
        "phase_description": "Insufficient data to determine rotation phase.",
        "sectors_ranked": [],
        "buy_sectors": [],
        "sell_sectors": [],
        "rotation_signal": "Neutral",
    }

    tickers = list(SECTOR_ETFS.keys())

    try:
        raw = yf.download(tickers, period="3mo", progress=False, group_by="ticker")
    except Exception as exc:
        logger.error("Failed to download sector ETF data: %s", exc)
        return result

    if raw is None or raw.empty:
        logger.warning("No data returned for sector ETFs.")
        return result

    sector_data: list[dict] = []

    for ticker in tickers:
        try:
            # Handle both multi-level and single-level column structures
            if isinstance(raw.columns, pd.MultiIndex):
                if ticker in raw.columns.get_level_values(0):
                    prices = raw[ticker]["Close"].dropna()
                else:
                    continue
            else:
                # Single ticker fallback (should not happen with our list)
                prices = raw["Close"].dropna()

            if prices.empty:
                continue

            returns = _calculate_returns(prices)

            entry: dict[str, Any] = {
                "ticker": ticker,
                "name": SECTOR_ETFS[ticker],
                "current_price": round(float(prices.iloc[-1]), 2),
                **returns,
            }

            # Composite momentum score (weighted average of timeframes)
            scores: list[float] = []
            weights = {"return_1w": 0.2, "return_1m": 0.4, "return_3m": 0.4}
            for key, weight in weights.items():
                val = returns.get(key)
                if val is not None:
                    scores.append(val * weight)
            entry["momentum_score"] = round(sum(scores), 2) if scores else 0.0

            sector_data.append(entry)

        except Exception as exc:
            logger.warning("Error processing %s: %s", ticker, exc)

    if not sector_data:
        return result

    # Sort by momentum score descending
    sector_data.sort(key=lambda s: s.get("momentum_score", 0), reverse=True)
    result["sectors_ranked"] = sector_data

    # Buy sectors: positive and accelerating momentum (top quartile)
    quartile_size = max(1, len(sector_data) // 4)
    result["buy_sectors"] = [
        s for s in sector_data[:quartile_size]
        if s.get("momentum_score", 0) > 0
    ]

    # Sell sectors: negative and decelerating momentum (bottom quartile)
    result["sell_sectors"] = [
        s for s in sector_data[-quartile_size:]
        if s.get("momentum_score", 0) < 0
    ]

    # Determine phase
    phase, desc = _determine_phase(sector_data)
    result["phase"] = phase
    result["phase_description"] = desc

    # Rotation signal
    if result["buy_sectors"] and not result["sell_sectors"]:
        result["rotation_signal"] = "Broad strength -- stay invested"
    elif result["sell_sectors"] and not result["buy_sectors"]:
        result["rotation_signal"] = "Broad weakness -- reduce exposure"
    elif result["buy_sectors"] and result["sell_sectors"]:
        buy_names = ", ".join(s["name"] for s in result["buy_sectors"])
        sell_names = ", ".join(s["name"] for s in result["sell_sectors"])
        result["rotation_signal"] = f"Rotate into {buy_names}; reduce {sell_names}"
    else:
        result["rotation_signal"] = "Mixed signals -- hold current allocation"

    return result


def rotation_chart() -> go.Figure:
    """
    Build a Plotly heatmap showing sector performance across timeframes.

    Rows = sectors, Columns = 1W / 1M / 3M returns.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    data = analyze_sector_rotation()
    sectors = data.get("sectors_ranked", [])

    if not sectors:
        fig = go.Figure()
        fig.add_annotation(text="No sector data available", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           font=dict(size=16))
        fig.update_layout(title="Sector Rotation Heatmap")
        return fig

    sector_labels = [f"{s['ticker']} ({s['name']})" for s in sectors]
    timeframes = ["1 Week", "1 Month", "3 Month"]

    z_values: list[list[float]] = []
    text_values: list[list[str]] = []

    for s in sectors:
        row_z: list[float] = []
        row_text: list[str] = []
        for key in ["return_1w", "return_1m", "return_3m"]:
            val = s.get(key)
            if val is not None:
                row_z.append(val)
                row_text.append(f"{val:+.2f}%")
            else:
                row_z.append(0.0)
                row_text.append("N/A")
        z_values.append(row_z)
        text_values.append(row_text)

    fig = go.Figure(
        data=go.Heatmap(
            z=z_values,
            x=timeframes,
            y=sector_labels,
            text=text_values,
            texttemplate="%{text}",
            textfont=dict(size=12),
            colorscale=[
                [0.0, "#d32f2f"],
                [0.25, "#ff8a80"],
                [0.5, "#ffffff"],
                [0.75, "#69f0ae"],
                [1.0, "#2e7d32"],
            ],
            zmid=0,
            colorbar=dict(title="Return %"),
            hovertemplate=(
                "Sector: %{y}<br>"
                "Timeframe: %{x}<br>"
                "Return: %{text}<extra></extra>"
            ),
        )
    )

    phase = data.get("phase", "Unknown")
    signal = data.get("rotation_signal", "")

    fig.update_layout(
        title=dict(
            text=f"Sector Rotation Heatmap | Phase: {phase}",
            font=dict(size=16),
        ),
        xaxis=dict(title="Timeframe", side="bottom"),
        yaxis=dict(title="Sector", autorange="reversed"),
        height=max(500, len(sectors) * 45 + 120),
        template="plotly_dark",
        annotations=[
            dict(
                text=f"Signal: {signal}",
                xref="paper", yref="paper",
                x=0.5, y=-0.12,
                showarrow=False,
                font=dict(size=12, color="white"),
                align="center",
            )
        ],
    )

    return fig
