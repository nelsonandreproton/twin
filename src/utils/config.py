import os
from dotenv import load_dotenv
from pydantic import BaseModel


# Load environment variables
load_dotenv()


class Config(BaseModel):
    # MongoDB Configuration
    mongo_connection_string: str = os.getenv('MONGO_CONNECTION_STRING', 'mongodb://localhost:27017/')
    mongo_database: str = os.getenv('MONGO_DATABASE', 'publications_db')
    mongo_collection: str = os.getenv('MONGO_COLLECTION', 'articles')
    
    # LinkedIn Configuration (removed)
    
    # Medium Configuration  
    medium_username: str = os.getenv('MEDIUM_USERNAME', '')
    
    # Facebook Configuration
    facebook_data_path: str = os.getenv('FACEBOOK_DATA_PATH', '/home/na/DEV/twin/data/Facebook')
    include_facebook: bool = os.getenv('INCLUDE_FACEBOOK', 'true').lower() in ('true', '1', 'yes')
    include_medium: bool = os.getenv('INCLUDE_MEDIUM', 'true').lower() in ('true', '1', 'yes')
    
    # NP Blog Configuration
    npblog_url: str = os.getenv('NPBLOG_URL', 'https://www.nearpartner.com/blog/')
    include_npblog: bool = os.getenv('INCLUDE_NPBLOG', 'true').lower() in ('true', '1', 'yes')
    
    # X (Twitter) Configuration
    x_data_path: str = os.getenv('X_DATA_PATH', '/home/na/DEV/twin/data/X')
    include_x: bool = os.getenv('INCLUDE_X', 'true').lower() in ('true', '1', 'yes')
    
    # Scraping Configuration
    max_articles_per_platform: int = int(os.getenv('MAX_ARTICLES_PER_PLATFORM', '10000'))
    scraping_delay_seconds: int = int(os.getenv('SCRAPING_DELAY_SECONDS', '2'))


# Global config instance
config = Config()