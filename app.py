# app.py  ─  1억 만들기 프로그램
"""
1억 만들기  ─  AI 주식 매수/매도 추천 프로그램
실행: streamlit run app.py
"""

from __future__ import annotations
import streamlit as st

# ── 페이지 설정 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="1억 만들기",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
#  Boltshift 스타일 전역 CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  /* ── 글로벌: 라벤더 그라디언트 배경 ── */
  .stApp {
    background: linear-gradient(160deg, #E8E0F0 0%, #D5E8F0 35%, #E0EDE8 65%, #F0E8E0 100%) !important;
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
  }
  #MainMenu, footer, header { visibility: hidden !important; height: 0 !important; }
  .block-container { padding: 1rem 2rem 2rem 2rem !important; max-width: 1440px; }
  div[data-testid="stHeader"],
  div[data-testid="stToolbar"],
  div[data-testid="stDecoration"],
  .stDeployButton { display: none !important; }

  /* ── 상단 네비게이션 바 (글래스) ── */
  .top-nav {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.5);
    border-radius: 20px; padding: 14px 24px; margin-bottom: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    display: flex; align-items: center; justify-content: space-between;
  }
  .nav-logo { display: flex; align-items: center; gap: 10px; font-size: 1.15rem; font-weight: 800; color: #1E293B; text-decoration: none; }
  .nav-logo-icon {
    background: linear-gradient(135deg, #14B8A6, #0D9488);
    color: white; border-radius: 12px; width: 38px; height: 38px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem; box-shadow: 0 3px 12px rgba(20,184,166,0.4);
  }
  .nav-links { display: flex; gap: 4px; }
  .nav-link { padding: 7px 18px; border-radius: 22px; font-size: 0.84rem; font-weight: 500; color: #64748B; cursor: pointer; }
  .nav-link.active { background: #1E293B; color: white; }
  .nav-right { display: flex; align-items: center; gap: 12px; }
  .nav-avatar { width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #14B8A6, #0EA5E9); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 0.85rem; }
  .nav-user-name { font-size: 0.85rem; font-weight: 600; color: #1E293B; }
  .nav-user-sub  { font-size: 0.73rem; color: #94A3B8; }

  /* ── 글래스 카드 (핵심) ── */
  .glass {
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.6);
    border-radius: 20px; padding: 22px 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.05);
    margin-bottom: 14px;
    transition: box-shadow .2s, transform .2s;
  }
  .glass:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.09); transform: translateY(-2px); }

  /* ── 대형 피처드 카드 (상단 2열) ── */
  .featured {
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.7);
    border-radius: 24px; padding: 24px 28px;
    box-shadow: 0 6px 30px rgba(0,0,0,0.07);
    position: relative; overflow: hidden;
  }
  .featured-thumb {
    width: 80px; height: 80px; border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem; flex-shrink: 0;
  }

  /* ── 4열 그리드 종목 카드 ── */
  .stock-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 16px; }
  @media (max-width: 1024px) { .stock-grid { grid-template-columns: repeat(2, 1fr); } }
  .stock-card {
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.6);
    border-radius: 18px; padding: 18px 20px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.04);
    transition: all .2s;
  }
  .stock-card:hover { box-shadow: 0 6px 28px rgba(0,0,0,0.09); transform: translateY(-2px); }
  .stock-card-alert { border: 1.5px solid rgba(239,68,68,0.3); }
  .stock-thumb {
    width: 44px; height: 44px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; flex-shrink: 0;
  }

  /* ── 진행률 바 (세그먼트) ── */
  .prog-bar { display: flex; gap: 3px; margin-top: 8px; }
  .prog-seg { height: 6px; border-radius: 3px; flex: 1; }

  /* ── 상태 도트 ── */
  .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .dot-green { background: #14B8A6; }
  .dot-red   { background: #EF4444; }
  .dot-yellow{ background: #F59E0B; }

  /* ── KPI 카드 (분석 결과용) ── */
  .kpi-row { display: grid; grid-template-columns: 1.3fr 1fr 1fr 1fr; gap: 14px; margin-bottom: 16px; }
  .kpi-card { background: rgba(255,255,255,0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.6); border-radius: 18px; padding: 20px 22px; position: relative; overflow: hidden; }
  .kpi-card:hover { box-shadow: 0 6px 24px rgba(0,0,0,0.08); }
  .kpi-card-primary { background: linear-gradient(135deg, #14B8A6 0%, #0D9488 100%); border: none; }
  .kpi-label { font-size: 0.8rem; font-weight: 500; color: #64748B; margin-bottom: 6px; }
  .kpi-label-primary { color: rgba(255,255,255,0.8); }
  .kpi-value { font-size: 2rem; font-weight: 800; color: #1E293B; line-height: 1.1; }
  .kpi-value-primary { color: white; }
  .kpi-sub { font-size: 0.76rem; color: #94A3B8; margin-top: 4px; }
  .kpi-sub-primary { color: rgba(255,255,255,0.65); }
  .kpi-badge { display: inline-flex; align-items: center; gap: 3px; padding: 3px 9px; border-radius: 20px; font-size: 0.74rem; font-weight: 600; margin-top: 8px; }
  .badge-up   { background: #CCFBF1; color: #0D9488; }
  .badge-down { background: #FEE2E2; color: #DC2626; }
  .badge-neutral { background: rgba(0,0,0,0.05); color: #64748B; }
  .badge-up-light { background: rgba(255,255,255,0.25); color: white; }
  .kpi-icon { position: absolute; right: 16px; top: 50%; transform: translateY(-50%); width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; }
  .kpi-icon-white { background: rgba(255,255,255,0.2); }
  .kpi-icon-blue  { background: rgba(14,165,233,0.1); }
  .kpi-icon-green { background: rgba(20,184,166,0.1); }
  .kpi-icon-orange{ background: rgba(245,158,11,0.1); }

  /* ── 섹션 카드 (분석 결과) ── */
  .section-card { background: rgba(255,255,255,0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.6); border-radius: 20px; padding: 22px 24px; box-shadow: 0 2px 16px rgba(0,0,0,0.04); margin-bottom: 14px; }
  .section-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
  .section-title { font-size: 1rem; font-weight: 700; color: #1E293B; }
  .section-sub   { font-size: 0.76rem; color: #94A3B8; margin-top: 2px; }
  .section-badge { background: rgba(0,0,0,0.04); color: #64748B; border-radius: 20px; padding: 5px 14px; font-size: 0.76rem; font-weight: 500; }

  /* ── AI 코멘트 ── */
  .ai-box { background: rgba(14,165,233,0.06); border: 1px solid rgba(14,165,233,0.15); border-radius: 14px; padding: 18px 20px; font-size: 0.85rem; line-height: 1.75; color: #334155; }
  .ai-box strong { color: #0D9488; }
  .risk-tag { display: inline-block; background: #FEF2F2; border: 1px solid #FECACA; color: #DC2626; border-radius: 20px; padding: 3px 12px; font-size: 0.76rem; font-weight: 500; margin: 3px 3px 3px 0; }

  /* ── 리스크 카드 ── */
  .risk-card { background: rgba(255,255,255,0.5); border: 1px solid rgba(255,255,255,0.6); border-radius: 14px; padding: 16px 20px; text-align: center; }
  .risk-label  { font-size: 0.76rem; font-weight: 500; color: #64748B; margin-bottom: 4px; }
  .risk-value  { font-size: 1.4rem; font-weight: 800; color: #0D9488; }
  .risk-delta  { font-size: 0.78rem; font-weight: 600; margin-top: 4px; }

  /* ── Streamlit overrides ── */
  div[data-testid="metric-container"] { background: transparent !important; border: none !important; padding: 0 !important; }
  .stButton > button {
    background: linear-gradient(135deg, #14B8A6, #0D9488) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important; font-weight: 600 !important;
    padding: 10px 22px !important; font-size: 0.86rem !important;
    box-shadow: 0 3px 12px rgba(20,184,166,0.35) !important;
  }
  .stButton > button:hover { box-shadow: 0 6px 20px rgba(20,184,166,0.5) !important; transform: translateY(-1px) !important; }
  .stTextInput > div > div > input {
    border-radius: 12px !important; border: 1.5px solid rgba(255,255,255,0.7) !important;
    background: rgba(255,255,255,0.6) !important; color: #1E293B !important;
    backdrop-filter: blur(8px) !important; font-size: 0.9rem !important; padding: 10px 14px !important;
  }
  .stTextInput > div > div > input:focus { border-color: #14B8A6 !important; box-shadow: 0 0 0 3px rgba(20,184,166,0.15) !important; }
  div[data-testid="stExpander"] { background: rgba(255,255,255,0.5); border-radius: 14px; border: 1px solid rgba(255,255,255,0.5) !important; }
  div[data-testid="stExpander"] summary { color: #334155 !important; font-weight: 600 !important; }
  .stDataFrame { border-radius: 14px !important; overflow: hidden !important; }
  .stAlert { border-radius: 14px !important; }
  div[data-testid="stSidebar"] { background: rgba(255,255,255,0.7) !important; backdrop-filter: blur(12px) !important; }
</style>
""", unsafe_allow_html=True)

import traceback
from engine.data_loader    import load_all
from engine.ai_analyzer    import analyze_sentiment
from engine.strategy       import run_full_analysis
from engine.kis_api        import is_korean_stock, check_api_status
from engine.market_heatmap import scan_index, get_top_picks, create_treemap
from engine.market_overview import fetch_market_overview
from engine.theme_analyzer  import analyze_market_themes
from engine.daily_briefing  import get_daily_briefing
from engine.backtester      import run_backtest, backtest_chart
from engine.earnings_calendar import get_upcoming_earnings, get_earnings_surprise
from engine.insider_tracker import insider_signal
from engine.pattern_detector import detect_patterns, pattern_chart
from engine.sector_rotation import analyze_sector_rotation, rotation_chart
from config import GEMINI_API_KEY
from ui.components         import (
    gauge_chart_modern, candlestick_chart_modern, rsi_chart_modern,
    radar_chart_modern, layer_score_bar, investor_flow_chart,
    sell_gauge_chart,
)


# ══════════════════════════════════════════════════════════════════════════════
#  상단 네비게이션 바
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="top-nav">
  <a class="nav-logo">
    <div class="nav-logo-icon">💰</div>
    <span>1억 만들기</span>
  </a>
  <div class="nav-links">
    <div class="nav-link active">Dashboard</div>
    <div class="nav-link">Heatmap</div>
    <div class="nav-link">Briefing</div>
    <div class="nav-link">Tools</div>
  </div>
  <div class="nav-right">
    <div style="font-size:0.72rem; color:#94A3B8; text-align:right">
      <b style="color:#0D9488">매수:</b> 관망→선발대→본부대→몰빵<br>
      <b style="color:#EF4444">매도:</b> 관망→일부분→강력→무조건
    </div>
    <div class="nav-avatar">AI</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  페이지 선택 라디오 (탭 대신)
# ══════════════════════════════════════════════════════════════════════════════

page_mode = st.radio(
    "📌 메뉴",
    ["📈 종목 분석 (Dashboard)", "🗺️ 시장 히트맵 & 추천", "📋 데일리 브리핑", "🛠️ 투자 도구"],
    horizontal=True,
    key="page_radio",
    label_visibility="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
#  페이지 2: 시장 히트맵 (Finviz) & AI 추천
# ══════════════════════════════════════════════════════════════════════════════

elif page_mode == "🗺️ 시장 히트맵 & 추천":
    st.markdown("""<div class="section-card" style="padding:14px 20px">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px">
    <div class="section-title" style="margin:0; font-size:1.15rem">🗺️ Market Heatmap & AI Recommendations</div>
    <div style="font-size:0.76rem; color:#6B7280">
      <b style="color:#16A34A">매수:</b> ⚪관망→🟡선발대→🟠본부대→🔴몰빵 &nbsp;|&nbsp;
      <b style="color:#DC2626">매도:</b> ⚪관망→🟡일부분→🟠강력→🔴무조건
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    hm_choice = st.selectbox("지수 선택", ["S&P 500", "Russell 2000", "KOSPI 100"], key="hm_sel")
    idx_map = {"S&P 500": "sp500", "Russell 2000": "russell2000", "KOSPI 100": "kospi100"}

    # ── 스캔 버튼 ─────────────────────────────────────────────────────
    scan_btn = st.button("🔍 AI 종목 스캔 + 히트맵 생성", use_container_width=True, key="scan_go")

    if scan_btn:
        with st.spinner(f"📡 {hm_choice} 종목 분석 중... (30초~1분)"):
            scan_df = scan_index(idx_map[hm_choice])

        if scan_df.empty:
            st.warning("데이터를 가져오지 못했습니다.")
        else:
            # ── Plotly 히트맵 (트리맵) ────────────────────────────────
            st.plotly_chart(
                create_treemap(scan_df, f"{hm_choice} — 1개월 수익률 히트맵 (매수/매도 기준 포함)"),
                use_container_width=True,
            )

            picks = get_top_picks(scan_df, n=7)

            c_buy, c_sell = st.columns(2)
            with c_buy:
                st.markdown("""<div class="section-card" style="border-left:4px solid #16A34A; padding:14px 18px">
  <div class="section-title" style="color:#16A34A">🟢 매수 추천 (선발대~몰빵)</div>
</div>""", unsafe_allow_html=True)
                if picks["buy"]:
                    for i, b in enumerate(picks["buy"], 1):
                        lbl = b.get("buy_label", "")
                        reasons = " · ".join(b.get("buy_reasons", [])[:2]) or "저점 매수 신호"
                        lbl_co = "#DC2626" if "몰빵" in lbl else "#F97316" if "본부대" in lbl else "#EAB308"
                        st.markdown(f"""<div style="background:white; border-radius:10px; padding:10px 14px; margin-bottom:5px; box-shadow:0 1px 2px rgba(0,0,0,0.04)">
  <div style="display:flex; justify-content:space-between; align-items:center">
    <b style="font-size:0.86rem">{i}. {b['name']} <span style="color:#9CA3AF; font-weight:400">{b['ticker']}</span></b>
    <span style="color:{lbl_co}; font-weight:700; font-size:0.78rem">{lbl}</span>
  </div>
  <div style="font-size:0.75rem; color:#6B7280; margin-top:3px">RSI {b['rsi']:.0f} · {b['ret_1m']:+.1f}%(1M) · {b['ret_5d']:+.1f}%(5D) · Vol {b['vol_ratio']:.1f}x</div>
  <div style="font-size:0.73rem; color:#16A34A; margin-top:2px">💡 {reasons}</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.info("매수 추천 종목 없음")

            with c_sell:
                st.markdown("""<div class="section-card" style="border-left:4px solid #DC2626; padding:14px 18px">
  <div class="section-title" style="color:#DC2626">🔴 매도 추천 (일부분~무조건)</div>
</div>""", unsafe_allow_html=True)
                if picks["sell"]:
                    for i, s in enumerate(picks["sell"], 1):
                        lbl = s.get("sell_label", "")
                        reasons = " · ".join(s.get("sell_reasons", [])[:2]) or "매도 주의"
                        lbl_co = "#DC2626" if "무조건" in lbl else "#F97316" if "강력" in lbl else "#EAB308"
                        st.markdown(f"""<div style="background:white; border-radius:10px; padding:10px 14px; margin-bottom:5px; box-shadow:0 1px 2px rgba(0,0,0,0.04)">
  <div style="display:flex; justify-content:space-between; align-items:center">
    <b style="font-size:0.86rem">{i}. {s['name']} <span style="color:#9CA3AF; font-weight:400">{s['ticker']}</span></b>
    <span style="color:{lbl_co}; font-weight:700; font-size:0.78rem">{lbl}</span>
  </div>
  <div style="font-size:0.75rem; color:#6B7280; margin-top:3px">RSI {s['rsi']:.0f} · {s['ret_1m']:+.1f}%(1M) · {s['ret_5d']:+.1f}%(5D) · Vol {s['vol_ratio']:.1f}x</div>
  <div style="font-size:0.73rem; color:#DC2626; margin-top:2px">⚠ {reasons}</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.info("매도 추천 종목 없음")

            # ── 전체 종목 테이블 ──────────────────────────────────────
            with st.expander(f"📋 전체 {len(scan_df)}개 종목 데이터"):
                show_cols = [c for c in ["ticker","name","price","ret_1d","ret_5d","ret_1m","rsi","vol_ratio","buy_label","sell_label"] if c in scan_df.columns]
                st.dataframe(scan_df[show_cols], use_container_width=True, hide_index=True, height=400)


# ══════════════════════════════════════════════════════════════════════════════
#  페이지 3: 데일리 브리핑
# ══════════════════════════════════════════════════════════════════════════════

elif page_mode == "📋 데일리 브리핑":
    st.markdown("""<div class="section-card" style="padding:14px 20px">
  <div class="section-title" style="margin:0; font-size:1.15rem">📋 데일리 마켓 브리핑 — 미국/한국 지수 분석</div>
  <div class="section-sub" style="margin-top:4px">Gemini AI가 분석하는 오늘의 시장 동향, 상승/하락 이유, 내일 전망</div>
</div>""", unsafe_allow_html=True)

    with st.spinner("📡 지수 데이터 수집 + AI 분석 중... (15~30초)"):
        briefing = get_daily_briefing()

    # 지수 카드
    idx = briefing.get("indices", {})
    if idx:
        idx_items = list(idx.items())
        cols = st.columns(min(len(idx_items), 5))
        for col, (name, d) in zip(cols, idx_items[:5]):
            chg = d.get("chg_pct", 0)
            c = "#16A34A" if chg > 0 else "#EF4444" if chg < 0 else "#64748B"
            arrow = "▲" if chg > 0 else "▼" if chg < 0 else "─"
            col.markdown(f"""<div class="glass" style="padding:12px 14px; text-align:center">
  <div style="font-size:0.7rem; color:#94A3B8">{name}</div>
  <div style="font-size:1.1rem; font-weight:800; color:#1E293B">{d.get('price', 0):,.2f}</div>
  <div style="font-size:0.78rem; font-weight:700; color:{c}">{arrow} {chg:+.2f}%</div>
</div>""", unsafe_allow_html=True)

        # 나머지 지수
        if len(idx_items) > 5:
            cols2 = st.columns(min(len(idx_items) - 5, 5))
            for col, (name, d) in zip(cols2, idx_items[5:]):
                chg = d.get("chg_pct", 0)
                c = "#16A34A" if chg > 0 else "#EF4444" if chg < 0 else "#64748B"
                arrow = "▲" if chg > 0 else "▼" if chg < 0 else "─"
                col.markdown(f"""<div class="glass" style="padding:12px 14px; text-align:center">
  <div style="font-size:0.7rem; color:#94A3B8">{name}</div>
  <div style="font-size:1.1rem; font-weight:800; color:#1E293B">{d.get('price', 0):,.2f}</div>
  <div style="font-size:0.78rem; font-weight:700; color:{c}">{arrow} {chg:+.2f}%</div>
</div>""", unsafe_allow_html=True)

    # 미국 시장 분석
    st.markdown(f"""<div class="glass" style="padding:18px 22px; border-left:4px solid #3B82F6">
  <div style="font-size:0.95rem; font-weight:800; color:#1E293B; margin-bottom:8px">🇺🇸 미국 시장 분석</div>
  <div style="font-size:0.88rem; color:#334155; line-height:1.8">{briefing.get('us_analysis', '분석 데이터 없음')}</div>
</div>""", unsafe_allow_html=True)

    # 한국 시장 분석
    st.markdown(f"""<div class="glass" style="padding:18px 22px; border-left:4px solid #EF4444">
  <div style="font-size:0.95rem; font-weight:800; color:#1E293B; margin-bottom:8px">🇰🇷 한국 시장 분석</div>
  <div style="font-size:0.88rem; color:#334155; line-height:1.8">{briefing.get('kr_analysis', '분석 데이터 없음')}</div>
</div>""", unsafe_allow_html=True)

    # 주요 이벤트
    events = briefing.get("key_events", [])
    if events:
        ev_html = '<div class="glass" style="padding:18px 22px"><div style="font-size:0.95rem; font-weight:800; color:#1E293B; margin-bottom:10px">🔑 주요 이벤트</div>'
        for i, ev in enumerate(events, 1):
            ev_html += f'<div style="font-size:0.85rem; color:#334155; padding:6px 0; border-bottom:1px solid rgba(0,0,0,0.04)">  {i}. {ev}</div>'
        ev_html += '</div>'
        st.markdown(ev_html, unsafe_allow_html=True)

    # 내일 전망
    st.markdown(f"""<div class="glass" style="padding:18px 22px; border-left:4px solid #14B8A6">
  <div style="font-size:0.95rem; font-weight:800; color:#1E293B; margin-bottom:8px">🔮 내일 전망</div>
  <div style="font-size:0.88rem; color:#334155; line-height:1.8">{briefing.get('tomorrow_outlook', '전망 데이터 없음')}</div>
</div>""", unsafe_allow_html=True)

    # 한국어 번역 뉴스
    news_list = briefing.get("news", [])
    if news_list and any(n.get("title_kr") for n in news_list):
        news_html = '<div class="glass" style="padding:18px 22px"><div style="font-size:0.95rem; font-weight:800; color:#1E293B; margin-bottom:10px">📰 주요 뉴스 (한국어 번역)</div>'
        for n in news_list:
            title_kr = n.get("title_kr") or n.get("title", "")
            src = n.get("source", "")
            news_html += f'<div style="font-size:0.83rem; color:#334155; padding:6px 0; border-bottom:1px solid rgba(0,0,0,0.04)"><span style="background:rgba(59,130,246,0.1); color:#3B82F6; padding:1px 7px; border-radius:6px; font-size:0.72rem; font-weight:600; margin-right:6px">{src}</span>{title_kr}</div>'
        news_html += '</div>'
        st.markdown(news_html, unsafe_allow_html=True)

    api_badge = "🤖 Claude AI 분석" if briefing.get("api_used") else "📊 규칙 기반 분석 (API 미사용)"
    st.markdown(f'<div style="text-align:right; font-size:0.72rem; color:#94A3B8; margin-top:4px">{api_badge} · {briefing.get("timestamp", "")[:19]}</div>', unsafe_allow_html=True)

    # ── 섹터 로테이션 (브리핑 페이지 하단에 배치) ──
    st.markdown("---")
    st.markdown("""<div class="section-card" style="padding:14px 20px">
  <div class="section-title" style="margin:0; font-size:1.05rem">🔄 섹터 로테이션 전략</div>
  <div class="section-sub" style="margin-top:4px">11개 S&P 섹터 ETF의 모멘텀 분석 — 1주/1개월/3개월 수익률 기반</div>
</div>""", unsafe_allow_html=True)

    with st.spinner("📡 섹터 ETF 데이터 분석 중..."):
        rot_data = analyze_sector_rotation()
        rot_fig = rotation_chart()

    # 로테이션 페이즈 + 시그널
    phase = rot_data.get("phase", "Unknown")
    phase_desc = rot_data.get("phase_description", "")
    rot_signal = rot_data.get("rotation_signal", "")

    phase_colors = {"Early Bull": "#16A34A", "Late Bull": "#F59E0B", "Early Bear": "#EF4444", "Late Bear": "#DC2626", "Transition": "#6B7280"}
    p_color = phase_colors.get(phase, "#6B7280")

    st.markdown(f"""<div class="glass" style="padding:16px 20px">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px">
    <div>
      <span style="font-size:1.1rem; font-weight:800; color:{p_color}">📍 {phase}</span>
      <div style="font-size:0.82rem; color:#64748B; margin-top:4px">{phase_desc}</div>
    </div>
    <div style="background:rgba(20,184,166,0.1); color:#0D9488; padding:6px 14px; border-radius:12px; font-size:0.8rem; font-weight:600; max-width:300px; text-align:right">
      💡 {rot_signal}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    st.plotly_chart(rot_fig, use_container_width=True)

    # 매수/매도 추천 섹터
    buy_secs = rot_data.get("buy_sectors", [])
    sell_secs = rot_data.get("sell_sectors", [])
    if buy_secs or sell_secs:
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown('<div class="glass" style="border-left:4px solid #16A34A; padding:14px 18px"><b style="color:#16A34A">🟢 매수 추천 섹터</b></div>', unsafe_allow_html=True)
            for s in buy_secs:
                st.markdown(f'<div style="background:white; border-radius:8px; padding:8px 12px; margin-bottom:4px; font-size:0.85rem"><b>{s["ticker"]}</b> ({s["name"]}) — 모멘텀 {s.get("momentum_score",0):+.2f} · 1M {s.get("return_1m",0):+.1f}%</div>', unsafe_allow_html=True)
            if not buy_secs:
                st.info("현재 매수 추천 섹터 없음")
        with rc2:
            st.markdown('<div class="glass" style="border-left:4px solid #EF4444; padding:14px 18px"><b style="color:#EF4444">🔴 매도/축소 섹터</b></div>', unsafe_allow_html=True)
            for s in sell_secs:
                st.markdown(f'<div style="background:white; border-radius:8px; padding:8px 12px; margin-bottom:4px; font-size:0.85rem"><b>{s["ticker"]}</b> ({s["name"]}) — 모멘텀 {s.get("momentum_score",0):+.2f} · 1M {s.get("return_1m",0):+.1f}%</div>', unsafe_allow_html=True)
            if not sell_secs:
                st.info("현재 매도 추천 섹터 없음")

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  페이지 4: 투자 도구 (백테스팅, 실적캘린더, 내부자, 차트패턴)
# ══════════════════════════════════════════════════════════════════════════════

elif page_mode == "🛠️ 투자 도구":
    st.markdown("""<div class="section-card" style="padding:14px 20px">
  <div class="section-title" style="margin:0; font-size:1.15rem">🛠️ 투자 도구 모음</div>
  <div class="section-sub" style="margin-top:4px">백테스팅 · 실적 캘린더 · 내부자 거래 · 차트 패턴 분석</div>
</div>""", unsafe_allow_html=True)

    tool_tab = st.radio(
        "도구 선택",
        ["📊 백테스팅", "📅 실적 캘린더", "🕵️ 내부자 거래", "📐 차트 패턴"],
        horizontal=True,
        key="tool_radio",
        label_visibility="collapsed",
    )

    # ─────────────────────────────────────────────────────────────────
    #  백테스팅
    # ─────────────────────────────────────────────────────────────────
    if tool_tab == "📊 백테스팅":
        st.markdown("""<div class="glass" style="padding:14px 18px">
  <div style="font-size:0.95rem; font-weight:700; color:#1E293B">📊 Golden Bottom Score 백테스팅</div>
  <div style="font-size:0.8rem; color:#64748B; margin-top:4px">RSI 과매도 + 볼린저밴드 하단 돌파 시 매수 → RSI 과매수 또는 목표수익 도달 시 매도</div>
</div>""", unsafe_allow_html=True)

        bt_c1, bt_c2, bt_c3 = st.columns([2, 1, 1])
        with bt_c1:
            bt_ticker = st.text_input("종목 티커", value="AAPL", key="bt_ticker").strip().upper()
        with bt_c2:
            bt_years = st.selectbox("테스트 기간", [1, 2, 3, 5], index=2, key="bt_years")
        with bt_c3:
            bt_target = st.number_input("목표수익(%)", value=15.0, step=1.0, key="bt_target")

        if st.button("🚀 백테스트 실행", key="bt_run", use_container_width=True):
            with st.spinner(f"📡 {bt_ticker} {bt_years}년 백테스트 실행 중..."):
                bt_result = run_backtest(bt_ticker, lookback_years=bt_years, profit_target_pct=bt_target)

            trades = bt_result.get("trades", [])
            summary = bt_result.get("summary", {})

            if not trades:
                st.warning(f"⚠️ {bt_ticker}에 대한 매수 신호가 발생하지 않았습니다.")
            else:
                # 요약 KPI
                win_c = "#16A34A" if summary.get("win_rate", 0) >= 50 else "#EF4444"
                ret_c = "#16A34A" if summary.get("total_return_pct", 0) >= 0 else "#EF4444"
                st.markdown(f"""<div style="display:grid; grid-template-columns:repeat(5,1fr); gap:10px; margin:12px 0">
  <div class="glass" style="padding:12px; text-align:center">
    <div style="font-size:0.72rem; color:#94A3B8">총 거래수</div>
    <div style="font-size:1.4rem; font-weight:800; color:#1E293B">{summary.get('total_trades',0)}</div>
  </div>
  <div class="glass" style="padding:12px; text-align:center">
    <div style="font-size:0.72rem; color:#94A3B8">승률</div>
    <div style="font-size:1.4rem; font-weight:800; color:{win_c}">{summary.get('win_rate',0):.1f}%</div>
  </div>
  <div class="glass" style="padding:12px; text-align:center">
    <div style="font-size:0.72rem; color:#94A3B8">총 수익률</div>
    <div style="font-size:1.4rem; font-weight:800; color:{ret_c}">{summary.get('total_return_pct',0):+.2f}%</div>
  </div>
  <div class="glass" style="padding:12px; text-align:center">
    <div style="font-size:0.72rem; color:#94A3B8">최대 낙폭</div>
    <div style="font-size:1.4rem; font-weight:800; color:#EF4444">-{summary.get('max_drawdown_pct',0):.2f}%</div>
  </div>
  <div class="glass" style="padding:12px; text-align:center">
    <div style="font-size:0.72rem; color:#94A3B8">샤프 비율</div>
    <div style="font-size:1.4rem; font-weight:800; color:#3B82F6">{summary.get('sharpe_ratio',0):.2f}</div>
  </div>
</div>""", unsafe_allow_html=True)

                # 차트
                fig = backtest_chart(trades, bt_result.get("price_df"), bt_ticker)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

                # 거래 내역 테이블
                with st.expander(f"📋 전체 거래 내역 ({len(trades)}건)"):
                    import pandas as pd
                    trades_df = pd.DataFrame(trades)
                    st.dataframe(trades_df, use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────────
    #  실적 캘린더
    # ─────────────────────────────────────────────────────────────────
    elif tool_tab == "📅 실적 캘린더":
        st.markdown("""<div class="glass" style="padding:14px 18px">
  <div style="font-size:0.95rem; font-weight:700; color:#1E293B">📅 실적 캘린더 & 어닝 서프라이즈</div>
  <div style="font-size:0.8rem; color:#64748B; margin-top:4px">주요 종목의 실적 발표 일정 + 과거 어닝 서프라이즈 분석</div>
</div>""", unsafe_allow_html=True)

        ec_days = st.slider("조회 기간 (일)", 7, 60, 14, key="ec_days")

        if st.button("📡 실적 캘린더 조회", key="ec_run", use_container_width=True):
            with st.spinner("📡 실적 일정 수집 중..."):
                upcoming = get_upcoming_earnings(days_ahead=ec_days)

            found = upcoming.get("upcoming", [])
            st.markdown(f"""<div class="glass" style="padding:12px 18px">
  <div style="font-size:0.85rem; color:#64748B">
    조회 기간: {upcoming.get('window_start','')} ~ {upcoming.get('window_end','')} ·
    확인 종목: {upcoming.get('checked_tickers',0)}개 ·
    발표 예정: <b style="color:#1E293B">{upcoming.get('found_earnings',0)}개</b>
  </div>
</div>""", unsafe_allow_html=True)

            if found:
                for entry in found:
                    days_until = entry.get("days_until", 0)
                    urgency_c = "#EF4444" if days_until <= 3 else "#F59E0B" if days_until <= 7 else "#64748B"
                    flag = "🇰🇷" if entry.get("is_korean") else "🇺🇸"
                    st.markdown(f"""<div class="glass" style="padding:12px 16px; display:flex; justify-content:space-between; align-items:center">
  <div>
    <span style="font-size:1rem">{flag}</span>
    <b style="font-size:0.9rem; margin-left:6px">{entry.get('ticker','')}</b>
    <span style="font-size:0.82rem; color:#64748B; margin-left:4px">({entry.get('company','')})</span>
  </div>
  <div style="text-align:right">
    <div style="font-size:0.82rem; font-weight:700; color:{urgency_c}">D-{days_until}</div>
    <div style="font-size:0.72rem; color:#94A3B8">{entry.get('earnings_date','')}</div>
  </div>
</div>""", unsafe_allow_html=True)

                # 어닝 서프라이즈 (첫번째 종목)
                st.markdown("---")
                es_ticker = st.selectbox("어닝 서프라이즈 조회", [e["ticker"] for e in found], key="es_sel")
                if st.button("🔍 서프라이즈 분석", key="es_run"):
                    with st.spinner(f"{es_ticker} 어닝 서프라이즈 분석 중..."):
                        surprise = get_earnings_surprise(es_ticker)

                    st.markdown(f"""<div class="glass" style="padding:14px 18px">
  <div style="font-size:0.92rem; font-weight:700; color:#1E293B">{surprise.get('ticker','')} ({surprise.get('company','')}) — 어닝 서프라이즈</div>
  <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-top:10px">
    <div style="text-align:center; padding:10px; background:#F8FAFF; border-radius:10px">
      <div style="font-size:0.72rem; color:#94A3B8">분석 분기수</div>
      <div style="font-size:1.3rem; font-weight:800; color:#1E293B">{surprise.get('total_quarters',0)}</div>
    </div>
    <div style="text-align:center; padding:10px; background:#F0FDF4; border-radius:10px">
      <div style="font-size:0.72rem; color:#94A3B8">Beat Rate</div>
      <div style="font-size:1.3rem; font-weight:800; color:#16A34A">{surprise.get('beat_rate','N/A')}{'%' if surprise.get('beat_rate') is not None else ''}</div>
    </div>
    <div style="text-align:center; padding:10px; background:#EFF6FF; border-radius:10px">
      <div style="font-size:0.72rem; color:#94A3B8">평균 서프라이즈</div>
      <div style="font-size:1.3rem; font-weight:800; color:#3B82F6">{f"{surprise.get('avg_surprise_pct'):+.2f}%" if surprise.get('avg_surprise_pct') is not None else 'N/A'}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

                    hist = surprise.get("history", [])
                    if hist:
                        import pandas as pd
                        hist_df = pd.DataFrame(hist)
                        st.dataframe(hist_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"향후 {ec_days}일 내 실적 발표 예정 종목이 없습니다.")

    # ─────────────────────────────────────────────────────────────────
    #  내부자 거래
    # ─────────────────────────────────────────────────────────────────
    elif tool_tab == "🕵️ 내부자 거래":
        st.markdown("""<div class="glass" style="padding:14px 18px">
  <div style="font-size:0.95rem; font-weight:700; color:#1E293B">🕵️ 내부자 거래 추적</div>
  <div style="font-size:0.8rem; color:#64748B; margin-top:4px">최근 90일 내부자 매수/매도 활동 + 기관 보유 현황 → 투자 시그널</div>
</div>""", unsafe_allow_html=True)

        ins_ticker = st.text_input("종목 티커", value="AAPL", key="ins_ticker").strip().upper()

        if st.button("🔍 내부자 거래 분석", key="ins_run", use_container_width=True):
            with st.spinner(f"📡 {ins_ticker} 내부자/기관 데이터 수집 중..."):
                ins_data = insider_signal(ins_ticker)

            signal = ins_data.get("signal", "Neutral")
            sig_colors = {"Strong Buy": "#16A34A", "Buy": "#22C55E", "Neutral": "#6B7280", "Sell": "#F97316", "Weak Sell": "#EAB308", "Strong Sell": "#EF4444"}
            sig_c = sig_colors.get(signal, "#6B7280")

            st.markdown(f"""<div class="glass" style="padding:16px 20px; border-left:4px solid {sig_c}">
  <div style="display:flex; justify-content:space-between; align-items:center">
    <div>
      <div style="font-size:1.1rem; font-weight:800; color:#1E293B">{ins_ticker} — 내부자 시그널</div>
      <div style="font-size:0.82rem; color:#64748B; margin-top:4px">최근 90일: 매수 {ins_data.get('insider_buy_count',0)}건 · 매도 {ins_data.get('insider_sell_count',0)}건</div>
    </div>
    <div style="background:{sig_c}; color:white; padding:8px 18px; border-radius:12px; font-weight:800; font-size:0.95rem">{signal}</div>
  </div>
</div>""", unsafe_allow_html=True)

            # 시그널 근거
            reasons = ins_data.get("reasons", [])
            if reasons:
                for r in reasons:
                    st.markdown(f'<div style="font-size:0.85rem; color:#334155; padding:4px 0">• {r}</div>', unsafe_allow_html=True)

            # 최근 내부자 거래 테이블
            trades = ins_data.get("insider_trades", [])
            if trades:
                with st.expander(f"📋 내부자 거래 내역 ({len(trades)}건)"):
                    import pandas as pd
                    trades_df = pd.DataFrame(trades[:20])
                    st.dataframe(trades_df, use_container_width=True, hide_index=True)

            # 기관 보유 현황
            inst = ins_data.get("recent_institutional_holders", [])
            if inst:
                with st.expander(f"🏦 주요 기관 투자자 ({len(inst)}개)"):
                    import pandas as pd
                    inst_df = pd.DataFrame(inst)
                    st.dataframe(inst_df, use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────────
    #  차트 패턴
    # ─────────────────────────────────────────────────────────────────
    elif tool_tab == "📐 차트 패턴":
        st.markdown("""<div class="glass" style="padding:14px 18px">
  <div style="font-size:0.95rem; font-weight:700; color:#1E293B">📐 차트 패턴 자동 인식</div>
  <div style="font-size:0.8rem; color:#64748B; margin-top:4px">골든크로스 · 데스크로스 · 더블바텀/탑 · RSI 다이버전스 · 볼륨 클라이맥스 · 지지/저항선</div>
</div>""", unsafe_allow_html=True)

        cp_ticker = st.text_input("종목 티커", value="AAPL", key="cp_ticker").strip().upper()

        if st.button("🔍 패턴 분석", key="cp_run", use_container_width=True):
            with st.spinner(f"📡 {cp_ticker} 차트 패턴 분석 중..."):
                import yfinance as yf
                import pandas as pd
                try:
                    cp_df = yf.download(cp_ticker, period="1y", progress=False)
                    if isinstance(cp_df.columns, pd.MultiIndex):
                        cp_df.columns = cp_df.columns.get_level_values(0)
                except Exception as e:
                    st.error(f"데이터 로드 실패: {e}")
                    cp_df = pd.DataFrame()

            if cp_df.empty:
                st.warning(f"⚠️ {cp_ticker} 데이터를 가져올 수 없습니다.")
            else:
                patterns = detect_patterns(cp_df)

                if patterns:
                    bullish = [p for p in patterns if p["type"] == "bullish"]
                    bearish = [p for p in patterns if p["type"] == "bearish"]

                    st.markdown(f"""<div class="glass" style="padding:14px 18px">
  <div style="font-size:0.88rem; color:#64748B">
    감지된 패턴: <b style="color:#1E293B">{len(patterns)}개</b>
    (<span style="color:#16A34A">강세 {len(bullish)}</span> · <span style="color:#EF4444">약세 {len(bearish)}</span>)
  </div>
</div>""", unsafe_allow_html=True)

                    for p in patterns:
                        p_c = "#16A34A" if p["type"] == "bullish" else "#EF4444"
                        p_icon = "📈" if p["type"] == "bullish" else "📉"
                        conf_bg = "rgba(20,184,166,0.1)" if p["confidence"] >= 70 else "rgba(245,158,11,0.1)"
                        st.markdown(f"""<div class="glass" style="padding:12px 16px; border-left:3px solid {p_c}">
  <div style="display:flex; justify-content:space-between; align-items:center">
    <div>
      <span style="font-size:0.95rem; font-weight:700; color:{p_c}">{p_icon} {p['name']}</span>
      <span style="font-size:0.72rem; color:#94A3B8; margin-left:8px">{p.get('date','')}</span>
    </div>
    <div style="background:{conf_bg}; padding:3px 10px; border-radius:8px; font-size:0.76rem; font-weight:600; color:#1E293B">신뢰도 {p['confidence']}%</div>
  </div>
  <div style="font-size:0.82rem; color:#64748B; margin-top:4px">{p['description']}</div>
</div>""", unsafe_allow_html=True)

                    # 패턴 차트
                    fig = pattern_chart(cp_df, patterns)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"⚠️ {cp_ticker}에서 감지된 차트 패턴이 없습니다.")

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  페이지 1: 종목 분석 Dashboard
# ══════════════════════════════════════════════════════════════════════════════

else:  # 📈 종목 분석 (Dashboard)
    # ── 세션 상태 초기화 ──────────────────────────────────────────────────
    if "detail_stock" not in st.session_state:
        st.session_state.detail_stock = None
    if "mkt_cache" not in st.session_state:
        st.session_state.mkt_cache = None
    if "all_picks_cache" not in st.session_state:
        st.session_state.all_picks_cache = None
    if "theme_cache" not in st.session_state:
        st.session_state.theme_cache = None

    # ── 검색 바 ────────────────────────────────────────────────────────────
    col_search, col_btn, col_spacer = st.columns([3, 1, 4])
    with col_search:
        ticker_input = st.text_input(
            "종목 티커",
            value="AAPL",
            placeholder="예: AAPL, TSLA, 005930.KS",
            label_visibility="collapsed",
        ).strip().upper()
    with col_btn:
        run_btn = st.button("🔍  분석 시작", use_container_width=True)

    if not run_btn:
        # ── 헤더 ─────────────────────────────────────────────────────
        st.markdown("""<div style="margin-bottom:6px">
  <div style="font-size:0.78rem; color:#94A3B8">Dashboard</div>
  <div style="font-size:1.5rem; font-weight:800; color:#1E293B">💰 1억 만들기 — 오늘의 시장 & AI 추천</div>
</div>""", unsafe_allow_html=True)

        # ── 새로고침 버튼 ──────────────────────────────────────────────
        if st.button("🔄 시장 데이터 새로고침", key="refresh_dashboard"):
            st.session_state.mkt_cache = None
            st.session_state.all_picks_cache = None
            st.session_state.theme_cache = None
            # 세부 분석 캐시도 초기화
            for k in [k for k in st.session_state.keys() if k.startswith("detail_analysis_")]:
                del st.session_state[k]
            st.rerun()

        # ── 시장 흐름 분석 (캐시) ──────────────────────────────────────
        if st.session_state.mkt_cache is None:
            with st.spinner("📡 글로벌 시장 데이터 수집 중..."):
                st.session_state.mkt_cache = fetch_market_overview()
        mkt = st.session_state.mkt_cache

        # 시장 방향 + Fear & Greed
        fg = mkt["fear_score"]
        fg_color = "#EF4444" if fg <= 30 else "#F59E0B" if fg <= 50 else "#14B8A6" if fg <= 70 else "#16A34A"
        st.markdown(f"""<div class="glass" style="padding:18px 22px">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px">
    <div>
      <div style="font-size:1.1rem; font-weight:800; color:#1E293B">{mkt['direction']}</div>
      <div style="font-size:0.82rem; color:#64748B; margin-top:2px">{mkt['direction_detail']}</div>
    </div>
    <div style="text-align:center">
      <div style="font-size:0.72rem; color:#64748B">Fear & Greed</div>
      <div style="font-size:1.8rem; font-weight:800; color:{fg_color}">{fg}</div>
      <div style="font-size:0.72rem; color:{fg_color}; font-weight:600">{mkt['fear_label']}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        # 주요 지수 카드
        idx_items = list(mkt.get("indices", {}).items())
        if idx_items:
            cols = st.columns(len(idx_items))
            for col, (name, d) in zip(cols, idx_items):
                chg = d["chg_1d"]
                c = "#16A34A" if chg > 0 else "#EF4444" if chg < 0 else "#64748B"
                arrow = "▲" if chg > 0 else "▼" if chg < 0 else "─"
                col.markdown(f"""<div class="glass" style="padding:12px 14px; text-align:center">
  <div style="font-size:0.7rem; color:#94A3B8">{name}</div>
  <div style="font-size:1.1rem; font-weight:800; color:#1E293B">{d['price']:,.1f}</div>
  <div style="font-size:0.78rem; font-weight:700; color:{c}">{arrow} {chg:+.2f}%</div>
</div>""", unsafe_allow_html=True)

        # 섹터 동향 바
        sectors = mkt.get("sectors", {})
        if sectors:
            sec_html = '<div class="glass" style="padding:14px 18px"><div style="font-size:0.82rem; font-weight:700; color:#1E293B; margin-bottom:8px">섹터 동향 (금일)</div><div style="display:flex; flex-wrap:wrap; gap:6px">'
            for name, chg in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
                bg = "rgba(20,184,166,0.12)" if chg > 0 else "rgba(239,68,68,0.12)" if chg < 0 else "rgba(0,0,0,0.04)"
                tc = "#0D9488" if chg > 0 else "#EF4444" if chg < 0 else "#64748B"
                sec_html += f'<div style="background:{bg}; color:{tc}; padding:4px 10px; border-radius:10px; font-size:0.74rem; font-weight:600">{name} {chg:+.1f}%</div>'
            sec_html += '</div></div>'
            st.markdown(sec_html, unsafe_allow_html=True)

        # ── 3개 지수 스캔 ─────────────────────────────────────────────
        _indices = [
            ("sp500",       "S&P 500",      "linear-gradient(135deg,#F0ABFC,#C084FC)", "#A855F7"),
            ("russell2000", "Russell 2000",  "linear-gradient(135deg,#6EE7B7,#34D399)", "#10B981"),
            ("kospi100",    "KOSPI 100",     "linear-gradient(135deg,#93C5FD,#60A5FA)", "#3B82F6"),
        ]

        if st.session_state.all_picks_cache is None:
            all_picks = {}
            with st.spinner("📡 실시간 종목 스캔 중... (최초 1회, 이후 캐시 사용)"):
                for idx_key, _, _, _ in _indices:
                    _df = scan_index(idx_key)
                    all_picks[idx_key] = get_top_picks(_df, n=5)
            st.session_state.all_picks_cache = all_picks
        else:
            all_picks = st.session_state.all_picks_cache

        # ── 상단 2열 대형 피처드 카드 (S&P 500 / KOSPI 100) ─────────
        fc1, fc2 = st.columns(2)
        for col, (idx_key, idx_name, thumb_bg, accent) in zip([fc1, fc2], [_indices[0], _indices[2]]):
            picks = all_picks.get(idx_key, {"buy":[], "sell":[]})
            buy_top = picks["buy"][0] if picks["buy"] else None
            sell_top = picks["sell"][0] if picks["sell"] else None
            with col:
                buy_info = f'<b>{buy_top["name"]}</b> ({buy_top["buy_label"]}) RSI {buy_top["rsi"]:.0f} · {buy_top["ret_1m"]:+.1f}%' if buy_top else "추천 종목 없음"
                sell_info = f'<b>{sell_top["name"]}</b> ({sell_top["sell_label"]}) RSI {sell_top["rsi"]:.0f} · {sell_top["ret_1m"]:+.1f}%' if sell_top else "추천 종목 없음"
                st.markdown(f"""<div class="featured">
  <div style="display:flex; gap:18px; align-items:flex-start; margin-bottom:14px">
    <div class="featured-thumb" style="background:{thumb_bg}">📊</div>
    <div style="flex:1">
      <div style="font-size:0.76rem; color:#94A3B8; margin-bottom:2px">AI 실시간 분석</div>
      <div style="font-size:1.15rem; font-weight:800; color:#1E293B; margin-bottom:6px">{idx_name}</div>
      <div style="font-size:0.8rem; color:#1E293B; line-height:1.6">
        🟢 매수 TOP: {buy_info}<br>
        🔴 매도 TOP: {sell_info}
      </div>
    </div>
  </div>
  <div class="prog-bar">
    <div class="prog-seg" style="background:#14B8A6"></div>
    <div class="prog-seg" style="background:#F59E0B"></div>
    <div class="prog-seg" style="background:#94A3B8; opacity:0.4"></div>
  </div>
</div>""", unsafe_allow_html=True)

        # ── "All Picks" 4열 그리드 ────────────────────────────────────
        st.markdown('<div style="font-size:1.15rem; font-weight:800; color:#1E293B; margin:16px 0 10px">All Picks</div>', unsafe_allow_html=True)

        # 모든 매수+매도 종목 합치기
        all_cards = []
        for idx_key, idx_name, thumb_bg, accent in _indices:
            picks = all_picks.get(idx_key, {"buy":[], "sell":[]})
            for b in picks["buy"][:3]:
                all_cards.append({**b, "type": "buy", "index": idx_name, "thumb_bg": thumb_bg, "accent": accent})
            for s in picks["sell"][:3]:
                all_cards.append({**s, "type": "sell", "index": idx_name, "thumb_bg": thumb_bg, "accent": accent})

        if all_cards:
            N_COLS = 4
            rows = [all_cards[i:i+N_COLS] for i in range(0, len(all_cards), N_COLS)]
            for row in rows:
                cols = st.columns(N_COLS)
                for col, c in zip(cols, row):
                    with col:
                        is_sell = c["type"] == "sell"
                        lbl   = c.get("sell_label" if is_sell else "buy_label", "관망")
                        dot_c = "dot-red" if is_sell else "dot-green"
                        border = ' stock-card-alert' if is_sell and '무조건' in lbl else ''
                        score_val = min(c.get('buy_score' if not is_sell else 'sell_score', 30), 100)
                        lbl_color = '#EF4444' if is_sell else '#0D9488'
                        bar_color = '#EF4444' if is_sell else '#14B8A6'
                        st.markdown(f"""<div class="stock-card{border}">
  <div style="display:flex; gap:10px; align-items:center; margin-bottom:8px">
    <div class="stock-thumb" style="background:{c['thumb_bg']}">{c['name'][:1]}</div>
    <div style="flex:1; min-width:0">
      <div style="font-size:0.72rem; color:#94A3B8">{c['index']} · RSI {c['rsi']:.0f}</div>
      <div style="font-size:0.9rem; font-weight:700; color:#1E293B; white-space:nowrap; overflow:hidden; text-overflow:ellipsis">{c['name']}</div>
    </div>
    <div class="dot {dot_c}"></div>
  </div>
  <div style="font-size:0.76rem; font-weight:600; color:{lbl_color}; margin-bottom:2px">{lbl}</div>
  <div style="font-size:0.72rem; color:#94A3B8">{c['ret_1m']:+.1f}%(1M) · Vol {c['vol_ratio']:.1f}x</div>
  <div class="prog-bar">
    <div class="prog-seg" style="background:{bar_color}; flex:{score_val/100}"></div>
    <div class="prog-seg" style="background:#F59E0B; flex:0.15"></div>
    <div class="prog-seg" style="background:#E2E8F0; flex:{1 - score_val/100}"></div>
  </div>
</div>""", unsafe_allow_html=True)
                        if st.button("📊 세부 분석", key=f"detail_{c['ticker']}_{c['type']}", use_container_width=True):
                            st.session_state.detail_stock = c
        else:
            st.info("현재 추천 종목이 없습니다. 시장이 중립 상태입니다.")

        # ── 선택 종목 세부 분석 패널 ──────────────────────────────────
        if st.session_state.detail_stock:
            import yfinance as _yf
            import pandas as _pd
            import anthropic as _anth
            from config import ANTHROPIC_API_KEY as _akey

            _dc = st.session_state.detail_stock
            _ticker = _dc["ticker"]
            _is_sell = (_dc["type"] == "sell")
            _lbl = _dc.get("sell_label" if _is_sell else "buy_label", "")
            _reasons = _dc.get("sell_reasons" if _is_sell else "buy_reasons", [])
            _border_c = "#EF4444" if _is_sell else "#14B8A6"
            _cache_key = f"detail_analysis_{_ticker}"

            st.markdown(f"""<div class="glass" style="border-left:4px solid {_border_c}; padding:18px 22px; margin-top:8px">
  <div style="display:flex; justify-content:space-between; align-items:center">
    <div style="font-size:1.1rem; font-weight:800; color:#1E293B">📊 {_dc['name']} ({_ticker}) — 세부 분석</div>
    <div style="font-size:0.78rem; color:#94A3B8">{_dc['index']} · RSI {_dc['rsi']:.0f} · {_dc['ret_1m']:+.1f}%(1M) · <b style="color:{_border_c}">{_lbl}</b></div>
  </div>
</div>""", unsafe_allow_html=True)

            # 캐시에 없으면 데이터 수집
            if _cache_key not in st.session_state:
                with st.spinner(f"📡 {_ticker} 데이터 수집 + Claude AI 분석 중... (5~10초)"):
                    _cache = {}
                    try:
                        # 가격 데이터
                        _hist = _yf.download(_ticker, period="1y", progress=False)
                        if isinstance(_hist.columns, _pd.MultiIndex):
                            _hist.columns = _hist.columns.get_level_values(0)
                        _close = _hist["Close"].squeeze()
                        _delta = _close.diff()
                        _gain  = _delta.clip(lower=0).ewm(com=13, adjust=False).mean()
                        _loss  = (-_delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
                        _rs    = (_gain / _loss.where(_loss != 0, other=1e-9))
                        _hist["RSI"]      = 100 - (100 / (1 + _rs))
                        _hist["BB_mid"]   = _close.rolling(20).mean()
                        _std              = _close.rolling(20).std()
                        _hist["BB_upper"] = _hist["BB_mid"] + 2 * _std
                        _hist["BB_lower"] = _hist["BB_mid"] - 2 * _std
                        _hist["MA50"]     = _close.rolling(50).mean()
                        _hist["MA200"]    = _close.rolling(200).mean()
                        _cache["hist"]    = _hist

                        # 재무 데이터 (EPS, 순이익 등)
                        _info = _yf.Ticker(_ticker).info
                        _cache["info"] = {
                            "trailing_eps":     _info.get("trailingEps"),
                            "forward_eps":      _info.get("forwardEps"),
                            "net_income":       _info.get("netIncomeToCommon"),
                            "revenue":          _info.get("totalRevenue"),
                            "pe":               _info.get("trailingPE"),
                            "pb":               _info.get("priceToBook"),
                            "eps_growth":       _info.get("earningsGrowth"),
                            "revenue_growth":   _info.get("revenueGrowth"),
                            "profit_margin":    _info.get("profitMargins"),
                            "roe":              _info.get("returnOnEquity"),
                            "debt_to_equity":   _info.get("debtToEquity"),
                            "market_cap":       _info.get("marketCap"),
                        }

                        _latest  = float(_hist["Close"].squeeze().iloc[-1])
                        _prev    = float(_hist["Close"].squeeze().iloc[-2])
                        _chg_1d  = (_latest / _prev - 1) * 100
                        _ret_3m  = (_latest / float(_hist["Close"].squeeze().iloc[-min(66,len(_hist)-1)]) - 1) * 100
                        _rsi_now = float(_hist["RSI"].iloc[-1])
                        _cache["price"] = {"latest": _latest, "chg_1d": _chg_1d, "ret_3m": _ret_3m, "rsi": _rsi_now}

                        # Claude AI 분석
                        _fi = _cache["info"]
                        def _fmt(v, unit="", pct=False):
                            if v is None: return "N/A"
                            if pct: return f"{v*100:+.1f}%"
                            if abs(v) >= 1e9: return f"{v/1e9:.2f}B{unit}"
                            if abs(v) >= 1e6: return f"{v/1e6:.2f}M{unit}"
                            return f"{v:.2f}{unit}"

                        _fund_block = f"""[재무 지표]
주당순이익(EPS, TTM): {_fmt(_fi['trailing_eps'])} / 선행EPS: {_fmt(_fi['forward_eps'])}
기업순이익(Net Income): {_fmt(_fi['net_income'])}
매출(Revenue): {_fmt(_fi['revenue'])}
PER: {_fmt(_fi['pe'],'x')} / PBR: {_fmt(_fi['pb'],'x')}
EPS 성장률: {_fmt(_fi['eps_growth'], pct=True)} / 매출 성장률: {_fmt(_fi['revenue_growth'], pct=True)}
순이익률: {_fmt(_fi['profit_margin'], pct=True)} / ROE: {_fmt(_fi['roe'], pct=True)}
부채비율: {_fmt(_fi['debt_to_equity'],'%')} / 시가총액: {_fmt(_fi['market_cap'])}"""

                        _prompt = f"""종목: {_ticker} ({_dc['name']})
신호: {'매도 추천' if _is_sell else '매수 추천'} — {_lbl}
현재가: {_latest:,.2f} | 금일: {_chg_1d:+.2f}% | RSI: {_rsi_now:.1f}
1개월 수익률: {_dc['ret_1m']:+.1f}% | 5일: {_dc['ret_5d']:+.1f}% | 거래량 비율: {_dc['vol_ratio']:.1f}x
신호 근거: {', '.join(_reasons)}

{_fund_block}

위 기술적+재무적 데이터를 종합하여 한국어로 세부 투자 분석을 제공해주세요:

1. **기술적 분석** (2문장): RSI·볼린저밴드·거래량 해석
2. **재무 분석** (2문장): EPS, 순이익, PER/PBR, 수익성 평가
3. **{'매도' if _is_sell else '매수'} 근거** (2문장): 기술적+재무적 통합 판단
4. **리스크** (2가지): 투자 시 주의사항
5. **전망 & 전략** (2문장): 단기(1-2주)/중기(1-3개월) 방향 + 포지션 제언"""

                        if _akey:
                            _cli = _anth.Anthropic(api_key=_akey)
                            _msg = _cli.messages.create(
                                model="claude-haiku-4-5-20251001",
                                max_tokens=1500,
                                messages=[{"role": "user", "content": _prompt}],
                            )
                            _cache["analysis"] = _msg.content[0].text
                        else:
                            _cache["analysis"] = "ANTHROPIC_API_KEY 미설정"

                        _cache["ok"] = True
                    except Exception as _e:
                        _cache["ok"] = False
                        _cache["error"] = str(_e)

                st.session_state[_cache_key] = _cache

            # 캐시에서 꺼내어 표시
            _c = st.session_state.get(_cache_key, {})
            if not _c.get("ok"):
                st.error(f"데이터 로드 실패: {_c.get('error', '알 수 없는 오류')}")
            else:
                _hist  = _c["hist"]
                _fi    = _c["info"]
                _pv    = _c["price"]
                _sig_c = "#EF4444" if _is_sell else "#0D9488"

                _cc1, _cc2 = st.columns([2, 1])
                with _cc1:
                    st.plotly_chart(candlestick_chart_modern(_hist, _ticker), use_container_width=True)
                    st.plotly_chart(rsi_chart_modern(_hist), use_container_width=True)

                with _cc2:
                    def _fv(v, sfx="", pct=False, dec=2):
                        if v is None: return "N/A"
                        if pct: return f"{v*100:+.1f}%"
                        if sfx == "" and abs(v) >= 1e9: return f"{v/1e9:.1f}B"
                        if sfx == "" and abs(v) >= 1e6: return f"{v/1e6:.1f}M"
                        return f"{v:.{dec}f}{sfx}"

                    # 가격 KPI
                    st.markdown(f"""<div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:10px">
  <div class="glass" style="padding:12px; text-align:center">
    <div style="font-size:0.7rem; color:#94A3B8">현재가</div>
    <div style="font-size:1.2rem; font-weight:800; color:#1E293B">{_pv['latest']:,.2f}</div>
    <div style="font-size:0.74rem; color:{'#16A34A' if _pv['chg_1d']>=0 else '#EF4444'}">{'▲' if _pv['chg_1d']>=0 else '▼'} {_pv['chg_1d']:+.2f}%</div>
  </div>
  <div class="glass" style="padding:12px; text-align:center">
    <div style="font-size:0.7rem; color:#94A3B8">RSI(14)</div>
    <div style="font-size:1.2rem; font-weight:800; color:#1E293B">{_pv['rsi']:.1f}</div>
    <div style="font-size:0.74rem; color:#64748B">{'과매도' if _pv['rsi']<30 else '과매수' if _pv['rsi']>70 else '중립'}</div>
  </div>
  <div class="glass" style="padding:12px; text-align:center">
    <div style="font-size:0.7rem; color:#94A3B8">3개월 수익률</div>
    <div style="font-size:1.2rem; font-weight:800; color:{'#16A34A' if _pv['ret_3m']>=0 else '#EF4444'}">{_pv['ret_3m']:+.1f}%</div>
  </div>
  <div class="glass" style="padding:12px; text-align:center">
    <div style="font-size:0.7rem; color:#94A3B8">신호</div>
    <div style="font-size:0.88rem; font-weight:800; color:{_sig_c}">{_lbl}</div>
  </div>
</div>""", unsafe_allow_html=True)

                    # 재무 지표 카드
                    _eps_c = "#16A34A" if _fi.get("trailing_eps") and _fi["trailing_eps"] > 0 else "#EF4444"
                    _ni    = _fi.get("net_income")
                    _ni_c  = "#16A34A" if _ni and _ni > 0 else "#EF4444"
                    _eg_c  = "#16A34A" if _fi.get("eps_growth") and _fi["eps_growth"] > 0 else "#EF4444"
                    st.markdown(f"""<div class="glass" style="padding:14px 16px; margin-bottom:8px">
  <div style="font-size:0.82rem; font-weight:700; color:#1E293B; margin-bottom:10px">📈 재무 분석 (EPS · 순이익)</div>
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px">
    <div style="background:#F8FAFF; border-radius:10px; padding:10px; text-align:center">
      <div style="font-size:0.68rem; color:#94A3B8">주당순이익 (EPS)</div>
      <div style="font-size:1.05rem; font-weight:800; color:{_eps_c}">{_fv(_fi.get('trailing_eps'))}</div>
      <div style="font-size:0.68rem; color:#64748B">선행: {_fv(_fi.get('forward_eps'))}</div>
    </div>
    <div style="background:#F8FAFF; border-radius:10px; padding:10px; text-align:center">
      <div style="font-size:0.68rem; color:#94A3B8">기업순이익</div>
      <div style="font-size:1.05rem; font-weight:800; color:{_ni_c}">{_fv(_ni)}</div>
      <div style="font-size:0.68rem; color:#64748B">순이익률 {_fv(_fi.get('profit_margin'), pct=True)}</div>
    </div>
    <div style="background:#F8FAFF; border-radius:10px; padding:10px; text-align:center">
      <div style="font-size:0.68rem; color:#94A3B8">EPS 성장률</div>
      <div style="font-size:1.05rem; font-weight:800; color:{_eg_c}">{_fv(_fi.get('eps_growth'), pct=True)}</div>
    </div>
    <div style="background:#F8FAFF; border-radius:10px; padding:10px; text-align:center">
      <div style="font-size:0.68rem; color:#94A3B8">매출 성장률</div>
      <div style="font-size:1.05rem; font-weight:800; color:#3B82F6">{_fv(_fi.get('revenue_growth'), pct=True)}</div>
    </div>
    <div style="background:#F8FAFF; border-radius:10px; padding:10px; text-align:center">
      <div style="font-size:0.68rem; color:#94A3B8">PER / PBR</div>
      <div style="font-size:1.05rem; font-weight:800; color:#1E293B">{_fv(_fi.get('pe'),'x')} / {_fv(_fi.get('pb'),'x')}</div>
    </div>
    <div style="background:#F8FAFF; border-radius:10px; padding:10px; text-align:center">
      <div style="font-size:0.68rem; color:#94A3B8">ROE / 부채비율</div>
      <div style="font-size:1.05rem; font-weight:800; color:#1E293B">{_fv(_fi.get('roe'), pct=True)} / {_fv(_fi.get('debt_to_equity'),'%')}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

                    # Claude AI 분석
                    _at = _c.get("analysis", "")
                    st.markdown(f"""<div class="glass" style="padding:14px 16px">
  <div style="font-size:0.82rem; font-weight:700; color:#0D9488; margin-bottom:8px">🤖 Claude AI 종합 분석</div>
  <div style="font-size:0.81rem; color:#334155; line-height:1.85">{__import__('re').sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', _at).replace(chr(10), '<br>')}</div>
</div>""", unsafe_allow_html=True)

            if st.button("✕ 세부 분석 닫기", key="close_detail"):
                st.session_state.detail_stock = None
                st.rerun()

        # ── Claude AI 테마 분석 + 상세 추천사유 (캐시) ───────────────
        all_recs = []
        for idx_key, _, _, _ in _indices:
            picks = all_picks.get(idx_key, {"buy":[], "sell":[]})
            all_recs.extend(picks["buy"][:3])
            all_recs.extend(picks["sell"][:2])

        if all_recs:
            if st.session_state.theme_cache is None:
                with st.spinner("🤖 Claude AI — 시장 테마 & 종목 분석 중..."):
                    st.session_state.theme_cache = analyze_market_themes(mkt, all_recs)
            theme_result = st.session_state.theme_cache

            if theme_result.get("api_used"):
                # 시장 내러티브
                narrative = theme_result.get("market_narrative", "")
                if narrative:
                    st.markdown(f"""<div class="glass" style="padding:16px 20px; border-left:4px solid #14B8A6">
  <div style="font-size:0.82rem; font-weight:700; color:#0D9488; margin-bottom:6px">🤖 AI 시장 내러티브</div>
  <div style="font-size:0.88rem; color:#1E293B; line-height:1.7">{narrative}</div>
</div>""", unsafe_allow_html=True)

                # 테마 배지
                themes = theme_result.get("themes", [])
                if themes:
                    theme_html = '<div class="glass" style="padding:14px 18px"><div style="font-size:0.88rem; font-weight:700; color:#1E293B; margin-bottom:10px">🔥 현재 시장 핫 테마</div><div style="display:flex; flex-wrap:wrap; gap:8px">'
                    for t in themes:
                        hot = t.get("hot_level", 5)
                        bg = "rgba(239,68,68,0.12)" if hot >= 8 else "rgba(245,158,11,0.12)" if hot >= 5 else "rgba(20,184,166,0.08)"
                        tc = "#DC2626" if hot >= 8 else "#D97706" if hot >= 5 else "#0D9488"
                        fire = "🔥" * min(hot // 3, 3)
                        theme_html += f'<div style="background:{bg}; color:{tc}; padding:6px 14px; border-radius:12px; font-size:0.82rem; font-weight:600">{fire} {t["name"]} <span style="font-weight:400; font-size:0.74rem">({t.get("description","")})</span></div>'
                    theme_html += '</div></div>'
                    st.markdown(theme_html, unsafe_allow_html=True)

                # 종목별 상세 분석 카드
                analyses = theme_result.get("picks_analysis", [])
                if analyses:
                    st.markdown('<div style="font-size:1.05rem; font-weight:800; color:#1E293B; margin:14px 0 8px">📋 AI 종목 상세 분석</div>', unsafe_allow_html=True)
                    for a in analyses:
                        ticker = a.get("ticker", "")
                        theme_fit = a.get("theme_fit", "")
                        report = a.get("report_summary", "")
                        context = a.get("market_context", "")
                        risks = a.get("risk_factors", "")
                        verdict = a.get("verdict", "")

                        # verdict 색상
                        v_color = "#0D9488"
                        if "매도" in verdict or "무조건" in verdict: v_color = "#DC2626"
                        elif "몰빵" in verdict or "본부대" in verdict: v_color = "#F97316"

                        st.markdown(f"""<div class="glass" style="padding:16px 20px; margin-bottom:10px">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px">
    <div style="font-size:0.95rem; font-weight:800; color:#1E293B">{ticker}</div>
    <div style="background:rgba(20,184,166,0.1); color:#0D9488; padding:4px 12px; border-radius:10px; font-size:0.76rem; font-weight:600">🏷️ {theme_fit[:40]}</div>
  </div>
  <div style="font-size:0.82rem; color:#334155; line-height:1.7; margin-bottom:8px">
    <b style="color:#0D9488">📊 리포트:</b> {report}
  </div>
  <div style="font-size:0.82rem; color:#334155; line-height:1.7; margin-bottom:8px">
    <b style="color:#3B82F6">🌊 시장 맥락:</b> {context}
  </div>
  <div style="font-size:0.8rem; color:#94A3B8; margin-bottom:8px">
    ⚠️ 리스크: {risks}
  </div>
  <div style="background:rgba(0,0,0,0.03); border-radius:10px; padding:8px 14px; font-size:0.85rem; font-weight:700; color:{v_color}">
    💡 최종 판단: {verdict}
  </div>
</div>""", unsafe_allow_html=True)

        # ── 경고문 + API 설정 ─────────────────────────────────────────
        st.markdown("""<div class="glass" style="padding:12px 18px; background:rgba(255,237,213,0.6); border-color:rgba(253,186,116,0.5)">
  <div style="display:flex; align-items:center; gap:8px; color:#92400E; font-size:0.8rem; font-weight:500">
    ⚠️ 교육 및 참고 목적. 실제 투자 결정은 본인 책임.
  </div>
</div>""", unsafe_allow_html=True)

        with st.expander("⚙️ API 설정 (Claude · NewsAPI)"):
            import config as cfg
            c1, c2, c3 = st.columns(3)
            with c1:
                a_key = st.text_input("Anthropic (Claude) API Key", value=cfg.ANTHROPIC_API_KEY, type="password")
            with c2:
                n_key = st.text_input("NewsAPI Key", value=cfg.NEWS_API_KEY, type="password")
            with c3:
                g_key = st.text_input("Gemini API Key (구버전)", value=cfg.GEMINI_API_KEY, type="password")
            if st.button("저장", key="save_keys_init"):
                cfg.ANTHROPIC_API_KEY = a_key
                cfg.NEWS_API_KEY      = n_key
                cfg.GEMINI_API_KEY    = g_key
                st.success("저장 완료!")
        st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  아래는 종목 분석 결과 화면 (run_btn=True 일 때만 도달)
#  히트맵 페이지에서는 실행되지 않도록 가드
# ══════════════════════════════════════════════════════════════════════════════
if page_mode != "📈 종목 분석 (Dashboard)":
    st.stop()

progress_bar = st.progress(0, text="📡 데이터 수집 중...")
try:
    data = load_all(ticker_input)
except Exception as e:
    st.error(f"데이터 로드 실패: {e}")
    st.code(traceback.format_exc())
    st.stop()

progress_bar.progress(40, text="🤖 Claude AI 뉴스 심리 분석 중...")
close_s   = data["price_df"]["Close"].squeeze()
price_30d = float((close_s.iloc[-1] / close_s.iloc[-min(30, len(close_s))] - 1) * 100)
ai_result = analyze_sentiment(
    ticker=data["ticker"],
    company_name=data["fundamentals"].get("company_name", ticker_input),
    news_list=data["news"],
    price_change_pct=price_30d,
)

progress_bar.progress(80, text="⚡ Golden Bottom Score 계산 중...")
result = run_full_analysis(data, ai_result)
progress_bar.progress(100, text="✅ 분석 완료!")
progress_bar.empty()


# ══════════════════════════════════════════════════════════════════════════════
#  공통 변수
# ══════════════════════════════════════════════════════════════════════════════

fund     = result["fundamentals"]
currency = fund.get("currency", "USD")
sym      = "$" if currency == "USD" else "₩" if currency == "KRW" else ""
score    = result["golden_score"]
signal   = result["signal"]
s_color  = result["signal_color"]

# 점수 배지 색상
if score >= 70:
    badge_cls, arrow = "badge-up",   "↑"
elif score >= 50:
    badge_cls, arrow = "badge-neutral", "→"
else:
    badge_cls, arrow = "badge-down", "↓"

# RSI 배지
rsi_val = result['technical']['rsi_val']
if rsi_val < 30:
    rsi_badge = "badge-down"; rsi_hint = "과매도"
elif rsi_val > 70:
    rsi_badge = "badge-up";   rsi_hint = "과매수"
else:
    rsi_badge = "badge-neutral"; rsi_hint = "중립"

# 30일 수익률 배지
pct30    = result['price_30d_chg']
pct_cls  = "badge-up" if pct30 >= 0 else "badge-down"
pct_arrow= "↑" if pct30 >= 0 else "↓"


# ══════════════════════════════════════════════════════════════════════════════
#  섹션 헤더 + KPI 카드 4개
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div class="section-card" style="padding-bottom:8px">
  <div class="section-head">
    <div>
      <div class="section-title" style="font-size:1.3rem">
        {result['company_name']}
        <span style="font-size:0.9rem; color:#6B7280; font-weight:500; margin-left:8px">{result['ticker']}</span>
      </div>
      <div class="section-sub">섹터: {result['sector']}  ·  통화: {currency}  ·  Your current stock analysis summary</div>
    </div>
    <div style="display:flex; gap:8px; align-items:center;">
      <div class="section-badge">📅 실시간</div>
      <div class="section-badge" style="background:#EFF6FF; color:#2563EB">🔍 {result['ticker']}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="kpi-row">

  <div class="kpi-card kpi-card-primary">
    <div class="kpi-label kpi-label-primary">Golden Bottom Score</div>
    <div class="kpi-value kpi-value-primary">{score:.0f}<span style="font-size:1.2rem; font-weight:500">점</span></div>
    <div class="kpi-sub kpi-sub-primary">기술적 30% · 펀더멘탈 20% · AI심리 30% · 수급 20% 종합</div>
    <div class="kpi-badge badge-up-light">{arrow} {signal}</div>
    <div style="font-size:0.65rem; color:rgba(255,255,255,0.75); margin-top:6px; line-height:1.5">
      0–35 관망 &nbsp;|&nbsp; 35–50 중립 &nbsp;|&nbsp; 50–70 매수검토 &nbsp;|&nbsp; 70+ 강력매수
    </div>
    <div class="kpi-icon kpi-icon-white">🏆</div>
  </div>

  <div class="kpi-card">
    <div class="kpi-label">현재가</div>
    <div class="kpi-value">{sym}{result['latest_price']:,.2f}</div>
    <div class="kpi-sub">Last price</div>
    <div class="kpi-badge {pct_cls}">{pct_arrow} {abs(pct30):.1f}% (30일)</div>
    <div class="kpi-icon kpi-icon-blue">💰</div>
  </div>

  <div class="kpi-card">
    <div class="kpi-label">RSI (14)</div>
    <div class="kpi-value">{rsi_val:.1f}</div>
    <div class="kpi-sub">Relative Strength Index</div>
    <div class="kpi-badge {rsi_badge}">{rsi_hint}</div>
    <div class="kpi-icon kpi-icon-green">📉</div>
  </div>

  <div class="kpi-card">
    <div class="kpi-label">AI 심리 점수</div>
    <div class="kpi-value">{result['sentiment']['sentiment_raw']:+.1f}</div>
    <div class="kpi-sub">-10 공포 ~ +10 환희</div>
    <div class="kpi-badge {'badge-down' if result['sentiment']['sentiment_raw'] < -3 else 'badge-up' if result['sentiment']['sentiment_raw'] > 3 else 'badge-neutral'}">{result['sentiment']['fear_greed_label']}</div>
    <div class="kpi-icon kpi-icon-orange">🤖</div>
  </div>

</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  차트 영역: 캔들 차트 (좌) + 종합 게이지 (우)
# ══════════════════════════════════════════════════════════════════════════════

col_chart, col_gauge = st.columns([1.85, 1])

with col_chart:
    st.markdown("""
    <div class="section-card" style="padding-bottom:0">
      <div class="section-head">
        <div>
          <div class="section-title">Performance Overview</div>
          <div class="section-sub">기술적 분석 차트 (캔들 + 볼린저밴드 + 이동평균)</div>
        </div>
        <div class="section-badge">📅 최근 90일</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    with st.container():
        st.plotly_chart(
            candlestick_chart_modern(result["price_df"], result["ticker"]),
            use_container_width=True,
        )
        st.plotly_chart(
            rsi_chart_modern(result["price_df"]),
            use_container_width=True,
        )

with col_gauge:
    pbr = result['fundamental'].get('pbr')
    dte = result['fundamental'].get('debt_to_equity')
    vol = result['flow']['vol_ratio_20d']
    bad_priced = '✅ 선반영' if result['sentiment']['bad_news_priced'] else '❌ 미반영'

    st.markdown(f"""
    <div class="section-card">
      <div class="section-head">
        <div>
          <div class="section-title">Score Overview</div>
          <div class="section-sub">Golden Bottom 종합 분석 &nbsp;|&nbsp; <span style="font-size:0.68rem; color:#9CA3AF">0–35 관망 · 35–50 중립 · 50–70 매수검토 · 70+ 강력매수</span></div>
        </div>
        <div style="cursor:pointer; color:#9CA3AF; font-size:1.2rem">⋯</div>
      </div>
    """, unsafe_allow_html=True)

    st.plotly_chart(
        gauge_chart_modern(score, signal, s_color),
        use_container_width=True,
    )

    # 하단 2열 지표
    st.markdown(f"""
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:4px">
        <div style="background:#F8FAFF; border-radius:10px; padding:14px; text-align:center">
          <div style="font-size:0.75rem; color:#6B7280; margin-bottom:4px">PBR</div>
          <div style="font-size:1.3rem; font-weight:800; color:#1D4ED8">
            {f"{pbr:.2f}x" if pbr else "N/A"}
          </div>
          <div style="font-size:0.68rem; color:#9CA3AF; margin-top:2px; line-height:1.4">장부가 대비 주가 배수<br>낮을수록 저평가 (1x 미만 관심)</div>
        </div>
        <div style="background:#F8FAFF; border-radius:10px; padding:14px; text-align:center">
          <div style="font-size:0.75rem; color:#6B7280; margin-bottom:4px">부채비율</div>
          <div style="font-size:1.3rem; font-weight:800; color:#1D4ED8">
            {f"{dte:.0f}%" if dte else "N/A"}
          </div>
          <div style="font-size:0.68rem; color:#9CA3AF; margin-top:2px; line-height:1.4">자기자본 대비 부채<br>낮을수록 재무 안정 (100% 미만 양호)</div>
        </div>
        <div style="background:#F8FAFF; border-radius:10px; padding:14px; text-align:center">
          <div style="font-size:0.75rem; color:#6B7280; margin-bottom:4px">거래량 비율</div>
          <div style="font-size:1.3rem; font-weight:800; color:#1D4ED8">{vol}x</div>
          <div style="font-size:0.68rem; color:#9CA3AF; margin-top:2px; line-height:1.4">20일 평균 대비 오늘 거래량<br>1.5x 초과 시 세력 관심 급증</div>
        </div>
        <div style="background:#F8FAFF; border-radius:10px; padding:14px; text-align:center">
          <div style="font-size:0.75rem; color:#6B7280; margin-bottom:4px">악재 선반영</div>
          <div style="font-size:1.05rem; font-weight:700; color:#1D4ED8">{bad_priced}</div>
          <div style="font-size:0.68rem; color:#9CA3AF; margin-top:2px; line-height:1.4">나쁜 뉴스가 주가에 반영됐는지<br>선반영 시 역발상 반등 가능성 ↑</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  레이어별 점수 + AI 코멘트
# ══════════════════════════════════════════════════════════════════════════════

col_layer, col_ai = st.columns([1.1, 1])

with col_layer:
    st.markdown("""
    <div class="section-card">
      <div class="section-head">
        <div>
          <div class="section-title">Layer Score Analysis</div>
          <div class="section-sub">4가지 레이어별 세부 점수 &nbsp;|&nbsp; <span style="font-size:0.68rem; color:#9CA3AF">기술적(30%) · 펀더멘탈(20%) · AI심리(30%) · 수급(20%)</span></div>
        </div>
      </div>
    """, unsafe_allow_html=True)

    layer_score_bar(result)

    # 레이더 차트
    st.plotly_chart(radar_chart_modern(result), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_ai:
    sent = result["sentiment"]
    contrarian = sent["contrarian_signal"]
    c_color = "#16A34A" if "강한" in contrarian or "매수" in contrarian else "#D97706" if "주의" in contrarian else "#6B7280"

    st.markdown(f"""
    <div class="section-card">
      <div class="section-head">
        <div>
          <div class="section-title">🤖 AI Sentiment Analysis</div>
          <div class="section-sub">Claude AI 뉴스 심리 분석 &nbsp;|&nbsp; <span style="font-size:0.68rem; color:#9CA3AF">-10 극단 공포 ~ 0 중립 ~ +10 극단 환희</span></div>
        </div>
        <div class="section-badge" style="background:#EFF6FF; color:#2563EB">
          Claude AI
        </div>
      </div>

      <div class="ai-box">
        <strong>📊 시장 심리 요약</strong><br><br>
        {sent['summary']}
        <br><br>
        <strong>💡 역발상 기회</strong><br>
        {sent['opportunity']}
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:16px">
        <div style="background:#F8FAFF; border-radius:10px; padding:14px; text-align:center">
          <div style="font-size:0.75rem; color:#6B7280; margin-bottom:4px">감성 점수</div>
          <div style="font-size:1.6rem; font-weight:800; color:#1D4ED8">{sent['sentiment_raw']:+.1f}</div>
          <div style="font-size:0.72rem; color:#9CA3AF">-10 공포 ~ +10 환희</div>
        </div>
        <div style="background:#F8FAFF; border-radius:10px; padding:14px; text-align:center">
          <div style="font-size:0.75rem; color:#6B7280; margin-bottom:4px">역발상 신호</div>
          <div style="font-size:0.9rem; font-weight:700; color:{c_color}; margin-top:4px">{contrarian}</div>
          <div style="font-size:0.68rem; color:#9CA3AF; margin-top:2px; line-height:1.4">공포 극대화 시 매수 기회<br>강한 매수 신호일수록 반등 가능성 ↑</div>
        </div>
      </div>
    """, unsafe_allow_html=True)

    if sent.get("key_risks"):
        risks_html = "".join(f'<span class="risk-tag">⚠ {r}</span>' for r in sent["key_risks"])
        st.markdown(f"""
        <div style="margin-top:14px">
          <div style="font-size:0.82rem; font-weight:600; color:#374151; margin-bottom:8px">주요 리스크</div>
          {risks_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

if not ai_result.get("api_used"):
    st.markdown("""
    <div class="section-card" style="background:#FFFBEB; border:1px solid #FDE68A; padding:14px 20px">
      <div style="display:flex; align-items:center; gap:10px; color:#92400E; font-size:0.85rem; font-weight:500">
        ⚠️ Claude API 키 미설정 — AI 심리 점수는 중립(50점)으로 적용되었습니다.
        사이드바 또는 아래 설정에서 Anthropic API 키를 입력하면 실제 분석이 가능합니다.
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  리스크 관리 플랜
# ══════════════════════════════════════════════════════════════════════════════

risk = result["risk"]
target_pct = round((risk['target_price'] / risk['entry_price'] - 1) * 100, 1)

st.markdown(f"""
<div class="section-card">
  <div class="section-head">
    <div>
      <div class="section-title">🛡️ Risk Management Plan</div>
      <div class="section-sub">리스크 관리 플랜 — 매수가 · 손절가 · 목표가 · 권장 비중</div>
    </div>
    <div class="section-badge" style="background:#F0FDF4; color:#16A34A">R/R: 1:{risk['risk_reward']}</div>
  </div>
  <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:14px">
    <div class="risk-card">
      <div class="risk-label">진입가 (현재가)</div>
      <div class="risk-value">{sym}{risk['entry_price']:,.2f}</div>
      <div class="risk-delta" style="color:#6B7280">Entry Price</div>
    </div>
    <div class="risk-card" style="background:#FFF1F2; border-color:#FECDD3">
      <div class="risk-label">손절가</div>
      <div class="risk-value" style="color:#DC2626">{sym}{risk['stop_loss']:,.2f}</div>
      <div class="risk-delta" style="color:#DC2626">-{risk['stop_loss_pct']}% Stop Loss</div>
    </div>
    <div class="risk-card" style="background:#F0FDF4; border-color:#BBF7D0">
      <div class="risk-label">단기 목표가</div>
      <div class="risk-value" style="color:#16A34A">{sym}{risk['target_price']:,.2f}</div>
      <div class="risk-delta" style="color:#16A34A">+{target_pct}% Target</div>
    </div>
    <div class="risk-card" style="background:#F5F3FF; border-color:#DDD6FE">
      <div class="risk-label">권장 비중</div>
      <div class="risk-value" style="color:#7C3AED">{risk['position_pct']}%</div>
      <div class="risk-delta" style="color:#7C3AED">Position Size</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  섹션: 매도 신호 분석
# ══════════════════════════════════════════════════════════════════════════════

sell = result.get("sell_analysis", {})
sell_score  = sell.get("sell_score", 50)
sell_signal = sell.get("sell_signal", "🟡 분석 불가")

# 매도 점수 색상
if sell_score >= 75:
    sell_s_color = "#DC2626"
elif sell_score >= 55:
    sell_s_color = "#F97316"
elif sell_score >= 40:
    sell_s_color = "#EAB308"
else:
    sell_s_color = "#16A34A"

col_sell_gauge, col_sell_detail = st.columns([1, 1.6])

with col_sell_gauge:
    st.markdown(f"""
    <div class="section-card">
      <div class="section-head">
        <div>
          <div class="section-title">📤 Sell Signal Analysis</div>
          <div class="section-sub">매도 타이밍 분석 — 기술적 + 수급 결합 &nbsp;|&nbsp; <span style="font-size:0.68rem; color:#9CA3AF">0–40 보유 · 40–55 관망 · 55–75 매도검토 · 75+ 강력매도</span></div>
        </div>
        <div class="section-badge" style="background:{'#FEF2F2' if sell_score >= 55 else '#F0FDF4'}; color:{sell_s_color}">{sell_signal}</div>
      </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(sell_gauge_chart(sell_score, sell_signal, sell_s_color), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_sell_detail:
    st.markdown("""
    <div class="section-card">
      <div class="section-head">
        <div>
          <div class="section-title">📋 매도/보유 판단 근거</div>
          <div class="section-sub">Sell Reasons vs. Hold Reasons</div>
        </div>
      </div>
    """, unsafe_allow_html=True)

    sell_col_l, sell_col_r = st.columns(2)

    with sell_col_l:
        st.markdown("**🔴 매도 근거**")
        if sell.get("sell_reasons"):
            for r in sell["sell_reasons"]:
                st.markdown(f'<span class="risk-tag" style="background:#FEF2F2; border-color:#FECACA; color:#DC2626">⚠ {r}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span style="color:#9CA3AF; font-size:0.85rem">매도 신호 없음</span>', unsafe_allow_html=True)

    with sell_col_r:
        st.markdown("**🟢 보유 근거**")
        if sell.get("hold_reasons"):
            for r in sell["hold_reasons"]:
                st.markdown(f'<span class="risk-tag" style="background:#F0FDF4; border-color:#BBF7D0; color:#16A34A">✓ {r}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span style="color:#9CA3AF; font-size:0.85rem">보유 근거 없음</span>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  섹션: KIS 수급 상세 (한국주식)
# ══════════════════════════════════════════════════════════════════════════════

kis_data = result.get("kis_flow")
if kis_data and kis_data.get("available") and kis_data.get("summary"):
    s = kis_data["summary"]

    st.markdown(f"""
    <div class="section-card">
      <div class="section-head">
        <div>
          <div class="section-title">🇰🇷 KIS 실시간 수급 분석</div>
          <div class="section-sub">한국투자증권 OpenAPI — 기관/외국인/개인 매매동향</div>
        </div>
        <div style="display:flex; gap:8px">
          <div class="section-badge" style="background:#EFF6FF; color:#2563EB">🔗 KIS API</div>
          <div class="section-badge" style="background:{'#F0FDF4' if s.get('foreign_turning') else '#F3F4F6'}; color:{'#16A34A' if s.get('foreign_turning') else '#6B7280'}">
            {'🔄 외국인 전환!' if s.get('foreign_turning') else '외국인'}
          </div>
        </div>
      </div>
    """, unsafe_allow_html=True)

    # KPI 카드 3개
    f_net = s.get("foreign_net_5d", 0)
    i_net = s.get("inst_net_5d", 0)
    p_net = s.get("indiv_net_5d", 0)
    f_color = "#16A34A" if f_net > 0 else "#DC2626"
    i_color = "#16A34A" if i_net > 0 else "#DC2626"
    p_color = "#16A34A" if p_net > 0 else "#DC2626"

    st.markdown(f"""
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:14px; margin-bottom:16px">
      <div class="risk-card">
        <div class="risk-label">외국인 5일 순매수</div>
        <div class="risk-value" style="color:{f_color}; font-size:1.3rem">{f_net:+,}주</div>
        <div class="risk-delta" style="color:{'#16A34A' if s.get('foreign_turning') else '#6B7280'}">{'🔄 순매수 전환!' if s.get('foreign_turning') else '▸ 추이 유지'}</div>
      </div>
      <div class="risk-card">
        <div class="risk-label">기관 5일 순매수</div>
        <div class="risk-value" style="color:{i_color}; font-size:1.3rem">{i_net:+,}주</div>
        <div class="risk-delta" style="color:{'#16A34A' if s.get('inst_turning') else '#6B7280'}">{'🔄 순매수 전환!' if s.get('inst_turning') else '▸ 추이 유지'}</div>
      </div>
      <div class="risk-card">
        <div class="risk-label">개인 5일 순매수</div>
        <div class="risk-value" style="color:{p_color}; font-size:1.3rem">{p_net:+,}주</div>
        <div class="risk-delta" style="color:#6B7280">▸ 역발상 참고</div>
      </div>
      <div class="risk-card" style="background:#F5F3FF; border-color:#DDD6FE">
        <div class="risk-label">외인 소진율</div>
        <div class="risk-value" style="color:#7C3AED; font-size:1.3rem">{s.get('foreign_rate', 0):.1f}%</div>
        <div class="risk-delta" style="color:#7C3AED">Foreign Ownership</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 투자자별 매매 바 차트
    inv_df = kis_data.get("investor_trend")
    if inv_df is not None and len(inv_df) > 0:
        st.plotly_chart(investor_flow_chart(inv_df), use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  최근 뉴스
# ══════════════════════════════════════════════════════════════════════════════

if data["news"]:
    st.markdown("""
    <div class="section-card">
      <div class="section-head">
        <div>
          <div class="section-title">📰 Recent News Headlines</div>
          <div class="section-sub">최신 뉴스 헤드라인 (AI 감성 분석 소스)</div>
        </div>
      </div>
    """, unsafe_allow_html=True)

    ncols = st.columns(2)
    for i, n in enumerate(data["news"][:6]):
        with ncols[i % 2]:
            with st.expander(f"[{n.get('source', '')}] {n.get('title', '')[:60]}..."):
                st.caption(n.get("publishedAt", ""))
                st.write(n.get("description", "내용 없음"))

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  API 설정 섹션
# ══════════════════════════════════════════════════════════════════════════════

with st.expander("⚙️ API 설정 (Gemini · NewsAPI)"):
    import config as cfg
    c1, c2 = st.columns(2)
    with c1:
        g_key = st.text_input("Gemini API Key", value=cfg.GEMINI_API_KEY, type="password", key="g2")
    with c2:
        n_key = st.text_input("NewsAPI Key",    value=cfg.NEWS_API_KEY,   type="password", key="n2")
    if st.button("저장", key="save_keys_bottom"):
        cfg.GEMINI_API_KEY = g_key
        cfg.NEWS_API_KEY   = n_key
        import engine.ai_analyzer as _ai
        _ai._model = None
        st.success("저장 완료!")


# ══════════════════════════════════════════════════════════════════════════════
#  푸터
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="text-align:center; padding:20px 0 8px; color:#9CA3AF; font-size:0.78rem">
  ⚠️ <strong>면책 조항</strong>: 본 분석은 교육 목적으로 제공되며 투자 권유가 아닙니다.
  모든 투자 결정은 투자자 본인의 책임입니다.<br>
  데이터: yfinance · NewsAPI · Google Gemini &nbsp;|&nbsp;
  <strong style="color:#3B82F6">Bottom-Fisher AI</strong> © 2025
</div>
""", unsafe_allow_html=True)
