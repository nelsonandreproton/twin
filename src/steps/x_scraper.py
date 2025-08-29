from zenml import step
from typing import List, Optional
import json
import re
from pathlib import Path
from datetime import datetime
import logging
from src.models import Article

logger = logging.getLogger(__name__)

@step
def scrape_x_tweets(
    x_data_path: str = "/home/na/DEV/twin/data/X",
    max_tweets: int = 10000
) -> List[Article]:
    """
    Scrapes X (Twitter) tweets from JavaScript export file.
    
    Args:
        x_data_path: Path to X data directory containing tweets.js
        max_tweets: Maximum number of tweets to process
    
    Returns:
        List of Article objects containing X tweets
    """
    articles = []
    
    try:
        x_path = Path(x_data_path)
        tweets_file = x_path / "tweets.js"
        
        if not tweets_file.exists():
            logger.warning(f"X tweets file does not exist: {tweets_file}")
            return articles

        # Read the tweets.js file
        with open(tweets_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract JSON data from JavaScript format
        # The file starts with "window.YTD.tweets.part0 = " followed by JSON
        json_match = re.search(r'window\.YTD\.tweets\.part0\s*=\s*(\[.*\])', content, re.DOTALL)
        if not json_match:
            logger.error("Could not extract JSON data from tweets.js file")
            return articles
        
        json_data = json_match.group(1)
        tweets_data = json.loads(json_data)
        
        logger.info(f"Found {len(tweets_data)} tweets in the export file")
        
        # Process tweets
        processed_count = 0
        for tweet_entry in tweets_data:
            if processed_count >= max_tweets:
                break
                
            try:
                tweet = tweet_entry.get('tweet', {})
                article = _extract_tweet_data(tweet)
                if article:
                    articles.append(article)
                    processed_count += 1
            except Exception as e:
                logger.error(f"Error processing individual tweet: {str(e)}")
                continue
        
        logger.info(f"Successfully processed {len(articles)} X tweets")
        
    except Exception as e:
        logger.error(f"Error scraping X tweets: {str(e)}")
    
    return articles[:max_tweets]


def _extract_tweet_data(tweet: dict) -> Optional[Article]:
    """Extract tweet data into Article format."""
    try:
        # Extract basic tweet information
        tweet_id = tweet.get('id_str', '')
        full_text = tweet.get('full_text', '')
        created_at_str = tweet.get('created_at', '')
        
        if not tweet_id or not full_text:
            return None
        
        # Parse created_at timestamp
        # Format: "Fri Aug 15 16:57:44 +0000 2025"
        published_date = _parse_twitter_timestamp(created_at_str)
        
        # Extract engagement metrics
        favorite_count = int(tweet.get('favorite_count', 0))
        retweet_count = int(tweet.get('retweet_count', 0))
        
        # Extract entities
        entities = tweet.get('entities', {})
        hashtags = [tag['text'] for tag in entities.get('hashtags', [])]
        user_mentions = [mention['screen_name'] for mention in entities.get('user_mentions', [])]
        urls = [url['expanded_url'] if 'expanded_url' in url else url.get('url', '') 
                for url in entities.get('urls', [])]
        
        # Check if it's a reply, retweet, or quote tweet
        is_reply = tweet.get('in_reply_to_status_id_str') is not None
        is_retweet = tweet.get('retweeted', False)
        
        # Create tags
        tags = ['x', 'twitter']
        if is_reply:
            tags.append('reply')
        if is_retweet:
            tags.append('retweet')
        if hashtags:
            tags.extend([f'#{tag}' for tag in hashtags[:3]])  # Limit hashtag tags
        
        # Create URL
        url = f"https://x.com/nelsonandre_/status/{tweet_id}"
        
        # Determine title (first 50 chars of tweet or generate one)
        title = full_text[:50] + "..." if len(full_text) > 50 else full_text
        if not title.strip():
            title = f"X Tweet {tweet_id}"
        
        # Extract additional data
        additional_data = {
            "tweet_id": tweet_id,
            "is_reply": is_reply,
            "is_retweet": is_retweet,
            "reply_to_status_id": tweet.get('in_reply_to_status_id_str'),
            "reply_to_user": tweet.get('in_reply_to_screen_name'),
            "hashtags": hashtags,
            "user_mentions": user_mentions,
            "urls": urls,
            "source": tweet.get('source', ''),
            "lang": tweet.get('lang', ''),
            "truncated": tweet.get('truncated', False)
        }
        
        article = Article(
            title=title,
            url=url,
            author="Nelson André",  # Your X handle
            published_date=published_date,
            content=full_text,
            platform="x",
            tags=tags,
            engagement_metrics={
                "likes": favorite_count,
                "retweets": retweet_count,
                "replies": 0  # Not available in export data
            },
            additional_data=additional_data
        )
        
        return article
        
    except Exception as e:
        logger.error(f"Error extracting tweet data: {str(e)}")
        return None


def _parse_twitter_timestamp(timestamp_str: str) -> datetime:
    """Parse Twitter timestamp format."""
    try:
        # Twitter format: "Fri Aug 15 16:57:44 +0000 2025"
        if timestamp_str:
            return datetime.strptime(timestamp_str, "%a %b %d %H:%M:%S %z %Y")
        else:
            return datetime.now()
    except ValueError:
        try:
            # Try alternative parsing without timezone
            return datetime.strptime(timestamp_str.replace(" +0000", ""), "%a %b %d %H:%M:%S %Y")
        except ValueError:
            logger.warning(f"Could not parse timestamp: {timestamp_str}")
            return datetime.now()
    except Exception as e:
        logger.error(f"Error parsing timestamp '{timestamp_str}': {str(e)}")
        return datetime.now()