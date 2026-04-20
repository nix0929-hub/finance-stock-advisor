# engine/theme_analyzer.py  ─  시장 테마/트렌드 AI 분석
"""
Claude AI를 사용하여:
1. 현재 시장의 주요 테마/트렌드를 분석
2. 각 종목이 테마에 얼마나 부합하는지 판단
3. 추천사유를 시장흐름 + 리포트 스타일로 생성
"""

from __future__ import annotations
import json
import re

import anthropic
from config import _get_anthropic_key


def analyze_market_themes(market_data: dict, top_picks: list[dict]) -> dict:
    """
    시장 데이터 + 추천 종목을 Claude에 전달하여
    테마 분석 + 종목별 상세 추천사유를 생성.

    반환:
    {
        "themes": [{"name": "AI 반도체", "description": "...", "hot_level": 9}, ...],
        "picks_analysis": [
            {
                "ticker": "NVDA",
                "theme_fit": "AI 반도체 핵심 수혜주",
                "report_summary": "월가 리포트 스타일 분석...",
                "market_context": "시장 흐름과 연계된 매수 근거...",
                "risk_factors": "주요 리스크...",
                "verdict": "본부대 투입 — RSI 극단 과매도 + AI 테마 핵심"
            }, ...
        ],
        "market_narrative": "전체 시장 내러티브 요약..."
    }
    """
    # 시장 데이터 텍스트 구성
    idx_text = ""
    for name, d in market_data.get("indices", {}).items():
        idx_text += f"  {name}: {d['price']:,.1f} ({d['chg_1d']:+.2f}%)\n"

    sector_text = ""
    for name, chg in market_data.get("sectors", {}).items():
        sector_text += f"  {name}: {chg:+.1f}%\n"

    # 추천 종목 텍스트
    picks_text = ""
    for p in top_picks[:12]:
        picks_text += (
            f"  {p['ticker']} ({p['name']}): "
            f"금일 {p['ret_1d']:+.1f}%, 5일 {p['ret_5d']:+.1f}%, 1개월 {p['ret_1m']:+.1f}%, "
            f"RSI {p['rsi']:.0f}, Vol비 {p['vol_ratio']:.1f}x, "
            f"매수:{p.get('buy_label','')}, 매도:{p.get('sell_label','')}\n"
        )

    prompt = f"""당신은 월가 최고 리서치 애널리스트입니다.

## 현재 시장 상황
Fear & Greed: {market_data.get('fear_score', 50)} ({market_data.get('fear_label', '중립')})
시장 방향: {market_data.get('direction', '혼조')}
VIX: {market_data.get('vix', 20)}

### 주요 지수 (금일)
{idx_text}

### 섹터 동향 (금일)
{sector_text}

### AI가 선별한 추천 후보 종목
{picks_text}

## 요청사항

아래 JSON 형식으로 분석해주세요:

1. **themes**: 현재 시장의 주요 투자 테마/트렌드 3~5개 (AI반도체, 방어주, 에너지 등)
2. **picks_analysis**: 위 추천 종목 각각에 대해 상세 분석
3. **market_narrative**: 전체 시장 내러티브 요약 (2~3문장)

반드시 아래 JSON만 출력하세요 (마크다운 없이):
{{
  "themes": [
    {{"name": "테마명", "description": "테마 설명", "hot_level": 1~10}}
  ],
  "picks_analysis": [
    {{
      "ticker": "종목코드",
      "theme_fit": "어떤 테마에 해당하는지 + 테마 부합도 설명",
      "report_summary": "이 종목의 현재 상황을 월가 리포트 스타일로 3~4문장 분석. 실적, 사업전망, 밸류에이션 관점 포함.",
      "market_context": "현재 시장 흐름(약세/강세/테마)과 연계하여 왜 지금이 매수/매도 타이밍인지 2~3문장.",
      "risk_factors": "주요 리스크 1~2가지",
      "verdict": "최종 판단 한 줄 (매수등급 + 핵심근거)"
    }}
  ],
  "market_narrative": "전체 시장 내러티브 2~3문장"
}}"""

    try:
        client = anthropic.Anthropic(api_key=_get_anthropic_key())
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()

        # JSON 추출
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if not json_match:
            raise ValueError("JSON 파싱 실패")

        result = json.loads(json_match.group())
        result["api_used"] = True
        return result

    except Exception as e:
        return {
            "themes": [{"name": "분석 불가", "description": str(e), "hot_level": 0}],
            "picks_analysis": [],
            "market_narrative": f"Claude AI 분석 실패: {e}",
            "api_used": False,
        }
