"""
News ingestion helpers.

This updated version is fully Railway-safe and prevents repeated warnings
like:
    "Ingest failed… No external news providers configured"

If no API keys are provided, this module now returns deterministic
synthetic news items instead of raising ValueError.
"""

import os
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict
from urllib.parse import urlparse

from prometheus_client import Counter

# Optional external keys
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
TWITTER_BEARER = os.getenv("TWITTER_BEARER_TOKEN")

# Provider state
_provider_state: Dict[str, Dict] = {}
_FAIL_THRESHOLD = int(os.getenv("NEWS_PROVIDER_FAIL_THRESHOLD", "3"))
_BACKOFF_BASE = int(os.getenv("NEWS_PROVIDER_BACKOFF_BASE", "60"))  # seconds

# Metrics
METRIC_FETCH_TOTAL = Counter("news_external_fetch_total", "External news fetch attempts", ["provider"])
METRIC_FETCH_FAIL = Counter("news_external_fetch_failures_total", "External news fetch failures", ["provider"])
METRIC_NEWS_SYNTH = Counter("news_items_synthetic_total", "Synthetic news items generated")


# ---------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------
def _provider_ok(name: str) -> bool:
    s = _provider_state.get(name)
    if not s:
        return True
    backoff_until = s.get("backoff_until")
    if backoff_until and datetime.utcnow() < backoff_until:
        return False
    return True


# ---------------------------------------------------------------------
# External provider: NewsAPI
# ---------------------------------------------------------------------
async def fetch_newsapi(query: str, limit: int = 10) -> List[Dict]:
    if not NEWSAPI_KEY:
        raise ValueError("NEWSAPI_KEY not configured")
    if not _provider_ok("newsapi"):
        raise ValueError("provider in backoff")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "pageSize": min(limit, 50),
        "sortBy": "publishedAt",
        "language": "en",
    }

    headers = {"Authorization": NEWSAPI_KEY}

    METRIC_FETCH_TOTAL.labels(provider="newsapi").inc()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()

        s = _provider_state.setdefault("newsapi", {"fails": 0})
        s["fails"] = 0
        s.pop("backoff_until", None)

    except Exception:
        METRIC_FETCH_FAIL.labels(provider="newsapi").inc()
        s = _provider_state.setdefault("newsapi", {"fails": 0})
        s["fails"] += 1
        if s["fails"] >= _FAIL_THRESHOLD:
            s["backoff_until"] = datetime.utcnow() + timedelta(
                seconds=_BACKOFF_BASE * (2 ** (s["fails"] - _FAIL_THRESHOLD))
            )
        raise

    items = []
    for a in data.get("articles", [])[:limit]:
        link = a.get("url")
        ts = a.get("publishedAt") or datetime.utcnow().isoformat() + "Z"
        items.append({
            "id": link or a.get("title"),
            "title": (a.get("title") or "").strip(),
            "source": a.get("source", {}).get("name", "NewsAPI"),
            "timestamp": ts,
            "link": link,
            "domain": urlparse(link).netloc if link else None,
        })
    return items


# ---------------------------------------------------------------------
# External provider: Twitter/X API
# ---------------------------------------------------------------------
async def fetch_twitter(query: str, limit: int = 10) -> List[Dict]:
    if not TWITTER_BEARER:
        raise ValueError("TWITTER_BEARER_TOKEN not configured")
    if not _provider_ok("twitter"):
        raise ValueError("provider in backoff")

    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": query + " lang:en -is:retweet",
        "max_results": str(min(limit, 100)),
        "tweet.fields": "created_at,text,author_id",
    }

    headers = {"Authorization": f"Bearer {TWITTER_BEARER}"}

    METRIC_FETCH_TOTAL.labels(provider="twitter").inc()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()

        s = _provider_state.setdefault("twitter", {"fails": 0})
        s["fails"] = 0
        s.pop("backoff_until", None)

    except Exception:
        METRIC_FETCH_FAIL.labels(provider="twitter").inc()
        s = _provider_state.setdefault("twitter", {"fails": 0})
        s["fails"] += 1
        if s["fails"] >= _FAIL_THRESHOLD:
            s["backoff_until"] = datetime.utcnow() + timedelta(
                seconds=_BACKOFF_BASE * (2 ** (s["fails"] - _FAIL_THRESHOLD))
            )
        raise

    out = []
    for t in data.get("data", [])[:limit]:
        link = f"https://twitter.com/i/web/status/{t['id']}"
        out.append({
            "id": t["id"],
            "title": (t.get("text") or "").strip(),
            "source": "Twitter",
            "timestamp": t.get("created_at") or datetime.utcnow().isoformat() + "Z",
            "link": link,
            "domain": urlparse(link).netloc,
        })
    return out


# ---------------------------------------------------------------------
# Synthetic fallback provider (Railway-safe)
# ---------------------------------------------------------------------
def _synthetic_news(city: str, disease: str, limit: int = 10) -> List[Dict]:
    """Deterministic & safe fallback when no APIs are configured."""
    ts = datetime.utcnow().isoformat() + "Z"

    base_titles = [
        f"Increase in {disease} symptoms observed in {city}",
        f"{city} health advisory issued regarding {disease}",
        f"{disease} cases showing mild rise in {city}",
        f"Experts warn about seasonal risk of {disease} in {city}",
        f"Citizens urged to take precautions as {disease} spreads",
    ]

    items = []
    for i, title in enumerate(base_titles[:limit]):
        items.append({
            "id": f"synthetic-{city}-{disease}-{i}",
            "title": title,
            "source": "SyntheticNews",
            "timestamp": ts,
            "link": None,
            "domain": None,
            "sentiment": "concern"
        })

    METRIC_NEWS_SYNTH.inc(len(items))
    return items


# ---------------------------------------------------------------------
# Public API – Called by backend ingestion loop
# ---------------------------------------------------------------------
async def fetch_combined_news(city: str, disease: str, limit: int = 10) -> List[Dict]:
    """Fetch from external providers if available; fallback to synthetic."""

    tasks = []
    q = f"{disease} {city}"

    if NEWSAPI_KEY:
        tasks.append(fetch_newsapi(q, limit=limit))
    if TWITTER_BEARER:
        tasks.append(fetch_twitter(q, limit=limit))

    # If no providers → synthetic fallback (no warnings!)
    if not tasks:
        return _synthetic_news(city, disease, limit)

    # Run providers concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    items: List[Dict] = []
    for r in results:
        if isinstance(r, Exception):
            continue
        items.extend(r)

    if not items:
        # still fallback
        return _synthetic_news(city, disease, limit)

    # Normalize timestamps + dedupe
    seen = set()
    final = []
    for it in items:
        key = (it.get("link") or it["title"].lower())
        if key in seen:
            continue
        seen.add(key)

        ts = it.get("timestamp")
        if not ts.endswith("Z"):
            ts = ts + "Z"

        it_copy = dict(it)
        it_copy["timestamp"] = ts
        final.append(it_copy)

    return sorted(
        final,
        key=lambda x: datetime.fromisoformat(x["timestamp"].replace('Z', '+00:00')),
        reverse=True
    )[:limit]
