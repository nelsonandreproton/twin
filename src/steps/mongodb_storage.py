from typing import List
from zenml import step, get_step_context
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from src.models import Article
import os


@step(enable_cache=False)
def store_articles_in_mongodb(
    articles: List[Article],
    connection_string: str = None,
    database_name: str = None,
    collection_name: str = None
) -> dict:
    """
    Store scraped articles in MongoDB.
    Returns a dictionary with storage statistics.
    """
    # Use environment variables if parameters not provided
    connection_string = connection_string or os.getenv('MONGO_CONNECTION_STRING', 'mongodb://localhost:27017/')
    database_name = database_name or os.getenv('MONGO_DATABASE', 'publications_db')
    collection_name = collection_name or os.getenv('MONGO_COLLECTION', 'articles')
    
    stats = {
        'total_articles': len(articles),
        'stored_articles': 0,
        'updated_articles': 0,
        'duplicate_articles': 0,
        'errors': 0
    }
    
    try:
        # Connect to MongoDB
        client = MongoClient(connection_string)
        db = client[database_name]
        collection = db[collection_name]
        
        # Create index on URL to prevent duplicates
        collection.create_index([("url", 1)], unique=True)
        
        for article in articles:
            try:
                # Convert Article to dictionary
                article_dict = article.model_dump()
                
                # Check if article already exists
                existing_article = collection.find_one({"url": article.url})
                
                if existing_article:
                    # Article already exists, skip it
                    stats['duplicate_articles'] += 1
                else:
                    # New article, insert it
                    try:
                        result = collection.insert_one(article_dict)
                        if result.inserted_id:
                            stats['stored_articles'] += 1
                        else:
                            print(f"Failed to get insert ID for: {article.title[:50]}...")
                            stats['errors'] += 1
                    except Exception as e:
                        print(f"Error inserting article '{article.title[:50]}...' (URL: {article.url}): {e}")
                        stats['errors'] += 1
                        
            except Exception as e:
                print(f"Error processing article '{getattr(article, 'title', 'Unknown')}': {e}")
                print(f"Article data: {article}")
                stats['errors'] += 1
                
        # Close connection
        client.close()
        
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        stats['errors'] = len(articles)
    
    # Add metadata to step context
    step_context = get_step_context()
    metadata = {
        "mongodb": {
            "database": database_name,
            "collection": collection_name,
            "storage_stats": stats,
            "success_rate": (stats['stored_articles'] + stats['updated_articles']) / stats['total_articles'] if stats['total_articles'] > 0 else 0
        }
    }
    step_context.add_output_metadata(output_name="output", metadata=metadata)
    
    return stats


@step(enable_cache=False)
def get_stored_articles_count(
    platform: str = "",
    connection_string: str = None,
    database_name: str = None,
    collection_name: str = None,
    after_storage: dict = None  # Dependency parameter to ensure this runs after storage
) -> dict:
    """
    Get count of stored articles, optionally filtered by platform.
    """
    connection_string = connection_string or os.getenv('MONGO_CONNECTION_STRING', 'mongodb://localhost:27017/')
    database_name = database_name or os.getenv('MONGO_DATABASE', 'publications_db')
    collection_name = collection_name or os.getenv('MONGO_COLLECTION', 'articles')
    
    try:
        client = MongoClient(connection_string)
        db = client[database_name]
        collection = db[collection_name]
        
        if platform and platform != "":
            count = collection.count_documents({"platform": platform})
        else:
            count = collection.count_documents({})
            
        client.close()
        
        result = {
            "platform": platform if platform and platform != "" else "all",
            "count": count
        }
        
        # Add metadata to step context
        step_context = get_step_context()
        metadata = {
            "mongodb_count": {
                "database": database_name,
                "collection": collection_name,
                "platform_filter": platform,
                "count_result": result
            }
        }
        step_context.add_output_metadata(output_name="output", metadata=metadata)
        
        return result
        
    except Exception as e:
        print(f"Error getting article count: {e}")
        result = {"platform": platform if platform and platform != "" else "all", "count": 0}
        
        # Add error metadata to step context
        step_context = get_step_context()
        metadata = {
            "mongodb_count": {
                "database": database_name,
                "collection": collection_name,
                "platform_filter": platform,
                "count_result": result,
                "error": str(e)
            }
        }
        step_context.add_output_metadata(output_name="output", metadata=metadata)
        
        return result