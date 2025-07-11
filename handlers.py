# handlers.py (Upgraded for Phase 2)

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

# हमारे दूसरे मॉड्यूल्स से ज़रूरी चीजें इम्पोर्ट करें
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
        except BadRequest: return False
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

async def auto_delete_messages(context: ContextTypes.DEFAULT_TYPE):
    """वीडियो और वार्निंग मैसेज, दोनों को डिलीट करता है और री-सेंड मैसेज भेजता है।"""
    job = context.job
    chat_id, message_ids, file_key = job.chat_id, job.data['message_ids'], job.data['file_key']
    try:
        for msg_id in message_ids:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        
        keyboard = [[
            InlineKeyboardButton("♻️ Click Here", callback_data=f"resend_{file_key}"),
            InlineKeyboardButton("❌ Close ❌", callback_data="close_msg")
        ]]
        
        # मैसेज में फाइल का नाम भी दिखाएं
        text = (f"Yᴏᴜʀ Fɪʟᴇ ({file_key}) ᴡᴀs Dᴇʟᴇᴛᴇᴅ 🗑\n"
                "Iғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɢᴇᴛ ɪᴛ ᴀɢᴀɪɴ, ᴄʟɪᴄᴋ ᴛʜᴇ [♻️ Cʟɪᴄᴋ Hᴇʀᴇ] ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ.")
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info(f"Messages {message_ids} deleted and resend prompt sent to user {chat_id}")
    except Exception as e:
        logger.error(f"Error in auto_delete_messages: {e}")

async def send_file(user_id: int, file_key: str, context: ContextTypes.DEFAULT_TYPE, is_resend=False):
    """फाइल/सीरीज भेजता है और डिलीट का काम शेड्यूल करता है।"""
    if file_key not in FILE_DATA:
        if not is_resend: await context.bot.send_message(chat_id=user_id, text="Sorry, this file key is invalid.")
        return

    file_info = FILE_DATA[file_key]
    file_type = file_info.get("type", "video")

    if file_type == 'series':
        if not is_resend: await context.bot.send_message(chat_id=user_id, text=f"Sending all episodes of the series. Please wait...")
        for episode_key in file_info.get("episodes", []):
            await asyncio.sleep(2)
            await send_file(user_id, episode_key, context, is_resend=True) # Recursive call
        if not is_resend: await context.bot.send_message(chat_id=user_id, text="✅ All episodes sent!")
        return

    # सिंगल फाइल भेजने का लॉजिक
    caption = file_info.get("caption", "")
    file_id = file_info.get("id")

    try:
        if file_type == 'video':
            message_to_delete = await context.bot.send_video(chat_id=user_id, video=file_id, caption=caption, parse_mode=ParseMode.HTML)
        elif file_type == 'document':
            message_to_delete = await context.bot.send_document(chat_id=user_id, document=file_id, caption=caption, parse_mode=ParseMode.HTML)
        
        warning_text = "⚠️ Dᴜᴇ ᴛᴏ Cᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs....\nYᴏᴜʀ ғɪʟᴇs ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ᴡɪᴛʜɪɴ 15 Mɪɴᴜᴛᴇs. Sᴏ ᴘʟᴇᴀsᴇ ᴅᴏᴡɴʟᴏᴀᴅ ᴏʀ ғᴏʀᴡᴀʀᴅ ᴛʜᴇᴍ."
        warning_message = await context.bot.send_message(chat_id=user_id, text=warning_text)
        
        # ऑटो-डिलीट शेड्यूल करें
        context.job_queue.run_once(
            auto_delete_messages, 
            DELETE_DELAY, 
            data={'message_ids': [message_to_delete.message_id, warning_message.message_id], 'file_key': file_key}, 
            chat_id=user_id
        )
        logger.info(f"Sent file '{file_key}' and scheduled deletion for user {user_id}")
    except Exception as e:
        logger.error(f"Error sending file {file_key}: {e}")
        if not is_resend: await context.bot.send_message(chat_id=user_id, text="Sorry, an error occurred while sending the file.")

# --- कमांड और बटन हैंडलर्स ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)
    if user.id in db["banned_users"]: return

    if context.args:
        file_key = context.args[0]
        context.user_data['file_key'] = file_key
        if await is_user_member(user.id, context):
            await send_file(user.id, file_key, context)
        else:
            await send_force_subscribe_message(update, context)
    else:
        # यहाँ हम बाद में मेन्यू बनाएंगे
        await update.message.reply_text(f"Welcome, {user.first_name}!")

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
            
    elif data.startswith("resend_"):
        await query.answer()
        file_key = data.split("_", 1)[1]
        await query.message.delete()
        await send_file(user_id, file_key, context)
        
    elif data == "close_msg":
        await query.message.delete()

# --- एडमिन कमांड्स ---
async def id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (यह फंक्शन वैसा ही रहेगा)

async def get_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (यह फंक्शन वैसा ही रहेगा)

def register_handlers(application):
    """सभी हैंडलर्स को रजिस्टर करता है।"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", id_handler))
    application.add_handler(CommandHandler("get", get_handler))
    application.add_handler(CallbackQueryHandler(button_handler))
