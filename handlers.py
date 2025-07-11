# handlers.py (Final and Complete)
import logging, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

from config import ADMIN_IDS, FORCE_SUB_CHANNELS, FILE_DATA, DELETE_DELAY
from database import db, add_user, ban_user, unban_user, get_all_user_ids

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

async def send_file(user_id: int, file_key: str, context: ContextTypes.DEFAULT_TYPE):
    if file_key not in FILE_DATA:
        await context.bot.send_message(chat_id=user_id, text="Sorry, file key not found.")
        return
    file_info = FILE_DATA[file_key]
    await context.bot.send_video(chat_id=user_id, video=file_info["id"], caption=file_info["caption"], parse_mode=ParseMode.HTML)
    logger.info(f"Sent file '{file_key}' to user {user_id}")

# --- कमांड और बटन हैंडलर्स ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)
    if user.id in db["banned_users"]:
        await update.message.reply_text("You are banned from using this bot."); return
    if context.args:
        file_key = context.args[0]
        context.user_data['file_key'] = file_key
        if await is_user_member(user.id, context): await send_file(user.id, file_key, context)
        else: await send_force_subscribe_message(update, context)
    else:
        await update.message.reply_text(f"Welcome, {user.first_name}! Please use a link from our main channel.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user_id = query.from_user.id; data = query.data
    if data.startswith("check_"):
        file_key = data.split("_", 1)[1]
        if await is_user_member(user_id, context):
            await query.message.delete(); await send_file(user_id, file_key, context)
        else:
            await query.answer("You haven't joined all channels yet. Please join and try again.", show_alert=True)

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    total = len(db["users"]); banned = len(db["banned_users"])
    await update.message.reply_text(f"📊 Stats: {total} total users, {banned} banned.")

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = update.message.reply_to_message
    if not msg: await update.message.reply_text("Please reply to a message to broadcast."); return
    users = get_all_user_ids(); sent, failed = 0, 0
    await update.message.reply_text(f"Starting broadcast to {len(users)} users...")
    for user in users:
        try:
            await msg.copy(chat_id=int(user)); sent += 1; await asyncio.sleep(0.1)
        except Exception: failed += 1
    await update.message.reply_text(f"Broadcast finished. Sent: {sent}, Failed: {failed}.")

async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, ban=True):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: await update.message.reply_text(f"Usage: /{'ban' if ban else 'unban'} <user_id>"); return
    try:
        user_id = int(context.args[0])
        if ban:
            if ban_user(user_id): await update.message.reply_text(f"User {user_id} banned.")
            else: await update.message.reply_text("User already banned.")
        else:
            if unban_user(user_id): await update.message.reply_text(f"User {user_id} unbanned.")
            else: await update.message.reply_text("User not in ban list.")
    except ValueError: await update.message.reply_text("Invalid User ID.")

def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_handler))
    application.add_handler(CommandHandler("broadcast", broadcast_handler))
    application.add_handler(CommandHandler("ban", ban_handler))
    application.add_handler(CommandHandler("unban", lambda u, c: ban_handler(u, c, ban=False)))
    application.add_handler(CallbackQueryHandler(button_handler))
