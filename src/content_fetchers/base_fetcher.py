from abc import ABC, abstractmethod
from typing import List, Dict
import logging

class BaseFetcher(ABC):
    """Base class for all content fetchers."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def fetch_articles(self) -> List[Dict]:
        """
        Fetch articles from the source.
        
        Returns:
            List[Dict]: List of articles with standardized format:
            {
                'title': str,
                'url': str,
                'summary': str,
                'content': str,
                'source': str,
                'date': str,
                'topic': str,
                'topic_hashtag': str,
                'relevance_score': float
            }
        """
        pass
    
    def format_article(self, raw_article: Dict, source: str) -> Dict:
        """Format raw article data into standardized format."""
        return {
            'title': raw_article.get('title', ''),
            'url': raw_article.get('url', ''),
            'summary': raw_article.get('summary', raw_article.get('description', '')),
            'content': raw_article.get('content', ''),
            'source': source,
            'date': raw_article.get('date', raw_article.get('publishedAt', '')),
            'topic': raw_article.get('topic', 'artificial intelligence'),
            'topic_hashtag': raw_article.get('topic_hashtag', 'AI'),
            'relevance_score': raw_article.get('relevance_score', 0.8)
        }
