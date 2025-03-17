import sys
import os

# Add the project root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.facebook_bot import FacebookBot
from ai_engine.response_generator import AIResponseGenerator
from dotenv import load_dotenv
from textblob import TextBlob
import os

load_dotenv()

def test_facebook_bot_login():
    # Load environment variables
    load_dotenv()

    # Initialize and test the bot
    bot = FacebookBot()
    try:
        # Test login
        bot.login(os.getenv("FB_USERNAME"), os.getenv("FB_PASSWORD"))
        print("Login successful!")

        # Test message checking
        bot.check_messages()
        print("Message check complete!")

    finally:
        # Ensure the bot closes properly
        bot.close()
        print("Bot closed.")

def test_ai_response_generator():
    # Test the AI response generator
    persona = {
        "name": "Eldrin the Wise",
        "backstory": "A centuries-old wizard who guards the secrets of the ancient library.",
        "personality": "Wise, patient, and slightly cryptic."
    }
    ai = AIResponseGenerator(persona)
    response = ai.generate_response("What is the meaning of life?")
    print("AI Response:", response)

if __name__ == "__main__":
    test_facebook_bot_login()
    test_ai_response_generator()