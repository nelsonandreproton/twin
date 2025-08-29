from zenml import step
from typing import List, Dict, Any, Optional
import os
import re
import hashlib
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from src.models import Article

logger = logging.getLogger(__name__)

@step
def scrape_facebook_data(
    facebook_data_path: str = "/home/na/DEV/twin/data/Facebook",
    max_items: int = 100
) -> List[Article]:
    """
    Scrapes Facebook activity data from HTML export files.
    
    Args:
        facebook_data_path: Path to Facebook data directory
        max_items: Maximum number of items to process
    
    Returns:
        List of Article objects containing Facebook data
    """
    articles = []
    
    try:
        facebook_path = Path(facebook_data_path)
        if not facebook_path.exists():
            logger.warning(f"Facebook data path does not exist: {facebook_data_path}")
            return articles

        # Process different types of Facebook activity
        activity_processors = {
            "posts": _process_posts
        }

        processed_count = 0
        
        for activity_type, processor in activity_processors.items():
            if processed_count >= max_items:
                break
                
            activity_path = facebook_path / "your_facebook_activity" / activity_type
            if activity_path.exists():
                try:
                    items = processor(activity_path, max_items - processed_count)
                    articles.extend(items)
                    processed_count += len(items)
                    logger.info(f"Processed {len(items)} items from {activity_type}")
                except Exception as e:
                    logger.error(f"Error processing {activity_type}: {str(e)}")

        # Skip root level activity files since we only want posts

        logger.info(f"Successfully scraped {len(articles)} Facebook activity items")
        
    except Exception as e:
        logger.error(f"Error scraping Facebook data: {str(e)}")
    
    return articles[:max_items]


def _process_posts(posts_path: Path, max_items: int) -> List[Article]:
    """Process Facebook posts data"""
    articles = []
    
    try:
        # List of post files to process
        post_files = [
            "your_posts__check_ins__photos_and_videos_1.html",
            "posts_on_other_pages_and_profiles.html", 
            "your_photos.html",
            "your_videos.html",
            "archive.html",
            "your_uncategorized_photos.html",
            "birthday_media.html",
            "media_used_for_memories.html",
            "places_you_have_been_tagged_in.html",
            "edits_you_made_to_posts.html",
            "content_sharing_links_you_have_created.html",
            "album/0.html"
        ]
        
        for post_file_name in post_files:
            if len(articles) >= max_items:
                break
                
            posts_file = posts_path / post_file_name
            if posts_file.exists():
                try:
                    with open(posts_file, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        
                        # Extract post sections
                        sections = soup.find_all('section', class_='_a6-g')
                        remaining_items = max_items - len(articles)
                        
                        for section in sections[:remaining_items]:
                            article = _extract_post_data(section, "facebook_post")
                            if article:
                                articles.append(article)
                        
                        if len(sections) > 0:
                            logger.info(f"Processed {min(len(sections), remaining_items)} posts from {post_file_name}")
                            
                except Exception as e:
                    logger.error(f"Error processing {post_file_name}: {str(e)}")
                        
    except Exception as e:
        logger.error(f"Error processing posts: {str(e)}")
    
    return articles


def _process_comments(comments_path: Path, max_items: int) -> List[Article]:
    """Process Facebook comments and reactions data"""
    articles = []
    
    try:
        # Process comments file
        comments_file = comments_path / "comments.html"
        if comments_file.exists():
            with open(comments_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                
                sections = soup.find_all('section', class_='_a6-g')
                for section in sections[:max_items]:
                    article = _extract_post_data(section, "facebook_comment")
                    if article:
                        articles.append(article)

        # Process reactions file if exists
        reactions_file = comments_path / "likes_and_reactions.html"
        if reactions_file.exists() and len(articles) < max_items:
            remaining = max_items - len(articles)
            with open(reactions_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                
                sections = soup.find_all('section', class_='_a6-g')
                for section in sections[:remaining]:
                    article = _extract_post_data(section, "facebook_reaction")
                    if article:
                        articles.append(article)
                        
    except Exception as e:
        logger.error(f"Error processing comments: {str(e)}")
    
    return articles


def _process_messages(messages_path: Path, max_items: int) -> List[Article]:
    """Process Facebook messages data"""
    articles = []
    
    try:
        # Process main messages file
        messages_file = messages_path / "your_messages.html"
        if messages_file.exists():
            with open(messages_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                
                sections = soup.find_all('section', class_='_a6-g')
                for section in sections[:max_items]:
                    article = _extract_post_data(section, "facebook_message")
                    if article:
                        articles.append(article)
                        
    except Exception as e:
        logger.error(f"Error processing messages: {str(e)}")
    
    return articles


def _process_ads_info(ads_path: Path, max_items: int) -> List[Article]:
    """Process Facebook ads information"""
    articles = []
    
    try:
        ads_files = [
            "ad_preferences.html",
            "advertisers_using_your_activity_or_information.html",
            "advertisers_you've_interacted_with.html"
        ]
        
        processed_count = 0
        for ads_file in ads_files:
            if processed_count >= max_items:
                break
                
            file_path = ads_path / ads_file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    
                    sections = soup.find_all('section', class_='_a6-g')
                    remaining = max_items - processed_count
                    for section in sections[:remaining]:
                        article = _extract_post_data(section, "facebook_ads_info")
                        if article:
                            articles.append(article)
                            processed_count += 1
                            
    except Exception as e:
        logger.error(f"Error processing ads info: {str(e)}")
    
    return articles


def _process_security_info(security_path: Path, max_items: int) -> List[Article]:
    """Process Facebook security and login information"""
    articles = []
    
    try:
        security_files = [
            "account_activity.html",
            "logins_and_logouts.html",
            "ip_address_activity.html"
        ]
        
        processed_count = 0
        for security_file in security_files:
            if processed_count >= max_items:
                break
                
            file_path = security_path / security_file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    
                    sections = soup.find_all('section', class_='_a6-g')
                    remaining = max_items - processed_count
                    for section in sections[:remaining]:
                        article = _extract_post_data(section, "facebook_security_info")
                        if article:
                            articles.append(article)
                            processed_count += 1
                            
    except Exception as e:
        logger.error(f"Error processing security info: {str(e)}")
    
    return articles


def _process_root_activity(facebook_path: Path, max_items: int) -> List[Article]:
    """Process root level activity files"""
    articles = []
    
    try:
        root_files = [
            "start_here.html"
        ]
        
        for root_file in root_files:
            if len(articles) >= max_items:
                break
                
            file_path = facebook_path / root_file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    
                    title = soup.find('title')
                    if title:
                        article = Article(
                            title=title.get_text(strip=True),
                            url=f"facebook://root/{root_file}",
                            author="Facebook Data Export",
                            published_date=datetime.now(),
                            content=soup.get_text(strip=True)[:1000],  # Limit content
                            platform="facebook",
                            tags=["facebook_export", "root_activity"]
                        )
                        articles.append(article)
                        
    except Exception as e:
        logger.error(f"Error processing root activity: {str(e)}")
    
    return articles


def _extract_post_data(section_elem, content_type: str) -> Optional[Article]:
    """Extract data from a Facebook post/activity section"""
    try:
        # Extract title from h2 element
        title_elem = section_elem.find('h2')
        title = title_elem.get_text(strip=True) if title_elem else "Facebook Activity"
        
        # Extract content from main div
        content_elem = section_elem.find('div', class_='_a6-p')
        content = content_elem.get_text(strip=True) if content_elem else ""
        
        # Extract timestamp from footer
        footer_elem = section_elem.find('footer')
        timestamp = None
        if footer_elem:
            time_elem = footer_elem.find('div', class_='_a72d')
            if time_elem:
                timestamp_text = time_elem.get_text(strip=True)
                timestamp = _parse_facebook_timestamp(timestamp_text)
        
        # Extract any links
        links = []
        for link_elem in section_elem.find_all('a'):
            href = link_elem.get('href', '')
            if href and not href.startswith('#'):
                links.append(href)
        
        # Create deterministic URL identifier using MD5 hash
        content_hash = hashlib.md5((title + content).encode('utf-8')).hexdigest()
        url = f"facebook://{content_type}/{content_hash}"
        
        # Extract tags based on content
        tags = [content_type, "facebook"]
        if "photo" in title.lower():
            tags.append("photo")
        if "comment" in title.lower():
            tags.append("comment")
        if "message" in title.lower():
            tags.append("message")
            
        article = Article(
            title=title,
            url=url,
            author="Nelson André",  # From the Facebook export data
            published_date=timestamp or datetime.now(),
            content=content,
            platform="facebook",
            tags=tags,
            additional_data={
                "content_type": content_type,
                "links": links,
                "raw_html_length": len(str(section_elem))
            }
        )
        
        return article
        
    except Exception as e:
        logger.error(f"Error extracting post data: {str(e)}")
        return None


def _parse_facebook_timestamp(timestamp_text: str) -> Optional[datetime]:
    """Parse Facebook timestamp formats"""
    try:
        # Handle empty or None timestamps
        if not timestamp_text or not timestamp_text.strip():
            return datetime.now()
            
        # Facebook timestamps are in Portuguese format from the export
        # Examples: "Jun 03, 2025 10:53:49 da tarde", "Nov 16, 2024 12:44:41 da tarde"
        
        # Replace Portuguese time indicators
        timestamp_text = timestamp_text.replace(" da tarde", " PM")
        timestamp_text = timestamp_text.replace(" da manhã", " AM")
        timestamp_text = timestamp_text.replace(" da madrugada", " AM")
        
        # Replace Portuguese month abbreviations
        portuguese_months = {
            "Jan": "Jan", "Fev": "Feb", "Mar": "Mar", "Abr": "Apr",
            "Mai": "May", "Jun": "Jun", "Jul": "Jul", "Ago": "Aug",
            "Set": "Sep", "Out": "Oct", "Nov": "Nov", "Dez": "Dec"
        }
        
        for pt_month, en_month in portuguese_months.items():
            timestamp_text = timestamp_text.replace(pt_month, en_month)
        
        # Try to parse the timestamp
        try:
            return datetime.strptime(timestamp_text, "%b %d, %Y %I:%M:%S %p")
        except ValueError:
            try:
                return datetime.strptime(timestamp_text, "%d %b %Y %I:%M:%S %p")
            except ValueError:
                try:
                    # Try without seconds
                    return datetime.strptime(timestamp_text, "%b %d, %Y %I:%M %p")
                except ValueError:
                    # If parsing fails, return current time
                    if timestamp_text.strip():  # Only log if timestamp is not empty
                        logger.debug(f"Could not parse timestamp: {timestamp_text}")
                    return datetime.now()
                
    except Exception as e:
        logger.error(f"Error parsing timestamp '{timestamp_text}': {str(e)}")
        return datetime.now()