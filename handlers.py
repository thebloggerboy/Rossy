# handlers.py (Final with All New Features)

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

from config import ADMIN_IDS, FORCE_SUB_CHANNELS, FILE_DATA, DELETE_DELAY, MAIN_CHANNEL_LINK
from database import db, add_user, ban_user, unban_user, get_all_user_ids, save_db

logger = logging.getLogger(__name__)

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
    keyboard = [join_buttons, [InlineKeyboardButton("✅ Joined", callback_data=f"check_{file_key}")]]
    await update.message.reply_text("Please join all required channels to get the file.", reply_markup=InlineKeyboardMarkup(keyboard))

async def auto_delete_messages(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id, message_ids, file_key, caption = job.chat_id, job.data['message_ids'], job.data['file_key'], job.data['caption']
    try:
        for msg_id in message_ids:
            try: await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except BadRequest: pass
        
        keyboard = [[
            InlineKeyboardButton("▶️ Watch Again", callback_data=f"resend_{file_key}"),
            InlineKeyboardButton("❌ Delete", callback_data="close_msg")
        ]]
        
        # ओरिजिनल कैप्शन के साथ मैसेज भेजें
        text = f"{caption}\n\n<i>This file has been deleted. Click 'Watch Again' to get it back.</i>"
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Error in auto_delete_messages: {e}")

async def send_file(user_id: int, file_key: str, context: ContextTypes.DEFAULT_TYPE):
    if file_key not in FILE_DATA:
        await context.bot.send_message(chat_id=user_id, text="Sorry, file key not found.")
        return
        
    file_info = FILE_DATA[file_key]
    caption = file_info.get("caption", "")
    
    video_message = await context.bot.send_video(chat_id=user_id, video=file_info["id"], caption=caption, parse_mode=ParseMode.HTML)
    warning_text = "⚠️ Your file will be deleted within 15 Minutes due to Copyright issues. Please download or forward it."
    warning_message = await context.bot.send_message(chat_id=user_id, text=warning_text)
    
    context.job_queue.run_once(
        auto_delete_messages, 
        DELETE_DELAY, 
        data={'message_ids': [video_message.message_id, warning_message.message_id], 'file_key': file_key, 'caption': caption}, 
        chat_id=user_id
    )

# --- कमांड और बटन हैंडलर्स ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)
    if user.id in db["banned_users"]: return

    if context.args:
        file_key = context.args[0]
        context.user_data['file_key'] = file_key
        if await is_user_member(user.id, context): await send_file(user.id, file_key, context)
        else: await send_force_subscribe_message(update, context)
    else:
        keyboard = [[InlineKeyboardButton("Go to Main Channel", url=MAIN_CHANNEL_LINK)]]
        await update.message.reply_text(
            f"Welcome, {user.first_name}! Please use a link from our main channel.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

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
            
    elif data.startswith("resend_"):
        await query.answer()
        file_key = data.split("_", 1)[1]
        await query.message.delete()
        await send_file(user_id, file_key, context)
        
    elif data == "close_msg" or data == "delete_broadcast":
        await query.message.delete()
        await query.answer("Message deleted.")

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = update.message.reply_to_message
    if not msg: await update.message.reply_text("Please reply to a message to broadcast."); return
    
    users = get_all_user_ids()
    sent, failed = 0, 0
    await update.message.reply_text(f"Broadcasting to {len(users)} users...")

    # ब्रॉडकास्ट मैसेज के नीचे डिलीट बटन जोड़ें
    original_markup = msg.reply_markup
    new_buttons = [InlineKeyboardButton("❌ Delete This Message", callback_data="delete_broadcast")]
    
    if original_markup:
        new_keyboard = original_markup.inline_keyboard + [new_buttons]
    else:
        new_keyboard = [new_buttons]
        
    new_reply_markup = InlineKeyboardMarkup(new_keyboard)
    
    for user_id in users:
        try:
            await context.bot.copy_message(
                chat_id=int(user_id),
                from_chat_id=msg.chat_id,
                message_id=msg.message_id,
                reply_markup=new_reply_markup # नया कीबोर्ड भेजें
            )
            sent += 1; await asyncio.sleep(0.1)
        except Exception as e:
            failed += 1; logger.error(f"Broadcast failed for {user_id}: {e}")
            if "bot was blocked by the user" in str(e):
                db["users"].pop(str(user_id), None); save_db(db)

    await update.message.reply_text(f"Broadcast finished! Sent: {sent}, Failed: {failed}.")

# ... (बाकी के सभी एडमिन कमांड्स जैसे id, get, stats, ban, unban वैसे ही रहेंगे) ...

def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    # ... (बाकी के सभी हैंडलर) ...
