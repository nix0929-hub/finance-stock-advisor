"""
Automatic chart pattern recognition from OHLCV data.

Detects: Golden/Death Cross, Double Bottom/Top, RSI Divergence,
Volume Climax, and Support/Resistance levels.  Returns structured
pattern dicts and an optional Plotly candlestick figure with annotations.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make sure the DataFrame contains the columns we need, computing
    derived indicators when they are missing.
    """
    df = df.copy()

    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    if "MA50" not in df.columns:
        df["MA50"] = df["Close"].rolling(window=50, min_periods=1).mean()
    if "MA200" not in df.columns:
        df["MA200"] = df["Close"].rolling(window=200, min_periods=1).mean()

    if "RSI" not in df.columns:
        delta = df["Close"].diff()
        gain = delta.clip(lower=0).rolling(window=14, min_periods=1).mean()
        loss = (-delta.clip(upper=0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        df["RSI"] = 100 - (100 / (1 + rs))
        df["RSI"] = df["RSI"].fillna(50)

    if "BB_upper" not in df.columns or "BB_lower" not in df.columns:
        ma20 = df["Close"].rolling(window=20, min_periods=1).mean()
        std20 = df["Close"].rolling(window=20, min_periods=1).std().fillna(0)
        df["BB_upper"] = ma20 + 2 * std20
        df["BB_lower"] = ma20 - 2 * std20

    return df


def _date_str(idx: Any) -> str:
    """Convert an index value to an ISO date string."""
    try:
        return pd.Timestamp(idx).strftime("%Y-%m-%d")
    except Exception:
        return str(idx)


# ---------------------------------------------------------------------------
# Individual pattern detectors
# ---------------------------------------------------------------------------

def _detect_golden_death_cross(df: pd.DataFrame) -> list[dict]:
    """Detect Golden Cross (MA50 > MA200) and Death Cross (MA50 < MA200)."""
    patterns: list[dict] = []
    if len(df) < 201:
        return patterns

    ma50 = df["MA50"].values
    ma200 = df["MA200"].values

    for i in range(1, len(df)):
        if np.isnan(ma50[i]) or np.isnan(ma200[i]):
            continue
        if np.isnan(ma50[i - 1]) or np.isnan(ma200[i - 1]):
            continue

        if ma50[i - 1] <= ma200[i - 1] and ma50[i] > ma200[i]:
            patterns.append({
                "name": "Golden Cross",
                "type": "bullish",
                "confidence": 75,
                "description": "50-day MA crossed above 200-day MA, a classic long-term bullish signal.",
                "date": _date_str(df.index[i]),
            })
        elif ma50[i - 1] >= ma200[i - 1] and ma50[i] < ma200[i]:
            patterns.append({
                "name": "Death Cross",
                "type": "bearish",
                "confidence": 75,
                "description": "50-day MA crossed below 200-day MA, a classic long-term bearish signal.",
                "date": _date_str(df.index[i]),
            })

    return patterns


def _detect_double_bottom(df: pd.DataFrame) -> list[dict]:
    """
    Detect Double Bottom (W pattern).
    Look for two similar lows separated by 20-60 trading days.
    """
    patterns: list[dict] = []
    if len(df) < 60:
        return patterns

    lows = df["Low"].values
    closes = df["Close"].values

    # Find local minima using a rolling window of 5
    window = 5
    local_mins: list[int] = []
    for i in range(window, len(lows) - window):
        if lows[i] == np.min(lows[i - window : i + window + 1]):
            local_mins.append(i)

    # Compare pairs of minima
    for a_idx in range(len(local_mins)):
        for b_idx in range(a_idx + 1, len(local_mins)):
            i, j = local_mins[a_idx], local_mins[b_idx]
            gap = j - i
            if gap < 20 or gap > 60:
                continue

            low_a, low_b = lows[i], lows[j]
            if low_a == 0:
                continue
            similarity = abs(low_a - low_b) / low_a
            if similarity > 0.03:  # within 3%
                continue

            # Check that there is a peak between the two lows
            mid_high = np.max(closes[i:j])
            trough_avg = (low_a + low_b) / 2
            if trough_avg == 0:
                continue
            peak_ratio = (mid_high - trough_avg) / trough_avg
            if peak_ratio < 0.03:
                continue

            # Confirmation: price closed above mid-peak after second low
            if j + 1 < len(closes) and closes[j + 1] > trough_avg:
                confidence = min(90, int(60 + (1 - similarity) * 30))
            else:
                confidence = min(70, int(40 + (1 - similarity) * 30))

            patterns.append({
                "name": "Double Bottom",
                "type": "bullish",
                "confidence": confidence,
                "description": (
                    f"W-pattern detected with lows at {low_a:.2f} and {low_b:.2f}, "
                    f"separated by {gap} trading days."
                ),
                "date": _date_str(df.index[j]),
            })
            break  # one per first-low is enough
        if patterns and patterns[-1]["name"] == "Double Bottom":
            break  # keep only the most recent one for clarity

    return patterns[-1:] if patterns else []


def _detect_double_top(df: pd.DataFrame) -> list[dict]:
    """
    Detect Double Top (M pattern).
    Look for two similar highs separated by 20-60 trading days.
    """
    patterns: list[dict] = []
    if len(df) < 60:
        return patterns

    highs = df["High"].values
    closes = df["Close"].values

    window = 5
    local_maxs: list[int] = []
    for i in range(window, len(highs) - window):
        if highs[i] == np.max(highs[i - window : i + window + 1]):
            local_maxs.append(i)

    for a_idx in range(len(local_maxs)):
        for b_idx in range(a_idx + 1, len(local_maxs)):
            i, j = local_maxs[a_idx], local_maxs[b_idx]
            gap = j - i
            if gap < 20 or gap > 60:
                continue

            high_a, high_b = highs[i], highs[j]
            if high_a == 0:
                continue
            similarity = abs(high_a - high_b) / high_a
            if similarity > 0.03:
                continue

            mid_low = np.min(closes[i:j])
            peak_avg = (high_a + high_b) / 2
            if peak_avg == 0:
                continue
            valley_ratio = (peak_avg - mid_low) / peak_avg
            if valley_ratio < 0.03:
                continue

            confidence = min(85, int(55 + (1 - similarity) * 30))

            patterns.append({
                "name": "Double Top",
                "type": "bearish",
                "confidence": confidence,
                "description": (
                    f"M-pattern detected with highs at {high_a:.2f} and {high_b:.2f}, "
                    f"separated by {gap} trading days."
                ),
                "date": _date_str(df.index[j]),
            })
            break
        if patterns and patterns[-1]["name"] == "Double Top":
            break

    return patterns[-1:] if patterns else []


def _detect_rsi_divergence(df: pd.DataFrame) -> list[dict]:
    """
    Detect bullish/bearish RSI divergence.
    Bullish: price makes a lower low but RSI makes a higher low.
    Bearish: price makes a higher high but RSI makes a lower high.
    """
    patterns: list[dict] = []
    if len(df) < 30:
        return patterns

    closes = df["Close"].values
    rsi = df["RSI"].values
    window = 5
    lookback = min(60, len(df) - window * 2)

    # Collect local minima/maxima in recent data
    start = max(window, len(df) - lookback)

    mins_idx: list[int] = []
    maxs_idx: list[int] = []
    for i in range(start, len(df) - window):
        seg = closes[i - window : i + window + 1]
        if closes[i] == np.min(seg):
            mins_idx.append(i)
        if closes[i] == np.max(seg):
            maxs_idx.append(i)

    # Bullish divergence
    for a in range(len(mins_idx)):
        for b in range(a + 1, len(mins_idx)):
            i, j = mins_idx[a], mins_idx[b]
            if j - i < 5:
                continue
            if closes[j] < closes[i] and rsi[j] > rsi[i]:
                patterns.append({
                    "name": "Bullish RSI Divergence",
                    "type": "bullish",
                    "confidence": 65,
                    "description": (
                        "Price made a lower low while RSI made a higher low, "
                        "indicating weakening downward momentum."
                    ),
                    "date": _date_str(df.index[j]),
                })
                break
        if patterns and "Bullish RSI" in patterns[-1]["name"]:
            break

    # Bearish divergence
    for a in range(len(maxs_idx)):
        for b in range(a + 1, len(maxs_idx)):
            i, j = maxs_idx[a], maxs_idx[b]
            if j - i < 5:
                continue
            if closes[j] > closes[i] and rsi[j] < rsi[i]:
                patterns.append({
                    "name": "Bearish RSI Divergence",
                    "type": "bearish",
                    "confidence": 65,
                    "description": (
                        "Price made a higher high while RSI made a lower high, "
                        "indicating weakening upward momentum."
                    ),
                    "date": _date_str(df.index[j]),
                })
                break
        if patterns and "Bearish RSI" in patterns[-1]["name"]:
            break

    return patterns


def _detect_volume_climax(df: pd.DataFrame) -> list[dict]:
    """Detect volume climax -- volume >3x 20-day average with price reversal."""
    patterns: list[dict] = []
    if len(df) < 25:
        return patterns

    vol = df["Volume"].values.astype(float)
    closes = df["Close"].values
    vol_ma20 = pd.Series(vol).rolling(window=20, min_periods=1).mean().values

    for i in range(21, len(df) - 1):
        if vol_ma20[i] == 0:
            continue
        ratio = vol[i] / vol_ma20[i]
        if ratio < 3.0:
            continue

        # Check for price reversal the next day
        price_change_day = closes[i] - closes[i - 1]
        price_change_next = closes[i + 1] - closes[i] if i + 1 < len(closes) else 0

        if price_change_day < 0 and price_change_next > 0:
            patterns.append({
                "name": "Volume Climax (Bullish Reversal)",
                "type": "bullish",
                "confidence": 60,
                "description": (
                    f"Volume spike at {ratio:.1f}x the 20-day average with a "
                    f"subsequent upward reversal."
                ),
                "date": _date_str(df.index[i]),
            })
        elif price_change_day > 0 and price_change_next < 0:
            patterns.append({
                "name": "Volume Climax (Bearish Reversal)",
                "type": "bearish",
                "confidence": 60,
                "description": (
                    f"Volume spike at {ratio:.1f}x the 20-day average with a "
                    f"subsequent downward reversal."
                ),
                "date": _date_str(df.index[i]),
            })

    # Return only the most recent one
    return patterns[-1:] if patterns else []


def _detect_support_resistance(df: pd.DataFrame) -> list[dict]:
    """
    Find horizontal support/resistance levels with multiple price touches.
    Uses a clustering approach on local extrema.
    """
    patterns: list[dict] = []
    if len(df) < 30:
        return patterns

    highs = df["High"].values
    lows = df["Low"].values
    closes = df["Close"].values
    current_price = closes[-1]

    # Gather local extrema
    window = 3
    extrema: list[float] = []
    for i in range(window, len(df) - window):
        if lows[i] == np.min(lows[i - window : i + window + 1]):
            extrema.append(lows[i])
        if highs[i] == np.max(highs[i - window : i + window + 1]):
            extrema.append(highs[i])

    if not extrema:
        return patterns

    extrema_arr = np.array(sorted(extrema))
    price_range = extrema_arr[-1] - extrema_arr[0]
    if price_range == 0:
        return patterns

    # Cluster extrema within 1.5% tolerance
    tolerance = 0.015 * current_price
    levels: list[dict] = []
    used = set()

    for i, val in enumerate(extrema_arr):
        if i in used:
            continue
        cluster = [val]
        used.add(i)
        for j in range(i + 1, len(extrema_arr)):
            if j in used:
                continue
            if abs(extrema_arr[j] - val) <= tolerance:
                cluster.append(extrema_arr[j])
                used.add(j)

        if len(cluster) >= 3:  # at least 3 touches
            level_price = float(np.mean(cluster))
            levels.append({
                "price": level_price,
                "touches": len(cluster),
            })

    # Classify as support or resistance relative to current price
    for level in sorted(levels, key=lambda x: x["touches"], reverse=True)[:4]:
        if level["price"] < current_price:
            label = "Support"
            ptype = "bullish"
        else:
            label = "Resistance"
            ptype = "bearish"

        confidence = min(85, 40 + level["touches"] * 10)
        patterns.append({
            "name": f"{label} Level",
            "type": ptype,
            "confidence": confidence,
            "description": (
                f"{label} at ${level['price']:.2f} with {level['touches']} touches."
            ),
            "date": _date_str(df.index[-1]),
        })

    return patterns


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_patterns(price_df: pd.DataFrame) -> list[dict]:
    """
    Run all pattern detectors on the given OHLCV DataFrame.

    Parameters
    ----------
    price_df : pd.DataFrame
        Must contain at least: Open, High, Low, Close, Volume.
        Optionally: RSI, MA50, MA200, BB_upper, BB_lower (computed if missing).

    Returns
    -------
    list[dict]
        Each dict: {name, type, confidence, description, date}
    """
    try:
        df = _ensure_columns(price_df)
    except ValueError as exc:
        logger.error("Cannot detect patterns: %s", exc)
        return []

    if df.empty:
        return []

    all_patterns: list[dict] = []

    detectors = [
        _detect_golden_death_cross,
        _detect_double_bottom,
        _detect_double_top,
        _detect_rsi_divergence,
        _detect_volume_climax,
        _detect_support_resistance,
    ]

    for detector in detectors:
        try:
            found = detector(df)
            all_patterns.extend(found)
        except Exception as exc:
            logger.warning("Detector %s failed: %s", detector.__name__, exc)

    # Sort by date descending, then by confidence descending
    all_patterns.sort(key=lambda p: (p.get("date", ""), p.get("confidence", 0)), reverse=True)
    return all_patterns


def pattern_chart(price_df: pd.DataFrame, patterns: list[dict]) -> go.Figure:
    """
    Build a Plotly candlestick chart with detected patterns annotated.

    Parameters
    ----------
    price_df : pd.DataFrame
        OHLCV data (same as detect_patterns input).
    patterns : list[dict]
        Output of detect_patterns().

    Returns
    -------
    plotly.graph_objects.Figure
    """
    df = _ensure_columns(price_df)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("Price", "Volume", "RSI"),
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    # Moving averages
    fig.add_trace(
        go.Scatter(x=df.index, y=df["MA50"], name="MA50",
                   line=dict(color="orange", width=1)),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df["MA200"], name="MA200",
                   line=dict(color="purple", width=1)),
        row=1, col=1,
    )

    # Bollinger Bands
    fig.add_trace(
        go.Scatter(x=df.index, y=df["BB_upper"], name="BB Upper",
                   line=dict(color="gray", width=0.5, dash="dash")),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df["BB_lower"], name="BB Lower",
                   line=dict(color="gray", width=0.5, dash="dash"),
                   fill="tonexty", fillcolor="rgba(128,128,128,0.1)"),
        row=1, col=1,
    )

    # Volume
    colors = [
        "#26a69a" if c >= o else "#ef5350"
        for c, o in zip(df["Close"], df["Open"])
    ]
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], name="Volume",
               marker_color=colors, opacity=0.7),
        row=2, col=1,
    )

    # RSI
    fig.add_trace(
        go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                   line=dict(color="blue", width=1)),
        row=3, col=1,
    )
    fig.add_hline(y=70, line_dash="dash", line_color="red",
                  opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green",
                  opacity=0.5, row=3, col=1)

    # Annotate patterns
    for pat in patterns:
        date = pat.get("date")
        if date is None:
            continue

        try:
            ts = pd.Timestamp(date)
        except Exception:
            continue

        # Find closest index
        if ts not in df.index:
            idx_pos = df.index.get_indexer([ts], method="nearest")[0]
            if idx_pos < 0 or idx_pos >= len(df):
                continue
            ts = df.index[idx_pos]

        y_val = float(df.loc[ts, "Close"]) if ts in df.index else float(df["Close"].iloc[-1])

        marker_color = "green" if pat["type"] == "bullish" else "red"
        symbol = "triangle-up" if pat["type"] == "bullish" else "triangle-down"

        fig.add_trace(
            go.Scatter(
                x=[ts], y=[y_val],
                mode="markers+text",
                marker=dict(size=12, color=marker_color, symbol=symbol),
                text=[pat["name"]],
                textposition="top center",
                textfont=dict(size=9, color=marker_color),
                showlegend=False,
                hovertext=f"{pat['name']}\n{pat['description']}\nConfidence: {pat['confidence']}%",
            ),
            row=1, col=1,
        )

        # Support/Resistance levels as horizontal lines
        if "Level" in pat["name"]:
            try:
                price_level = float(pat["description"].split("$")[1].split(" ")[0])
                line_color = "green" if pat["type"] == "bullish" else "red"
                fig.add_hline(
                    y=price_level, line_dash="dot",
                    line_color=line_color, opacity=0.6,
                    annotation_text=pat["name"],
                    annotation_position="right",
                    row=1, col=1,
                )
            except (IndexError, ValueError):
                pass

    fig.update_layout(
        title="Chart Pattern Analysis",
        xaxis_rangeslider_visible=False,
        height=800,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)

    return fig
