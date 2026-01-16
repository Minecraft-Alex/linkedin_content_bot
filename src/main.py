import logging
import yaml
from typing import Dict, List
from datetime import datetime
from dotenv import load_dotenv
import os

from content_fetchers import (
    NewsAPIFetcher,
    GoogleNewsFetcher,
    RSSFetcher,
    TwitterFetcher,
    MediumFetcher,
    DevToFetcher
)
from content_filter import ContentFilter
from linkedin_poster import LinkedInPoster
from database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ContentBot:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the content bot with configuration."""
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.logger.info("Loading configuration...")
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.logger.info("Initializing content fetchers...")
        self.fetchers = []
        
        if self.config.get('sources', {}).get('news_api', {}).get('enabled', False):
            self.fetchers.append(NewsAPIFetcher(self.config))
            self.logger.info("Initialized news_api fetcher")
            
        if self.config.get('sources', {}).get('google_news', {}).get('enabled', False):
            self.fetchers.append(GoogleNewsFetcher(self.config))
            self.logger.info("Initialized google_news fetcher")
            
        if self.config.get('sources', {}).get('rss', {}).get('enabled', False):
            self.fetchers.append(RSSFetcher(self.config))
            self.logger.info("Initialized rss fetcher")
        
        self.logger.info("Initializing other components...")
        self.content_filter = ContentFilter(self.config)
        
        self.logger.info("All components initialized successfully")

    def run(self):
        """Run the content bot."""
        try:
            self.logger.info("Starting content bot...")
            
            # Step 1: Fetch articles from all sources
            self.logger.info("Step 1: Fetching articles from all sources...")
            all_articles = []
            
            for fetcher in self.fetchers:
                try:
                    articles = fetcher.fetch_articles()
                    self.logger.info(f"Fetched {len(articles)} articles from {fetcher.__class__.__name__}")
                    all_articles.extend(articles)
                except Exception as e:
                    self.logger.error(f"Error fetching from {fetcher.__class__.__name__}: {str(e)}")
            
            self.logger.info(f"Total articles fetched: {len(all_articles)}")
            
            # Step 2: Filter content
            self.logger.info("Step 2: Filtering content...")
            filtered_articles = self.content_filter.filter_articles(all_articles)
            self.logger.info(f"Filtered down to {len(filtered_articles)} articles")
            
            if not filtered_articles:
                self.logger.warning("No articles passed filtering")
                return
            
            # Step 3: Post content
            self.logger.info("Step 3: Posting content...")
            with LinkedInPoster(self.config) as poster:
                try:
                    poster.post_content(filtered_articles[0])
                    self.logger.info("Successfully posted article")
                except Exception as e:
                    self.logger.error(f"Error posting article: {str(e)}")
                    raise
            
        except Exception as e:
            self.logger.error(f"Error running bot: {str(e)}")
            raise
        finally:
            # Clean up any remaining browser processes
            try:
                import psutil
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if 'chrome' in proc.info['name'].lower():
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except Exception as e:
                self.logger.warning(f"Error cleaning up browser processes: {str(e)}")

    def __enter__(self):
        """Support context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context."""
        pass

if __name__ == "__main__":
    with ContentBot() as bot:
        bot.run()
