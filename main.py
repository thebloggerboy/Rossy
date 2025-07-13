# main.py (Final with Universal ID Finder & Sender)
import os
import logging
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest
from dotenv import load_dotenv

# हमारे बनाए हुए मॉड्यूल्स को इम्पोर्ट करें
from config import ADMIN_IDS, FORCE_SUB_CHANNELS, FILE_DATA, DELETE_DELAY, MAIN_CHANNEL_LINK
from database import db, add_user, ban_user, unban_user, get_all_user_ids, save_db

# .env फाइल लोड करें
load_dotenv()

# === बेसिक सेटअप ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# --- फैंसी टेक्स्ट ---
WELCOME_TEXT = "Wᴇʟᴄᴏᴍᴇ, {user_name}! Pʟᴇᴀsᴇ ᴜsᴇ ᴀ ʟɪɴᴋ ғʀᴏᴍ ᴏᴜʀ ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ."
JOIN_CHANNEL_TEXT = "Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴀʟʟ ʀᴇǫᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟs ᴛᴏ ɢᴇᴛ ᴛʜᴇ ғɪʟᴇ."
NOT_JOINED_ALERT = "Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ ᴀʟʟ ʀᴇǫᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟs ʏᴇᴛ. Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ."
BANNED_TEXT = "Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ."
FILE_NOT_FOUND_TEXT = "Sᴏʀʀʏ, ғɪʟᴇ ᴋᴇʏ ɴᴏᴛ ғᴏᴜɴᴅ."
DELETE_WARNING_TEXT = "⚠️ Yᴏᴜʀ ғɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ᴡɪᴛʜɪɴ 15 Mɪɴᴜᴛᴇs. Pʟᴇᴀsᴇ ᴅᴏᴡɴʟᴏᴀᴅ ᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴛ."
RESEND_PROMPT_TEXT = "<i>Yᴏᴜʀ Fɪʟᴇ ({file_key}) ᴡᴀs Dᴇʟᴇᴛᴇᴅ 🗑\nIғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɢᴇᴛ ɪᴛ ᴀɢᴀɪɴ, ᴄʟɪᴄᴋ ᴛʜᴇ 'Wᴀᴛᴄʜ Aɢᴀɪɴ' ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ.</i>"

# --- Keep-Alive सर्वर ---
app = Flask('')
@app.route('/')
def home(): return "Bot is alive and running!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run_flask).start()

# --- हेल्पर फंक्शन्स ---
async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if user_id in ADMIN_IDS: return True
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
    keyboard = [join_buttons, [InlineKeyboardButton("✅ Jᴏɪɴᴇᴅ", callback_data=f"check_{file_key}")]]
    await update.message.reply_text(JOIN_CHANNEL_TEXT, reply_markup=InlineKeyboardMarkup(keyboard))

async def auto_delete_messages(context: ContextTypes.DEFAULT_TYPE):
    job = context.job; chat_id, message_ids, file_key, caption = job.chat_id, job.data['message_ids'], job.data['file_key'], job.data['caption']
    try:
        for msg_id in message_ids:
            try: await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except BadRequest: pass
        keyboard = [[InlineKeyboardButton("▶️ Wᴀᴛᴄʜ Aɢᴀɪɴ", callback_data=f"resend_{file_key}"), InlineKeyboardButton("❌ Dᴇʟᴇᴛᴇ", callback_data="close_msg")]]
        text = f"{caption}\n\n{RESEND_PROMPT_TEXT.format(file_key=file_key)}"
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e: logger.error(f"Error in auto_delete_messages: {e}")

# --- Universal File Sender ---
async def send_file(user_id: int, file_key: str, context: ContextTypes.DEFAULT_TYPE, is_resend: bool = False):
    if file_key not in FILE_DATA:
        if not is_resend: await context.bot.send_message(chat_id=user_id, text=FILE_NOT_FOUND_TEXT)
        return
    
    file_info = FILE_DATA[file_key]
    file_type = file_info.get("type", "video")
    caption = file_info.get("caption", "")
    file_id = file_info.get("id")
    
    reply_markup = None
    if "buttons" in file_info:
        keyboard = []
        for row in file_info["buttons"]:
            button_row = [InlineKeyboardButton(btn["text"], url=btn.get("url"), callback_data=btn.get("callback_data")) for btn in row]
            keyboard.append(button_row)
        if keyboard: reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        message_to_delete = None
        if file_type == 'video':
            message_to_delete = await context.bot.send_video(chat_id=user_id, video=file_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        elif file_type == 'photo':
            message_to_delete = await context.bot.send_photo(chat_id=user_id, photo=file_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        elif file_type == 'document':
            message_to_delete = await context.bot.send_document(chat_id=user_id, document=file_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        
        if message_to_delete:
            warning_message = await context.bot.send_message(chat_id=user_id, text=DELETE_WARNING_TEXT)
            context.job_queue.run_once(auto_delete_messages, DELETE_DELAY, data={'message_ids': [message_to_delete.message_id, warning_message.message_id], 'file_key': file_key, 'caption': caption, 'is_resent': is_resend}, chat_id=user_id)
    except Exception as e:
        logger.error(f"Error sending file {file_key}: {e}")

# --- कमांड और बटन हैंडलर्स ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; add_user(user.id)
    if user.id in db["banned_users"]: await update.message.reply_text(BANNED_TEXT); return
    if context.args:
        file_key = context.args[0]; context.user_data['file_key'] = file_key
        if await is_user_member(user.id, context): await send_file(user.id, file_key, context)
        else: await send_force_subscribe_message(update, context)
    else:
        keyboard = [[InlineKeyboardButton("Mᴀɪɴ Cʜᴀɴɴᴇʟ", url=MAIN_CHANNEL_LINK)]]
        await update.message.reply_text(WELCOME_TEXT.format(user_name=user.first_name), reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = query.from_user.id; data = query.data
    await query.answer()
    if data.startswith("check_"):
        file_key = data.split("_", 1)[1]
        if await is_user_member(user_id, context): await query.message.delete(); await send_file(user_id, file_key, context)
        else: await query.answer(text=NOT_JOINED_ALERT, show_alert=True)
    elif data.startswith("resend_"):
        file_key = data.split("_", 1)[1]
        await query.message.delete(); await send_file(user_id, file_key, context, is_resend=True)
    elif data == "close_msg": await query.message.delete()

# --- Universal ID Finder ---
async def id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = update.message.reply_to_message
    if not msg: await update.message.reply_text("Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ."); return
    text = f"👤 Usᴇʀ ID: `{msg.from_user.id}`\n💬 Cʜᴀᴛ ID: `{msg.chat.id}`"
    file_id = None
    if msg.video: file_id = msg.video.file_id
    elif msg.document: file_id = msg.document.file_id
    elif msg.photo: file_id = msg.photo[-1].file_id
    elif msg.audio: file_id = msg.audio.file_id
    elif msg.voice: file_id = msg.voice.file_id
    elif msg.animation: file_id = msg.animation.file_id
    elif msg.sticker: file_id = msg.sticker.file_id
    if file_id: text += f"\n📄 Fɪʟᴇ ID: `{file_id}`"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

async def get_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = update.message.reply_to_message
    if not msg or not msg.forward_origin: await update.message.reply_text("Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ FORWARDED ᴍᴇssᴀɢᴇ."); return
    origin = msg.forward_origin
    text = f"📢 Oʀɪɢɪɴᴀʟ Cʜᴀɴɴᴇʟ ID: `{origin.chat.id}`"
    file_id = None
    if msg.video: file_id = msg.video.file_id
    elif msg.document: file_id = msg.document.file_id
    elif msg.photo: file_id = msg.photo[-1].file_id
    # आप और भी फाइल टाइप यहाँ जोड़ सकते हैं
    if file_id: text += f"\n📄 Fɪʟᴇ ID: `{file_id}`"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

# ... (बाकी के एडमिन कमांड्स जैसे stats, broadcast, ban वैसे ही रहेंगे) ...

# --- मुख्य फंक्शन ---
def main():
    if not TOKEN: logger.critical("TOKEN not set!"); return
    application = Application.builder().token(TOKEN).build()
    
    # --- सभी हैंडलर्स को यहाँ सीधे रजिस्टर करें ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", id_handler))
    application.add_handler(CommandHandler("get", get_handler))
    # ... (बाकी के एडमिन हैंडलर)
    application.add_handler(CallbackQueryHandler(button_handler))
    
    keep_alive()
    logger.info("Bot is ready and polling!")
    application.run_polling()

if __name__ == '__main__':
    main()
