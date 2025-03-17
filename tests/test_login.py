from dotenv import load_dotenv
import os

load_dotenv()

bot = FacebookBot()
bot.login(os.getenv("FB_USERNAME"), os.getenv("FB_PASSWORD"))
bot.check_messages()
bot.close()