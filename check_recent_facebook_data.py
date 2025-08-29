#!/usr/bin/env python3
"""
Script to check the most recently processed Facebook data in MongoDB.
Shows only Facebook posts from the latest pipeline runs.
"""

import sys
from pathlib import Path
from pymongo import MongoClient
import json
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils import config


def check_recent_facebook_data():
    """Check the recent Facebook posts stored in MongoDB."""
    try:
        # Connect to MongoDB
        client = MongoClient(config.mongo_connection_string)
        db = client[config.mongo_database]
        collection = db[config.mongo_collection]
        
        print("Recent Facebook Posts Analysis")
        print("=" * 50)
        
        # Get recent Facebook posts only (from last 24 hours of processing)
        recent_cutoff = datetime.now() - timedelta(days=1)
        
        facebook_posts_pipeline = [
            {"$match": {
                "platform": "facebook", 
                "tags": {"$in": ["facebook_post"]},
                "scraped_at": {"$gte": recent_cutoff}
            }},
            {"$sort": {"scraped_at": -1}},
            {"$limit": 20}
        ]
        
        recent_posts = list(collection.aggregate(facebook_posts_pipeline))
        
        print("Recent Facebook Posts (last 24 hours of processing):")
        for post in recent_posts:
            scraped_str = post["scraped_at"].strftime("%Y-%m-%d %H:%M")
            published_str = post["published_date"].strftime("%Y-%m-%d") if post.get("published_date") else "Unknown"
            print(f"  {scraped_str} - Published: {published_str} - {post['title'][:80]}...")
        
        # Count posts by processing date
        posts_by_date_pipeline = [
            {"$match": {
                "platform": "facebook", 
                "tags": {"$in": ["facebook_post"]}
            }},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$scraped_at"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 10}
        ]
        
        posts_by_date = list(collection.aggregate(posts_by_date_pipeline))
        
        print(f"\nFacebook Posts by Processing Date:")
        for item in posts_by_date:
            date = item["_id"]
            count = item["count"]
            print(f"  {date}: {count} posts")
        
        # Total counts
        total_facebook_posts = collection.count_documents({
            "platform": "facebook",
            "tags": {"$in": ["facebook_post"]}
        })
        total_facebook_all = collection.count_documents({"platform": "facebook"})
        total_all = collection.count_documents({})
        
        print(f"\nSummary:")
        print(f"  Total Facebook posts: {total_facebook_posts}")
        print(f"  Total Facebook activities (all types): {total_facebook_all}")
        print(f"  Total all items: {total_all}")
        
        # Check if there are other activity types (legacy data)
        other_activities = collection.count_documents({
            "platform": "facebook",
            "tags": {"$nin": ["facebook_post"]}
        })
        
        if other_activities > 0:
            print(f"\nNote: {other_activities} legacy Facebook activities (reactions/comments) still in database")
            print("These are from previous pipeline runs and will not be processed again.")
        
        client.close()
        
    except Exception as e:
        print(f"Error checking Facebook data: {str(e)}")


if __name__ == "__main__":
    check_recent_facebook_data()