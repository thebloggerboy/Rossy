# handlers.py

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

from config import ADMIN_IDS, FORCE_SUB_CHANNELS, FILE_DATA, DELETE_DELAY
from database import db, add_user

logger = logging.getLogger(__name__)

# --- हेल्पर फंक्शन्स ---
async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if user_id in ADMIN_IDS: return True
    if not FORCE_SUB_CHANNELS: return True
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel["chat_id"], user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']: return False
        except BadRequest:
            logger.warning(f"Could not check membership for user {user_id} in channel {channel['chat_id']}.")
            return False
    return True

async def send_force_subscribe_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if file_key not in FILE_DATA:
        await context.bot.send_message(chat_id=user_id, text="Sorry, this file key is invalid.")
        return

    file_info = FILE_DATA[file_key]
    file_type = file_info.get("type", "video")

    # --- यहाँ हम बाद में ऑटो-डिलीट और सीरीज का लॉजिक जोड़ेंगे ---
    
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
    user = update.effective_user
    add_user(user.id)

    if user.id in db["banned_users"]:
        await update.message.reply_text("You are banned from using this bot.")
        return

    if context.args:
        file_key = context.args[0]
        context.user_data['file_key'] = file_key
        
        if await is_user_member(user.id, context):
            await send_file(user.id, file_key, context)
        else:
            await send_force_subscribe_message(update, context)
    else:
        await update.message.reply_text(f"Welcome, {user.first_name}! Please use a link from our main channel to get files.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
