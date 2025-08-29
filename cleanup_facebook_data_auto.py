#!/usr/bin/env python3
"""
Script to automatically clean up old Facebook comments and reactions from MongoDB.
Keeps only Facebook posts and Medium articles.
"""

import sys
from pathlib import Path
from pymongo import MongoClient

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils import config


def cleanup_facebook_data():
    """Remove old Facebook comments and reactions from MongoDB, keeping only posts."""
    try:
        # Connect to MongoDB
        client = MongoClient(config.mongo_connection_string)
        db = client[config.mongo_database]
        collection = db[config.mongo_collection]
        
        print("Facebook Data Cleanup (Auto)")
        print("=" * 50)
        
        # Activities to delete (everything except posts)
        activities_to_delete = [
            "facebook_comment",
            "facebook_reaction", 
            "facebook_message",
            "facebook_ads_info",
            "facebook_security_info",
            "facebook_export"
        ]
        
        print("Checking what will be removed:")
        total_to_delete = 0
        
        for activity_type in activities_to_delete:
            count = collection.count_documents({
                "platform": "facebook",
                "tags": {"$in": [activity_type]}
            })
            if count > 0:
                print(f"  {activity_type}: {count} records")
                total_to_delete += count
        
        if total_to_delete == 0:
            print("  No records to delete.")
            return
        
        print(f"\nTotal records to delete: {total_to_delete}")
        print("Proceeding with automatic deletion...")
        
        # Delete the records
        print("\nDeleting records:")
        deleted_count = 0
        
        for activity_type in activities_to_delete:
            result = collection.delete_many({
                "platform": "facebook",
                "tags": {"$in": [activity_type]}
            })
            if result.deleted_count > 0:
                print(f"  ✓ Deleted {result.deleted_count} {activity_type} records")
                deleted_count += result.deleted_count
        
        print(f"\nCleanup completed successfully!")
        print(f"Total records deleted: {deleted_count}")
        
        # Show final statistics
        print("\nRemaining data:")
        facebook_posts = collection.count_documents({
            "platform": "facebook",
            "tags": {"$in": ["facebook_post"]}
        })
        medium_articles = collection.count_documents({"platform": "medium"})
        total_items = collection.count_documents({})
        
        print(f"  Facebook posts: {facebook_posts}")
        print(f"  Medium articles: {medium_articles}")
        print(f"  Total items: {total_items}")
        
        client.close()
        
    except Exception as e:
        print(f"Error cleaning up Facebook data: {str(e)}")


if __name__ == "__main__":
    cleanup_facebook_data()