#!/usr/bin/env python3
"""
Script to run the Facebook data scraping pipeline.

This script demonstrates how to use the new Facebook data integration
alongside the existing Medium scraping functionality.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.pipelines.facebook_pipeline import facebook_scraping_pipeline


def main():
    """Run the Facebook + Medium scraping pipeline."""
    print("Starting Facebook Data Scraping Pipeline")
    print("=" * 50)
    
    # Configuration
    facebook_data_path = "/home/na/DEV/twin/data/Facebook"
    medium_username = ""  # Set to your Medium username if you want to include Medium articles
    max_items_per_platform = 25  # Adjust as needed
    
    # Verify Facebook data path exists
    if not Path(facebook_data_path).exists():
        print(f"Warning: Facebook data path does not exist: {facebook_data_path}")
        print("Please ensure you have placed your Facebook data export in the correct location.")
        return
    
    try:
        # Run the pipeline
        facebook_scraping_pipeline(
            medium_username=medium_username,
            facebook_data_path=facebook_data_path,
            max_articles_per_platform=max_items_per_platform,
            include_medium=bool(medium_username.strip()) if medium_username else False,  # Only include Medium if username provided
            include_facebook=True
        )
        
        print("\nPipeline completed successfully!")
        
    except Exception as e:
        print(f"Error running pipeline: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()