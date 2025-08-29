from zenml import step
from typing import List, Optional
import time
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from src.models import Article
import re
import json

logger = logging.getLogger(__name__)

@step
def scrape_npblog_articles(
    base_url: str = "https://www.nearpartner.com/blog/",
    max_articles: int = 100
) -> List[Article]:
    """
    Scrapes articles from NearPartner blog using requests and BeautifulSoup.
    
    Args:
        base_url: The blog URL to scrape
        max_articles: Maximum number of articles to scrape
    
    Returns:
        List of Article objects containing blog posts
    """
    articles = []
    
    try:
        # Set up session with headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Load multiple pages to get more articles
        page = 1
        max_pages = 10  # Reasonable limit
        
        while len(articles) < max_articles and page <= max_pages:
            # Try different URL patterns for pagination
            url_patterns = [
                f"{base_url.rstrip('/')}/?paged={page}",
                f"{base_url.rstrip('/')}/page/{page}/",
                f"{base_url}?page={page}",
                base_url if page == 1 else None
            ]
            
            page_articles_found = False
            
            for url_pattern in url_patterns:
                if not url_pattern:
                    continue
                    
                try:
                    logger.info(f"Fetching page {page}: {url_pattern}")
                    response = session.get(url_pattern, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_articles = _extract_blog_posts(soup)
                    
                    # Add new articles that we haven't seen before
                    new_articles = []
                    for article in page_articles:
                        if not any(existing.url == article.url for existing in articles):
                            new_articles.append(article)
                    
                    if new_articles:
                        articles.extend(new_articles)
                        logger.info(f"Found {len(new_articles)} new articles on page {page}")
                        page_articles_found = True
                        break
                    
                except requests.RequestException as e:
                    logger.warning(f"Error fetching {url_pattern}: {str(e)}")
                    continue
            
            # If no articles found on this page, stop trying
            if not page_articles_found:
                logger.info(f"No new articles found on page {page}, stopping pagination")
                break
                
            page += 1
            time.sleep(1)  # Be respectful to the server
        
        logger.info(f"Successfully scraped {len(articles)} NP Blog articles")
        
    except Exception as e:
        logger.error(f"Error scraping NP Blog: {str(e)}")
    
    return articles[:max_articles]


def _extract_blog_posts(soup: BeautifulSoup) -> List[Article]:
    """Extract blog post information from the soup."""
    articles = []
    
    try:
        # Look for common blog post container patterns
        post_selectors = [
            "article",
            ".post",
            ".blog-post", 
            ".entry",
            "[class*='post-']",
            ".jet-listing-item",
            ".elementor-post",
            ".wp-block-post"
        ]
        
        posts = []
        for selector in post_selectors:
            found_posts = soup.select(selector)
            if found_posts:
                posts = found_posts
                break
        
        if not posts:
            # Fallback: look for any container with typical blog post elements
            posts = soup.find_all(['div', 'article'], class_=re.compile(r'.*(post|article|blog|entry).*', re.I))
        
        for post in posts:
            try:
                article = _extract_single_post(post)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.error(f"Error extracting individual post: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error extracting blog posts: {str(e)}")
    
    return articles


def _extract_single_post(post_element) -> Optional[Article]:
    """Extract a single blog post from its HTML element."""
    try:
        # Extract title
        title_selectors = ['h1', 'h2', 'h3', '.title', '.post-title', '.entry-title', '[class*="title"]']
        title = None
        for selector in title_selectors:
            title_elem = post_element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        if not title:
            return None
            
        # Extract URL
        url = None
        link_elem = post_element.select_one('a[href]')
        if link_elem:
            href = link_elem.get('href')
            if href:
                if href.startswith('http'):
                    url = href
                elif href.startswith('/'):
                    url = f"https://www.nearpartner.com{href}"
                else:
                    url = f"https://www.nearpartner.com/{href}"
        
        if not url:
            # Generate URL based on title if no link found
            url = f"https://www.nearpartner.com/blog/{title.lower().replace(' ', '-')}"
        
        # Extract date
        date_selectors = ['.date', '.published', '.post-date', '.entry-date', 'time', '[class*="date"]']
        published_date = None
        for selector in date_selectors:
            date_elem = post_element.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                try:
                    # Try to parse different date formats
                    published_date = _parse_date(date_text)
                    break
                except:
                    continue
        
        if not published_date:
            published_date = datetime.now()
        
        # Extract content/excerpt
        content_selectors = ['.excerpt', '.summary', '.content', '.entry-content', '.post-content', 'p']
        content = ""
        for selector in content_selectors:
            content_elem = post_element.select_one(selector)
            if content_elem:
                content = content_elem.get_text(strip=True)[:500]  # Limit content length
                break
        
        # Extract author
        author_selectors = ['.author', '.by-author', '.post-author', '[class*="author"]']
        author = "NearPartner"  # Default
        for selector in author_selectors:
            author_elem = post_element.select_one(selector)
            if author_elem:
                author = author_elem.get_text(strip=True)
                break
        
        # Extract categories/tags
        category_selectors = ['.category', '.categories', '.tags', '.post-category', '[class*="categor"]']
        tags = ["npblog"]  # Default tag
        for selector in category_selectors:
            category_elems = post_element.select(selector)
            if category_elems:
                for cat_elem in category_elems:
                    cat_text = cat_elem.get_text(strip=True)
                    if cat_text and cat_text not in tags:
                        tags.append(cat_text.lower())
        
        # Create Article object
        article = Article(
            title=title,
            url=url,
            author=author,
            published_date=published_date,
            content=content,
            platform="npblog",
            tags=tags,
            additional_data={
                "source": "nearpartner_blog",
                "scraped_method": "selenium"
            }
        )
        
        return article
        
    except Exception as e:
        logger.error(f"Error extracting single post: {str(e)}")
        return None


def _parse_date(date_text: str) -> datetime:
    """Parse various date formats."""
    import dateutil.parser
    
    try:
        # Try to parse using dateutil which handles many formats
        return dateutil.parser.parse(date_text)
    except:
        # Fallback to current time
        return datetime.now()