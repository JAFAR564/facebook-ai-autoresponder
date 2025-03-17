from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
import pyotp
import os
import time
import random
import pickle

# Load environment variables
load_dotenv()
secret_key = os.getenv("FB_2FA_SECRET")

class FacebookBot:
    def __init__(self):
        self.options = ChromeOptions()
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = Chrome(options=self.options, headless=False)
        self.secret_key = secret_key  # Store the 2FA secret key

        # Load cookies if they exist
        if os.path.exists("cookies.pkl"):
            self.load_cookies()

    def login(self, username, password):
        self.driver.get("https://www.facebook.com")
        time.sleep(random.uniform(2, 5))

        # Load cookies if they exist
        if os.path.exists("cookies.pkl"):
            self.load_cookies()

        # Enter username and password
        self.driver.find_element(By.ID, "email").send_keys(username)
        self.driver.find_element(By.ID, "pass").send_keys(password + Keys.RETURN)
        time.sleep(random.uniform(5, 10))

        # Debug: Print the current page title and URL
        print("Current Page Title:", self.driver.title)
        print("Current Page URL:", self.driver.current_url)

        # Check if 2FA is required
        if self.is_2fa_required():
            print("2FA is required. Generating and submitting code...")
            code = self.generate_2fa_code()
            print("Generated 2FA Code:", code)
            self.submit_2fa_code(code)
        else:
            print("2FA is not required.")

        # Save cookies after successful login
        self.save_cookies()

    def is_2fa_required(self):
        # Check if the 2FA page is displayed
        page_source = self.driver.page_source
        return (
            "Go to your authentication app" in page_source
            or "Enter the 6-digit code for this account" in page_source
        )

    def generate_2fa_code(self):
        # Generate a 2FA code using pyotp
        totp = pyotp.TOTP(self.secret_key)
        return totp.now()

    def submit_2fa_code(self, code):
        try:
            # Find the 2FA input field and submit button
            code_input = self.driver.find_element(By.NAME, "approvals_code")  # Updated selector
            submit_button = self.driver.find_element(By.ID, "checkpointSubmitButton")

            # Enter the code and submit
            code_input.send_keys(code)
            submit_button.click()
            time.sleep(random.uniform(5, 10))
            print("2FA code submitted successfully.")
        except Exception as e:
            print("Failed to submit 2FA code:", e)

    def save_cookies(self):
        # Save cookies to a file
        cookies = self.driver.get_cookies()
        with open("cookies.pkl", "wb") as file:
            pickle.dump(cookies, file)
        print("Cookies saved successfully.")

    def load_cookies(self):
        # Navigate to Facebook before loading cookies
        self.driver.get("https://www.facebook.com")
        time.sleep(random.uniform(2, 5))

        # Load cookies from a file
        with open("cookies.pkl", "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
        print("Cookies loaded successfully.")

    def check_messages(self):
        self.driver.get("https://www.facebook.com/messages")
        time.sleep(random.uniform(3, 7))
        # Add logic to parse and respond to messages

    def close(self):
        self.driver.quit()

    def __del__(self):
        try:
            self.driver.quit()
        except:
            pass  # Ignore any errors during cleanup