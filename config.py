# config.py - API 키 및 전역 설정
import os

# ─── API Keys ────────────────────────────────────────────────────────────────
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY",    "")   # 초기값 — _load_secrets_toml() 로드 후 재할당됨
NEWS_API_KEY      = os.getenv("NEWS_API_KEY",      "")   # 초기값 — _load_secrets_toml() 로드 후 재할당됨
def _load_secrets_toml() -> dict:
    """secrets.toml에서 모든 키를 읽어 dict로 반환."""
    try:
        import pathlib, re as _re
        _sec = pathlib.Path(__file__).parent / ".streamlit" / "secrets.toml"
        if not _sec.exists():
            return {}
        text = _sec.read_text(encoding="utf-8")
        result = {}
        for m in _re.finditer(r'^(\w+)\s*=\s*"([^"]*)"', text, _re.MULTILINE):
            result[m.group(1)] = m.group(2)
        return result
    except Exception:
        return {}


def _get_anthropic_key() -> str:
    """
    Anthropic API 키 로드 우선순위:
    1) ANTHROPIC_API_KEY 환경변수 (표준 API 키, sk-ant-api- 로 시작)
    2) secrets.toml의 ANTHROPIC_API_KEY
    3) Streamlit st.secrets

    ※ CLAUDE_CODE_OAUTH_TOKEN(sk-ant-oat01-)은 OAuth 토큰으로
      일반 API 호출에 사용 불가 — 의도적으로 제외
    """
    # 1) 환경변수 (OAuth 토큰 제외)
    env_key = os.getenv("ANTHROPIC_API_KEY", "")
    if env_key and not env_key.startswith("sk-ant-oat"):
        return env_key

    # 2) secrets.toml
    secrets = _load_secrets_toml()
    toml_key = secrets.get("ANTHROPIC_API_KEY", "")
    if toml_key and not toml_key.startswith("sk-ant-oat"):
        return toml_key

    # 3) Streamlit st.secrets
    try:
        import streamlit as _st
        k = _st.secrets.get("ANTHROPIC_API_KEY", "")
        if k and not k.startswith("sk-ant-oat"):
            return k
    except Exception:
        pass

    return ""


ANTHROPIC_API_KEY = _get_anthropic_key()  # Anthropic Claude API

# ─── 한국투자증권 API ──────────────────────────────────────────────────────────
_secrets = _load_secrets_toml()
KIS_APP_KEY    = os.getenv("KIS_APP_KEY",    _secrets.get("KIS_APP_KEY", ""))
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET", _secrets.get("KIS_APP_SECRET", ""))
KIS_ACCOUNT_NO = os.getenv("KIS_ACCOUNT_NO", _secrets.get("KIS_ACCOUNT_NO", ""))

# secrets.toml에서 GEMINI/NEWS 키도 재로드 (환경변수 없을 경우)
if not GEMINI_API_KEY:
    GEMINI_API_KEY = _secrets.get("GEMINI_API_KEY", "")
if not NEWS_API_KEY:
    NEWS_API_KEY = _secrets.get("NEWS_API_KEY", "")
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
