"""
Database connection module for MongoDB Atlas.
Safe, Railway-compatible version.
Handles optional connection (silent if database is not configured).
"""

import os
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

# Global instances
_mongo_client: Optional[MongoClient] = None
_db = None


# ---------------------------------------------------------------------
# CREATE CLIENT (SILENT IF NO MONGO_URI)
# ---------------------------------------------------------------------
def get_mongo_client() -> Optional[MongoClient]:
    """Create MongoDB client if MONGO_URI exists. Otherwise disable MongoDB silently."""
    global _mongo_client

    # If already created → reuse
    if _mongo_client is not None:
        return _mongo_client

    mongo_uri = os.environ.get("MONGO_URI")

    if not mongo_uri:
        logger.info("MONGO_URI not set → MongoDB disabled (safe mode).")
        return None

    try:
        _mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        _mongo_client.admin.command("ping")
        logger.info("✅ Connected to MongoDB Atlas.")
        return _mongo_client

    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        _mongo_client = None
        return None


# ---------------------------------------------------------------------
# GET DATABASE
# ---------------------------------------------------------------------
def get_database():
    """Return the MongoDB database instance or None if unavailable."""
    global _db

    if _db is not None:
        return _db

    client = get_mongo_client()
    if client is None:
        return None

    try:
        _db = client.get_database("medguardian")
        return _db
    except Exception as e:
        logger.error(f"❌ Failed to access MongoDB database: {e}")
        return None


# ---------------------------------------------------------------------
# TREND DATA SAVE
# ---------------------------------------------------------------------
def save_trend_data(city: str, disease: str, date: datetime,
                    cases: int, avg_temp: float, real_time_aqi: float) -> bool:
    """Upsert trend data. Returns False if DB disabled."""
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
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
        return True

    except Exception as e:
        logger.error(f"❌ Error saving trend data: {e}")
        return False


# ---------------------------------------------------------------------
# NEWS ITEM SAVE
# ---------------------------------------------------------------------
def save_news_item(item: dict) -> bool:
    """Save a normalized news item (optional)."""
    db = get_database()
    if db is None:
        return False

    try:
        collection = db["news"]

        # Non-blocking index creation
        try:
            collection.create_index([("id", 1)], unique=True)
            collection.create_index([("timestamp", -1)])
        except Exception:
            pass

        # Timestamp normalization
        ts = item.get("timestamp")
        if isinstance(ts, str):
            try:
                from dateutil.parser import isoparse
                ts = isoparse(ts)
            except Exception:
                ts = datetime.utcnow()
        elif not isinstance(ts, datetime):
            ts = datetime.utcnow()

        doc = dict(item)
        doc["timestamp"] = ts
        doc["ingested_at"] = datetime.utcnow()

        collection.update_one({"id": doc.get("id")}, {"$set": doc}, upsert=True)
        return True

    except Exception as e:
        logger.error(f"❌ Error saving news item: {e}")
        return False


# ---------------------------------------------------------------------
# GET TREND HISTORY
# ---------------------------------------------------------------------
def get_trend_history(city: str, disease: str, days: int = 30) -> List[Dict]:
    """Fetch trend history for plotting or forecasting."""
    db = get_database()
    if db is None:
        return []

    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        collection = db["trends"]

        cursor = collection.find(
            {
                "city": city,
                "disease": disease,
                "date": {"$gte": start_date},
            }
        ).sort("date", 1)

        output = []
        for doc in cursor:
            output.append({
                "ds": doc["date"].strftime("%Y-%m-%d"),
                "y": doc.get("cases", 0),
                "avg_temp": doc.get("avg_temp", 25.0),
                "real_time_aqi": doc.get("real_time_aqi", 80.0),
            })

        return output

    except Exception as e:
        logger.error(f"❌ Error fetching trend history: {e}")
        return []


# ---------------------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------------------
def is_mongodb_available() -> bool:
    return get_mongo_client() is not None


# ---------------------------------------------------------------------
# CLEANUP
# ---------------------------------------------------------------------
def close_mongo_connection():
    """Close the Mongo client cleanly."""
    global _mongo_client, _db

    if _mongo_client:
        try:
            _mongo_client.close()
            logger.info("MongoDB connection closed.")
        except Exception:
            pass

    _mongo_client = None
    _db = None
