# handlers.py
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

# हमारे दूसरे मॉड्यूल्स से ज़रूरी चीजें इम्पोर्ट करें
from config import ADMIN_IDS, FORCE_SUB_CHANNELS, FILE_DATA, DELETE_DELAY
from database import db, add_user, ban_user, unban_user # हम बाद में इन फंक्शन्स को बनाएंगे

logger = logging.getLogger(__name__)

# --- हेल्पर फंक्शन्स ---
async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if user_id in ADMIN_IDS: return True
    if not FORCE_SUB_CHANNELS: return True
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel["chat_id"], user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']: return False
        except BadRequest: return False
    return True

async def send_force_subscribe_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_key = context.user_data.get('file_key')
    if not file_key: return
    join_buttons = [InlineKeyboardButton(ch["name"], url=ch["invite_link"]) for ch in FORCE_SUB_CHANNELS]
    keyboard = [join_buttons, [InlineKeyboardButton("✅ Joined", callback_data=f"check_{file_key}")]]
    await update.message.reply_text("Please join all required channels to get the file.", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_file(user_id: int, file_key: str, context: ContextTypes.DEFAULT_TYPE):
    # यह फंक्शन बाद में ऑटो-डिलीट और सीरीज को हैंडल करेगा
    if file_key in FILE_DATA:
        file_info = FILE_DATA[file_key]
        await context.bot.send_video(chat_id=user_id, video=file_info["id"], caption=file_info["caption"], parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id=user_id, text="Sorry, file key not found.")

# --- कमांड और बटन हैंडलर्स ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id) # नए यूजर को डेटाबेस में जोड़ें

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
        await update.message.reply_text(f"Welcome, {user.first_name}! Please use a link from our main channel.")

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
            await query.answer("You haven't joined all channels yet. Please join and try again.", show_alert=True)

async def id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = update.message.reply_to_message
    if not msg:
        await update.message.reply_text("Please reply to a message to get IDs.")
        return
    text = f"User ID: {msg.from_user.id}\nChat ID: {msg.chat.id}"
    if msg.video: text += f"\nFile ID: {msg.video.file_id}"
    await update.message.reply_text(text)

async def get_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = update.message.reply_to_message
    if not msg or not msg.forward_origin:
        await update.message.reply_text("Please reply to a FORWARDED message.")
        return
    origin = msg.forward_origin
    text = f"Original Channel ID: {origin.chat.id}"
    if msg.video: text += f"\nFile ID: {msg.video.file_id}"
    await update.message.reply_text(text)

def register_handlers(application):
    """सभी हैंडलर्स को रजिस्टर करता है।"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", id_handler))
    application.add_handler(CommandHandler("get", get_handler))
    application.add_handler(CallbackQueryHandler(button_handler))
