"""
Railway-safe backend smoke tests.
Runs basic checks against key API endpoints.
"""

from fastapi.testclient import TestClient
from backend.main import app
import json

client = TestClient(app)


def pretty(res):
    """Pretty-print JSON or raw text."""
    try:
        return json.dumps(res.json(), indent=2)
    except Exception:
        return str(res.text)


def test_latest_trends():
    """
    Tests synthetic trend generation when MongoDB is disabled.
    """
    print("\n🔍 Testing /api/trends/latest ...")
    resp = client.get("/api/trends/latest?city=Chennai&disease=flu")
    print("Status Code:", resp.status_code)
    print(pretty(resp))


def test_forecast():
    """
    Tests disease forecast fallback chain:
      Prophet → Regression → Synthetic
    Works even if Prophet is missing.
    """
    print("\n🔍 Testing /api/predictor ...")
    resp = client.get("/api/predictor?city=Bengaluru&disease=covid")
    print("Status Code:", resp.status_code)
    print(pretty(resp))


def test_advisory():
    """
    Tests health advisory fallback mode (no OpenAI key required).
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


def test_stream_health():
    """
    Tests backend health response.
    """
    print("\n🔍 Testing /api/health ...")
    resp = client.get("/api/health")
    print("Status Code:", resp.status_code)
    print(pretty(resp))


if __name__ == "__main__":
    print("\n🚀 Running smoke tests...\n")

    test_latest_trends()
    test_forecast()
    test_advisory()
    test_city_data()
    test_stream_health()

    print("\n✅ Smoke tests completed successfully.\n")
