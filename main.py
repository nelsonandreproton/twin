#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.pipelines.publications_pipeline import publications_pipeline
from src.utils import config


def main():
    """Main entry point for the publications scraping pipeline."""
    
    # Load environment variables
    load_dotenv()
    
    print("Publications & Social Media Scraping Pipeline")
    print("=" * 60)
    
    # Configure data sources
    medium_username = config.medium_username
    include_medium = config.include_medium
    include_facebook = config.include_facebook
    facebook_data_path = config.facebook_data_path
    include_npblog = config.include_npblog
    npblog_url = config.npblog_url
    include_x = config.include_x
    x_data_path = config.x_data_path
    
    # Interactive configuration if Medium username not set
    if include_medium and not medium_username:
        print("\nMedium Configuration:")
        medium_username = input("Enter your Medium username (without @) or press Enter to skip: ").strip()
        include_medium = bool(medium_username)
    
    # Check Facebook data availability
    if include_facebook and not Path(facebook_data_path).exists():
        print(f"\nWarning: Facebook data path not found: {facebook_data_path}")
        response = input("Do you want to continue without Facebook data? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Please place your Facebook data export in the correct location and try again.")
            sys.exit(1)
        include_facebook = False
    
    # Check X data availability
    if include_x and not Path(x_data_path).exists():
        print(f"\nWarning: X data path not found: {x_data_path}")
        response = input("Do you want to continue without X data? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Please place your X data export in the correct location and try again.")
            sys.exit(1)
        include_x = False
    
    # Validate that at least one source is enabled
    if not include_medium and not include_facebook and not include_npblog and not include_x:
        print("Error: At least one data source (Medium, Facebook, NP Blog, or X) must be enabled")
        sys.exit(1)
    
    # Display configuration
    print("\nConfiguration:")
    print(f"  Facebook data: {'✓ Enabled' if include_facebook else '✗ Disabled'}")
    if include_facebook:
        print(f"    Path: {facebook_data_path}")
    print(f"  Medium articles: {'✓ Enabled' if include_medium else '✗ Disabled'}")
    if include_medium:
        print(f"    Username: @{medium_username}")
    print(f"  NP Blog articles: ✗ Disabled (scraping disabled)")
    print(f"  X tweets: {'✓ Enabled' if include_x else '✗ Disabled'}")
    if include_x:
        print(f"    Path: {x_data_path}")
    print(f"  Max items per platform: {config.max_articles_per_platform}")
    print("-" * 60)
    
    try:
        # Run the enhanced ZenML pipeline
        pipeline_run = publications_pipeline(
            medium_username=medium_username,
            facebook_data_path=facebook_data_path,
            npblog_url=npblog_url,
            x_data_path=x_data_path,
            max_articles_per_platform=config.max_articles_per_platform,
            include_medium=include_medium,
            include_facebook=include_facebook,
            include_npblog=include_npblog,
            include_x=include_x
        )
        
        print("\n" + "=" * 60)
        print("Pipeline completed successfully!")
        
    except Exception as e:
        print(f"Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()