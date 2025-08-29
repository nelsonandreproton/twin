# Publications & Social Media Scraping Pipeline

A ZenML pipeline that scrapes your social media content from multiple platforms (Medium, Facebook, X/Twitter) and stores them in MongoDB for analysis and archival.

## 📚 About This Project

This repository is based on concepts and patterns from the excellent book ["LLM Engineer's Handbook"](https://github.com/PacktPublishing/LLM-Engineers-Handbook) by Maxime Labonne and Paul Iusztin. This is my personal implementation and extension of the ideas presented in the book as I work through it.

**📖 I highly recommend reading the book!** It provides comprehensive coverage of LLM engineering practices, MLOps pipelines, and modern AI system architecture. This project serves as a practical application of those concepts.

**Original Repository:** https://github.com/PacktPublishing/LLM-Engineers-Handbook

## Features

- **Medium Scraping**: Scrapes articles from Medium profiles using requests and BeautifulSoup  
- **Facebook Activity Processing**: Processes Facebook data export files including posts, comments, reactions, messages, and more
- **X (Twitter) Processing**: Processes X/Twitter data export files including tweets, replies, retweets with engagement metrics
- **MongoDB Storage**: Stores articles and activities with deduplication based on URL
- **ZenML Orchestration**: Uses ZenML for pipeline orchestration and step management
- **Multi-platform Integration**: Unified storage and analysis across platforms
- **High Volume Processing**: Handles up to 10,000 items per platform in a single run
- **Portuguese Language Support**: Handles Portuguese timestamps and content from Facebook exports
- **Deterministic URLs**: Consistent URL generation for reliable duplicate detection
- **Configurable**: Environment-based configuration for all parameters

## Installation

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up data exports (optional):
   - **Facebook**: Download from Facebook Settings > Your Facebook Information > Download Your Information. Select HTML format and extract to `/data/Facebook/`
   - **X (Twitter)**: Download from X Settings > Your account > Download an archive of your data. Extract `tweets.js` to `/data/X/`

4. Set up MongoDB:
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install MongoDB locally
```

5. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Create a `.env` file based on `.env.example`:

```env
# MongoDB Configuration
MONGO_CONNECTION_STRING=mongodb://localhost:27017/
MONGO_DATABASE=publications_db
MONGO_COLLECTION=articles

# Medium Configuration
MEDIUM_USERNAME=your-medium-username
INCLUDE_MEDIUM=true

# Facebook Configuration
FACEBOOK_DATA_PATH=/home/na/DEV/twin/data/Facebook
INCLUDE_FACEBOOK=true

# X (Twitter) Configuration
X_DATA_PATH=/home/na/DEV/twin/data/X
INCLUDE_X=true

# NP Blog Configuration (currently disabled)
NPBLOG_URL=https://www.nearpartner.com/blog/
INCLUDE_NPBLOG=false

# Scraping Configuration
MAX_ARTICLES_PER_PLATFORM=10000
SCRAPING_DELAY_SECONDS=2
```

## Usage

### Running the Pipeline

```bash
python main.py
```

The script will:
1. Check configuration and prompt for missing information
2. Verify data export files are available
3. Scrape Medium articles (if enabled and username provided)  
4. Process Facebook data export files (if enabled)
5. Process X tweets export file (if enabled)
6. Store all data in MongoDB with deduplication based on deterministic URLs
7. Count items in database after storage
8. Print a comprehensive summary with platform breakdowns

### Single Platform Processing

```bash
# Process only Facebook data
export INCLUDE_FACEBOOK=true
export INCLUDE_MEDIUM=false
export INCLUDE_X=false
python main.py

# Process only X tweets
export INCLUDE_X=true
export INCLUDE_MEDIUM=false
export INCLUDE_FACEBOOK=false
python main.py

# Process only Medium articles
export INCLUDE_MEDIUM=true
export INCLUDE_FACEBOOK=false
export INCLUDE_X=false
python main.py
```

### Manage MongoDB Data

```bash
# Check current data counts
python -c "from src.utils import config; from pymongo import MongoClient; client = MongoClient(config.mongo_connection_string); db = client[config.mongo_database]; print(f'Total: {db[config.mongo_collection].count_documents({})}'); print(f'Medium: {db[config.mongo_collection].count_documents({\"platform\": \"medium\"})}'); print(f'Facebook: {db[config.mongo_collection].count_documents({\"platform\": \"facebook\"})}'); print(f'X: {db[config.mongo_collection].count_documents({\"platform\": \"x\"})}'); client.close()"

# Delete all data
python delete_all_mongodb_data.py --force

# Delete specific platform data
python delete_facebook_items.py facebook --force
python delete_facebook_items.py x --force
python delete_facebook_items.py medium --force
```

### ZenML Setup

Initialize ZenML (first time only):
```bash
zenml init
```

View pipeline runs:
```bash
zenml pipeline list
zenml step list
```

## Project Structure

```
├── data/                       # Data exports (gitignored)
│   ├── Facebook/              # Facebook HTML export files
│   └── X/                     # X/Twitter tweets.js file
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── article.py          # Unified article data model
│   ├── steps/
│   │   ├── __init__.py
│   │   ├── medium_scraper.py   # Medium scraping step
│   │   ├── facebook_scraper.py # Facebook data processing step
│   │   ├── x_scraper.py        # X/Twitter data processing step
│   │   ├── npblog_scraper.py   # NP Blog scraper (disabled)
│   │   └── mongodb_storage.py  # MongoDB storage and counting steps
│   ├── pipelines/
│   │   ├── __init__.py
│   │   └── publications_pipeline.py # Multi-platform pipeline
│   └── utils/
│       ├── __init__.py
│       └── config.py           # Configuration management
├── main.py                     # Main entry point
├── delete_all_mongodb_data.py  # Database cleanup utility
├── delete_facebook_items.py    # Platform-specific cleanup utility
├── requirements.txt            # Dependencies
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Data Model

Each article/activity is stored with the following structure:

```python
{
    "title": "Article Title, Tweet text, or Facebook Activity Description",
    "url": "https://..." | "facebook://activity_type/hash" | "https://x.com/user/status/123",
    "platform": "medium" | "facebook" | "x", 
    "content": "Full article content, tweet text, or activity description...",
    "summary": "Optional summary",
    "published_date": "2024-01-01T00:00:00Z",
    "author": "username, Twitter handle, or Facebook name",
    "tags": ["medium_article"] | ["facebook_post", "photo"] | ["x", "reply", "#hashtag"],
    "engagement_metrics": {
        "claps": 123,        # Medium only
        "comments": 45,      # Medium only
        "likes": 42,         # X only
        "retweets": 12,      # X only
        "replies": 5         # X only
    },
    "additional_data": {     # Platform-specific metadata
        # Facebook
        "content_type": "facebook_post",
        "links": ["https://..."],
        "raw_html_length": 1234,
        
        # X/Twitter  
        "tweet_id": "1234567890",
        "is_reply": false,
        "is_retweet": false,
        "hashtags": ["ai", "tech"],
        "user_mentions": ["@username"],
        "urls": ["https://..."],
        "source": "Twitter for Android",
        "lang": "en"
    },
    "scraped_at": "2024-01-01T00:00:00Z"
}
```

### Supported Content Types

**Medium:**
- Published articles with engagement metrics

**Facebook:**
- Posts, photos, videos, status updates
- Comments on posts and photos  
- Reactions (likes, loves, angry, etc.)
- Check-ins and tagged locations
- Media uploads and albums

**X (Twitter):**
- Original tweets with engagement metrics
- Replies and mentions
- Retweets (metadata only)
- Hashtags and user mentions
- Media posts (metadata only)

## Limitations

- **Medium**: Works for public articles only, requires valid username
- **Facebook**: Requires HTML export files (not live API), assumes Portuguese timestamp format
- **X (Twitter)**: Requires JavaScript export files (not live API), processes tweets.js only
- **Export Dependencies**: All platforms except Medium require manual data exports
- **Media Files**: Images/videos are not processed, only metadata and references
- **Engagement Metrics**: Limited to what's available in export data
- **Rate Limits**: Medium scraping may be subject to rate limiting

## Troubleshooting

1. **Data export not found**: 
   - Ensure Facebook export is extracted to `/data/Facebook/` 
   - Ensure X export contains `tweets.js` in `/data/X/`
2. **Timestamp parsing errors**: 
   - Facebook exports should be in Portuguese format
   - X timestamps are parsed automatically from export format
3. **MongoDB connection**: Verify MongoDB is running and connection string is correct
4. **ZenML issues**: Run `zenml init` if first time, check ZenML dashboard at displayed URL
5. **Rate limiting**: Increase `SCRAPING_DELAY_SECONDS` if encountering issues with Medium
6. **Missing dependencies**: Run `pip install -r requirements.txt` to ensure all packages are installed
7. **Pipeline step order**: Count steps now run after storage for accurate statistics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request