import logging
from typing import List, Dict
import requests
from datetime import datetime, timedelta

class NewsFetcher:
    def __init__(self, config: Dict):
        """Initialize the news fetcher with configuration."""
        self.config = config
        self.api_key = config.get('api_key')
        if not self.api_key:
            raise ValueError("NewsAPI key is required")
        self.base_url = "https://newsapi.org/v2/everything"
        self.logger = logging.getLogger(__name__)

    def fetch_articles(self) -> List[Dict]:
        """Fetch articles from NewsAPI."""
        try:
            # Get articles from the last 24 hours
            from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Prepare query from topics
            topics = " OR ".join(self.config.get('topics', ['AI', 'artificial intelligence']))
            
            # Parameters for the API request
            params = {
                'q': topics,
                'from': from_date,
                'sortBy': 'relevancy',
                'language': 'en',
                'apiKey': self.api_key,
                'pageSize': 100  # Get up to 100 articles
            }
            
            self.logger.info(f"Fetching articles about: {topics}")
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            articles = response.json().get('articles', [])
            self.logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            
            # Format articles to match our existing structure
            formatted_articles = []
            for article in articles:
                formatted_article = {
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'summary': article.get('description', ''),
                    'content': article.get('content', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'date': article.get('publishedAt', ''),
                    'topic': 'artificial intelligence',  # Default topic
                    'topic_hashtag': 'AI',  # Default hashtag
                    'relevance_score': 0.8  # Default score, can be adjusted based on title/content
                }
                formatted_articles.append(formatted_article)
            
            return formatted_articles
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching articles from NewsAPI: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching articles: {str(e)}")
            return []
