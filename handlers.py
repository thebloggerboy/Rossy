# handlers.py (Final and Complete)

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

# हमारे दूसरे मॉड्यूल्स से ज़रूरी चीजें इम्पोर्ट करें
from config import ADMIN_IDS, FORCE_SUB_CHANNELS, FILE_DATA, DELETE_DELAY
from database import db, add_user, ban_user, unban_user # ये फंक्शन्स हम बाद में बनाएंगे

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
            logger.warning(f"Could not check membership for user {user_id} in channel {channel['chat_id']}. Is the bot an admin?")
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

async def auto_delete_messages(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id, message_ids, file_key = job.chat_id, job.data['message_ids'], job.data['file_key']
    try:
        for msg_id in message_ids:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except BadRequest:
                logger.warning(f"Could not delete message {msg_id}. Maybe it was already deleted.")
        
        keyboard = [[
            InlineKeyboardButton("♻️ Click Here", callback_data=f"resend_{file_key}"),
            InlineKeyboardButton("❌ Close ❌", callback_data="close_msg")
        ]]
        
        text = (f"Yᴏᴜʀ Fɪʟᴇ ({file_key}) ᴡᴀs Dᴇʟᴇᴛᴇᴅ 🗑\n"
                "Iғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɢᴇᴛ ɪᴛ ᴀɢᴀɪɴ, ᴄʟɪᴄᴋ ᴛʜᴇ [♻️ Cʟɪᴄᴋ Hᴇʀᴇ] ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ.")
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info(f"Messages deleted and resend prompt sent to user {chat_id}")
    except Exception as e:
        logger.error(f"Error in auto_delete_messages for user {chat_id}: {e}")

async def send_file(user_id: int, file_key: str, context: ContextTypes.DEFAULT_TYPE):
    if file_key not in FILE_DATA:
        await context.bot.send_message(chat_id=user_id, text="Sorry, this file key is invalid.")
        return

    file_info = FILE_DATA[file_key]
    file_type = file_info.get("type", "video")
    
    # --- बल्क/सीरीज सेंडिंग का लॉजिक ---
    if file_type == 'series':
        await context.bot.send_message(chat_id=user_id, text=f"Sending all episodes of the series. Please wait...")
        for episode_key in file_info.get("episodes", []):
            await asyncio.sleep(2) # स्पैम से बचने के लिए
            await send_file(user_id, episode_key, context) # हर एपिसोड को भेजें
        await context.bot.send_message(chat_id=user_id, text="✅ All episodes have been sent!")
        return

    # --- सिंगल फाइल भेजने का लॉजिक ---
    caption = file_info.get("caption", "")
    file_id = file_info.get("id")

    try:
        if file_type == 'video':
            message_to_delete = await context.bot.send_video(chat_id=user_id, video=file_id, caption=caption, parse_mode=ParseMode.HTML)
        elif file_type == 'document':
            message_to_delete = await context.bot.send_document(chat_id=user_id, document=file_id, caption=caption, parse_mode=ParseMode.HTML)
        else: # डिफॉल्ट वीडियो है
            message_to_delete = await context.bot.send_video(chat_id=user_id, video=file_id, caption=caption, parse_mode=ParseMode.HTML)

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
    if update.effective_user.id not in ADMIN_IDS: return
    
    msg = update.message.reply_to_message
    if not msg:
        await update.message.reply_text("Please reply to a message to get its IDs.")
        return
        
    text = f"--- ℹ️ IDs Found ℹ️ ---\n\n"
    text += f"👤 User ID: {msg.from_user.id}\n"
    text += f"💬 Chat ID: {msg.chat.id}\n\n"
    
    file_id = None
    if msg.video: file_id = msg.video.file_id
    elif msg.document: file_id = msg.document.file_id
    elif msg.audio: file_id = msg.audio.file_id
    elif msg.photo: file_id = msg.photo[-1].file_id
        
    if file_id:
        text += f"📄 File ID:\n{file_id}"
    
    await update.message.reply_text(text)

async def get_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    
    msg = update.message.reply_to_message
    if not msg or not msg.forward_origin:
        await update.message.reply_text("Please reply to a FORWARDED message from a channel.")
        return

    origin = msg.forward_origin
    text = f"--- ℹ️ Forwarded Message IDs ℹ️ ---\n\n"
    text += f"📢 Original Channel ID: {origin.chat.id}\n\n"
    
    file_id = None
    if msg.video: file_id = msg.video.file_id
    elif msg.document: file_id = msg.document.file_id
    
    if file_id:
        text += f"📄 File ID:\n{file_id}"
    
    await update.message.reply_text(text)

# --- सभी हैंडलर्स को रजिस्टर करने के लिए एक फंक्शन ---
def register_handlers(application):
    """सभी कमांड्स और बटनों के हैंडलर्स को रजिस्टर करता है।"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", id_handler))
    application.add_handler(CommandHandler("get", get_handler))
    application.add_handler(CallbackQueryHandler(button_handler))
