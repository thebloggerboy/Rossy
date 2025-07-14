# main.py
import os
import logging
from threading import Thread
from flask import Flask
from telegram.ext import Application
from dotenv import load_dotenv

# हमारे बनाए हुए मॉड्यूल्स को इम्पोर्ट करें
from handlers import register_handlers
from config import TOKEN # अब हम config.py से TOKEN इम्पोर्ट करेंगे

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Flask वेब सर्वर ---
app = Flask('')
@app.route('/')
def home(): return "Hanny Bot is alive!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run_flask).start()

# --- मुख्य फंक्शन ---
def main():
    bot_token = TOKEN or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.critical("TELEGRAM_BOT_TOKEN not set!")
        return

    application = Application.builder().token(bot_token).build()
    
    register_handlers(application)
    
    keep_alive()
    logger.info("Bot is ready and polling!")
    application.run_polling()

if __name__ == '__main__':
    main()