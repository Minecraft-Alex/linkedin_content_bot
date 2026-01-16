from typing import List, Dict
import tweepy
from datetime import datetime, timedelta
from .base_fetcher import BaseFetcher
import time

class TwitterFetcher(BaseFetcher):
    """Fetches content from Twitter using Twitter API v2."""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.bearer_token = config.get('bearer_token')
        if not self.bearer_token:
            raise ValueError("Twitter bearer token is required")
        
        self.client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        self.search_queries = config.get('search_queries', ['#AI', '#MachineLearning'])
        self.accounts = config.get('accounts', [])
        self.max_results_per_query = 10  # Reduced to avoid rate limits

    def fetch_articles(self) -> List[Dict]:
        try:
            all_tweets = []
            
            # Search for tweets with specific hashtags/keywords
            for query in self.search_queries:
                try:
                    self.logger.info(f"Searching tweets for: {query}")
                    tweets = self.client.search_recent_tweets(
                        query=query,
                        max_results=self.max_results_per_query,
                        tweet_fields=['created_at', 'author_id', 'text', 'public_metrics']
                    )
                    
                    if tweets and tweets.data:
                        for tweet in tweets.data:
                            # Skip tweets with low engagement
                            metrics = getattr(tweet, 'public_metrics', {})
                            if metrics and (metrics.get('retweet_count', 0) + metrics.get('like_count', 0)) < 5:
                                continue
                                
                            article = {
                                'title': f"Tweet about {query}",
                                'url': f"https://twitter.com/user/status/{tweet.id}",
                                'summary': tweet.text,
                                'content': tweet.text,
                                'date': tweet.created_at.isoformat() if tweet.created_at else datetime.now().isoformat(),
                                'source': 'Twitter',
                                'topic': query.replace('#', ''),
                                'topic_hashtag': query.replace('#', '')
                            }
                            all_tweets.append(self.format_article(article, 'Twitter'))
                    
                    # Add delay between queries
                    time.sleep(2)
                    
                except tweepy.TooManyRequests:
                    self.logger.warning(f"Rate limit reached for query: {query}, moving to next source")
                    break
                except Exception as e:
                    self.logger.error(f"Error fetching tweets for query {query}: {str(e)}")
                    continue
            
            # Fetch tweets from specific accounts
            for account in self.accounts:
                try:
                    self.logger.info(f"Fetching tweets from account: {account}")
                    user = self.client.get_user(username=account)
                    if user and user.data:
                        tweets = self.client.get_users_tweets(
                            id=user.data.id,
                            max_results=self.max_results_per_query,
                            tweet_fields=['created_at', 'text', 'public_metrics']
                        )
                        
                        if tweets and tweets.data:
                            for tweet in tweets.data:
                                # Skip tweets with low engagement
                                metrics = getattr(tweet, 'public_metrics', {})
                                if metrics and (metrics.get('retweet_count', 0) + metrics.get('like_count', 0)) < 5:
                                    continue
                                    
                                article = {
                                    'title': f"Tweet by {account}",
                                    'url': f"https://twitter.com/{account}/status/{tweet.id}",
                                    'summary': tweet.text,
                                    'content': tweet.text,
                                    'date': tweet.created_at.isoformat() if tweet.created_at else datetime.now().isoformat(),
                                    'source': f"Twitter - {account}",
                                    'topic': 'artificial intelligence',
                                    'topic_hashtag': 'AI'
                                }
                                all_tweets.append(self.format_article(article, f"Twitter - {account}"))
                        
                        # Add delay between accounts
                        time.sleep(2)
                        
                except tweepy.TooManyRequests:
                    self.logger.warning(f"Rate limit reached for account: {account}, moving to next source")
                    break
                except Exception as e:
                    self.logger.error(f"Error fetching tweets from {account}: {str(e)}")
                    continue
            
            self.logger.info(f"Fetched {len(all_tweets)} tweets")
            return all_tweets
            
        except Exception as e:
            self.logger.error(f"Error fetching from Twitter: {str(e)}")
            return []
