import requests
from datetime import datetime, timedelta
from typing import List, Dict
from .base_fetcher import BaseFetcher
import logging

class NewsAPIFetcher(BaseFetcher):
    """Fetches articles from NewsAPI."""
    
    def __init__(self, config: Dict):
        """Initialize the NewsAPI fetcher with configuration."""
        self.logger = logging.getLogger(__name__)
        
        # Get API key from config
        news_api_config = config.get('sources', {}).get('news_api', {})
        self.api_key = news_api_config.get('api_key')
        
        if not self.api_key:
            raise ValueError("NewsAPI key is required")
        
        # Get other config values
        self.query = news_api_config.get('query', 'artificial intelligence OR machine learning')
        self.language = news_api_config.get('language', 'en')
        self.sort_by = news_api_config.get('sort_by', 'publishedAt')
        self.max_articles = news_api_config.get('max_articles', 10)
        
        # Initialize the NewsAPI client
        # self.newsapi = NewsApiClient(api_key=self.api_key)  # This line is commented out because NewsApiClient is not imported
        
        self.base_url = "https://newsapi.org/v2/everything"

    def fetch_articles(self) -> List[Dict]:
        try:
            # Get articles from the last 24 hours
            from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            params = {
                'q': self.query,
                'from': from_date,
                'sortBy': self.sort_by,
                'language': self.language,
                'apiKey': self.api_key,
                'pageSize': min(self.max_articles, 100)  # Respect max_articles setting
            }
            
            self.logger.info(f"Fetching articles about: {self.query}")
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            articles = response.json().get('articles', [])
            self.logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            
            return [self.format_article(article, article.get('source', {}).get('name', 'NewsAPI')) 
                   for article in articles]
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching from NewsAPI: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return []
