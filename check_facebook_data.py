#!/usr/bin/env python3
"""
Script to check the stored Facebook data in MongoDB.
"""

import sys
from pathlib import Path
from pymongo import MongoClient
import json
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils import config


def check_facebook_data():
    """Check the Facebook data stored in MongoDB."""
    try:
        # Connect to MongoDB
        client = MongoClient(config.mongo_connection_string)
        db = client[config.mongo_database]
        collection = db[config.mongo_collection]
        
        print("Facebook Data Analysis")
        print("=" * 50)
        
        # Get Facebook activity counts by type
        facebook_pipeline = [
            {"$match": {"platform": "facebook"}},
            {"$group": {
                "_id": "$tags",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        facebook_counts = list(collection.aggregate(facebook_pipeline))
        
        print("Facebook Activity Types:")
        for item in facebook_counts:
            tags = item["_id"]
            count = item["count"]
            activity_type = [tag for tag in tags if tag.startswith("facebook_")][0] if any(tag.startswith("facebook_") for tag in tags) else "unknown"
            print(f"  {activity_type}: {count} items")
        
        print("\nRecent Facebook Activities:")
        recent_facebook = collection.find(
            {"platform": "facebook"},
            {"title": 1, "published_date": 1, "tags": 1, "_id": 0}
        ).sort("published_date", -1).limit(10)
        
        for activity in recent_facebook:
            date_str = activity["published_date"].strftime("%Y-%m-%d %H:%M")
            tags = [tag for tag in activity.get("tags", []) if tag.startswith("facebook_")]
            activity_type = tags[0] if tags else "unknown"
            print(f"  {date_str} - {activity_type}: {activity['title'][:60]}...")
        
        # Total counts
        total_facebook = collection.count_documents({"platform": "facebook"})
        total_all = collection.count_documents({})
        
        print(f"\nSummary:")
        print(f"  Total Facebook activities: {total_facebook}")
        print(f"  Total all items: {total_all}")
        
        client.close()
        
    except Exception as e:
        print(f"Error checking Facebook data: {str(e)}")


if __name__ == "__main__":
    check_facebook_data()