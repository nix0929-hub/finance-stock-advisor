# config.py - API 키 및 전역 설정
import os

# ─── API Keys ────────────────────────────────────────────────────────────────
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY",    "AIzaSyBL_cP81afG6F6_NDXpS0oXuag4WLB4c5I")   # Google AI Studio
NEWS_API_KEY      = os.getenv("NEWS_API_KEY",      "1f2235fdfdc2420ca85404e9fdaeb249")            # newsapi.org
def _get_anthropic_key() -> str:
    """
    우선순위:
    1) ANTHROPIC_API_KEY 환경변수
    2) CLAUDE_CODE_OAUTH_TOKEN 환경변수 (Claude Code 세션 토큰)
    3) Streamlit st.secrets (앱 내 실행 시)
    4) .streamlit/secrets.toml 직접 파싱
    """
    # 1·2) 환경변수
    key = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "")
    if key:
        return key
    # 3) Streamlit secrets
    try:
        import streamlit as _st
        k = _st.secrets.get("ANTHROPIC_API_KEY", "")
        if k:
            return k
    except Exception:
        pass
    # 4) secrets.toml 파싱
    try:
        import pathlib, re as _re
        _sec = pathlib.Path(__file__).parent / ".streamlit" / "secrets.toml"
        if _sec.exists():
            m = _re.search(r'ANTHROPIC_API_KEY\s*=\s*"([^"]+)"', _sec.read_text(encoding="utf-8"))
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""


def _refresh_key_if_needed() -> str:
    """
    OAuth 토큰은 세션마다 교체됨.
    현재 환경변수가 secrets.toml과 다르면 secrets.toml을 자동 갱신.
    """
    env_key = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "")
    if not env_key:
        return _get_anthropic_key()

    # secrets.toml 갱신
    try:
        import pathlib
        _sec = pathlib.Path(__file__).parent / ".streamlit" / "secrets.toml"
        current = _sec.read_text(encoding="utf-8") if _sec.exists() else ""
        if env_key not in current:
            _sec.parent.mkdir(exist_ok=True)
            _sec.write_text(f'ANTHROPIC_API_KEY = "{env_key}"\n', encoding="utf-8")
    except Exception:
        pass
    return env_key


ANTHROPIC_API_KEY = _refresh_key_if_needed()  # Anthropic Claude API

# ─── 한국투자증권 API ──────────────────────────────────────────────────────────
KIS_APP_KEY    = os.getenv("KIS_APP_KEY",    "PSq2C6SKYHdV2BCeRwouqGkwwosATUpkwpw5")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET", "/BgfJldjxZZ2EYeZIlhOcPIPQBUxm640s7cac8X+xZ7HnKXQLUK53FdBtavgAR7Bjdhj/2TIrCH9M7AdPn4Zuo6pWASyldi6ERdLZ+dhlOD5jYLC9xZBQHMyxXwX6vAFop/v4J6WG6XU6p+uEn2PothdUEUJPQH4yiy5rKNZ6XnUtpbqbVM=")
KIS_ACCOUNT_NO = os.getenv("KIS_ACCOUNT_NO", "")       # 계좌번호 (예: 50123456-01)
KIS_IS_PAPER   = True                                   # True=모의투자, False=실거래

# ─── Scoring Weights ──────────────────────────────────────────────────────────
WEIGHTS = {
    "technical":   0.30,   # RSI, 볼린저밴드, 200일선
    "fundamental": 0.20,   # PBR, FCF, 부채비율
    "sentiment":   0.30,   # Gemini AI 뉴스 심리 분석
    "flow":        0.20,   # 수급 (거래량 급증, 공매도 대리 지표)
}

# ─── Technical Thresholds ────────────────────────────────────────────────────
RSI_OVERSOLD        = 30
RSI_PERIOD          = 14
BB_PERIOD           = 20
BB_STD              = 2
MA_LONG             = 200
MA_SHORT            = 50
LOOKBACK_DAYS       = 365   # 데이터 수집 기간

# ─── Risk Management ─────────────────────────────────────────────────────────
STOP_LOSS_PCT       = 0.07   # 손절 7%
POSITION_MAX_PCT    = 0.10   # 최대 포지션 10%

# ─── Score Thresholds ────────────────────────────────────────────────────────
SCORE_BUY_STRONG    = 70
SCORE_BUY_WATCH     = 50
SCORE_NEUTRAL       = 35
