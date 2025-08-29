# Publications & Social Media Scraping Pipeline

A ZenML pipeline that scrapes your Medium publications and Facebook activity data, storing them in MongoDB for analysis and archival.

## Features

- **Medium Scraping**: Scrapes articles from Medium profiles using requests and BeautifulSoup  
- **Facebook Activity Processing**: Processes Facebook data export files including posts, comments, reactions, messages, and more
- **MongoDB Storage**: Stores articles and activities with deduplication based on URL
- **ZenML Orchestration**: Uses ZenML for pipeline orchestration and step management
- **Multi-platform Integration**: Unified storage and analysis across platforms
- **Portuguese Language Support**: Handles Portuguese timestamps and content from Facebook exports
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

2. Set up your Facebook data export (optional):
   - Download your Facebook data from Facebook Settings > Your Facebook Information > Download Your Information
   - Select JSON format and extract to `/data/Facebook/` in the project directory

3. Set up MongoDB:
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install MongoDB locally
```

4. Configure environment variables:
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
FACEBOOK_DATA_PATH=/path/to/your/facebook/data
INCLUDE_FACEBOOK=true

# Scraping Configuration
MAX_ARTICLES_PER_PLATFORM=50
SCRAPING_DELAY_SECONDS=2
```

## Usage

### Running the Pipeline

```bash
python main.py
```

The script will:
1. Check configuration and prompt for missing information
2. Process Facebook data export files (if enabled)
3. Scrape Medium articles (if enabled and username provided)
4. Store all data in MongoDB with deduplication
5. Print a comprehensive summary with platform breakdowns

### Facebook Data Processing Only

```bash
# Set environment variables
export INCLUDE_FACEBOOK=true
export INCLUDE_MEDIUM=false
export FACEBOOK_DATA_PATH=/path/to/your/facebook/data

python main.py
```

### Check Stored Data

```bash
python check_facebook_data.py
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
├── data/
│   └── Facebook/               # Facebook data export directory
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── article.py          # Article data model
│   ├── steps/
│   │   ├── __init__.py
│   │   ├── medium_scraper.py   # Medium scraping step
│   │   ├── facebook_scraper.py # Facebook data processing step
│   │   └── mongodb_storage.py  # MongoDB storage steps
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── publications_pipeline.py # Original Medium-only pipeline
│   │   └── facebook_pipeline.py     # Enhanced Facebook + Medium pipeline
│   └── utils/
│       ├── __init__.py
│       └── config.py           # Configuration management
├── main.py                     # Main entry point (Facebook + Medium)
├── run_facebook_pipeline.py    # Facebook-only runner
├── check_facebook_data.py      # Data analysis utility
├── requirements.txt            # Dependencies
├── .env.example               # Environment template
├── FACEBOOK_INTEGRATION.md    # Facebook integration documentation
└── README.md
```

## Data Model

Each article/activity is stored with the following structure:

```python
{
    "title": "Article Title or Facebook Activity Description",
    "url": "https://..." | "facebook://activity_type/hash",
    "platform": "medium" | "facebook", 
    "content": "Article content or activity text...",
    "summary": "Optional summary",
    "published_date": "2024-01-01T00:00:00Z",
    "author": "username or Facebook name",
    "tags": ["medium_article"] | ["facebook_post", "facebook_comment", "photo"],
    "engagement_metrics": {"claps": 123, "comments": 45},  # Medium only
    "additional_data": {  # Facebook activities only
        "content_type": "facebook_post",
        "links": ["https://..."],
        "raw_html_length": 1234
    },
    "scraped_at": "2024-01-01T00:00:00Z"
}
```

### Facebook Activity Types

- **facebook_post**: Posts, photos, videos, status updates
- **facebook_comment**: Comments on posts and photos  
- **facebook_reaction**: Likes, loves, angry reactions, etc.
- **facebook_message**: Private messages and conversations
- **facebook_ads_info**: Ad preferences and advertiser interactions
- **facebook_security_info**: Login activity and security logs

## Limitations

- Medium scraping works for public articles only
- Facebook processing requires data export files (not live API access)
- Facebook timestamps assume Portuguese export format
- Some engagement metrics may not be available depending on privacy settings
- Facebook media files (images, videos) are not processed, only metadata

## Troubleshooting

1. **Facebook data not found**: Ensure Facebook export is placed in correct directory structure
2. **Timestamp parsing errors**: Check that Facebook export is in Portuguese format as expected
3. **MongoDB connection**: Verify MongoDB is running and connection string is correct
4. **Rate limiting**: Increase `SCRAPING_DELAY_SECONDS` if encountering rate limits with Medium
5. **Missing dependencies**: Run `pip install -r requirements.txt` to ensure all packages are installed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request