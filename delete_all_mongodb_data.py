#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import config

def delete_all_mongodb_data():
    """Delete all data from MongoDB collection."""
    
    # Load environment variables
    load_dotenv()
    
    print("Deleting ALL data from MongoDB...")
    print("=" * 50)
    
    try:
        # Connect to MongoDB using config
        client = MongoClient(config.mongo_connection_string)
        db = client[config.mongo_database]
        collection = db[config.mongo_collection]
        
        # Count all items
        total_count = collection.count_documents({})
        print(f"Found {total_count} total items in the database")
        
        if total_count == 0:
            print("No items found to delete.")
            client.close()
            return
        
        # Show breakdown by platform
        print("\nBreakdown by platform:")
        platforms = ["medium", "facebook", "x", "npblog"]
        for platform in platforms:
            count = collection.count_documents({"platform": platform})
            if count > 0:
                print(f"  {platform}: {count} items")
        
        # Confirm deletion
        if len(sys.argv) > 1 and sys.argv[1] == '--force':
            print("Force flag provided, proceeding with deletion...")
        else:
            try:
                response = input(f"\nAre you sure you want to delete ALL {total_count} items? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("Deletion cancelled.")
                    client.close()
                    return
            except EOFError:
                print("Cannot get user confirmation in non-interactive mode. Use --force flag to proceed.")
                client.close()
                return
        
        # Delete all items
        result = collection.delete_many({})
        
        print(f"Successfully deleted {result.deleted_count} items")
        
        # Verify deletion
        remaining_count = collection.count_documents({})
        
        print(f"Remaining items in database: {remaining_count}")
        
        # Close connection
        client.close()
        
        print("=" * 50)
        print("All MongoDB data deletion completed!")
        
    except Exception as e:
        print(f"Error deleting MongoDB data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    delete_all_mongodb_data()