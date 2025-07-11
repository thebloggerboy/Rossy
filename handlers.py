# handlers.py (Phase 2 - Upgraded)
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

from config import ADMIN_IDS, FORCE_SUB_CHANNELS, FILE_DATA, DELETE_DELAY
from database import db, add_user, ban_user, unban_user, get_all_user_ids

logger = logging.getLogger(__name__)

# --- ... (is_user_member, send_force_subscribe_message, send_file, auto_delete_messages) ---
# --- ये सभी हेल्पर फंक्शन्स पिछले कोड जैसे ही रहेंगे ---
# --- (मैं उन्हें यहाँ संक्षिप्तता के लिए नहीं डाल रहा हूँ, लेकिन वे आपके कोड में होने चाहिए) ---

# --- कमांड और बटन हैंडलर्स ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (यह फंक्शन वैसा ही रहेगा) ...

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (यह फंक्शन वैसा ही रहेगा) ...

# --- एडमिन कमांड्स ---
async def id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (यह फंक्शन वैसा ही रहेगा) ...

async def get_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (यह फंक्शन वैसा ही रहेगा) ...

# --- यहाँ से नए एडमिन कमांड्स शुरू होते हैं ---

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """बॉट के आँकड़े भेजता है।"""
    if update.effective_user.id not in ADMIN_IDS: return

    total_users = len(db["users"])
    banned_count = len(db["banned_users"])
    
    text = (
        f"📊 **Bot Stats** 📊\n\n"
        f"👤 Total Users: {total_users}\n"
        f"🚫 Banned Users: {banned_count}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """सभी यूज़र्स को मैसेज ब्रॉडकास्ट करता है।"""
    if update.effective_user.id not in ADMIN_IDS: return
    
    message_to_broadcast = update.message.reply_to_message
    if not message_to_broadcast:
        await update.message.reply_text("Please reply to a message to broadcast it.")
        return
        
    all_users = get_all_user_ids()
    sent_count = 0
    failed_count = 0
    
    await update.message.reply_text(f"Broadcasting started to {len(all_users)} users... Please wait.")
    
    for user_id_str in all_users:
        try:
            await context.bot.copy_message(
                chat_id=int(user_id_str),
                from_chat_id=update.message.chat_id,
                message_id=message_to_broadcast.message_id
            )
            sent_count += 1
            await asyncio.sleep(0.1) # टेलीग्राम को स्पैम से बचाने के लिए
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to send broadcast to {user_id_str}: {e}")
            
    await update.message.reply_text(f"Broadcast finished!\n\n✅ Sent to: {sent_count} users\n❌ Failed for: {failed_count} users")

async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """एक यूजर को बैन करता है।"""
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    
    try:
        user_id_to_ban = int(context.args[0])
        if ban_user(user_id_to_ban):
            await update.message.reply_text(f"User {user_id_to_ban} has been banned.")
        else:
            await update.message.reply_text(f"User {user_id_to_ban} is already banned.")
    except ValueError:
        await update.message.reply_text("Invalid User ID.")

async def unban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """एक यूजर को अनबैन करता है।"""
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
        
    try:
        user_id_to_unban = int(context.args[0])
        if unban_user(user_id_to_unban):
            await update.message.reply_text(f"User {user_id_to_unban} has been unbanned.")
        else:
            await update.message.reply_text(f"User {user_id_to_unban} was not found in the ban list.")
    except ValueError:
        await update.message.reply_text("Invalid User ID.")

# --- सभी हैंडलर्स को रजिस्टर करने के लिए एक फंक्शन ---
def register_handlers(application):
    """सभी कमांड्स और बटनों के हैंडलर्स को रजिस्टर करता है।"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", id_handler))
    application.add_handler(CommandHandler("get", get_handler))
    application.add_handler(CommandHandler("stats", stats_handler))
    application.add_handler(CommandHandler("broadcast", broadcast_handler))
    application.add_handler(CommandHandler("ban", ban_handler))
    application.add_handler(CommandHandler("unban", unban_handler))
    application.add_handler(CallbackQueryHandler(button_handler))
