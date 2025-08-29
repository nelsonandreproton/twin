# Facebook Data Integration

This document describes the Facebook data integration added to your scraping pipeline.

## Overview

The Facebook integration allows you to process and store your Facebook activity data export alongside your existing Medium articles. It handles various types of Facebook data including posts, comments, reactions, messages, ads information, and security logs.

## Files Added

### Core Components

1. **`src/steps/facebook_scraper.py`** - Main Facebook data processor
   - `scrape_facebook_data()` - ZenML step for processing Facebook export data
   - Processes HTML files from Facebook data export
   - Extracts posts, comments, reactions, messages, ads info, and security data
   - Handles Portuguese timestamps and content parsing

2. **`src/pipelines/facebook_pipeline.py`** - Enhanced pipeline
   - `facebook_scraping_pipeline()` - Main pipeline combining Facebook and Medium data
   - `combine_articles()` - Merges data from multiple sources  
   - `print_facebook_summary()` - Enhanced reporting with platform breakdowns

3. **`run_facebook_pipeline.py`** - Execution script
   - Simple script to run the Facebook data processing pipeline
   - Configurable settings for data paths and processing limits

4. **`check_facebook_data.py`** - Data verification utility
   - Analyzes stored Facebook data in MongoDB
   - Provides activity type breakdowns and recent activity lists

## Data Processing Capabilities

### Supported Facebook Activity Types

- **Posts**: Photos, videos, status updates, check-ins
- **Comments**: Comments on posts and photos
- **Reactions**: Likes, loves, angry reactions, etc.
- **Messages**: Private messages and conversations
- **Ads Information**: Ad preferences, advertiser interactions
- **Security Information**: Login activity, IP addresses, device information

### Data Structure

Facebook activities are stored as `Article` objects with:
- `platform`: "facebook"
- `title`: Activity description (e.g., "Nelson André published a photo")
- `content`: Activity text content
- `published_date`: Parsed timestamp from Facebook export
- `tags`: Activity type classification (e.g., "facebook_post", "facebook_comment")
- `additional_data`: Metadata including content type, links, raw HTML length

## Usage

### Basic Facebook-Only Processing

```python
from src.pipelines.facebook_pipeline import facebook_scraping_pipeline

# Process Facebook data only
facebook_scraping_pipeline(
    facebook_data_path="/path/to/facebook/data",
    max_articles_per_platform=50,
    include_facebook=True,
    include_medium=False
)
```

### Combined Facebook + Medium Processing

```python
# Process both Facebook and Medium data
facebook_scraping_pipeline(
    medium_username="your-medium-username",
    facebook_data_path="/path/to/facebook/data", 
    max_articles_per_platform=50,
    include_facebook=True,
    include_medium=True
)
```

### Command Line Execution

```bash
# Run the pipeline
python run_facebook_pipeline.py

# Check stored data
python check_facebook_data.py
```

## Configuration

### Required Setup

1. **Facebook Data Export**: Download your Facebook data export and place in `/home/na/DEV/twin/data/Facebook/`
2. **MongoDB Connection**: Ensure MongoDB is running and connection string is configured in `src/utils/config.py`

### Customizable Parameters

- `facebook_data_path`: Path to Facebook export directory
- `max_articles_per_platform`: Maximum items to process per platform
- `include_facebook`: Whether to process Facebook data
- `include_medium`: Whether to process Medium articles
- `medium_username`: Medium username for article scraping

## Data Export Structure

The integration expects Facebook data in the standard export format:

```
data/Facebook/
├── your_facebook_activity/
│   ├── posts/
│   │   └── your_posts__check_ins__photos_and_videos_1.html
│   ├── comments_and_reactions/
│   │   ├── comments.html
│   │   └── likes_and_reactions.html
│   ├── messages/
│   │   └── your_messages.html
│   ├── ads_information/
│   │   ├── ad_preferences.html
│   │   └── advertisers_using_your_activity_or_information.html
│   └── security_and_login_information/
│       ├── account_activity.html
│       ├── logins_and_logouts.html
│       └── ip_address_activity.html
└── start_here.html
```

## Features

### Portuguese Language Support
- Handles Portuguese timestamps (e.g., "Fev 05, 2025 8:25:54 da tarde")
- Converts Portuguese month abbreviations to English
- Processes Portuguese time indicators ("da tarde", "da manhã")

### Content Extraction
- Extracts titles, content, timestamps, and metadata
- Preserves HTML structure information
- Automatically categorizes by activity type
- Links preservation and reference tracking

### Database Integration
- Stores in existing MongoDB collection alongside Medium articles
- Platform distinction via `platform` field
- Consistent Article model structure
- Duplicate detection and updating

## Pipeline Output

The pipeline provides comprehensive reporting including:

```
FACEBOOK + MEDIUM PROCESSING SUMMARY
==================================================
Total articles processed: 25
New articles stored: 21
Articles updated: 4
Duplicate articles skipped: 0
Errors encountered: 0

Current database statistics:
  medium: 1 articles
  facebook: 21 activities
  all: 22 total items
==================================================
```

## Database Analysis

Use the verification script to analyze stored data:

```bash
python check_facebook_data.py
```

Output example:
```
Facebook Activity Types:
  facebook_post: 18 items
  facebook_comment: 16 items
  facebook_reaction: 8 items

Recent Facebook Activities:
  2025-08-28 10:16 - facebook_comment: Nelson André comentou a foto...
  2025-08-28 10:16 - facebook_post: Nelson André publicou uma foto...
```

## Error Handling

The integration includes robust error handling for:
- Missing or invalid Facebook export files
- Corrupted HTML content
- Timestamp parsing failures
- MongoDB connection issues
- Content extraction errors

All errors are logged with appropriate detail levels while allowing the pipeline to continue processing other data.

## Performance

The integration is optimized for:
- **Batch Processing**: Processes multiple activity types in parallel
- **Memory Efficiency**: Streams large HTML files without loading entirely in memory
- **Rate Limiting**: Respects `max_articles_per_platform` parameter
- **Caching**: Compatible with ZenML's caching system

## Next Steps

Consider enhancing the integration with:
- Additional Facebook activity types (groups, pages, etc.)
- Media file processing (images, videos)
- Advanced content analysis and sentiment tracking  
- Export scheduling and automation
- Data visualization and reporting dashboards