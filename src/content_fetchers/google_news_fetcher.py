from typing import List, Dict
import feedparser
from datetime import datetime, timedelta
from .base_fetcher import BaseFetcher

class GoogleNewsFetcher(BaseFetcher):
    """Fetches articles from Google News RSS feeds."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.topics = config.get('topics', ['artificial intelligence', 'machine learning'])
        self.base_url = "https://news.google.com/rss/search"
        self.max_articles = config.get('max_articles', 50)

    def fetch_articles(self) -> List[Dict]:
        try:
            all_articles = []
            for topic in self.topics:
                # Create Google News search URL
                query = topic.replace(' ', '+')
                url = f"{self.base_url}?q={query}&hl=en-US&gl=US&ceid=US:en"
                
                self.logger.info(f"Fetching Google News for topic: {topic}")
                feed = feedparser.parse(url)
                
                # Process each entry
                for entry in feed.entries[:self.max_articles]:  # Limit articles per topic
                    article = {
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'summary': entry.get('description', ''),
                        'content': entry.get('content', [{}])[0].get('value', ''),
                        'date': entry.get('published', ''),
                        'source': entry.get('source', {}).get('title', 'Google News'),
                        'topic': topic,
                        'topic_hashtag': topic.replace(' ', '').title()
                    }
                    all_articles.append(self.format_article(article, 'Google News'))
                
            self.logger.info(f"Fetched {len(all_articles)} articles from Google News")
            return all_articles
            
        except Exception as e:
            self.logger.error(f"Error fetching from Google News: {str(e)}")
            return []
