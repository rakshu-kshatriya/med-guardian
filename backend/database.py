"""
Database connection module for MongoDB Atlas.
Handles connection, disconnection, and data operations.
"""

import os
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

# Global MongoDB client
_mongo_client: Optional[MongoClient] = None
_db = None


def get_mongo_client() -> Optional[MongoClient]:
    """Get or create MongoDB client."""
    global _mongo_client
    
    if _mongo_client is not None:
        return _mongo_client
    
    mongo_uri = os.environ.get("MONGO_URI")
    
    if not mongo_uri:
        logger.info("MONGO_URI not set, MongoDB disabled")
        return None
    
    try:
        _mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        # Test connection
        _mongo_client.admin.command('ping')
        logger.info("✅ Connected to MongoDB Atlas")
        return _mongo_client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        _mongo_client = None
        return None
    except Exception as e:
        logger.error(f"❌ MongoDB connection error: {e}")
        _mongo_client = None
        return None


def get_database():
    """Get database instance."""
    global _db
    
    if _db is not None:
        return _db
    
    client = get_mongo_client()
    if client is None:
        return None
    
    _db = client.get_database("medguardian")
    return _db


def save_trend_data(city: str, disease: str, date: datetime, cases: int, avg_temp: float, real_time_aqi: float):
    """Save trend data to MongoDB."""
    db = get_database()
    if db is None:
        return False
    
    try:
        collection = db["trends"]
        collection.update_one(
            {
                "city": city,
                "disease": disease,
                "date": date
            },
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


def get_trend_history(city: str, disease: str, days: int = 30) -> List[Dict]:
    """Get trend history from MongoDB."""
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
                "real_time_aqi": doc.get("real_time_aqi", 80.0)
            })
        
        return results
    except Exception as e:
        logger.error(f"Error fetching trend history: {e}")
        return []


def is_mongodb_available() -> bool:
    """Check if MongoDB is available."""
    return get_mongo_client() is not None


def close_mongo_connection():
    """Close MongoDB connection."""
    global _mongo_client, _db
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        _db = None
        logger.info("MongoDB connection closed")

