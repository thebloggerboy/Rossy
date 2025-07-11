# main.py
import os
import logging
from threading import Thread
from flask import Flask
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

# .env फाइल लोड करें
load_dotenv()

# हमारे बनाए हुए मॉड्यूल्स को इम्पोर्ट करें
from config import ADMIN_IDS
from handlers import start #, button_handler, broadcast_handler, etc.

# === बेसिक सेटअप ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# --- Keep-Alive सर्वर ---
app = Flask('')
@app.route('/')
def home(): return "Bot is alive and running!"
def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- मुख्य फंक्शन ---
def main():
    if not TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN not set!")
        return

    application = Application.builder().token(TOKEN).build()
    
    # कमांड्स को रजिस्टर करें
    application.add_handler(CommandHandler("start", start))
    # --- बाकी के हैंडलर बाद में यहाँ जोड़े जाएंगे ---
    
    keep_alive()
    logger.info("Bot is ready and polling!")
    application.run_polling()

if __name__ == '__main__':
    main()