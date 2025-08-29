#!/usr/bin/env python3
"""
Script to check for duplicate entries in MongoDB and provide detailed analysis.
"""

import sys
from pathlib import Path
from pymongo import MongoClient
from collections import Counter
import json

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils import config


def check_duplicates_in_mongodb():
    """Check for duplicate entries in MongoDB and provide analysis."""
    try:
        # Connect to MongoDB
        client = MongoClient(config.mongo_connection_string)
        db = client[config.mongo_database]
        collection = db[config.mongo_collection]
        
        print("MongoDB Duplicate Analysis")
        print("=" * 60)
        
        # Check for duplicate URLs
        print("1. Checking for duplicate URLs...")
        url_duplicates = list(collection.aggregate([
            {"$group": {
                "_id": "$url",
                "count": {"$sum": 1},
                "documents": {"$push": {"id": "$_id", "title": "$title", "platform": "$platform"}}
            }},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}}
        ]))
        
        if url_duplicates:
            print(f"   ⚠️  Found {len(url_duplicates)} duplicate URLs:")
            for dup in url_duplicates[:10]:  # Show first 10
                print(f"     URL: {dup['_id'][:80]}...")
                print(f"     Count: {dup['count']} duplicates")
                for doc in dup['documents'][:3]:  # Show first 3 docs
                    print(f"       - {doc['platform']}: {doc['title'][:50]}...")
                print()
        else:
            print("   ✅ No duplicate URLs found")
        
        # Check for duplicate titles within same platform
        print("2. Checking for duplicate titles within platforms...")
        title_duplicates = list(collection.aggregate([
            {"$group": {
                "_id": {"title": "$title", "platform": "$platform"},
                "count": {"$sum": 1},
                "documents": {"$push": {"id": "$_id", "url": "$url"}}
            }},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}}
        ]))
        
        if title_duplicates:
            print(f"   ⚠️  Found {len(title_duplicates)} duplicate titles:")
            for dup in title_duplicates[:10]:
                print(f"     Platform: {dup['_id']['platform']}")
                print(f"     Title: {dup['_id']['title'][:60]}...")
                print(f"     Count: {dup['count']} duplicates")
                print()
        else:
            print("   ✅ No duplicate titles found within platforms")
        
        # Check for near-duplicate titles (same length, similar content)
        print("3. Checking for potential near-duplicate titles...")
        titles_by_length = {}
        all_docs = list(collection.find({}, {"title": 1, "platform": 1, "url": 1}))
        
        for doc in all_docs:
            title = doc.get('title', '')
            length = len(title)
            if length not in titles_by_length:
                titles_by_length[length] = []
            titles_by_length[length].append(doc)
        
        near_duplicates = []
        for length, docs in titles_by_length.items():
            if len(docs) > 1:
                # Check for similar titles of same length
                for i, doc1 in enumerate(docs):
                    for doc2 in docs[i+1:]:
                        title1 = doc1.get('title', '').lower()
                        title2 = doc2.get('title', '').lower()
                        if title1 and title2:
                            # Simple similarity check
                            common_words = set(title1.split()) & set(title2.split())
                            if len(common_words) > len(title1.split()) * 0.7:  # 70% word overlap
                                near_duplicates.append((doc1, doc2, len(common_words)))
        
        if near_duplicates:
            print(f"   ⚠️  Found {len(near_duplicates)} potential near-duplicates:")
            for doc1, doc2, common_words in near_duplicates[:5]:
                print(f"     1: {doc1['title'][:50]}...")
                print(f"     2: {doc2['title'][:50]}...")
                print(f"        Common words: {common_words}")
                print()
        else:
            print("   ✅ No obvious near-duplicates found")
        
        # Check for documents with identical content
        print("4. Checking for identical content...")
        content_duplicates = list(collection.aggregate([
            {"$match": {"content": {"$ne": ""}}},
            {"$group": {
                "_id": "$content",
                "count": {"$sum": 1},
                "documents": {"$push": {"id": "$_id", "title": "$title", "platform": "$platform"}}
            }},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}}
        ]))
        
        if content_duplicates:
            print(f"   ⚠️  Found {len(content_duplicates)} sets of identical content:")
            for dup in content_duplicates[:5]:
                print(f"     Content preview: {dup['_id'][:100]}...")
                print(f"     Count: {dup['count']} duplicates")
                for doc in dup['documents'][:2]:
                    print(f"       - {doc['platform']}: {doc['title'][:40]}...")
                print()
        else:
            print("   ✅ No identical content found")
        
        # Platform distribution
        print("5. Platform Distribution:")
        platform_counts = collection.aggregate([
            {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        
        total_docs = collection.count_documents({})
        for platform in platform_counts:
            percentage = (platform['count'] / total_docs) * 100
            print(f"   {platform['_id']}: {platform['count']} documents ({percentage:.1f}%)")
        
        # Summary statistics
        print(f"\n6. Summary:")
        print(f"   Total documents: {total_docs}")
        print(f"   URL duplicates: {len(url_duplicates)}")
        print(f"   Title duplicates: {len(title_duplicates)}")
        print(f"   Content duplicates: {len(content_duplicates)}")
        print(f"   Near-duplicates: {len(near_duplicates)}")
        
        # Suggest cleanup actions
        if url_duplicates or title_duplicates or content_duplicates:
            print(f"\n7. Cleanup Recommendations:")
            if url_duplicates:
                print(f"   - Remove {sum(dup['count']-1 for dup in url_duplicates)} URL duplicates")
            if title_duplicates:
                print(f"   - Review {len(title_duplicates)} title duplicates for potential removal")
            if content_duplicates:
                print(f"   - Remove {sum(dup['count']-1 for dup in content_duplicates)} content duplicates")
            
            print(f"\n   Run with --fix flag to automatically remove exact duplicates (coming soon)")
        else:
            print(f"\n   ✅ Database is clean - no duplicates found!")
        
        client.close()
        
    except Exception as e:
        print(f"Error checking duplicates: {str(e)}")


def fix_duplicates_in_mongodb():
    """Remove duplicate entries from MongoDB (keeps first occurrence)."""
    try:
        # Connect to MongoDB
        client = MongoClient(config.mongo_connection_string)
        db = client[config.mongo_database]
        collection = db[config.mongo_collection]
        
        print("MongoDB Duplicate Cleanup")
        print("=" * 60)
        
        # Remove URL duplicates (keep first occurrence)
        url_duplicates = list(collection.aggregate([
            {"$group": {
                "_id": "$url",
                "count": {"$sum": 1},
                "documents": {"$push": "$_id"}
            }},
            {"$match": {"count": {"$gt": 1}}}
        ]))
        
        removed_count = 0
        for dup in url_duplicates:
            # Keep first document, remove others
            docs_to_remove = dup['documents'][1:]  # Skip first document
            if docs_to_remove:
                result = collection.delete_many({"_id": {"$in": docs_to_remove}})
                removed_count += result.deleted_count
                print(f"Removed {result.deleted_count} duplicates for URL: {dup['_id'][:60]}...")
        
        print(f"\nCleanup completed!")
        print(f"Total duplicates removed: {removed_count}")
        
        client.close()
        
    except Exception as e:
        print(f"Error fixing duplicates: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        response = input("This will permanently delete duplicate entries. Continue? (y/N): ")
        if response.lower() in ['y', 'yes']:
            fix_duplicates_in_mongodb()
        else:
            print("Cleanup cancelled.")
    else:
        check_duplicates_in_mongodb()
        print(f"\nTo fix duplicates, run: python {sys.argv[0]} --fix")