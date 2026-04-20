# engine/market_heatmap.py  ─  시장 히트맵 & 종목 추천 엔진
"""
Finviz 히트맵 임베드 + yfinance 기반 종목 스캔 → 매수/매도 추천
매수: 관망 → 선발대 투입 → 본부대 투입 → 몰빵
매도: 관망 → 일부분 매도 → 강력 매도 → 무조건 매도
"""

from __future__ import annotations

import warnings
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")


# ══════════════════════════════════════════════════════════════════════════════
#  Finviz 히트맵 URL (iframe 임베드용)
# ══════════════════════════════════════════════════════════════════════════════

import plotly.graph_objects as go


# ══════════════════════════════════════════════════════════════════════════════
#  종목 리스트
# ══════════════════════════════════════════════════════════════════════════════

QUICK_TICKERS = {
    "sp500": [
        # Tech
        "AAPL","MSFT","NVDA","AVGO","META","GOOG","AMZN","TSLA","CRM","AMD",
        "ADBE","INTC","CSCO","QCOM","TXN","NOW","ORCL","AMAT","MU","LRCX",
        "KLAC","SNPS","CDNS","MRVL","PANW","CRWD","FTNT",
        # Healthcare
        "UNH","JNJ","LLY","ABBV","MRK","TMO","PFE","ABT","DHR","AMGN",
        "BMY","ISRG","GILD","MDT","SYK","VRTX","REGN","BSX","EW","ZTS",
        # Financials
        "BRK-B","JPM","V","MA","BAC","WFC","GS","MS","AXP","BLK",
        "SCHW","C","SPGI","PGR","CME","ICE","MCO","CB","AON",
        # Consumer
        "HD","MCD","NKE","SBUX","LOW","TJX","COST","PG","KO","PEP",
        "PM","CL","WMT","TGT","ROST","DG","DLTR","EL","MO","KMB",
        # Energy
        "XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO","OXY",
        "DVN","HAL","FANG","BKR",
        # Industrials
        "CAT","UNP","HON","RTX","DE","BA","GE","LMT","MMM","UPS",
        "FDX","WM","EMR","ITW","ETN","PH","ROK","CARR","GD","NOC",
        # Communication
        "GOOGL","NFLX","DIS","CMCSA","T","VZ","TMUS","CHTR","EA",
        # Real Estate / Utilities
        "PLD","AMT","CCI","EQIX","SPG","NEE","DUK","SO","D","AEP",
    ],
    "russell2000": [
        "SMCI","BOOT","SHAK","PLNT","SM","NTNX","BWXT","CAVA",
        "WING","EAT","MTDR","PI","RBC","TXRH","FFIN","SFBS",
        "PNFP","IBOC","WSFS","BANR","AAON","MATX","AWI",
        "SRPT","PCVX","KROS","VERA","CWAN","BRZE","ALKT","CAMT",
        "RRC","CNX","TRGP","VNOM","HALO","ENSG","MASI","OMCL",
        "FNB","SPSC","DIN","GPOR","RXRX","NUVB",
    ],
    "kospi100": [
        "005930.KS","000660.KS","042700.KS","373220.KS","006400.KS","051910.KS",
        "005380.KS","000270.KS","012330.KS","207940.KS","068270.KS","326030.KS",
        "105560.KS","055550.KS","086790.KS","035420.KS","035720.KS","263750.KS",
        "005490.KS","010130.KS","009540.KS","329180.KS","017670.KS","030200.KS",
        "015760.KS","034730.KS","003670.KS","066570.KS","028260.KS","011200.KS",
        "096770.KS","036570.KS","018260.KS","032830.KS","003550.KS","004020.KS",
    ],
}

US_NAMES = {
    "AAPL":"애플","MSFT":"마이크로소프트","NVDA":"엔비디아","AVGO":"브로드컴","META":"메타",
    "GOOG":"구글","GOOGL":"구글","AMZN":"아마존","TSLA":"테슬라","JPM":"JP모건","UNH":"유나이티드헬스",
    "V":"비자","MA":"마스터카드","XOM":"엑슨모빌","JNJ":"존슨앤존슨","LLY":"일라이릴리",
    "HD":"홈디포","PG":"P&G","NFLX":"넷플릭스","BA":"보잉","INTC":"인텔",
    "CRM":"세일즈포스","AMD":"AMD","ADBE":"어도비","COST":"코스트코","WMT":"월마트",
    "MRK":"머크","ABBV":"애브비","PFE":"화이자","KO":"코카콜라","PEP":"펩시",
    "BAC":"뱅크오브아메리카","WFC":"웰스파고","GS":"골드만삭스","MS":"모건스탠리",
    "AXP":"아메리칸익스프레스","BLK":"블랙록","CSCO":"시스코","QCOM":"퀄컴","TXN":"텍사스인스트루먼트",
    "NOW":"서비스나우","ORCL":"오라클","AMAT":"어플라이드머티리얼즈","MU":"마이크론","LRCX":"램리서치",
    "KLAC":"KLA","SNPS":"시놉시스","CDNS":"케이던스","MRVL":"마벨","PANW":"팔로알토네트웍스",
    "CRWD":"크라우드스트라이크","FTNT":"포티넷","TMO":"써모피셔","ABT":"애보트","DHR":"다나허",
    "AMGN":"암젠","BMY":"BMS","ISRG":"인튜이티브서지컬","GILD":"길리어드","MDT":"메드트로닉",
    "SYK":"스트라이커","VRTX":"버텍스","REGN":"리제네론","BSX":"보스턴사이언티픽",
    "BRK-B":"버크셔해서웨이","SCHW":"찰스슈왑","C":"시티그룹","SPGI":"S&P글로벌",
    "PGR":"프로그레시브","CME":"CME그룹","ICE":"ICE","MCO":"무디스",
    "MCD":"맥도날드","NKE":"나이키","SBUX":"스타벅스","LOW":"로우스","TJX":"TJX",
    "TGT":"타겟","PM":"필립모리스","CL":"콜게이트","MO":"알트리아",
    "CVX":"셰브론","COP":"코노코필립스","EOG":"EOG리소시즈","SLB":"슐룸버거",
    "CAT":"캐터필러","UNP":"유니온퍼시픽","HON":"허니웰","RTX":"레이시온","DE":"디어",
    "GE":"GE에어로스페이스","LMT":"록히드마틴","MMM":"3M","UPS":"UPS",
    "DIS":"디즈니","CMCSA":"컴캐스트","T":"AT&T","VZ":"버라이즌","TMUS":"T모바일",
    "EA":"EA","PLD":"프로로지스","AMT":"아메리칸타워","CCI":"크라운캐슬",
    "NEE":"넥스트에라에너지","DUK":"듀크에너지","SO":"서던컴퍼니",
    "SMCI":"슈퍼마이크로","BOOT":"부트반","SHAK":"쉐이크쉑","PLNT":"플래닛피트니스",
    "CAVA":"카바","WING":"윙스탑","EAT":"잇브랜즈","SM":"SM에너지",
}

KR_NAMES = {
    "005930.KS":"삼성전자","000660.KS":"SK하이닉스","042700.KS":"한미반도체",
    "373220.KS":"LG에너지솔루션","006400.KS":"삼성SDI","051910.KS":"LG화학",
    "005380.KS":"현대차","000270.KS":"기아","012330.KS":"현대모비스",
    "207940.KS":"삼성바이오","068270.KS":"셀트리온","326030.KS":"SK바이오팜",
    "105560.KS":"KB금융","055550.KS":"신한지주","086790.KS":"하나금융",
    "035420.KS":"NAVER","035720.KS":"카카오","263750.KS":"펄어비스",
    "005490.KS":"POSCO홀딩스","010130.KS":"고려아연",
    "009540.KS":"한국조선해양","329180.KS":"HD현대중공업",
    "017670.KS":"SK텔레콤","030200.KS":"KT",
    "015760.KS":"한국전력","034730.KS":"SK가스",
    "003670.KS":"포스코퓨처엠","066570.KS":"LG전자","028260.KS":"삼성물산",
    "011200.KS":"HMM","096770.KS":"SK이노베이션","036570.KS":"엔씨소프트",
    "018260.KS":"삼성에스디에스","032830.KS":"삼성생명","003550.KS":"LG",
    "004020.KS":"현대제철",
}


# ══════════════════════════════════════════════════════════════════════════════
#  매수/매도 기준 판정
# ══════════════════════════════════════════════════════════════════════════════

def classify_buy(rsi, ret_1d, ret_5d, ret_1m, vol_ratio) -> tuple[str, int, list]:
    """실시간 기준 매수 판단: 관망 → 선발대 투입 → 본부대 투입 → 몰빵"""
    score = 0
    reasons = []

    # RSI (실시간 핵심)
    if rsi <= 20:      score += 40; reasons.append(f"RSI {rsi:.0f} 극단적 과매도")
    elif rsi <= 30:    score += 28; reasons.append(f"RSI {rsi:.0f} 과매도")
    elif rsi <= 40:    score += 12

    # 오늘 하루 급락 (실시간)
    if ret_1d <= -5:   score += 25; reasons.append(f"금일 {ret_1d:+.1f}% 급락")
    elif ret_1d <= -3: score += 18; reasons.append(f"금일 {ret_1d:+.1f}% 하락")
    elif ret_1d <= -1: score += 8

    # 1개월 누적 하락
    if ret_1m <= -20:  score += 20; reasons.append(f"1개월 {ret_1m:+.1f}% 폭락")
    elif ret_1m <= -10: score += 12; reasons.append(f"1개월 {ret_1m:+.1f}% 낙폭과대")

    # 반등 + 거래량 신호
    if ret_1d > 0 and ret_5d < -5: score += 12; reasons.append("금일 반등 + 5일 하락 → 저점 탈출")
    if vol_ratio >= 2.0: score += 10; reasons.append(f"거래량 {vol_ratio:.1f}x 급증")

    if score >= 70:    return "🔴 몰빵", score, reasons
    elif score >= 45:  return "🟠 본부대 투입", score, reasons
    elif score >= 25:  return "🟡 선발대 투입", score, reasons
    else:              return "⚪ 관망", score, reasons


def classify_sell(rsi, ret_1d, ret_5d, ret_1m, vol_ratio) -> tuple[str, int, list]:
    """실시간 기준 매도 판단: 관망 → 일부분 매도 → 강력 매도 → 무조건 매도"""
    score = 0
    reasons = []

    # RSI (실시간 핵심)
    if rsi >= 85:      score += 40; reasons.append(f"RSI {rsi:.0f} 극단적 과매수")
    elif rsi >= 70:    score += 28; reasons.append(f"RSI {rsi:.0f} 과매수")
    elif rsi >= 60:    score += 10

    # 오늘 하루 급등 (실시간)
    if ret_1d >= 5:    score += 25; reasons.append(f"금일 +{ret_1d:.1f}% 급등")
    elif ret_1d >= 3:  score += 18; reasons.append(f"금일 +{ret_1d:.1f}% 상승")
    elif ret_1d >= 1:  score += 5

    # 1개월 누적 급등
    if ret_1m >= 30:   score += 20; reasons.append(f"1개월 +{ret_1m:.1f}% 과열")
    elif ret_1m >= 15: score += 12; reasons.append(f"1개월 +{ret_1m:.1f}% 급등")

    # 거래량 분배
    if vol_ratio >= 3.0 and ret_1d > 2: score += 12; reasons.append(f"Vol {vol_ratio:.1f}x 분배 경고")

    if score >= 70:    return "🔴 무조건 매도", score, reasons
    elif score >= 45:  return "🟠 강력 매도", score, reasons
    elif score >= 25:  return "🟡 일부분 매도", score, reasons
    else:              return "⚪ 관망", score, reasons


# ══════════════════════════════════════════════════════════════════════════════
#  개별 종목 데이터 수집
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_one(ticker: str, retries: int = 2) -> Optional[dict]:
    """실시간(최근 1개월) 데이터 수집 → 1일 변동률 기준 판단.
    yfinance 1.2.x 스레드 안전성을 위해 Ticker.history() 사용 + 재시도 로직.
    """
    import time
    for attempt in range(retries + 1):
        try:
            # yf.download 대신 Ticker.history 사용 (스레드 안전)
            t_obj = yf.Ticker(ticker)
            df = t_obj.history(period="1mo", auto_adjust=True)

            if df.empty or len(df) < 3:
                return None

            # MultiIndex 컬럼 정리 (방어 코드)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            close = df["Close"].squeeze()
            vol   = df["Volume"].squeeze()

            # Series가 아닌 경우 변환
            if not isinstance(close, pd.Series):
                close = pd.Series(close)
            if not isinstance(vol, pd.Series):
                vol = pd.Series(vol)

            # 실시간 수익률
            c_last = float(close.iloc[-1])
            c_prev = float(close.iloc[-2]) if len(close) >= 2 else c_last
            c_5d   = float(close.iloc[-min(5, len(close))])
            c_1m   = float(close.iloc[0])

            ret_1d = (c_last / c_prev - 1) * 100 if c_prev else 0.0
            ret_5d = (c_last / c_5d  - 1) * 100 if c_5d else 0.0
            ret_1m = (c_last / c_1m  - 1) * 100 if c_1m else 0.0

            # RSI (14일)
            delta = close.diff()
            gain  = delta.clip(lower=0).rolling(14).mean()
            loss  = (-delta.clip(upper=0)).rolling(14).mean()
            rs    = gain / loss.where(loss != 0, other=np.nan)
            rsi_s = 100 - (100 / (1 + rs))
            rsi   = float(rsi_s.iloc[-1]) if not pd.isna(rsi_s.iloc[-1]) else 50.0

            # 거래량 비율
            vol_ma = vol.rolling(min(20, len(vol))).mean()
            vol_last   = float(vol.iloc[-1])
            vol_ma_val = float(vol_ma.iloc[-1]) if not pd.isna(vol_ma.iloc[-1]) else 0.0
            vol_ratio = vol_last / vol_ma_val if vol_ma_val > 0 else 1.0

            # 실시간 기준 매수/매도 판단
            buy_label, buy_score, buy_reasons   = classify_buy(rsi, ret_1d, ret_5d, ret_1m, vol_ratio)
            sell_label, sell_score, sell_reasons = classify_sell(rsi, ret_1d, ret_5d, ret_1m, vol_ratio)

            # 한글 이름
            kr = KR_NAMES.get(ticker) or US_NAMES.get(ticker)
            name = f"{ticker}({kr})" if kr else ticker

            return {
                "ticker": ticker, "name": name,
                "price": round(c_last, 2),
                "ret_1d": round(ret_1d, 2), "ret_5d": round(ret_5d, 2), "ret_1m": round(ret_1m, 2),
                "rsi": round(rsi, 1), "vol_ratio": round(vol_ratio, 2),
                "buy_label": buy_label, "buy_score": buy_score, "buy_reasons": buy_reasons,
                "sell_label": sell_label, "sell_score": sell_score, "sell_reasons": sell_reasons,
            }

        except Exception:
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))  # 재시도 전 대기
                continue
            return None


# ══════════════════════════════════════════════════════════════════════════════
#  지수별 종목 스캔
# ══════════════════════════════════════════════════════════════════════════════

def scan_index(index_name: str) -> pd.DataFrame:
    tickers = QUICK_TICKERS.get(index_name, [])
    if not tickers:
        return pd.DataFrame()

    results = []
    # max_workers=5 로 제한 (Yahoo Finance 레이트 리밋 방지)
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_fetch_one, t): t for t in tickers}
        for future in as_completed(futures):
            try:
                d = future.result()
                if d:
                    results.append(d)
            except Exception:
                pass

    if not results:
        return pd.DataFrame()
    return pd.DataFrame(results).sort_values("ret_1m", ascending=False).reset_index(drop=True)


def get_top_picks(df: pd.DataFrame, n: int = 3) -> dict:
    """매수 TOP n + 매도 TOP n 추출."""
    if df.empty:
        return {"buy": [], "sell": []}

    buy = df[df["buy_score"] >= 25].nlargest(n, "buy_score").to_dict("records")
    sell = df[df["sell_score"] >= 25].nlargest(n, "sell_score").to_dict("records")
    return {"buy": buy, "sell": sell}


# ══════════════════════════════════════════════════════════════════════════════
#  Plotly 히트맵 (트리맵) 생성
# ══════════════════════════════════════════════════════════════════════════════

def create_treemap(df: pd.DataFrame, title: str) -> go.Figure:
    """스캔 결과 DataFrame → Plotly Treemap 히트맵."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="데이터 없음", x=0.5, y=0.5, showarrow=False)
        return fig

    df = df.copy()
    df["abs_ret"] = df["ret_1d"].abs().clip(lower=0.3)

    # 라벨: 종목명 + 금일 수익률 + 매수/매도 기준
    df["label"] = df.apply(
        lambda r: (
            f"<b>{r['name']}</b><br>"
            f"금일 {r['ret_1d']:+.1f}% · RSI {r['rsi']:.0f}<br>"
            f"매수: {str(r.get('buy_label','관망')).split(' ',1)[-1]}<br>"
            f"매도: {str(r.get('sell_label','관망')).split(' ',1)[-1]}"
        ), axis=1
    )

    fig = go.Figure(go.Treemap(
        labels     = df["label"],
        parents    = [""] * len(df),
        values     = df["abs_ret"],
        customdata = df[["ticker","name","ret_1d","ret_5d","ret_1m","rsi","vol_ratio",
                         "buy_label","sell_label"]].values,
        textinfo   = "label",
        textfont   = dict(size=11, family="Inter, sans-serif"),
        hovertemplate = (
            "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
            "1일 %{customdata[2]:+.1f}% · 5일 %{customdata[3]:+.1f}% · 1개월 %{customdata[4]:+.1f}%<br>"
            "RSI %{customdata[5]:.0f} · Vol %{customdata[6]:.1f}x<br>"
            "매수: %{customdata[7]} · 매도: %{customdata[8]}"
            "<extra></extra>"
        ),
        marker = dict(
            colors     = df["ret_1d"],
            colorscale = [[0,"#DC2626"],[0.35,"#FB923C"],[0.5,"#F5F5F5"],[0.65,"#86EFAC"],[1,"#16A34A"]],
            cmid       = 0,
            cmin       = max(df["ret_1d"].quantile(0.05), -8),
            cmax       = min(df["ret_1d"].quantile(0.95), 8),
            line       = dict(width=2, color="white"),
            colorbar   = dict(title="금일 %", thickness=10, len=0.4),
        ),
    ))

    fig.update_layout(
        title  = dict(text=f"<b>{title}</b>", font=dict(size=14, color="#1E293B"), x=0),
        height = 500,
        paper_bgcolor = "rgba(0,0,0,0)",
        margin = dict(t=40, b=5, l=5, r=5),
        font   = dict(family="Inter, sans-serif"),
    )
    return fig
