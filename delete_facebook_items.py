#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import config

def delete_items_by_platform(platform: str):
    """Delete all items from specified platform in MongoDB."""
    
    # Load environment variables
    load_dotenv()
    
    print(f"Deleting all {platform} items from MongoDB...")
    print("=" * 50)
    
    try:
        # Connect to MongoDB using config
        client = MongoClient(config.mongo_connection_string)
        db = client[config.mongo_database]
        collection = db[config.mongo_collection]
        
        # First, count existing items for the platform
        platform_count = collection.count_documents({"platform": platform})
        print(f"Found {platform_count} {platform} items in the database")
        
        if platform_count == 0:
            print(f"No {platform} items found to delete.")
            client.close()
            return
        
        # Confirm deletion (skip if --force flag provided)
        if len(sys.argv) > 2 and sys.argv[2] == '--force':
            print("Force flag provided, proceeding with deletion...")
        else:
            try:
                response = input(f"Are you sure you want to delete {platform_count} {platform} items? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("Deletion cancelled.")
                    client.close()
                    return
            except EOFError:
                print("Cannot get user confirmation in non-interactive mode. Use --force flag to proceed.")
                client.close()
                return
        
        # Delete all items from the platform
        result = collection.delete_many({"platform": platform})
        
        print(f"Successfully deleted {result.deleted_count} {platform} items")
        
        # Verify deletion
        remaining_platform = collection.count_documents({"platform": platform})
        total_remaining = collection.count_documents({})
        
        print(f"Remaining {platform} items: {remaining_platform}")
        print(f"Total remaining items in database: {total_remaining}")
        
        # Close connection
        client.close()
        
        print("=" * 50)
        print(f"{platform} items deletion completed!")
        
    except Exception as e:
        print(f"Error deleting {platform} items: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_facebook_items.py <platform> [--force]")
        print("Available platforms: facebook, npblog, medium")
        sys.exit(1)
    
    platform = sys.argv[1]
    delete_items_by_platform(platform)