from typing import List, Dict
import feedparser
from datetime import datetime
import logging
from .base_fetcher import BaseFetcher

class RSSFetcher(BaseFetcher):
    """Fetches articles from RSS feeds."""
    
    def __init__(self, config: Dict):
        """Initialize the RSS fetcher with configuration."""
        self.logger = logging.getLogger(__name__)
        
        # Get RSS config
        rss_config = config.get('sources', {}).get('rss', {})
        self.feeds = rss_config.get('feeds', [])
        self.max_articles_per_feed = rss_config.get('max_articles', 20)
        
        if not self.feeds:
            raise ValueError("RSS feeds list is required")

    def fetch_articles(self) -> List[Dict]:
        try:
            all_articles = []
            for feed_url in self.feeds:
                self.logger.info(f"Fetching from RSS feed: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                feed_title = feed.feed.get('title', 'RSS Feed')
                
                # Process each entry up to the limit
                for entry in feed.entries[:self.max_articles_per_feed]:
                    article = {
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'content': entry.get('content', [{}])[0].get('value', '') 
                                 if 'content' in entry else entry.get('summary', ''),
                        'date': entry.get('published', ''),
                        'source': feed_title,
                        'topic': 'artificial intelligence',
                        'topic_hashtag': 'AI'
                    }
                    all_articles.append(self.format_article(article, feed_title))
                
            self.logger.info(f"Fetched {len(all_articles)} articles from RSS feeds")
            return all_articles
            
        except Exception as e:
            self.logger.error(f"Error fetching from RSS feeds: {str(e)}")
            return []
