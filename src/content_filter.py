import logging
from typing import List, Dict
import sqlite3
from datetime import datetime, timedelta

class ContentFilter:
    """Filter and sort content based on relevance and criteria."""
    
    def __init__(self, config: Dict):
        """Initialize the content filter with configuration."""
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.db_path = "posts.db"
        self._init_db()
        
        # Get filter config
        filter_config = config.get('filtering', {})
        self.min_relevance_score = filter_config.get('min_relevance_score', 0.5)
        self.max_articles = filter_config.get('max_articles', 3)
        self.keywords = filter_config.get('keywords', [])
        
        # Convert keywords to lowercase for case-insensitive matching
        self.keywords = [k.lower() for k in self.keywords]

    def _init_db(self):
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create posted_urls table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posted_urls (
                        url TEXT PRIMARY KEY,
                        title TEXT,
                        posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create posted_topics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posted_topics (
                        topic TEXT PRIMARY KEY,
                        posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise

    def _was_url_posted_recently(self, url: str, days: int = 30) -> bool:
        """Check if a URL was posted in the last N days."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM posted_urls WHERE url = ? AND posted_at > datetime('now', ?)",
                    (url, f'-{days} days')
                )
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Error checking URL status: {str(e)}")
            return False

    def _mark_url_posted(self, url: str, title: str):
        """Mark a URL as posted."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO posted_urls (url, title, posted_at) VALUES (?, ?, datetime('now'))",
                    (url, title)
                )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error marking URL as posted: {str(e)}")

    def filter_articles(self, articles: List[Dict]) -> List[Dict]:
        """Filter and sort articles by relevance."""
        try:
            if not articles:
                return []
            
            # First, filter out recently posted URLs
            unposted_articles = []
            for article in articles:
                url = article.get('url')
                if url and not self._was_url_posted_recently(url):
                    unposted_articles.append(article)
            
            if not unposted_articles:
                self.logger.info("All articles have been posted recently")
                return []
            
            # Calculate relevance scores for unposted articles
            scored_articles = []
            for article in unposted_articles:
                score = self.calculate_relevance_score(article)
                if score >= self.min_relevance_score:
                    article['relevance_score'] = score
                    scored_articles.append(article)
            
            # Sort by relevance score
            scored_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Take top N articles
            filtered_articles = scored_articles[:self.max_articles]
            
            # Mark the top article as posted
            if filtered_articles:
                top_article = filtered_articles[0]
                self._mark_url_posted(top_article['url'], top_article['title'])
            
            self.logger.info(f"Filtered {len(articles)} articles down to {len(filtered_articles)} unposted articles")
            if filtered_articles:
                self.logger.info(f"Top article score: {filtered_articles[0]['relevance_score']}")
            
            return filtered_articles
            
        except Exception as e:
            self.logger.error(f"Error filtering articles: {str(e)}")
            return []

    def calculate_relevance_score(self, article: Dict) -> float:
        """Calculate relevance score for an article."""
        score = 0.0
        
        # Get article text
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        content = article.get('content', '').lower()
        
        # Check title for keywords
        for keyword in self.keywords:
            if keyword in title:
                score += 2.0  # Title matches are worth more
            if keyword in summary:
                score += 1.0
            if keyword in content:
                score += 0.5
        
        # Normalize score
        score = min(score, 5.0)  # Cap at 5.0
        
        return score
