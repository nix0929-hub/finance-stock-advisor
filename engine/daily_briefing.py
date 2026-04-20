"""
Daily Market Briefing Engine
Fetches US/Korea index data and uses Gemini AI to analyze market movements.
Returns structured analysis of why indices moved, key events, and outlook.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

import anthropic
import requests
import yfinance as yf

from config import _get_anthropic_key, NEWS_API_KEY

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Index tickers and display names
# ---------------------------------------------------------------------------
INDEX_TICKERS: dict[str, str] = {
    "^GSPC":   "S&P 500",
    "^IXIC":   "NASDAQ",
    "^DJI":    "DOW",
    "^RUT":    "Russell 2000",
    "^KS11":   "KOSPI",
    "^KQ11":   "KOSDAQ",
    "^VIX":    "VIX",
    "^TNX":    "US 10Y Yield",
    "DX-Y.NYB": "DXY (Dollar Index)",
}


# ---------------------------------------------------------------------------
# Data fetching helpers
# ---------------------------------------------------------------------------

def _fetch_index_data() -> dict[str, dict[str, Any]]:
    """Fetch latest price data for all tracked indices via yfinance.

    Returns a dict keyed by display name with price, change, and change_pct.
    Missing or errored tickers are silently skipped.
    """
    results: dict[str, dict[str, Any]] = {}

    for ticker_symbol, display_name in INDEX_TICKERS.items():
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")

            if hist.empty or len(hist) < 2:
                logger.warning("Insufficient data for %s", ticker_symbol)
                continue

            latest_close: float = float(hist["Close"].iloc[-1])
            prev_close: float = float(hist["Close"].iloc[-2])
            change: float = latest_close - prev_close
            change_pct: float = (change / prev_close) * 100 if prev_close != 0 else 0.0

            results[display_name] = {
                "price": round(latest_close, 2),
                "chg": round(change, 2),
                "chg_pct": round(change_pct, 2),
            }
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", ticker_symbol, exc)

    return results


def _fetch_market_news(max_articles: int = 10) -> list[dict[str, str]]:
    """Fetch top market / business news from NewsAPI.

    Returns a list of dicts with title, description, and source.
    Returns empty list on failure.
    """
    if not NEWS_API_KEY:
        logger.warning("NEWS_API_KEY is not configured; skipping news fetch.")
        return []

    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "category": "business",
        "language": "en",
        "pageSize": max_articles,
        "apiKey": NEWS_API_KEY,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        articles: list[dict[str, str]] = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "source": article.get("source", {}).get("name", ""),
            })
        return articles

    except requests.RequestException as exc:
        logger.error("NewsAPI request failed: %s", exc)
        return []
    except (ValueError, KeyError) as exc:
        logger.error("Failed to parse NewsAPI response: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Claude AI analysis
# ---------------------------------------------------------------------------

def _build_analysis_prompt(
    indices: dict[str, dict[str, Any]],
    news: list[dict[str, str]],
) -> str:
    """Build the analysis prompt for Claude."""

    index_summary_lines: list[str] = []
    for name, vals in indices.items():
        direction = "+" if vals["chg"] >= 0 else ""
        index_summary_lines.append(
            f"- {name}: {vals['price']} ({direction}{vals['chg']}, "
            f"{direction}{vals['chg_pct']}%)"
        )
    index_block = "\n".join(index_summary_lines)

    news_lines: list[str] = []
    for article in news[:8]:
        news_lines.append(f"- [{article['source']}] {article['title']}")
    news_block = "\n".join(news_lines) if news_lines else "(No news data available)"

    today_str = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""당신은 월가 수석 이코노미스트입니다. 오늘({today_str}) 미국 및 한국 주요 지수의 변동 이유를 분석하세요.

## 오늘의 지수 데이터
{index_block}

## 주요 뉴스 헤드라인
{news_block}

## 분석 요청
위 데이터를 바탕으로 다음 항목을 한국어로 상세히 분석하세요:
1. 미국 시장 분석 (us_analysis): 미국 지수 상승/하락의 주요 원인 (3~5문장)
2. 한국 시장 분석 (kr_analysis): 한국 지수 변동 원인과 미국 시장과의 연관성 (3~5문장)
3. 주요 이벤트 (key_events): 시장에 영향을 준 핵심 이벤트 3~5개 (리스트)
4. 내일 전망 (tomorrow_outlook): 내일 시장 방향성 전망 (2~3문장)
5. 뉴스 번역 (news_kr): 위 영문 뉴스 헤드라인을 한국어로 번역한 리스트 (원문과 동일한 순서)

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만 출력하세요:
{{
    "us_analysis": "...",
    "kr_analysis": "...",
    "key_events": ["...", "...", "..."],
    "tomorrow_outlook": "...",
    "news_kr": ["번역된 뉴스1", "번역된 뉴스2", "..."]
}}"""
    return prompt


def _call_claude(prompt: str) -> Optional[dict[str, Any]]:
    """Call Claude API and parse the JSON response."""
    api_key = _get_anthropic_key()
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY is not configured; skipping AI analysis.")
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text: str = message.content[0].text.strip()

        # Strip markdown code fences if present
        cleaned = raw_text
        if cleaned.startswith("```"):
            first_newline = cleaned.index("\n")
            cleaned = cleaned[first_newline + 1:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        result = json.loads(cleaned)
        return result

    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to parse Claude response: %s", exc)
        return None
    except Exception as exc:
        logger.error("Claude API request failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Fallback analysis (when API is unavailable)
# ---------------------------------------------------------------------------

def _generate_fallback_analysis(
    indices: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Generate a basic rule-based analysis when Gemini is unavailable."""

    sp500 = indices.get("S&P 500", {})
    nasdaq = indices.get("NASDAQ", {})
    kospi = indices.get("KOSPI", {})
    vix = indices.get("VIX", {})

    # US analysis
    us_parts: list[str] = []
    if sp500:
        direction = "상승" if sp500["chg"] >= 0 else "하락"
        us_parts.append(
            f"S&P 500이 {abs(sp500['chg_pct']):.2f}% {direction}했습니다."
        )
    if nasdaq:
        direction = "상승" if nasdaq["chg"] >= 0 else "하락"
        us_parts.append(
            f"NASDAQ은 {abs(nasdaq['chg_pct']):.2f}% {direction}했습니다."
        )
    if vix:
        if vix["price"] > 25:
            us_parts.append("VIX가 25를 상회하며 시장 불안감이 높은 상태입니다.")
        elif vix["price"] < 15:
            us_parts.append("VIX가 낮은 수준으로 시장이 안정적입니다.")
    us_analysis = " ".join(us_parts) if us_parts else "미국 시장 데이터를 가져올 수 없습니다."

    # KR analysis
    kr_parts: list[str] = []
    if kospi:
        direction = "상승" if kospi["chg"] >= 0 else "하락"
        kr_parts.append(
            f"KOSPI가 {abs(kospi['chg_pct']):.2f}% {direction}했습니다."
        )
    kr_analysis = " ".join(kr_parts) if kr_parts else "한국 시장 데이터를 가져올 수 없습니다."

    key_events = ["AI 분석 미사용 - API 키 미설정 또는 호출 실패"]
    tomorrow_outlook = "AI 분석을 사용할 수 없어 자동 전망을 제공하지 않습니다. 주요 경제 지표와 뉴스를 직접 확인하세요."

    return {
        "us_analysis": us_analysis,
        "kr_analysis": kr_analysis,
        "key_events": key_events,
        "tomorrow_outlook": tomorrow_outlook,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_daily_briefing() -> dict[str, Any]:
    """Generate the full daily market briefing.

    Returns:
        {
            "indices": {name: {"price", "chg", "chg_pct"}, ...},
            "us_analysis": str,
            "kr_analysis": str,
            "key_events": [str, ...],
            "tomorrow_outlook": str,
            "api_used": bool,
            "timestamp": str,
        }
    """
    # 1) Fetch index data
    indices = _fetch_index_data()

    # 2) Fetch news
    news = _fetch_market_news()

    # 3) Call Claude for analysis
    api_used = False
    prompt = _build_analysis_prompt(indices, news)
    ai_result = _call_claude(prompt)

    if ai_result is not None:
        api_used = True
        us_analysis = ai_result.get("us_analysis", "")
        kr_analysis = ai_result.get("kr_analysis", "")
        key_events = ai_result.get("key_events", [])
        tomorrow_outlook = ai_result.get("tomorrow_outlook", "")
        news_kr = ai_result.get("news_kr", [])
    else:
        fallback = _generate_fallback_analysis(indices)
        us_analysis = fallback["us_analysis"]
        kr_analysis = fallback["kr_analysis"]
        key_events = fallback["key_events"]
        tomorrow_outlook = fallback["tomorrow_outlook"]
        news_kr = []

    # Attach Korean titles to news articles
    news_with_kr = []
    for i, article in enumerate(news):
        article_copy = dict(article)
        if i < len(news_kr):
            article_copy["title_kr"] = news_kr[i]
        news_with_kr.append(article_copy)

    return {
        "indices": indices,
        "us_analysis": us_analysis,
        "kr_analysis": kr_analysis,
        "key_events": key_events,
        "tomorrow_outlook": tomorrow_outlook,
        "news": news_with_kr,
        "api_used": api_used,
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    briefing = get_daily_briefing()
    print(json.dumps(briefing, ensure_ascii=False, indent=2))
