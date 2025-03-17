# config.py
from dotenv import load_dotenv
import os

load_dotenv()

secret_key = os.getenv("FB_2FA_SECRET")
