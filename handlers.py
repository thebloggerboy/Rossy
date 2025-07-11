# handlers.py

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

# हमारे दूसरे मॉड्यूल्स से ज़रूरी चीजें इम्पोर्ट करें
from config import ADMIN_IDS, FORCE_SUB_CHANNELS, FILE_DATA, DELETE_DELAY
from database import db, add_user, ban_user, unban_user # हम बाद में ban/unban का इस्तेमाल करेंगे

logger = logging.getLogger(__name__)

# --- हेल्पर फंक्शन्स (अब ये हैंडलर्स फाइल में हैं) ---

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """चेक करता है कि यूजर सभी ज़रूरी चैनलों का मेंबर है या नहीं।"""
    if user_id in ADMIN_IDS: return True
    if not FORCE_SUB_CHANNELS: return True
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel["chat_id"], user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except BadRequest:
            logger.warning(f"Could not check membership for user {user_id} in channel {channel['chat_id']}.")
            return False # अगर बॉट एडमिन नहीं है, तो एक्सेस न दें
    return True

async def send_force_subscribe_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """यूजर को चैनल ज्वाइन करने का मैसेज और बटन भेजता है।"""
    file_key = context.user_data.get('file_key')
    if not file_key: return

    join_buttons = [InlineKeyboardButton(ch["name"], url=ch["invite_link"]) for ch in FORCE_SUB_CHANNELS]
    keyboard = [
        join_buttons,
        [InlineKeyboardButton("✅ Joined", callback_data=f"check_{file_key}")]
    ]
    await update.message.reply_text(
        "Please join all required channels to get the file.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_file(user_id: int, file_key: str, context: ContextTypes.DEFAULT_TYPE):
    """Supabase या config से फाइल की जानकारी लेकर उसे भेजता है।"""
    if file_key not in FILE_DATA:
        await context.bot.send_message(chat_id=user_id, text="Sorry, this file key is invalid.")
        return

    file_info = FILE_DATA[file_key]
    file_type = file_info.get("type", "video")

    if file_type == 'series':
        # सीरीज भेजने का लॉजिक (हम इसे बाद में बनाएंगे)
        await context.bot.send_message(chat_id=user_id, text=f"Series sending is coming soon!")
        return
    
    # सिंगल फाइल भेजने का लॉजिक
    caption = file_info.get("caption", "")
    file_id = file_info.get("id")

    try:
        if file_type == 'video':
            await context.bot.send_video(chat_id=user_id, video=file_id, caption=caption, parse_mode=ParseMode.HTML)
        elif file_type == 'document':
            await context.bot.send_document(chat_id=user_id, document=file_id, caption=caption, parse_mode=ParseMode.HTML)
        
        logger.info(f"Sent file for key '{file_key}' to user {user_id}")
    except Exception as e:
        logger.error(f"Error sending file {file_key} to {user_id}: {e}")
        await context.bot.send_message(chat_id=user_id, text="Sorry, an error occurred while sending the file.")


# --- कमांड और बटन हैंडलर्स ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start कमांड को हैंडल करता है।"""
    user = update.effective_user
    user_id = user.id

    add_user(user_id) # नए यूजर को डेटाबेस में जोड़ें

    if user_id in db["banned_users"]:
        await update.message.reply_text("You are banned from using this bot.")
        return

    if context.args:
        file_key = context.args[0]
        context.user_data['file_key'] = file_key
        
        if await is_user_member(user_id, context):
            await send_file(user_id, file_key, context)
        else:
            await send_force_subscribe_message(update, context)
    else:
        await update.message.reply_text(f"Welcome, {user.first_name}! Please use a link from our main channel to get files.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """सभी Inline बटनों के क्लिक को हैंडल करता है।"""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("check_"):
        file_key = data.split("_", 1)[1]
        
        if await is_user_member(user_id, context):
            await query.answer()
            await query.message.delete()
            await send_file(user_id, file_key, context)
        else:
            await query.answer("You haven't joined all required channels yet. Please join and try again.", show_alert=True)
