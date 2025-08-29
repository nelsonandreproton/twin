from zenml import pipeline, step, get_step_context
from typing import List, Tuple
from src.steps import (
    scrape_medium_articles,
    scrape_facebook_data,
    scrape_npblog_articles,
    scrape_x_tweets,
    store_articles_in_mongodb,
    get_stored_articles_count
)
from src.models import Article
from src.utils import config


@step
def combine_articles(
    medium_articles: List[Article], 
    facebook_articles: List[Article],
    npblog_articles: List[Article],
    x_articles: List[Article]
) -> List[Article]:
    """Combine articles from different sources."""
    all_articles = medium_articles + facebook_articles + npblog_articles + x_articles
    print(f"Combined {len(medium_articles)} Medium articles, {len(facebook_articles)} Facebook activities, and {len(x_articles)} X tweets")
    return all_articles


@step
def print_summary(
    storage_stats: dict, 
    medium_count: dict,
    facebook_count: dict,
    npblog_count: dict,
    x_count: dict,
    total_count: dict
) -> dict:
    """Print a summary of the pipeline execution and generate pipeline metadata."""
    print("\n" + "="*50)
    print("PROCESSING SUMMARY")
    print("="*50)
    
    print(f"Total articles processed: {storage_stats['total_articles']}")
    print(f"New articles stored: {storage_stats['stored_articles']}")
    print(f"Articles updated: {storage_stats['updated_articles']}")
    print(f"Duplicate articles skipped: {storage_stats['duplicate_articles']}")
    print(f"Errors encountered: {storage_stats['errors']}")
    
    print("\nCurrent database statistics:")
    print(f"  {medium_count['platform']}: {medium_count['count']} articles")
    print(f"  {facebook_count['platform']}: {facebook_count['count']} activities")
    print(f"  {x_count['platform']}: {x_count['count']} tweets")
    print(f"  {total_count['platform']}: {total_count['count']} total items")
    
    print("="*50 + "\n")
    
    # Generate and add pipeline-level metadata
    step_context = get_step_context()
    pipeline_metadata = {
        "summary_text": f"Total articles processed: {storage_stats['total_articles']}\nNew articles stored: {storage_stats['stored_articles']}\nArticles updated: {storage_stats['updated_articles']}\nDuplicate articles skipped: {storage_stats['duplicate_articles']}\nErrors encountered: {storage_stats['errors']}\nCurrent database statistics:\n  {medium_count['platform']}: {medium_count['count']} articles\n  {facebook_count['platform']}: {facebook_count['count']} activities\n  {x_count['platform']}: {x_count['count']} tweets\n  {total_count['platform']}: {total_count['count']} total items",
        "pipeline_summary": {
            "title": "Processing Summary",
            "execution_stats": {
                "total_articles": storage_stats['total_articles'],
                "stored_articles": storage_stats['stored_articles'],
                "updated_articles": storage_stats['updated_articles'],
                "duplicate_articles": storage_stats['duplicate_articles'],
                "errors": storage_stats['errors']
            },
            "database_statistics": {
                "medium_count": {
                    "platform": medium_count['platform'],
                    "count": medium_count['count']
                },
                "facebook_count": {
                    "platform": facebook_count['platform'],
                    "count": facebook_count['count']
                },
                "x_count": {
                    "platform": x_count['platform'],
                    "count": x_count['count']
                },
                "total_count": {
                    "platform": total_count['platform'],
                    "count": total_count['count']
                }
            },
            "calculated_metrics": {
                "success_rate": (storage_stats['stored_articles'] + storage_stats['updated_articles']) / storage_stats['total_articles'] if storage_stats['total_articles'] > 0 else 0,
                "error_rate": storage_stats['errors'] / storage_stats['total_articles'] if storage_stats['total_articles'] > 0 else 0,
                "duplicate_rate": storage_stats['duplicate_articles'] / storage_stats['total_articles'] if storage_stats['total_articles'] > 0 else 0
            }
        }
    }
    step_context.add_output_metadata(output_name="output", metadata=pipeline_metadata)
    
    return pipeline_metadata["pipeline_summary"]


@pipeline(enable_cache=False)
def publications_pipeline(
    medium_username: str = "",
    facebook_data_path: str = "/home/na/DEV/twin/data/Facebook",
    npblog_url: str = "https://www.nearpartner.com/blog/",
    x_data_path: str = "/home/na/DEV/twin/data/X",
    max_articles_per_platform: int = 10000,
    include_medium: bool = True,
    include_facebook: bool = True,
    include_npblog: bool = True,
    include_x: bool = True
):
    """
    Main pipeline to scrape Medium publications, Facebook activity data, NP Blog articles, and X tweets, then store in MongoDB.
    
    Args:
        medium_username: Medium username (without @). If None and include_medium is True, will skip Medium
        facebook_data_path: Path to Facebook data export directory
        npblog_url: URL to NP Blog to scrape
        x_data_path: Path to X data directory containing tweets.js
        max_articles_per_platform: Maximum articles to scrape from each platform
        include_medium: Whether to include Medium scraping
        include_facebook: Whether to include Facebook data processing
        include_npblog: Whether to include NP Blog scraping
        include_x: Whether to include X tweets processing
    """
    
    medium_articles = []
    facebook_articles = []
    npblog_articles = []
    x_articles = []
    
    # Scrape articles from Medium if requested and username provided
    if include_medium and medium_username and medium_username.strip():
        medium_articles = scrape_medium_articles(
            username=medium_username,
            max_articles=max_articles_per_platform
        )
    elif include_medium and (not medium_username or not medium_username.strip()):
        print("Medium scraping requested but no username provided. Skipping Medium.")
    
    # Process Facebook data if requested
    if include_facebook:
        facebook_articles = scrape_facebook_data(
            facebook_data_path=facebook_data_path,
            max_items=max_articles_per_platform
        )
    
    # Scrape NP Blog articles if requested (DISABLED)
    if include_npblog:
        # npblog_articles = scrape_npblog_articles(
        #     base_url=npblog_url,
        #     max_articles=max_articles_per_platform
        # )
        npblog_articles = []  # Disabled npblog scraping
    
    # Scrape X tweets if requested
    if include_x:
        x_articles = scrape_x_tweets(
            x_data_path=x_data_path,
            max_tweets=max_articles_per_platform
        )
    
    # Combine all articles
    all_articles = combine_articles(medium_articles, facebook_articles, npblog_articles, x_articles)
    
    # Store articles in MongoDB
    storage_stats = store_articles_in_mongodb(
        all_articles,
        connection_string=config.mongo_connection_string,
        database_name=config.mongo_database,
        collection_name=config.mongo_collection
    )
    
    # Get updated counts for each platform (after storage)
    medium_count = get_stored_articles_count(
        platform="medium",
        connection_string=config.mongo_connection_string,
        database_name=config.mongo_database,
        collection_name=config.mongo_collection,
        after_storage=storage_stats
    )
    
    facebook_count = get_stored_articles_count(
        platform="facebook",
        connection_string=config.mongo_connection_string,
        database_name=config.mongo_database,
        collection_name=config.mongo_collection,
        after_storage=storage_stats
    )
    
    # npblog_count = get_stored_articles_count(
    #     platform="npblog",
    #     connection_string=config.mongo_connection_string,
    #     database_name=config.mongo_database,
    #     collection_name=config.mongo_collection,
    #     after_storage=storage_stats
    # )
    npblog_count = {"platform": "npblog", "count": 0}  # Disabled npblog counting
    
    x_count = get_stored_articles_count(
        platform="x",
        connection_string=config.mongo_connection_string,
        database_name=config.mongo_database,
        collection_name=config.mongo_collection,
        after_storage=storage_stats
    )
    
    total_count = get_stored_articles_count(
        platform="",
        connection_string=config.mongo_connection_string,
        database_name=config.mongo_database,
        collection_name=config.mongo_collection,
        after_storage=storage_stats
    )
    
    # Print summary
    print_summary(
        storage_stats,
        medium_count,
        facebook_count,
        npblog_count,
        x_count,
        total_count
    )