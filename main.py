# main.py
import os
import logging
from threading import Thread
from flask import Flask
from telegram.ext import Application
from dotenv import load_dotenv

# हमारे बनाए हुए मॉड्यूल्स को इम्पोर्ट करें
from handlers import register_handlers
from config import TOKEN

# .env फाइल लोड करें
load_dotenv()

# === बेसिक सेटअप ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Flask वेब सर्वर (यह हमारी मुख्य एप्लीकेशन है) ---
app = Flask('')

@app.route('/')
def home():
    return "Hanny Bot is alive and running!"

# --- Telegram बॉट का सेटअप ---
def run_bot():
    """बॉट एप्लीकेशन बनाता है, हैंडलर्स रजिस्टर करता है, और पोलिंग शुरू करता है।"""
    if not TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN not set!")
        return
        
    application = Application.builder().token(TOKEN).build()
    register_handlers(application) # हैंडलर्स को handlers.py से रजिस्टर करें
    
    logger.info("Bot is starting polling...")
    application.run_polling()

# --- मुख्य हिस्सा ---
if __name__ == '__main__':
    # बॉट को एक अलग थ्रेड में चलाएं
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    
    # Flask सर्वर को मुख्य थ्रेड में चलाएं
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
