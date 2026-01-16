import requests
from bs4 import BeautifulSoup
from bs4 import Tag
import logging
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin
import time
from random import randint, uniform
from datetime import datetime
import random

class WebScraper:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]

    def _get_random_headers(self):
        """Get random headers to avoid detection."""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

    def _make_request(self, url: str, retries: int = 3) -> Optional[str]:
        """Make HTTP request with retries and random delays."""
        for attempt in range(retries):
            try:
                headers = self._get_random_headers()
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                self.logger.error(f"Request failed for {url}: {str(e)}")
                if attempt < retries - 1:
                    delay = random.uniform(1, 3)
                    time.sleep(delay)
                    continue
                return None
            except Exception as e:
                self.logger.error(f"Unexpected error for {url}: {str(e)}")
                return None
        return None

    def scrape_content(self) -> List[Dict]:
        articles = []
        for source in self.config['sources']:
            try:
                logging.info(f"Scraping content from: {source}")
                source_articles = self._scrape_source(source)
                articles.extend(source_articles)
                logging.info(f"Successfully scraped {len(source_articles)} articles from {source}")
                # Add delay between requests
                time.sleep(randint(2, 4))
            except Exception as e:
                logging.error(f"Error scraping {source}: {str(e)}")
        
        # Sort articles by relevance and limit
        articles = sorted(articles, key=lambda x: x.get('relevance_score', 0), reverse=True)
        max_articles = self.config.get('max_articles_per_source', 5)
        articles = articles[:max_articles]
        logging.info(f"Total articles scraped: {len(articles)}")
        return articles

    def _scrape_source(self, source: str) -> List[Dict]:
        """Scrape articles from a source."""
        try:
            self.logger.info(f"Scraping content from: {source}")
            self.logger.info(f"Making request to {source}")
            
            html_content = self._make_request(source)
            if not html_content:
                self.logger.error(f"Failed to retrieve content from {source}")
                return []
            
            self.logger.info(f"Successfully retrieved content from {source}")
            soup = BeautifulSoup(html_content, 'html.parser')
            
            articles = []
            for topic in self.config.get('topics', []):
                self.logger.info(f"Searching for articles about '{topic}' in {source}")
                articles.extend(self._parse_articles(soup, source, topic))
            
            self.logger.info(f"Successfully scraped {len(articles)} articles from {source}")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error scraping {source}: {str(e)}")
            return []

    def _parse_articles(self, soup: BeautifulSoup, source_url: str, topic: str) -> List[Dict]:
        """Parse articles from HTML content."""
        articles = []
        article_patterns = [
            'article',
            '.post',
            '.entry',
            '.article',
            '[class*="article"]',
            '[class*="post"]',
            '.story',
            '.news-item',
            '.card',
            '.block',
            '.item'
        ]
        
        for pattern in article_patterns:
            containers = soup.select(pattern)
            if containers:
                self.logger.info(f"Found {len(containers)} containers with pattern '{pattern}'")
                for container in containers:
                    try:
                        article = self._extract_article_info(container, source_url, topic)
                        if article:
                            article['topic'] = topic
                            article['topic_hashtag'] = topic.replace(' ', '')
                            article['relevance_score'] = self._calculate_relevance_score(article['title'], article['content'], topic)
                            article['source'] = source_url
                            articles.append(article)
                    except Exception as e:
                        self.logger.error(f"Error extracting article info: {str(e)}")
                        continue
                break  # Stop if we found articles with any pattern
        
        return articles

    def _extract_article_info(self, container, source_url: str, topic: str) -> Optional[Dict[str, str]]:
        """Extract article information from a container."""
        try:
            # Site-specific patterns
            site_specific_patterns = {
                'theverge.com': {
                    'title': ['h2', '.heading-standard', '.font-polysans', 'h2 a', '.article-title', '.c-entry-title'],
                    'content': ['.duet--article--article-body-component', '.c-entry-content', '.article__body'],
                    'summary': ['.duet--article--article-body-component p:first-child', '.c-entry-summary', '.article__summary']
                },
                'zdnet.com': {
                    'title': ['h3', '.article__title', '.article-title', '.content-title'],
                    'content': ['.article__body', '.article-content', '.content-body'],
                    'summary': ['.article__summary', '.article-description', '.content-description']
                }
            }
            
            # Get domain-specific patterns
            domain = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', source_url)
            domain = domain.group(1) if domain else ''
            patterns = site_specific_patterns.get(domain, {})
            
            # Extract title
            title = None
            title_patterns = patterns.get('title', []) + [
                'h1', 'h2', 'h3',  # Try any heading first
                'h1 a', 'h2 a', 'h3 a',  # Then links within headings
                'a',  # Then any link
                '.title', '.headline', '.article-title'  # Finally, try classes
            ]
            
            for pattern in title_patterns:
                title_elems = container.select(pattern)
                for title_elem in title_elems:
                    potential_title = title_elem.get_text().strip()
                    if potential_title and len(potential_title) > 10:  # Ensure it's a substantial title
                        title = potential_title
                        break
                if title:
                    break
            
            if not title:
                return None
            
            # Extract URL
            url = None
            link_containers = container.find_all('a', href=True)
            for link in link_containers:
                if title.lower() in link.get_text().lower():
                    url = link['href']
                    break
            
            if not url:
                # If no matching link found, take the first link
                for link in link_containers:
                    if link.get('href'):
                        url = link['href']
                        break
            
            if not url:
                return None
            
            # Clean and normalize URL
            if not url.startswith(('http://', 'https://')):
                url = urljoin(source_url, url)
            
            # Extract date (use current date if not found)
            date = self._extract_date(container) or datetime.now().strftime('%Y-%m-%d')
            
            # Extract content/summary
            content = ""
            summary = ""
            
            # Try site-specific patterns first
            content_patterns = patterns.get('content', []) + [
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                'article',
                '.article-body',
                '.post-body',
                '.story-content'
            ]
            
            summary_patterns = patterns.get('summary', []) + [
                '.article-summary',
                '.post-summary',
                '.entry-summary',
                '.excerpt',
                '.description',
                'meta[name="description"]',
                'meta[property="og:description"]',
                '.article-excerpt',
                '.post-excerpt',
                'article p:first-child'
            ]
            
            # Try to get content first
            for pattern in content_patterns:
                content_elem = container.select_one(pattern)
                if content_elem:
                    content = content_elem.get_text().strip()
                    # Clean up the content
                    content = re.sub(r'\s+', ' ', content)  # Remove extra whitespace
                    content = content.replace('\n', ' ').strip()
                    logging.info(f"Found content with pattern {pattern}: {content[:100]}...")
                    break
            
            # Try to get summary
            for pattern in summary_patterns:
                summary_elem = container.select_one(pattern)
                if summary_elem:
                    summary = summary_elem.get_text().strip()
                    # Clean up the summary
                    summary = re.sub(r'\s+', ' ', summary)  # Remove extra whitespace
                    summary = summary.replace('\n', ' ').strip()
                    if len(summary) > 50:  # Only use if it's a substantial summary
                        logging.info(f"Found summary with pattern {pattern}: {summary}")
                        break
            
            # If no content found, use any paragraph text
            if not content:
                paragraphs = container.find_all('p')
                content = ' '.join(p.get_text().strip() for p in paragraphs)
                content = re.sub(r'\s+', ' ', content).strip()
                logging.info("Using paragraphs as content")
            
            # If no summary, generate one from content
            if not summary and content:
                # Get first 2-3 sentences or 200 characters
                sentences = re.split(r'[.!?]+', content)
                summary = '. '.join(sentences[:3]).strip()
                if len(summary) > 200:
                    summary = summary[:200].rsplit(' ', 1)[0] + '...'
                logging.info(f"Generated summary from content: {summary}")
            
            return {
                'title': title,
                'url': url,
                'date': date,
                'content': content,
                'summary': summary
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting article info: {str(e)}")
            return None

    def _extract_date(self, container) -> str:
        """Extract article date."""
        date_patterns = [
            'time',
            '[class*="date"]',
            '[class*="time"]',
            '[datetime]',
            '.meta'
        ]
        
        for pattern in date_patterns:
            date_elem = container.select_one(pattern)
            if date_elem:
                # Try datetime attribute
                date_str = date_elem.get('datetime', '') or date_elem.get_text().strip()
                
                # Try different date formats
                date_formats = ['%Y-%m-%d', '%B %d, %Y', '%d/%m/%Y', '%Y/%m/%d']
                for fmt in date_formats:
                    try:
                        return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                
                # Try extracting date with regex
                date_pattern = r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{4}/\d{2}/\d{2}'
                match = re.search(date_pattern, date_str)
                if match:
                    try:
                        return datetime.strptime(match.group(), '%Y-%m-%d').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
        
        return None

    def _calculate_relevance_score(self, title: str, content: str, topic: str) -> float:
        score = 0.0
        text = (title + " " + content).lower()
        
        # Check for topic presence (30%)
        if topic.lower() in text:
            score += 0.3
            
        # Check for required keywords (40%)
        keyword_count = 0
        required_keywords = ['ai', 'ml', 'artificial intelligence', 'machine learning', 'neural', 'deep learning']
        for keyword in required_keywords:
            if keyword.lower() in text:
                keyword_count += 1
        
        if keyword_count > 0:
            score += 0.4 * min(1.0, keyword_count / 2)  # Only need 2 keywords for full score
        
        # Title specific boost (20%)
        title_lower = title.lower()
        if topic.lower() in title_lower:
            score += 0.2
        elif any(k in title_lower for k in required_keywords):
            score += 0.1
        
        # Length bonus (10%)
        words = len(content.split())
        min_words = 100  # Default minimum word count
        if words >= min_words:
            score += 0.1
        
        return min(1.0, score)
