# ui/components.py  ─  Boltshift 스타일 리디자인 컴포넌트
"""
Streamlit + Plotly 차트 컴포넌트 — 화이트/블루 클린 디자인.
"""

from __future__ import annotations

import re
import plotly.graph_objects as go
import streamlit as st
import pandas as pd

# ── 공통 색상 팔레트 (Boltshift) ─────────────────────────────────────────────
C_BG        = "rgba(255,255,255,0)"   # 투명 (카드 배경은 CSS로)
C_PLOT_BG   = "rgba(248,250,255,1)"   # 차트 플롯 영역 연한 파란 배경
C_GRID      = "rgba(229,231,235,1)"   # 격자선
C_TEXT      = "#374151"
C_PRIMARY   = "#3B82F6"
C_BLUE_DARK = "#1D4ED8"
C_GREEN     = "#10B981"
C_RED       = "#EF4444"
C_YELLOW    = "#F59E0B"
C_PURPLE    = "#8B5CF6"
C_ORANGE    = "#F97316"

FONT = dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", color=C_TEXT)


# ══════════════════════════════════════════════════════════════════════════════
#  Golden Bottom Score 게이지 차트 (모던)
# ══════════════════════════════════════════════════════════════════════════════

def gauge_chart_modern(score: float, signal: str, color: str) -> go.Figure:
    # 점수에 따라 색상 결정
    if score >= 70:
        bar_color = C_GREEN
    elif score >= 50:
        bar_color = C_PRIMARY
    elif score >= 35:
        bar_color = C_YELLOW
    else:
        bar_color = C_RED

    fig = go.Figure(go.Indicator(
        mode  = "gauge+number",
        value = score,
        title = {
            "text": "Golden Bottom Score",
            "font": {"size": 14, "color": "#6B7280", "family": "Inter, sans-serif"},
        },
        gauge = {
            "axis"      : {
                "range"     : [0, 100],
                "tickwidth" : 1,
                "tickcolor" : "#E5E7EB",
                "tickfont"  : {"size": 11, "color": "#9CA3AF"},
            },
            "bar"       : {"color": bar_color, "thickness": 0.28},
            "bgcolor"   : "white",
            "borderwidth": 0,
            "steps"     : [
                {"range": [0,   35], "color": "#FEF2F2"},
                {"range": [35,  50], "color": "#FFFBEB"},
                {"range": [50,  70], "color": "#EFF6FF"},
                {"range": [70, 100], "color": "#F0FDF4"},
            ],
            "threshold" : {
                "line"     : {"color": bar_color, "width": 2},
                "thickness": 0.85,
                "value"    : score,
            },
        },
        number = {
            "font"   : {"size": 38, "color": bar_color, "family": "Inter, sans-serif"},
            "suffix" : "점",
        },
    ))
    fig.update_layout(
        height        = 240,
        margin        = dict(t=35, b=5, l=20, r=20),
        paper_bgcolor = "rgba(0,0,0,0)",
        font          = FONT,
        annotations   = [dict(
            text      = signal,
            x=0.5, y=-0.08,
            showarrow = False,
            font      = dict(size=13, color=bar_color, family="Inter, sans-serif"),
        )],
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  캔들스틱 + 볼린저밴드 + MA 차트 (모던)
# ══════════════════════════════════════════════════════════════════════════════

def candlestick_chart_modern(price_df: pd.DataFrame, ticker: str) -> go.Figure:
    df = price_df.tail(90).copy()

    for col in ["Open", "High", "Low", "Close",
                "BB_upper", "BB_lower", "BB_mid", "MA50", "MA200"]:
        if col in df.columns:
            df[col] = df[col].squeeze() if hasattr(df[col], "squeeze") else df[col]

    fig = go.Figure()

    # 볼린저 밴드 배경 채우기
    if "BB_upper" in df.columns and "BB_lower" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_upper"],
            name="BB Upper",
            line=dict(color="rgba(59,130,246,0.3)", width=1, dash="dot"),
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_lower"],
            name="BB Lower",
            fill="tonexty",
            fillcolor="rgba(59,130,246,0.06)",
            line=dict(color="rgba(59,130,246,0.3)", width=1, dash="dot"),
            showlegend=False,
        ))
        if "BB_mid" in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df["BB_mid"],
                name="BB Mid",
                line=dict(color="rgba(59,130,246,0.5)", width=1, dash="dash"),
                showlegend=False,
            ))

    # 캔들스틱
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        name=ticker,
        increasing=dict(
            line=dict(color=C_GREEN, width=1.5),
            fillcolor="rgba(16,185,129,0.85)",
        ),
        decreasing=dict(
            line=dict(color=C_RED, width=1.5),
            fillcolor="rgba(239,68,68,0.85)",
        ),
    ))

    # MA50
    if "MA50" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MA50"],
            name="MA 50",
            line=dict(color=C_YELLOW, width=1.8),
        ))
    # MA200
    if "MA200" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MA200"],
            name="MA 200",
            line=dict(color=C_ORANGE, width=1.8),
        ))

    fig.update_layout(
        title=dict(
            text=f"<b>{ticker}</b>  ·  캔들 차트 (최근 90일)",
            font=dict(size=13, color=C_TEXT),
            x=0,
        ),
        xaxis_rangeslider_visible=False,
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor =C_PLOT_BG,
        font=FONT,
        legend=dict(
            orientation="h", y=1.06, x=0,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(t=42, b=10, l=10, r=10),
        hovermode="x unified",
    )
    fig.update_xaxes(
        gridcolor=C_GRID, gridwidth=1,
        showline=True, linecolor=C_GRID,
        tickfont=dict(size=11, color="#9CA3AF"),
    )
    fig.update_yaxes(
        gridcolor=C_GRID, gridwidth=1,
        showline=False,
        tickfont=dict(size=11, color="#9CA3AF"),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  RSI 차트 (모던)
# ══════════════════════════════════════════════════════════════════════════════

def rsi_chart_modern(price_df: pd.DataFrame) -> go.Figure:
    df  = price_df.tail(90).copy()
    rsi = df["RSI"].squeeze()

    fig = go.Figure()

    # 과매도 / 과매수 영역
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(239,68,68,0.06)",   line_width=0)
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(16,185,129,0.05)",  line_width=0)
    fig.add_hline(
        y=30, line_dash="dot",
        line_color="rgba(239,68,68,0.6)", line_width=1.5,
        annotation_text="과매도 30", annotation_position="left",
        annotation_font=dict(size=10, color="rgba(239,68,68,0.8)"),
    )
    fig.add_hline(
        y=70, line_dash="dot",
        line_color="rgba(16,185,129,0.6)", line_width=1.5,
        annotation_text="과매수 70", annotation_position="left",
        annotation_font=dict(size=10, color="rgba(16,185,129,0.8)"),
    )

    # RSI 라인
    fig.add_trace(go.Scatter(
        x=df.index, y=rsi,
        name="RSI (14)",
        line=dict(color=C_PRIMARY, width=2.2),
        fill="tozeroy",
        fillcolor="rgba(59,130,246,0.06)",
    ))

    fig.update_layout(
        title=dict(
            text="<b>RSI (14)</b>",
            font=dict(size=13, color=C_TEXT), x=0,
        ),
        height=160,
        yaxis=dict(range=[0, 100], tickvals=[0, 30, 50, 70, 100]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor =C_PLOT_BG,
        font=FONT,
        margin=dict(t=36, b=8, l=10, r=10),
        showlegend=False,
        hovermode="x unified",
    )
    fig.update_xaxes(
        gridcolor=C_GRID, gridwidth=1,
        tickfont=dict(size=11, color="#9CA3AF"),
    )
    fig.update_yaxes(
        gridcolor=C_GRID, gridwidth=1,
        tickfont=dict(size=11, color="#9CA3AF"),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  레이더 차트 (모던)
# ══════════════════════════════════════════════════════════════════════════════

def radar_chart_modern(result: dict) -> go.Figure:
    categories = ["기술적 분석", "재무 분석", "AI 심리", "수급", "기술적 분석"]  # 마지막은 레이더 폐합용
    safe = {k: result.get(k, {}).get("score", 0) for k in ["technical", "fundamental", "sentiment", "flow"]}
    values = [
        safe["technical"],
        safe["fundamental"],
        safe["sentiment"],
        safe["flow"],
        safe["technical"],  # 폐합
    ]

    score = result["golden_score"]
    if score >= 70:
        fill_color = "rgba(16,185,129,0.12)"
        line_color = C_GREEN
    elif score >= 50:
        fill_color = "rgba(59,130,246,0.12)"
        line_color = C_PRIMARY
    elif score >= 35:
        fill_color = "rgba(245,158,11,0.12)"
        line_color = C_YELLOW
    else:
        fill_color = "rgba(239,68,68,0.12)"
        line_color = C_RED

    fig = go.Figure(go.Scatterpolar(
        r      = values,
        theta  = categories,
        fill   = "toself",
        line   = dict(color=line_color, width=2.2),
        fillcolor = fill_color,
        name   = "Score",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                range=[0, 100],
                gridcolor="#E5E7EB",
                tickfont=dict(size=10, color="#9CA3AF"),
                linecolor="#E5E7EB",
            ),
            angularaxis=dict(
                gridcolor="#E5E7EB",
                tickfont=dict(size=11, color="#374151"),
                linecolor="#E5E7EB",
            ),
            bgcolor="rgba(248,250,255,1)",
        ),
        height        = 280,
        paper_bgcolor = "rgba(0,0,0,0)",
        font          = FONT,
        margin        = dict(t=16, b=16, l=40, r=40),
        showlegend    = False,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  레이어별 점수 바 (HTML + st.markdown)
# ══════════════════════════════════════════════════════════════════════════════

def layer_score_bar(result: dict) -> None:
    from config import WEIGHTS

    layers = [
        ("🔵 기술적 분석", result.get("technical", {}).get("score", 0),  int(WEIGHTS["technical"]   * 100), C_PRIMARY),
        ("🟢 재무 분석",   result.get("fundamental", {}).get("score", 0), int(WEIGHTS["fundamental"] * 100), C_GREEN),
        ("🟣 AI 심리",     result.get("sentiment", {}).get("score", 0),   int(WEIGHTS["sentiment"]   * 100), C_PURPLE),
        ("🟠 수급",        result.get("flow", {}).get("score", 0),        int(WEIGHTS["flow"]        * 100), C_ORANGE),
    ]

    # 전체 HTML을 한 번에 렌더링 (st.markdown 4회 → 1회로 통합)
    rows_html = ""
    for name, score, weight, color in layers:
        pct = max(0, min(100, score))
        rows_html += f"""<div style="display:flex; align-items:center; gap:14px; padding:11px 0; border-bottom:1px solid #F3F4F6">
  <div style="font-size:0.83rem; font-weight:600; color:#374151; width:110px; flex-shrink:0">{name}</div>
  <div style="flex:1; height:7px; background:#F3F4F6; border-radius:4px; overflow:hidden">
    <div style="height:100%; width:{pct}%; background:{color}; border-radius:4px"></div>
  </div>
  <div style="font-size:0.85rem; font-weight:700; color:{color}; width:42px; text-align:right; flex-shrink:0">{score:.0f}</div>
  <div style="font-size:0.75rem; color:#9CA3AF; width:32px; text-align:right; flex-shrink:0">{weight}%</div>
</div>"""

    total = sum(score * weight / 100 for _, score, weight, _ in layers)
    rows_html += f"""<div style="padding:12px 0 0; display:flex; justify-content:space-between; align-items:center">
  <div style="font-size:0.82rem; font-weight:600; color:#6B7280">합산 기여 점수</div>
  <div style="font-size:1.2rem; font-weight:800; color:#1D4ED8">{total:.1f}점</div>
</div>"""
    st.markdown(rows_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  매도 신호 게이지 차트
# ══════════════════════════════════════════════════════════════════════════════

def sell_gauge_chart(score: float, signal: str, color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode  = "gauge+number",
        value = score,
        title = {
            "text": "Sell Signal Score",
            "font": {"size": 14, "color": "#6B7280", "family": "Inter, sans-serif"},
        },
        gauge = {
            "axis"      : {
                "range"    : [0, 100],
                "tickwidth": 1,
                "tickcolor": "#E5E7EB",
                "tickfont" : {"size": 11, "color": "#9CA3AF"},
            },
            "bar"       : {"color": color, "thickness": 0.28},
            "bgcolor"   : "white",
            "borderwidth": 0,
            "steps"     : [
                {"range": [0,   40], "color": "#F0FDF4"},   # 보유 권장 (초록)
                {"range": [40,  55], "color": "#FFFBEB"},   # 중립 (노랑)
                {"range": [55,  75], "color": "#FFF7ED"},   # 매도 검토 (주황)
                {"range": [75, 100], "color": "#FEF2F2"},   # 강력 매도 (빨강)
            ],
            "threshold" : {
                "line"     : {"color": color, "width": 2},
                "thickness": 0.85,
                "value"    : score,
            },
        },
        number = {
            "font"   : {"size": 36, "color": color, "family": "Inter, sans-serif"},
            "suffix" : "점",
        },
    ))
    fig.update_layout(
        height        = 220,
        margin        = dict(t=35, b=5, l=20, r=20),
        paper_bgcolor = "rgba(0,0,0,0)",
        font          = FONT,
        annotations   = [dict(
            text      = re.sub(r'[^\x00-\x7F\uAC00-\uD7A3\u3040-\u30FF\u4E00-\u9FFF ]', '', signal).strip(),
            x=0.5, y=-0.08,
            showarrow = False,
            font      = dict(size=12, color=color, family="Inter, sans-serif"),
        )],
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  투자자별 매매동향 차트 (KIS 데이터)
# ══════════════════════════════════════════════════════════════════════════════

def investor_flow_chart(inv_df: pd.DataFrame) -> go.Figure:
    """기관/외국인/개인 순매수 바 차트."""
    fig = go.Figure()

    dates = inv_df["date"].dt.strftime("%m/%d")

    fig.add_trace(go.Bar(
        x=dates, y=inv_df["외국인_순매수"],
        name="외국인", marker_color=C_PRIMARY,
    ))
    fig.add_trace(go.Bar(
        x=dates, y=inv_df["기관_순매수"],
        name="기관", marker_color=C_PURPLE,
    ))
    fig.add_trace(go.Bar(
        x=dates, y=inv_df["개인_순매수"],
        name="개인", marker_color="#9CA3AF",
    ))

    fig.update_layout(
        title=dict(
            text="<b>투자자별 매매동향</b> (최근 일별)",
            font=dict(size=13, color=C_TEXT), x=0,
        ),
        barmode="group",
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor =C_PLOT_BG,
        font=FONT,
        legend=dict(
            orientation="h", y=1.08, x=0,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(t=42, b=10, l=10, r=10),
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor=C_GRID, tickfont=dict(size=10, color="#9CA3AF"))
    fig.update_yaxes(gridcolor=C_GRID, tickfont=dict(size=10, color="#9CA3AF"))
    fig.add_hline(y=0, line_width=1.5, line_color="#374151", line_dash="solid")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  하위 호환성 — 구 함수명 → 신 함수명 alias
# ══════════════════════════════════════════════════════════════════════════════

def gauge_chart(score, signal, color):
    return gauge_chart_modern(score, signal, color)

def candlestick_chart(price_df, ticker):
    return candlestick_chart_modern(price_df, ticker)

def rsi_chart(price_df):
    return rsi_chart_modern(price_df)

def radar_chart(result):
    return radar_chart_modern(result)

def risk_card(risk: dict, currency: str = "USD") -> None:
    """하위 호환용 — app.py에서 직접 HTML로 렌더링하므로 no-op."""
    pass

def layer_score_table(result: dict) -> None:
    """하위 호환용 — layer_score_bar로 대체."""
    layer_score_bar(result)
