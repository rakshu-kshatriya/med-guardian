"""
Railway-safe backend smoke tests.
Runs basic checks against key API endpoints.
"""

from fastapi.testclient import TestClient
from backend.main import app
import json

client = TestClient(app)


def pretty(res):
    try:
        return json.dumps(res.json(), indent=2)
    except Exception:
        return str(res.text)


def test_news_fallback():
    """
    Test /api/news_trends fallback mode.
    Should work even when NEWSAPI_KEY or TWITTER_BEARER are not set.
    """
    print("\n🔍 Testing /api/news_trends fallback...")
    resp = client.get("/api/news_trends?city=Chennai&disease=flu&limit=5")
    print("Status Code:", resp.status_code)
    print(pretty(resp))


def test_latest_trends():
    """
    Test synthetic trend generation when MongoDB disabled.
    """
    print("\n🔍 Testing /api/trends/latest ...")
    resp = client.get("/api/trends/latest?city=Bengaluru&disease=covid")
    print("Status Code:", resp.status_code)
    print(pretty(resp))


def test_forecast():
    """
    Tests disease forecast fallback (Prophet → regression → synthetic).
    """
    print("\n🔍 Testing /api/predictor ...")
    resp = client.get("/api/predictor?city=Bengaluru&disease=covid")
    print("Status Code:", resp.status_code)
    print(pretty(resp))


def test_advisory():
    """
    Tests advisory generation (fallback since no OpenAI key by default).
    """
    print("\n🔍 Testing /api/advisory_service ...")
    resp = client.get("/api/advisory_service?city=Chennai&disease=flu&aqi=80&temp=28")
    print("Status Code:", resp.status_code)
    print(pretty(resp))


def test_city_data():
    """
    Tests city list endpoint.
    """
    print("\n🔍 Testing /api/city_data ...")
    resp = client.get("/api/city_data")
    print("Status Code:", resp.status_code)
    print(pretty(resp))


if __name__ == "__main__":
    print("\n🚀 Running smoke tests...")
    test_news_fallback()
    test_latest_trends()
    test_forecast()
    test_advisory()
    test_city_data()
    print("\n✅ Smoke tests completed.\n")
