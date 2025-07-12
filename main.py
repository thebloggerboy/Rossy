# main.py (Final All-in-One Version with All Fixes)

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

async def send_file(user_id: int, file_key: str, context: ContextTypes.DEFAULT_TYPE):
    if file_key not in FILE_DATA: await context.bot.send_message(chat_id=user_id, text=FILE_NOT_FOUND_TEXT); return
    file_info = FILE_DATA[file_key]; caption = file_info.get("caption", "")
    video_message = await context.bot.send_video(chat_id=user_id, video=file_info["id"], caption=caption, parse_mode=ParseMode.HTML)
    warning_message = await context.bot.send_message(chat_id=user_id, text=DELETE_WARNING_TEXT)
    context.job_queue.run_once(auto_delete_messages, DELETE_DELAY, data={'message_ids': [video_message.message_id, warning_message.message_id], 'file_key': file_key, 'caption': caption}, chat_id=user_id)

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
    if data.startswith("check_"):
        await query.answer()
        file_key = data.split("_", 1)[1]
        if await is_user_member(user_id, context):
            await query.message.delete(); await send_file(user_id, file_key, context)
        else: await query.answer(NOT_JOINED_ALERT, show_alert=True)
    elif data.startswith("resend_"):
        await query.answer(); file_key = data.split("_", 1)[1]
        await query.message.delete(); await send_file(user_id, file_key, context)
    elif data == "close_msg": await query.message.delete()

# --- एडमिन कमांड्स ---
async def id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = update.message.reply_to_message
    if not msg: await update.message.reply_text("Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ."); return
    text = f"👤 Usᴇʀ ID: `{msg.from_user.id}`\n💬 Cʜᴀᴛ ID: `{msg.chat.id}`"
    if msg.video: text += f"\n📄 Fɪʟᴇ ID: `{msg.video.file_id}`"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

async def get_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = update.message.reply_to_message
    if not msg or not msg.forward_origin: await update.message.reply_text("Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ FORWARDED ᴍᴇssᴀɢᴇ."); return
    origin = msg.forward_origin
    text = f"📢 Oʀɪɢɪɴᴀʟ Cʜᴀɴɴᴇʟ ID: `{origin.chat.id}`"
    if msg.video: text += f"\n📄 Fɪʟᴇ ID: `{msg.video.file_id}`"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    total, banned = len(db["users"]), len(db["banned_users"])
    await update.message.reply_text(f"📊 Bᴏᴛ Sᴛᴀᴛs 📊\n\n👤 Tᴏᴛᴀʟ Usᴇʀs: {total}\n🚫 Bᴀɴɴᴇᴅ Usᴇʀs: {banned}")

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = update.message.reply_to_message
    if not msg: await update.message.reply_text("Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ."); return
    users, sent, failed = get_all_user_ids(), 0, 0
    await update.message.reply_text(f"Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ sᴛᴀʀᴛᴇᴅ ᴛᴏ {len(users)} ᴜsᴇʀs...")
    reply_markup = msg.reply_markup
    for user_id in users:
        try:
            await context.bot.copy_message(chat_id=int(user_id), from_chat_id=msg.chat_id, message_id=msg.message_id, reply_markup=reply_markup)
            sent += 1; await asyncio.sleep(0.1)
        except Exception as e:
            failed += 1; logger.error(f"Bʀᴏᴀᴅᴄᴀsᴛ ғᴀɪʟᴇᴅ ғᴏʀ {user_id}: {e}")
            if "bot was blocked" in str(e): db["users"].pop(str(user_id), None)
    save_db(db)
    await update.message.reply_text(f"Bʀᴏᴀᴅᴄᴀsᴛ ғɪɴɪsʜᴇᴅ!\n\n✅ Sᴇɴᴛ ᴛᴏ: {sent}\n❌ Fᴀɪʟᴇᴅ ғᴏʀ: {failed}")

async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, ban=True):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: await update.message.reply_text(f"Usᴀɢᴇ: /{'ban' if ban else 'unban'} <user_id>"); return
    try:
        user_id, action = int(context.args[0]), "banned" if ban else "unbanned"
        success = ban_user(user_id) if ban else unban_user(user_id)
        if success: await update.message.reply_text(f"Usᴇʀ {user_id} ʜᴀs ʙᴇᴇɴ {action}.")
        else: await update.message.reply_text(f"Usᴇʀ {user_id} {'is already banned' if ban else 'was not in ban list'}.")
    except ValueError: await update.message.reply_text("Iɴᴠᴀʟɪᴅ Usᴇʀ ID.")

# --- मुख्य फंक्शन ---
def main():
    if not TOKEN: logger.critical("TOKEN not set!"); return
    application = Application.builder().token(TOKEN).build()
    
    # --- सभी हैंडलर्स को यहाँ सीधे रजिस्टर करें ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_handler))
    application.add_handler(CommandHandler("broadcast", broadcast_handler))
    application.add_handler(CommandHandler("ban", ban_handler))
    application.add_handler(CommandHandler("unban", lambda u, c: ban_handler(u, c, ban=False)))
    application.add_handler(CommandHandler("id", id_handler))
    application.add_handler(CommandHandler("get", get_handler))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    keep_alive()
    logger.info("Bot is ready and polling!")
    application.run_polling()

if __name__ == '__main__':
    main()
