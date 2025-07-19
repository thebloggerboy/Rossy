# handlers.py
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

from config import ADMIN_IDS, FORCE_SUB_CHANNELS, FILE_DATA, DELETE_DELAY, MAIN_CHANNEL_LINK, LOG_CHANNEL_ID
from database import db, add_user, ban_user, unban_user, get_all_user_ids, save_db

logger = logging.getLogger(__name__)

# --- फैंसी टेक्स्ट ---
WELCOME_TEXT = "Wᴇʟᴄᴏᴍᴇ, {user_name}! Pʟᴇᴀsᴇ ᴜsᴇ ᴀ ʟɪɴᴋ ғʀᴏᴍ ᴏᴜʀ ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ."
JOIN_CHANNEL_TEXT = "Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴀʟʟ ʀᴇǫᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟs ᴛᴏ ɢᴇᴛ ᴛʜᴇ ғɪʟᴇ."
NOT_JOINED_ALERT = "Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ ᴀʟʟ ʀᴇǫᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟs ʏᴇᴛ. Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ."
BANNED_TEXT = "Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ."
FILE_NOT_FOUND_TEXT = "Sᴏʀʀʏ, ғɪʟᴇ ᴋᴇʏ ɴᴏᴛ ғᴏᴜɴᴅ."
DELETE_WARNING_TEXT = "⚠️ Tʜɪs ᴍᴇᴅɪᴀ ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ᴀғᴛᴇʀ 15 ᴍɪɴᴜᴛᴇs.\nPʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇᴅɪᴀ ᴍᴇssᴀɢᴇ\nᴛᴏ ʏᴏᴜʀ ᴘᴇʀsᴏɴᴀʟ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs\nᴛᴏ ᴀᴠᴏɪᴅ ʟᴏsɪɴɢ ᴛʜᴇᴍ!"
RESEND_PROMPT_TEXT = "<i>Yᴏᴜʀ Fɪʟᴇ ({file_key}) ᴡᴀs Dᴇʟᴇᴛᴇᴅ 🗑\nIғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɢᴇᴛ ɪᴛ ᴀɢᴀɪɴ, ᴄʟɪᴄᴋ ᴛʜᴇ 'Wᴀᴛᴄʜ Aɢᴀɪɴ' ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ.</i>"
FINAL_DELETE_TEXT = "Tʜᴇ 'Wᴀᴛᴄʜ Aɢᴀɪɴ' ʙᴜᴛᴛᴏɴ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜsᴇᴅ ᴏɴᴄᴇ.\nIғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴡᴀᴛᴄʜ ᴛʜᴇ ᴠɪᴅᴇᴏ ᴀɢᴀɪɴ, ʏᴏᴜ ᴄᴀɴ ɢᴇᴛ ɪᴛ ғʀᴏᴍ ᴏᴜʀ ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ."

# handlers.py के अंदर

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    # एडमिन को हमेशा एक्सेस दें
    if user_id in ADMIN_IDS:
        logger.info(f"User {user_id} is an admin. Bypassing force subscribe.")
        return True

    # अगर कोई चैनल सेट नहीं है, तो सबको एक्सेस दें
    if not FORCE_SUB_CHANNELS:
        logger.info("No force subscribe channels set. Granting access.")
        return True

    # हर चैनल को एक-एक करके चेक करें
    for channel in FORCE_SUB_CHANNELS:
        chat_id = channel["chat_id"]
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            # अगर यूजर 'left' या 'kicked' है, तो एक्सेस न दें
            if member.status in ['left', 'kicked']:
                logger.info(f"User {user_id} is not a member of channel {chat_id}. Status: {member.status}")
                return False
        except BadRequest as e:
            # अगर बॉट एडमिन नहीं है या चैनल मौजूद नहीं है
            logger.error(f"Could not check membership for user {user_id} in channel {chat_id}. Error: {e}")
            # हम इसे एक फेलियर मानते हैं और एक्सेस नहीं देते
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while checking membership for user {user_id} in {chat_id}: {e}")
            return False
    
    # अगर यूजर सभी लूप्स को पास कर लेता है, तो वह मेंबर है
    logger.info(f"User {user_id} is a member of all required channels.")
    return True
    
async def send_force_subscribe_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_key = context.user_data.get('file_key')
    if not file_key: return
    join_buttons = [InlineKeyboardButton(ch["name"], url=ch["invite_link"]) for ch in FORCE_SUB_CHANNELS]
    keyboard = [join_buttons, [InlineKeyboardButton("✅ Jᴏɪɴᴇᴅ", callback_data=f"check_{file_key}")]]
    await update.message.reply_text(JOIN_CHANNEL_TEXT, reply_markup=InlineKeyboardMarkup(keyboard))

async def auto_delete_messages(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id, message_ids, file_key, caption, is_resent = job.chat_id, job.data['message_ids'], job.data['file_key'], job.data['caption'], job.data.get('is_resent', False)
    try:
        for msg_id in message_ids:
            try: await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except BadRequest: pass
        if not is_resent:
            keyboard = [[InlineKeyboardButton("▶️ Wᴀᴛᴄʜ Aɢᴀɪɴ", callback_data=f"resend_{file_key}"), InlineKeyboardButton("❌ Dᴇʟᴇᴛᴇ", callback_data="close_msg")]]
            text = f"{caption}\n\n{RESEND_PROMPT_TEXT.format(file_key=file_key)}"
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [[InlineKeyboardButton("Cʜᴇᴄᴋ Mᴀɪɴ Cʜᴀɴɴᴇʟ", url=MAIN_CHANNEL_LINK)]]
            await context.bot.send_message(chat_id=chat_id, text=FINAL_DELETE_TEXT, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e: logger.error(f"Error in auto_delete_messages: {e}")

# main.py के अंदर

async def send_file(user_id: int, file_key: str, context: ContextTypes.DEFAULT_TYPE, is_resend: bool = False, is_part_of_series: bool = False):
    if file_key not in FILE_DATA:
        if not is_part_of_series: await context.bot.send_message(chat_id=user_id, text=FILE_NOT_FOUND_TEXT)
        return
        
    file_info = FILE_DATA[file_key]
    file_type = file_info.get("type", "video")

    # --- सीरीज भेजने का लॉजिक ---
    if file_type == 'series':
        # यह मैसेज सिर्फ एक बार भेजा जाएगा, जब सीरीज शुरू हो
        if not is_part_of_series:
            episodes_to_send = file_info.get("episodes", [])
            await context.bot.send_message(chat_id=user_id, text=f"Sᴇɴᴅɪɴɢ ᴀʟʟ {len(episodes_to_send)} ᴇᴘɪsᴏᴅᴇs. Pʟᴇᴀsᴇ ᴡᴀɪᴛ...")
            for episode_key in episodes_to_send:
                await asyncio.sleep(2)
                # is_part_of_series=True भेजें ताकि बॉट को पता चले कि यह एक सीरीज का हिस्सा है
                await send_file(user_id, episode_key, context, is_resend=False, is_part_of_series=True)
            await context.bot.send_message(chat_id=user_id, text="✅ Aʟʟ ᴇᴘɪsᴏᴅᴇs ʜᴀᴠᴇ ʙᴇᴇɴ sᴇɴᴛ!")
        return

    # --- सिंगल फाइल भेजने का लॉजिक (अब यह सीरीज के लिए भी काम करेगा) ---
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
        # ... (वीडियो, फोटो, डॉक्यूमेंट भेजने का कोड वैसा ही रहेगा) ...
        if file_type == 'video':
            message_to_delete = await context.bot.send_video(chat_id=user_id, video=file_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        
        # ऑटो-डिलीट का लॉजिक
        if message_to_delete:
            warning_message = await context.bot.send_message(chat_id=user_id, text=DELETE_WARNING_TEXT)
            context.job_queue.run_once(
                auto_delete_messages, 
                DELETE_DELAY, 
                data={'message_ids': [message_to_delete.message_id, warning_message.message_id], 'file_key': file_key, 'caption': caption, 'is_resent': is_resend}, 
                chat_id=user_id
            )
            
    except Exception as e:
        logger.error(f"Error sending file {file_key}: {e}")
# --- कमांड और बटन हैंडलर्स ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new_user = add_user(user.id)
    
    if is_new_user and LOG_CHANNEL_ID:
        try:
            bot_username = (await context.bot.get_me()).username
            user_link = f"[{user.first_name}](tg://user?id={user.id})"
            text = f"✅ Nᴇᴡ Usᴇʀ\nBᴏᴛ: @{bot_username}\nNᴀᴍᴇ: {user_link}\nID: `{user.id}`"
            if user.username: text += f"\nUsᴇʀɴᴀᴍᴇ: @{user.username}"
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=text, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e: logger.error(f"Failed to send log: {e}")
        
    if user.id in db["banned_users"]: await update.message.reply_text(BANNED_TEXT); return
    if context.args:
        file_key = context.args[0]; context.user_data['file_key'] = file_key
        if await is_user_member(user.id, context): await send_file(user.id, file_key, context)
        else: await send_force_subscribe_message(update, context)
    else:
        keyboard = [[InlineKeyboardButton("Mᴀɪɴ Cʜᴀɴɴᴇʟ", url=MAIN_CHANNEL_LINK)]]
        await update.message.reply_text(WELCOME_TEXT.format(user_name=user.first_name), reply_markup=InlineKeyboardMarkup(keyboard))

# handlers.py के अंदर

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    # --- चेक बटन का लॉजिक ---
    if data.startswith("check_"):
        file_key = data.split("_", 1)[1]
        
        # पहले मेंबरशिप चेक करें
        if await is_user_member(user_id, context):
            # अगर मेंबर है, तो सामान्य जवाब दें और काम करें
            await query.answer()
            await query.message.delete()
            await send_file(user_id, file_key, context)
        else:
            # अगर मेंबर नहीं है, तो सिर्फ पॉप-अप अलर्ट वाला जवाब दें
            await query.answer(text=NOT_JOINED_ALERT, show_alert=True)
            
    # --- री-सेंड बटन का लॉजिक ---
    elif data.startswith("resend_"):
        await query.answer()
        file_key = data.split("_", 1)[1]
        await query.message.delete()
        await send_file(user_id, file_key, context, is_resend=True)
        
    # --- क्लोज बटन का लॉजिक ---
    elif data == "close_msg":
        # पहले मैसेज डिलीट करें, फिर जवाब दें
        await query.message.delete()
        await query.answer(text="Mᴇssᴀɢᴇ Dᴇʟᴇᴛᴇᴅ.", show_alert=False)
    
    # --- अगर कोई और बटन है तो ---
    else:
        # एक खाली जवाब भेजें ताकि लोडिंग बंद हो जाए
        await query.answer()
# --- एडमिन कमांड्स ---
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
    if file_id: text += f"\n📄 Fɪʟᴇ ID: `{file_id}`"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    total = len(db["users"]); banned = len(db["banned_users"])
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
    await update.message.reply_text(f"Bʀᴏᴀᴅᴄᴀsᴛ ғɪɴɪsʜᴇᴅ!\n\n✅ Sᴇɴᴛ ᴛᴏ: {sent} ᴜsᴇʀs\n❌ Fᴀɪʟᴇᴅ ғᴏʀ: {failed}")

async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, ban=True):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: await update.message.reply_text(f"Usᴀɢᴇ: /{'ban' if ban else 'unban'} <user_id>"); return
    try:
        user_id, action = int(context.args[0]), "banned" if ban else "unbanned"
        success = ban_user(user_id) if ban else unban_user(user_id)
        if success: await update.message.reply_text(f"Usᴇʀ {user_id} ʜᴀs ʙᴇᴇɴ {action}.")
        else: await update.message.reply_text(f"Usᴇʀ {user_id} {'is already banned' if ban else 'was not in ban list'}.")
    except ValueError: await update.message.reply_text("Iɴᴠᴀʟɪᴅ Usᴇʀ ID.")

# --- सभी हैंडलर्स को रजिस्टर करने के लिए एक फंक्शन ---
def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_handler))
    application.add_handler(CommandHandler("broadcast", broadcast_handler))
    application.add_handler(CommandHandler("ban", ban_handler))
    application.add_handler(CommandHandler("unban", lambda u, c: ban_handler(u, c, ban=False)))
    application.add_handler(CommandHandler("id", id_handler))
    application.add_handler(CommandHandler("get", get_handler))
    application.add_handler(CallbackQueryHandler(button_handler))
