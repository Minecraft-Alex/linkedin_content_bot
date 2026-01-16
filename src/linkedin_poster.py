import os
import time
import logging
from typing import Dict
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

class LinkedInPoster:
    """Posts content to LinkedIn using undetected-chromedriver."""
    
    def __init__(self, config: Dict):
        """Initialize the LinkedIn poster with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.logged_in = False
        
        # Load environment variables
        load_dotenv()
        
        # Validate credentials
        self.username = os.getenv('LINKEDIN_USERNAME')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError(
                "LinkedIn credentials not found. Please set LINKEDIN_USERNAME and "
                "LINKEDIN_PASSWORD environment variables in your .env file"
            )

    def _init_driver(self):
        """Initialize undetected-chromedriver."""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Create undetected-chromedriver instance
            self.driver = uc.Chrome(options=options)
            self.driver.implicitly_wait(10)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize undetected-chromedriver: {str(e)}")
            raise

    def _wait_and_find_element(self, by, value, timeout=10, retries=3):
        """Wait for and find an element with retries."""
        for attempt in range(retries):
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                return element
            except TimeoutException:
                if attempt == retries - 1:  # Last attempt
                    raise
                self.logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2)

    def _login(self):
        """Log in to LinkedIn."""
        if self.logged_in:
            return
            
        try:
            if not self.driver:
                self._init_driver()
                
            self.logger.info("Logging in to LinkedIn...")
            self.driver.get('https://www.linkedin.com/login')
            
            # Wait for and fill in username
            username_field = self._wait_and_find_element(By.ID, "username")
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Wait for and fill in password
            password_field = self._wait_and_find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self._wait_and_find_element(
                By.CSS_SELECTOR, "button[type='submit']"
            )
            login_button.click()
            
            # Wait for successful login
            self._wait_and_find_element(
                By.CSS_SELECTOR, 
                "div[class*='share-box']"
            )
            
            self.logged_in = True
            self.logger.info("Successfully logged in to LinkedIn")
            
        except TimeoutException:
            self.logger.error("Timeout while logging in to LinkedIn")
            raise
        except WebDriverException as e:
            self.logger.error(f"WebDriver error during login: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during login: {str(e)}")
            raise

    def post_content(self, article: Dict):
        """Post an article to LinkedIn."""
        try:
            if not self.logged_in:
                self._login()
            
            self.logger.info(f"Posting article: {article.get('title')}")
            
            # Go to LinkedIn feed
            self.driver.get('https://www.linkedin.com/feed/')
            time.sleep(3)  # Wait for feed to load
            
            # Format the post content
            post_content = self._format_post_content(article)
            
            # JavaScript to find and click the post box
            click_post_js = """
                let buttons = document.querySelectorAll('button,div[role="button"]');
                for (let btn of buttons) {
                    if (btn.textContent.includes('Start a post') || 
                        btn.textContent.includes('Create a post') || 
                        btn.getAttribute('aria-label')?.includes('post')) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            """
            
            # Execute JavaScript to click post box
            clicked = self.driver.execute_script(click_post_js)
            if not clicked:
                raise TimeoutException("Could not find post button")
            
            time.sleep(2)
            
            # JavaScript to find and fill the post content
            fill_content_js = f"""
                let textboxes = document.querySelectorAll('div[role="textbox"],div[contenteditable="true"]');
                for (let box of textboxes) {{
                    if (box.getAttribute('data-placeholder')?.includes('talk about') || 
                        box.getAttribute('aria-label')?.includes('post')) {{
                        box.innerHTML = `{post_content.replace("`", "\\`").replace("'", "\\'")}`;
                        return true;
                    }}
                }}
                return false;
            """
            
            # Execute JavaScript to fill content
            filled = self.driver.execute_script(fill_content_js)
            if not filled:
                raise TimeoutException("Could not find post field")
            
            time.sleep(2)
            
            # JavaScript to click the post button
            post_js = """
                let buttons = document.querySelectorAll('button');
                for (let btn of buttons) {
                    if (btn.textContent.trim() === 'Post' && btn.offsetParent !== null) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            """
            
            # Execute JavaScript to submit post
            posted = self.driver.execute_script(post_js)
            if not posted:
                raise TimeoutException("Could not find submit button")
            
            time.sleep(5)
            self.logger.info(f"Successfully posted article: {article.get('title')}")
            
        except TimeoutException as e:
            self.logger.error(f"Timeout while posting content: {str(e)}")
            raise
        except WebDriverException as e:
            self.logger.error(f"WebDriver error while posting: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error while posting: {str(e)}")
            raise

    def _format_post_content(self, article: Dict) -> str:
        """Format the article content for posting."""
        title = article.get('title', '').strip()
        summary = article.get('summary', '').strip()
        if summary:
            # Split summary into sentences and take first 2-3
            sentences = summary.split('.')
            summary = '. '.join(s.strip() for s in sentences[:3] if s.strip()) + '.'
            
        url = article.get('url', '').strip()
        topic = article.get('topic_hashtag', 'AI').replace(' ', '')
        source = article.get('source', '').strip()
        
        # Create an engaging headline
        headline = f" {title}"
        
        # Create an attention-grabbing hook
        hook = "Did you know? The latest breakthrough in AI is changing how we think about technology. "
        
        # Format the main content with bullet points
        key_points = [
            " What's new: " + summary,
            " Why it matters: This development could reshape how we approach AI and machine learning.",
            " Impact: Potential applications span from everyday tech to groundbreaking research."
        ]
        
        # Add actionable insights
        takeaways = [
            " Stay informed about these developments",
            " Explore potential applications in your field",
            " Share your thoughts and experiences"
        ]
        
        # Build the post content with proper spacing
        content_parts = [
            headline,
            "",
            hook,
            "",
            "Key Insights:",
            *key_points,
            "",
            "Quick Takeaways:",
            *takeaways,
            "",
            f" Read the full article: {url}",
            "",
            "What are your thoughts on this development? Let's discuss! ",
            "",
            f"#AI #Innovation #TechTrends #FutureOfTech #{topic}"
        ]
        
        # Filter out empty parts and join with line breaks
        content = "<br><br>".join([part for part in content_parts if part])
        
        # Ensure proper spacing
        content = content.replace("<br><br><br>", "<br><br>")
        
        return content

    def close(self):
        """Close the WebDriver safely."""
        if hasattr(self, 'driver') and self.driver:
            try:
                # Get the process ID before closing
                try:
                    self.driver.service.process.kill()
                except:
                    pass
                
                # Close all windows
                try:
                    if hasattr(self.driver, 'window_handles'):
                        for handle in self.driver.window_handles:
                            try:
                                self.driver.switch_to.window(handle)
                                self.driver.close()
                            except:
                                pass
                except:
                    pass
                
                # Quit the driver
                try:
                    self.driver.quit()
                except:
                    pass
                
            except Exception as e:
                self.logger.warning(f"Error while closing browser: {str(e)}")
            finally:
                # Clear the driver reference
                self.driver = None
                self.logged_in = False

    def __del__(self):
        """Ensure browser is closed on object deletion."""
        try:
            self.close()
        except:
            pass

    def __enter__(self):
        """Support context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure browser is closed when exiting context."""
        try:
            self.close()
        except:
            pass
