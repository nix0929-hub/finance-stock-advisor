# engine/ai_analyzer.py  ─  Module B: AI Sentiment Engine
"""
Claude AI(Anthropic)를 사용하여 뉴스 헤드라인의 감성을 수치화.
역발상(Contrarian) 로직: 극단적 공포(-10) → 매수 신호로 해석.
"""

from __future__ import annotations

import json
import re

import anthropic

from config import _get_anthropic_key

# ── Anthropic 클라이언트 싱글턴 (호출마다 재생성 방지) ───────────────────────
_client: anthropic.Anthropic | None = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = _get_anthropic_key()   # 런타임에 호출 → st.secrets 정상 동작
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 미설정 — config.py 또는 환경변수를 확인하세요.")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def reset_client() -> None:
    """API 키 변경 시 싱글턴 클라이언트를 리셋하여 새 키를 적용."""
    global _client
    _client = None


# ══════════════════════════════════════════════════════════════════════════════
#  프롬프트 설계
# ══════════════════════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """당신은 월가의 최고 퀀트 트레이더이자 역발상 투자 전문가입니다.
역할: 뉴스 심리를 수치화하여 저점 매수 신호를 포착하는 것입니다.

핵심 원칙:
- 극단적 공포(패닉셀, 투자자 탈출) = 진정한 매수 기회
- 과도한 낙관론(FOMO, 개인 쏠림) = 위험 경고
- 악재의 '선반영' 여부가 핵심 판단 기준

출력 형식은 반드시 아래 JSON만 출력하세요 (마크다운 코드블록 없이):
{
  "sentiment_score": <-10.0 ~ +10.0, 공포→매수신호, 환희→매도신호>,
  "contrarian_signal": <"STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL">,
  "fear_greed_label": <"극단적 공포" | "공포" | "중립" | "탐욕" | "극단적 탐욕">,
  "bad_news_priced_in": <true | false>,
  "key_risks": [<리스크 1>, <리스크 2>],
  "opportunity": "<역발상 기회 한 줄 요약>",
  "summary": "<전체 시장 심리 2-3문장 요약 (한국어)>"
}"""


def _build_news_text(news_list: list[dict]) -> str:
    if not news_list:
        return "최근 관련 뉴스 없음"
    lines = []
    for i, n in enumerate(news_list[:10], 1):
        title = n.get("title", "")
        desc  = n.get("description", "") or ""
        lines.append(f"{i}. [{n.get('source','')}] {title}\n   {desc[:120]}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  메인 분석 함수
# ══════════════════════════════════════════════════════════════════════════════

def analyze_sentiment(
    ticker: str,
    company_name: str,
    news_list: list[dict],
    price_change_pct: float = 0.0,
) -> dict:
    """
    뉴스 + 가격 변동을 Claude에 전달하여 감성 분석 결과 반환.

    반환 dict 키:
      sentiment_score, contrarian_signal, fear_greed_label,
      bad_news_priced_in, key_risks, opportunity, summary, raw_response
    """
    news_text = _build_news_text(news_list)

    user_prompt = f"""
종목: {ticker} ({company_name})
최근 가격 변동: {price_change_pct:+.1f}%
최근 뉴스 헤드라인:
{news_text}

위 정보를 바탕으로 역발상 투자 관점에서 시장 심리를 분석하고 JSON을 출력하세요.
"""

    try:
        client = _get_client()
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw_text = message.content[0].text.strip()

        # JSON 추출 (코드블록 감싸진 경우 대응)
        json_match = re.search(r"\{[\s\S]*\}", raw_text)
        if not json_match:
            raise ValueError("Claude 응답에서 JSON을 찾을 수 없습니다.")

        result = json.loads(json_match.group())
        result["raw_response"] = raw_text
        result["api_used"]     = True
        return result

    except Exception as e:
        return {
            "sentiment_score"   : 0.0,
            "contrarian_signal" : "NEUTRAL",
            "fear_greed_label"  : "중립 (API 오류)",
            "bad_news_priced_in": False,
            "key_risks"         : [str(e)],
            "opportunity"       : "AI 분석 불가 - API 키를 확인하세요.",
            "summary"           : f"Claude API 연결 실패: {e}",
            "raw_response"      : str(e),
            "api_used"          : False,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  sentiment_score → sentiment_layer_score 변환 (0~100)
# ══════════════════════════════════════════════════════════════════════════════

def sentiment_to_layer_score(sentiment_score: float) -> float:
    """
    역발상 로직 적용:
      sentiment_score = -10 (극공포) → layer_score = 100 (강력 매수)
      sentiment_score =   0 (중립)   → layer_score =  50
      sentiment_score = +10 (극탐욕) → layer_score =   0 (매도 경고)
    """
    return round(((-sentiment_score + 10) / 20) * 100, 1)
