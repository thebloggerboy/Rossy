# config.py

# 1. आपकी एडमिन ID (एक से ज़्यादा हों तो कॉमा लगाकर डालें)
ADMIN_IDS = [6056915535] 

# 2. आपके मेन चैनल का लिंक (डायरेक्ट /start के लिए)
MAIN_CHANNEL_LINK = "https://t.me/+ngy1Guv8koBiODM1" 

# 3. लॉग चैनल की ID (नए यूजर्स की जानकारी के लिए, वैकल्पिक)
LOG_CHANNEL_ID = -1002365365973 # अगर नहीं है तो 0 कर दें

# 4. फोर्स सब्सक्राइब के लिए चैनल
FORCE_SUB_CHANNELS = [
    {"chat_id": -1002599545967, "name": "Jᴏɪɴ 1", "invite_link": "https://t.me/+p2ErvvDmitZmYzdl"},
    {"chat_id": -1002391821078, "name": "Jᴏɪɴ 2", "invite_link": "https://t.me/+T4LO1ePja_I5NWQ1"}
]

# 5. आपकी सभी फाइलें, पैक, और सीरीज
# file_type: 'video', 'document', 'photo', 'series'
FILE_DATA = {
    "Episode1": {
        "type": "video", 
        "id": "BAACAgUAAxkBAANEaHW7EfEoyLY34V2h46PXRbDA_9oAAroTAALdcVBXIIL-uAu5A0Q2BA", 
        "caption": "<b>Eᴘɪsᴏᴅᴇ 1</b>\n\n Qᴜᴀʟɪᴛʏ: 1080p",
        "buttons": [
            [{"text": "🎬 Wᴀᴛᴄʜ Pᴀʀᴛ 2", "url": "https://t.me/YourRossyBot?start=Episode2"}]
        ]
    },
    "Episode2": {
        "type": "video", 
        "id": "BAACAgUAAxkBAAMKaGpLylL2eBYyfy9tX8wqGoVV12gAAv0VAALdcVBXBhEhvub79Q02BA", 
        "caption": "<b>Episode 2</b>",
        "buttons": [
            [{"text": "Watch Part 3", "url": "https://t.me/YourRossyBot?start=Episode3"}]
        ] # <-- यह वाला ']' ब्रैकेट लगाना है
    },
    "UpdatePhoto": {
        "type": "photo",
        "id": "YOUR_PHOTO_FILE_ID",
        "caption": "🔥 Nᴇᴡ Uᴘᴅᴀᴛᴇ!",
        "buttons": [
            [{"text": "Cʜᴇᴄᴋ Nᴏᴡ", "url": "https://t.me/YourMainChannel"}]
        ]
    },
    "SomeApp": {
        "type": "document",
        "id": "YOUR_APK_FILE_ID",
        "caption": "Lᴀᴛᴇsᴛ Aᴘᴘ Vᴇʀsɪᴏɴ"
    },
    "innobhabhiep2": {
        "type": "series",
        "episodes": ["BAACAgUAAxkBAANEaHW7EfEoyLY34V2h46PXRbDA_9oAAroTAALdcVBXIIL-uAu5A0Q2BA", "BAACAgUAAxkBAAOOaHtXCViOAAEOlcoWmydfao-TpaoNAAL9FQAC3XFQV6RvKzee8O2ANgQ"] 
    }
}

# 6. डिलीट का समय (सेकंड में)
DELETE_DELAY = 900  # 15 मिनट
