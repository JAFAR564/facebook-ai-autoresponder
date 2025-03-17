# automation/facebook_bot.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
import pyotp
import os
import time
import random
import pickle
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='facebook_bot.log'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class FacebookBot:
    def __init__(self, headless=False):
        """Initialize the Facebook bot with ChromeDriver options."""
        self.options = ChromeOptions()
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Add additional options for stability
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        
        if headless:
            self.options.add_argument("--headless")
        
        self.driver = Chrome(options=self.options)
        self.secret_key = os.getenv("FB_2FA_SECRET")
        
        # Add explicit waits
        self.wait = WebDriverWait(self.driver, 15)
        
        logger.info("FacebookBot initialized")

    def login(self, username, password):
        """Log in to Facebook with provided credentials."""
        try:
            logger.info("Attempting to log in")
            self.driver.get("https://www.facebook.com")
            self._add_random_delay(2, 5)
            
            # Try to load cookies first
            if os.path.exists("cookies.pkl"):
                self.load_cookies()
                self.driver.get("https://www.facebook.com")
                self._add_random_delay(3, 6)
                
                # Check if login was successful with cookies
                if self._is_logged_in():
                    logger.info("Login successful with cookies")
                    return True
            
            # Manual login if cookies didn't work
            logger.info("Performing manual login")
            
            # Wait for login form elements to be present
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            password_field = self.wait.until(EC.presence_of_element_located((By.ID, "pass")))
            
            # Enter credentials with human-like typing
            self._type_like_human(email_field, username)
            self._type_like_human(password_field, password)
            password_field.send_keys(Keys.RETURN)
            
            self._add_random_delay(5, 10)
            
            # Debug information
            logger.info(f"Current Page Title: {self.driver.title}")
            logger.info(f"Current Page URL: {self.driver.current_url}")
            
            # Check for 2FA
            if self._is_2fa_required():
                logger.info("2FA required, generating code")
                code = self._generate_2fa_code()
                logger.info(f"Generated 2FA code: {code}")
                self._submit_2fa_code(code)
                
                # Check for "save browser" prompt and handle it
                self._handle_save_browser_prompt()
            
            # Check if login was successful
            if self._is_logged_in():
                logger.info("Login successful")
                self.save_cookies()
                return True
            else:
                logger.error("Login failed")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def _is_logged_in(self):
        """Check if the user is logged in to Facebook."""
        try:
            # Look for elements that are only present when logged in
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Your profile' or @aria-label='Account' or contains(@aria-label, 'Facebook Menu')]")))
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    def _is_2fa_required(self):
        """Check if 2FA verification is required."""
        try:
            page_source = self.driver.page_source
            return (
                "Go to your authentication app" in page_source
                or "Enter the 6-digit code for this account" in page_source
                or "Two-factor authentication" in page_source
                or "Login approval" in page_source
            )
        except Exception as e:
            logger.error(f"Error checking for 2FA: {str(e)}")
            return False

    def _generate_2fa_code(self):
        """Generate a 2FA code using TOTP."""
        if not self.secret_key:
            logger.error("2FA secret key not found in environment variables")
            raise ValueError("2FA secret key not found")
        
        totp = pyotp.TOTP(self.secret_key)
        return totp.now()

    def _submit_2fa_code(self, code):
        """Submit the 2FA code."""
        try:
            # Try different selectors for 2FA input
            selectors = [
                (By.NAME, "approvals_code"),
                (By.ID, "approvals_code"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'code')]"),
                (By.XPATH, "//input[contains(@id, 'code') or contains(@name, 'code')]")
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    code_input = self.wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
                    code_input.clear()
                    self._type_like_human(code_input, code)
                    
                    # Look for submit button
                    submit_buttons = [
                        (By.ID, "checkpointSubmitButton"),
                        (By.NAME, "submit[Continue]"),
                        (By.XPATH, "//button[contains(text(), 'Continue') or contains(text(), 'Submit')]")
                    ]
                    
                    for btn_type, btn_value in submit_buttons:
                        try:
                            submit_button = self.wait.until(EC.element_to_be_clickable((btn_type, btn_value)))
                            submit_button.click()
                            self._add_random_delay(5, 10)
                            logger.info("2FA code submitted")
                            return
                        except:
                            continue
                            
                    # If we found the input but no button worked, just press Enter
                    code_input.send_keys(Keys.RETURN)
                    self._add_random_delay(5, 10)
                    logger.info("2FA code submitted with Enter key")
                    return
                    
                except:
                    continue
                    
            logger.error("Failed to locate 2FA input elements")
            
        except Exception as e:
            logger.error(f"Error submitting 2FA code: {str(e)}")

    def _handle_save_browser_prompt(self):
        """Handle the 'save this browser' prompt after 2FA."""
        try:
            # Try to find "Don't Save" or "This is a public computer" options
            selectors = [
                (By.XPATH, "//button[contains(text(), 'Don') and contains(text(), 'Save')]"),
                (By.XPATH, "//a[contains(text(), 'public') or contains(text(), 'Don')]"),
                (By.ID, "checkpointSubmitButton")  # Sometimes just continuing works
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    button = self.wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
                    button.click()
                    self._add_random_delay(3, 6)
                    logger.info("Handled save browser prompt")
                    return
                except:
                    continue
        except:
            logger.info("No save browser prompt found or handling failed")

    def _type_like_human(self, element, text):
        """Type text with random delays to mimic human typing."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))

    def _add_random_delay(self, min_seconds, max_seconds):
        """Add a random delay to mimic human behavior."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def save_cookies(self):
        """Save browser cookies to file."""
        try:
            cookies = self.driver.get_cookies()
            with open("cookies.pkl", "wb") as file:
                pickle.dump(cookies, file)
            logger.info("Cookies saved successfully")
        except Exception as e:
            logger.error(f"Error saving cookies: {str(e)}")

    def load_cookies(self):
        """Load cookies from file."""
        try:
            with open("cookies.pkl", "rb") as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception:
                        pass  # Skip invalid cookies
            logger.info("Cookies loaded")
            return True
        except Exception as e:
            logger.error(f"Error loading cookies: {str(e)}")
            return False

    def navigate_to_group(self, group_url):
        """Navigate to a Facebook group."""
        try:
            self.driver.get(group_url)
            self._add_random_delay(3, 7)
            logger.info(f"Navigated to group: {group_url}")
            return True
        except Exception as e:
            logger.error(f"Error navigating to group: {str(e)}")
            return False

    def post_to_group(self, group_url, message):
        """Post a message to a Facebook group."""
        try:
            self.navigate_to_group(group_url)
            
            # Find the post composer
            post_box_selectors = [
                (By.XPATH, "//div[@role='button' and contains(text(), 'Write something')]"),
                (By.XPATH, "//div[@aria-label='Create a post']"),
                (By.XPATH, "//div[contains(@aria-label, 'post')]")
            ]
            
            for selector_type, selector_value in post_box_selectors:
                try:
                    post_box = self.wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
                    post_box.click()
                    self._add_random_delay(1, 3)
                    break
                except:
                    continue
            
            # Find the text input area after the composer opens
            text_area_selectors = [
                (By.XPATH, "//div[@contenteditable='true']"),
                (By.XPATH, "//div[@role='textbox']")
            ]
            
            for selector_type, selector_value in text_area_selectors:
                try:
                    text_area = self.wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
                    self._add_random_delay(1, 2)
                    text_area.send_keys(message)
                    self._add_random_delay(2, 4)
                    break
                except:
                    continue
            
            # Click Post button
            post_button_selectors = [
                (By.XPATH, "//div[@aria-label='Post']"),
                (By.XPATH, "//button[contains(text(), 'Post')]")
            ]
            
            for selector_type, selector_value in post_button_selectors:
                try:
                    post_button = self.wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
                    post_button.click()
                    self._add_random_delay(5, 10)
                    logger.info(f"Posted to group: {group_url}")
                    return True
                except:
                    continue
                    
            logger.error("Failed to post to group")
            return False
            
        except Exception as e:
            logger.error(f"Error posting to group: {str(e)}")
            return False

    def check_messages(self):
        """Check for unread messages."""
        try:
            logger.info("Checking messages")
            self.driver.get("https://www.facebook.com/messages")
            self._add_random_delay(3, 7)
            
            # Find unread messages
            unread_message_selectors = [
                (By.XPATH, "//div[contains(@aria-label, 'unread')]"),
                (By.CSS_SELECTOR, "div[aria-label*='unread']"),
                (By.XPATH, "//div[contains(@class, 'unread')]")
            ]
            
            unread_messages = []
            
            for selector_type, selector_value in unread_message_selectors:
                try:
                    elements = self.driver.find_elements(selector_type, selector_value)
                    if elements:
                        unread_messages.extend(elements)
                except:
                    continue
            
            logger.info(f"Found {len(unread_messages)} unread messages")
            return unread_messages
            
        except Exception as e:
            logger.error(f"Error checking messages: {str(e)}")
            return []

    def reply_to_message(self, message_element, reply_text):
        """Reply to a specific message."""
        try:
            message_element.click()
            self._add_random_delay(2, 5)
            
            # Find reply input field
            reply_input = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='textbox' and @contenteditable='true']")))
            self._type_like_human(reply_input, reply_text)
            self._add_random_delay(1, 3)
            
            # Send the message
            reply_input.send_keys(Keys.RETURN)
            self._add_random_delay(2, 4)
            logger.info("Replied to message")
            return True
            
        except Exception as e:
            logger.error(f"Error replying to message: {str(e)}")
            return False

    def close(self):
        """Close the browser and clean up."""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
                logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

    def __del__(self):
        """Destructor to ensure the browser is closed."""
        self.close()
