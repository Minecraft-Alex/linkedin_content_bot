from typing import List, Dict
import requests
from datetime import datetime
from .base_fetcher import BaseFetcher

class MediumFetcher(BaseFetcher):
    """Fetches articles from Medium using their API."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_key = config.get('api_key')
        if not self.api_key:
            raise ValueError("Medium API key is required")
        
        self.publications = config.get('publications', [])
        self.tags = config.get('tags', ['artificial-intelligence', 'machine-learning'])

    def fetch_articles(self) -> List[Dict]:
        try:
            all_articles = []
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Fetch from specific publications
            for pub_id in self.publications:
                self.logger.info(f"Fetching from Medium publication: {pub_id}")
                url = f"https://api.medium.com/v1/publications/{pub_id}/posts"
                
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                posts = response.json().get('data', [])
                for post in posts:
                    article = {
                        'title': post.get('title', ''),
                        'url': post.get('url', ''),
                        'summary': post.get('content', '')[:200] + '...',
                        'content': post.get('content', ''),
                        'date': post.get('publishedAt', ''),
                        'source': 'Medium',
                        'topic': 'artificial intelligence',
                        'topic_hashtag': 'AI'
                    }
                    all_articles.append(self.format_article(article, 'Medium'))
            
            # Fetch posts by tags
            for tag in self.tags:
                self.logger.info(f"Fetching Medium posts with tag: {tag}")
                url = f"https://api.medium.com/v1/tags/{tag}/posts"
                
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                posts = response.json().get('data', [])
                for post in posts:
                    article = {
                        'title': post.get('title', ''),
                        'url': post.get('url', ''),
                        'summary': post.get('content', '')[:200] + '...',
                        'content': post.get('content', ''),
                        'date': post.get('publishedAt', ''),
                        'source': 'Medium',
                        'topic': tag.replace('-', ' '),
                        'topic_hashtag': tag.replace('-', '').title()
                    }
                    all_articles.append(self.format_article(article, 'Medium'))
            
            self.logger.info(f"Fetched {len(all_articles)} articles from Medium")
            return all_articles
            
        except Exception as e:
            self.logger.error(f"Error fetching from Medium: {str(e)}")
            return []
