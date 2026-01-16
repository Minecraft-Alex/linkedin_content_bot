from typing import List, Dict
import requests
from datetime import datetime, timedelta
from .base_fetcher import BaseFetcher

class DevToFetcher(BaseFetcher):
    """Fetches articles from Dev.to API."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_key = config.get('api_key')  # Optional, but recommended
        self.tags = config.get('tags', ['ai', 'machinelearning', 'artificialintelligence'])
        self.base_url = "https://dev.to/api/articles"

    def fetch_articles(self) -> List[Dict]:
        try:
            all_articles = []
            headers = {}
            if self.api_key:
                headers['api-key'] = self.api_key
            
            # Fetch articles for each tag
            for tag in self.tags:
                self.logger.info(f"Fetching Dev.to articles with tag: {tag}")
                
                params = {
                    'tag': tag,
                    'top': 10,  # Get top articles
                    'per_page': 30
                }
                
                response = requests.get(self.base_url, headers=headers, params=params)
                response.raise_for_status()
                
                articles = response.json()
                for article in articles:
                    formatted_article = {
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'summary': article.get('description', ''),
                        'content': article.get('body_markdown', ''),
                        'date': article.get('published_at', ''),
                        'source': 'Dev.to',
                        'topic': tag,
                        'topic_hashtag': tag.title(),
                        'relevance_score': article.get('positive_reactions_count', 0) / 100  # Use reactions as score
                    }
                    all_articles.append(self.format_article(formatted_article, 'Dev.to'))
            
            self.logger.info(f"Fetched {len(all_articles)} articles from Dev.to")
            return all_articles
            
        except Exception as e:
            self.logger.error(f"Error fetching from Dev.to: {str(e)}")
            return []
