"""
News ingestion helpers — fetch and normalize news/social items from external APIs.

Environment variables used:
 - NEWSAPI_KEY: NewsAPI.org key (optional)
 - TWITTER_BEARER_TOKEN: Twitter/X API v2 bearer token (optional)

If keys are not present, functions will raise a ValueError so callers can fallback to synthetic data.
"""
import os
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urlparse

from prometheus_client import Counter

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
TWITTER_BEARER = os.getenv("TWITTER_BEARER_TOKEN")

# Provider circuit-breaker state
_provider_state: Dict[str, Dict] = {}
_FAIL_THRESHOLD = int(os.getenv("NEWS_PROVIDER_FAIL_THRESHOLD", "3"))
_BACKOFF_BASE = int(os.getenv("NEWS_PROVIDER_BACKOFF_BASE", "60"))  # seconds

# Metrics
METRIC_FETCH_TOTAL = Counter("news_external_fetch_total", "Number of external news fetch attempts", ["provider"]) 
METRIC_FETCH_FAIL = Counter("news_external_fetch_failures_total", "Number of external news fetch failures", ["provider"]) 
METRIC_NEWS_SAVED = Counter("news_items_saved_total", "Number of news items saved to DB")


def _provider_ok(name: str) -> bool:
    s = _provider_state.get(name)
    if not s:
        return True
    backoff_until = s.get("backoff_until")
    if backoff_until and datetime.utcnow() < backoff_until:
        return False
    return True


async def fetch_newsapi(query: str, limit: int = 10) -> List[Dict]:
    """Fetch top articles from NewsAPI matching query."""
    provider = "newsapi"
    if not NEWSAPI_KEY:
        raise ValueError("NEWSAPI_KEY not configured")
    if not _provider_ok(provider):
        raise ValueError("provider in backoff")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "pageSize": min(limit, 50),
        "sortBy": "publishedAt",
        "language": "en",
    }

    headers = {"Authorization": NEWSAPI_KEY}

    METRIC_FETCH_TOTAL.labels(provider=provider).inc()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
        # reset failure counter on success
        s = _provider_state.setdefault(provider, {"fails": 0})
        s["fails"] = 0
        s.pop("backoff_until", None)
    except Exception as exc:
        METRIC_FETCH_FAIL.labels(provider=provider).inc()
        # update provider state
        s = _provider_state.setdefault(provider, {"fails": 0})
        s["fails"] = s.get("fails", 0) + 1
        if s["fails"] >= _FAIL_THRESHOLD:
            s["backoff_until"] = datetime.utcnow() + timedelta(seconds=_BACKOFF_BASE * (2 ** (s["fails"] - _FAIL_THRESHOLD)))
        raise

    items = []
    for a in data.get("articles", [])[:limit]:
        ts = a.get("publishedAt") or a.get("published_at") or datetime.utcnow().isoformat() + "Z"
        link = a.get("url")
        items.append({
            "id": link or a.get("title"),
            "title": (a.get("title") or "").strip(),
            "source": a.get("source", {}).get("name", "NewsAPI"),
            "timestamp": ts,
            "link": link,
            "raw": a,
            "domain": urlparse(link).netloc if link else None
        })

    return items


async def fetch_twitter(query: str, limit: int = 10) -> List[Dict]:
    """Fetch recent tweets using Twitter API v2 recent search.

    Note: This requires TWITTER_BEARER_TOKEN to be set and appropriate access.
    """
    provider = "twitter"
    if not TWITTER_BEARER:
        raise ValueError("TWITTER_BEARER_TOKEN not configured")
    if not _provider_ok(provider):
        raise ValueError("provider in backoff")

    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": query + " lang:en -is:retweet",
        "max_results": str(min(limit, 100)),
        "tweet.fields": "created_at,text,author_id",
    }

    headers = {"Authorization": f"Bearer {TWITTER_BEARER}"}

    METRIC_FETCH_TOTAL.labels(provider=provider).inc()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
        # reset failure counter on success
        s = _provider_state.setdefault(provider, {"fails": 0})
        s["fails"] = 0
        s.pop("backoff_until", None)
    except Exception as exc:
        METRIC_FETCH_FAIL.labels(provider=provider).inc()
        s = _provider_state.setdefault(provider, {"fails": 0})
        s["fails"] = s.get("fails", 0) + 1
        if s["fails"] >= _FAIL_THRESHOLD:
            s["backoff_until"] = datetime.utcnow() + timedelta(seconds=_BACKOFF_BASE * (2 ** (s["fails"] - _FAIL_THRESHOLD)))
        raise

    items = []
    for t in data.get("data", [])[:limit]:
        link = f"https://twitter.com/i/web/status/{t.get('id')}"
        items.append({
            "id": t.get("id"),
            "title": (t.get("text") or "").strip(),
            "source": "Twitter",
            "timestamp": t.get("created_at") or datetime.utcnow().isoformat() + "Z",
            "link": link,
            "raw": t,
            "domain": urlparse(link).netloc
        })

    return items


def _simple_sentiment(text: str) -> str:
    if not text:
        return "neutral"
    t = text.lower()
    if any(k in t for k in ["outbreak", "alarm", "urgent", "surge", "spike"]):
        return "alarm"
    if any(k in t for k in ["concern", "worry", "rise", "increase"]):
        return "concern"
    if any(k in t for k in ["advisory", "recommend", "precaution", "warn"]):
        return "advisory"
    return "neutral"


def _enhanced_sentiment(text: str) -> str:
    """Try to compute sentiment using NLTK VADER if available, otherwise fallback."""
    if not text:
        return "neutral"
    try:
        from nltk.sentiment import SentimentIntensityAnalyzer
        try:
            sia = SentimentIntensityAnalyzer()
        except Exception:
            # attempt to download vader_lexicon if missing
            import nltk
            nltk.download("vader_lexicon", quiet=True)
            from nltk.sentiment import SentimentIntensityAnalyzer
            sia = SentimentIntensityAnalyzer()

        scores = sia.polarity_scores(text)
        # return simplified categories
        if scores["compound"] >= 0.5:
            return "positive"
        if scores["compound"] <= -0.3:
            return "alarm"
        if scores["compound"] < 0:
            return "concern"
        return "neutral"
    except Exception:
        return _simple_sentiment(text)


async def fetch_combined_news(city: str, disease: str, limit: int = 10) -> List[Dict]:
    """Try to fetch combined items from configured providers. If none configured, raise ValueError."""
    q = f"{disease} {city}"
    tasks = []
    if NEWSAPI_KEY:
        tasks.append(fetch_newsapi(q, limit=limit))
    if TWITTER_BEARER:
        tasks.append(fetch_twitter(q, limit=limit))

    if not tasks:
        raise ValueError("No external news providers configured")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    items = []
    for res in results:
        if isinstance(res, Exception):
            continue
        for it in res:
            it_copy = dict(it)
            title = it_copy.get("title") or ""
            # enhanced sentiment
            it_copy["sentiment"] = _enhanced_sentiment(title)
            # normalize timestamp to ISO
            ts = it_copy.get("timestamp")
            try:
                if isinstance(ts, str):
                    # make sure it ends with Z
                    if ts.endswith("Z"):
                        iso_ts = ts
                    else:
                        iso_ts = ts
                else:
                    iso_ts = datetime.utcnow().isoformat() + "Z"
            except Exception:
                iso_ts = datetime.utcnow().isoformat() + "Z"
            it_copy["timestamp"] = iso_ts
            # extract domain
            link = it_copy.get("link")
            it_copy["domain"] = urlparse(link).netloc if link else None
            items.append(it_copy)

    # dedupe by link or normalized title
    seen = set()
    deduped = []
    for it in items:
        key = (it.get("link") or it.get("title", "").strip().lower())
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        deduped.append(it)

    # sort by timestamp desc
    def _ts(itm):
        try:
            return datetime.fromisoformat(itm.get("timestamp").replace('Z', '+00:00'))
        except Exception:
            return datetime.utcnow()

    items_sorted = sorted(deduped, key=_ts, reverse=True)[:limit]
    return items_sorted
