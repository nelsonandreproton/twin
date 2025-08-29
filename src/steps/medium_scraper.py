import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List
from zenml import step, get_step_context
from bs4 import BeautifulSoup
from src.models import Article
import re


@step(enable_cache=False)
def scrape_medium_articles(username: str, max_articles: int = 50) -> List[Article]:
    """
    Scrape Medium articles from a user's RSS feed.
    Uses RSS feed for reliable article discovery.
    """
    articles = []
    metadata = {
        "medium.com": {
            "successful": 0,
            "total": 0,
            "errors": []
        }
    }
    
    try:
        # Medium RSS feed URL
        rss_url = f"https://medium.com/feed/@{username}"
        
        # Headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        # Get the RSS feed
        response = requests.get(rss_url, headers=headers)
        response.raise_for_status()
        
        # Parse RSS XML
        root = ET.fromstring(response.content)
        
        # Find all items (articles) in the RSS feed
        items = root.findall('.//item')
        
        # Limit to max_articles
        items = items[:max_articles]
        metadata["medium.com"]["total"] = len(items)
        
        # Process each article
        for i, item in enumerate(items):
            try:
                # Extract basic information from RSS
                title_elem = item.find('title')
                title = title_elem.text if title_elem is not None else f"Medium Article {i+1}"
                
                link_elem = item.find('link')
                article_url = link_elem.text if link_elem is not None else ""
                
                # Extract publication date
                published_date = None
                pubdate_elem = item.find('pubDate')
                if pubdate_elem is not None:
                    try:
                        # Parse RFC 2822 date format from RSS
                        published_date = datetime.strptime(pubdate_elem.text, '%a, %d %b %Y %H:%M:%S %Z')
                    except:
                        try:
                            # Try alternative format
                            published_date = datetime.strptime(pubdate_elem.text, '%a, %d %b %Y %H:%M:%S GMT')
                        except:
                            pass
                
                # Extract content from RSS (CDATA content)
                content = ""
                content_elem = item.find('.//{http://purl.org/rss/1.0/modules/content/}encoded')
                if content_elem is not None:
                    # Parse HTML content and extract text
                    soup = BeautifulSoup(content_elem.text, 'html.parser')
                    # Remove images and get text from paragraphs
                    for img in soup.find_all('img'):
                        img.decompose()
                    paragraphs = soup.find_all('p')
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs[:10]])  # First 10 paragraphs
                
                # Extract tags/categories
                tags = []
                category_elems = item.findall('category')
                for cat_elem in category_elems:
                    if cat_elem.text:
                        tags.append(cat_elem.text.strip())
                
                # Create Article object
                article = Article(
                    title=title,
                    url=article_url,
                    platform="medium",
                    content=content,
                    author=username,
                    published_date=published_date,
                    tags=tags,
                    engagement_metrics={},  # Not available in RSS
                    scraped_at=datetime.now()
                )
                
                articles.append(article)
                metadata["medium.com"]["successful"] += 1
                
            except Exception as e:
                error_msg = f"Error processing Medium article from RSS: {e}"
                print(error_msg)
                metadata["medium.com"]["errors"].append(error_msg)
                continue
                
    except Exception as e:
        error_msg = f"Error fetching Medium RSS feed: {e}"
        print(error_msg)
        metadata["medium.com"]["errors"].append(error_msg)
    
    # Add metadata to step context
    step_context = get_step_context()
    step_context.add_output_metadata(output_name="output", metadata=metadata)
    
    return articles