#!/usr/bin/env python3

import os
import sys

# Add src to path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported correctly."""
    try:
        from src.models import Article
        from src.steps import scrape_linkedin_articles, scrape_medium_articles, store_articles_in_mongodb
        from src.pipelines import publications_scraping_pipeline
        from src.utils import config
        
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_article_model():
    """Test the Article model."""
    try:
        from src.models import Article
        from datetime import datetime
        
        # Create test article
        article = Article(
            title="Test Article",
            url="https://example.com/test",
            platform="test",
            author="testuser",
            content="This is a test article"
        )
        
        # Test serialization
        article_dict = article.model_dump()
        assert article_dict['title'] == "Test Article"
        assert article_dict['platform'] == "test"
        
        print("✅ Article model test passed!")
        return True
    except Exception as e:
        print(f"❌ Article model test failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    try:
        from src.utils import config
        
        # Check default values
        assert config.mongo_database == 'publications_db'
        assert config.max_articles_per_platform >= 1
        
        print("✅ Configuration test passed!")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Running setup tests...\n")
    
    tests = [
        ("Import tests", test_imports),
        ("Article model tests", test_article_model), 
        ("Configuration tests", test_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The pipeline is ready to use.")
        print("\nNext steps:")
        print("1. Set up your .env file with your usernames and MongoDB connection")
        print("2. Install Chrome/ChromeDriver for LinkedIn scraping")
        print("3. Start MongoDB")
        print("4. Run: python main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()