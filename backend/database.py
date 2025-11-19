"""
Database connection module for MongoDB Atlas.
Safe, Railway-compatible version.
Handles optional connection (no warnings if no DB available).
"""

import os
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

# Global MongoDB client & DB
_mongo_client: Optional[MongoClient] = None
_db = None


# ---------------------------------------------------------
# CONNECT TO MONGODB (SILENT if not available)
# ---------------------------------------------------------
def get_mongo_client() -> Optional[MongoClient]:
    """Create MongoDB client if MONGO_URI exists. Otherwise disable MongoDB silently."""
    global _mongo_client

    if _mongo_client is not None:
        return _mongo_client

    mongo_uri = os.environ.get("MONGO_URI")

    if not mongo_uri:
        # No DB configured → silently disable
        logger.info("MONGO_URI not set, MongoDB disabled.")
        return None

    try:
        _mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        _mongo_client.admin.command("ping")
        logger.info("Connected to MongoDB.")
        return _mongo_client

    except Exception:
        logger.error("MongoDB connection failed.")
        _mongo_client = None
        return None


def get_database():
    """Return DB instance, or None if Mongo is disabled."""
    global _db

    if _db is not None:
        return _db

    client = get_mongo_client()
    if client is None:
        return None

    _db = client.get_database("medguardian")
    return _db


# ---------------------------------------------------------
# SAVE TREND DATA (optional storage)
# ---------------------------------------------------------
def save_trend_data(city: str, disease: str, date: datetime, cases: int,
                    avg_temp: float, real_time_aqi: float):
    """Upsert trend data to DB. Returns False if DB is disabled."""
    db = get_database()
    if db is None:
        return False

    try:
        collection = db["trends"]
        collection.update_one(
            {"city": city, "disease": disease, "date": date},
            {
                "$set": {
                    "city": city,
                    "disease": disease,
                    "date": date,
                    "cases": cases,
                    "avg_temp": avg_temp,
                    "real_time_aqi": real_time_aqi,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        return True

    except Exception as e:
        logger.error(f"Error saving trend data: {e}")
        return False


# ---------------------------------------------------------
# SAVE NEWS ITEM (optional storage)
# ---------------------------------------------------------
def save_news_item(item: dict) -> bool:
    """Save normalized news item if DB enabled."""
    db = get_database()
    if db is None:
        return False

    try:
        collection = db["news"]

        # Indexes
        try:
            collection.create_index([("id", 1)], unique=True)
            collection.create_index([("timestamp", -1)])
        except Exception:
            pass

        # Parse timestamp if needed
        ts = item.get("timestamp", datetime.utcnow())
        if isinstance(ts, str):
            try:
                from dateutil.parser import isoparse
                ts = isoparse(ts)
            except Exception:
                ts = datetime.utcnow()

        doc = dict(item)
        doc["timestamp"] = ts
        doc["ingested_at"] = datetime.utcnow()

        collection.update_one({"id": doc.get("id")}, {"$set": doc}, upsert=True)
        return True

    except Exception as e:
        logger.error(f"Error saving news item: {e}")
        return False


# ---------------------------------------------------------
# TREND HISTORY FETCH
# ---------------------------------------------------------
def get_trend_history(city: str, disease: str, days: int = 30) -> List[Dict]:
    """Fetch historical trend data."""
    db = get_database()
    if db is None:
        return []

    try:
        collection = db["trends"]
        start_date = datetime.utcnow() - timedelta(days=days)

        cursor = collection.find(
            {
                "city": city,
                "disease": disease,
                "date": {"$gte": start_date}
            }
        ).sort("date", 1)

        results = []
        for doc in cursor:
            results.append({
                "ds": doc["date"].strftime("%Y-%m-%d"),
                "y": doc.get("cases", 0),
                "avg_temp": doc.get("avg_temp", 25.0),
                "real_time_aqi": doc.get("real_time_aqi", 80.0),
            })

        return results

    except Exception as e:
        logger.error(f"Error fetching trends: {e}")
        return []


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------
def is_mongodb_available() -> bool:
    return get_mongo_client() is not None


def close_mongo_connection():
    global _mongo_client, _db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _db = None
        logger.info("MongoDB connection closed.")
