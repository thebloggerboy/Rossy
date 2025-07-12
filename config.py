# config.py (Corrected and Merged)

# 1. आपकी एडमिन ID
ADMIN_IDS = [6056915535]

# 2. आपके लॉग चैनल की ID
LOG_CHANNEL_ID = -1002365365973

# 3. आपके मेन चैनल का लिंक (डायरेक्ट /start के लिए)
MAIN_CHANNEL_LINK = "https://t.me/+ngy1Guv8koBiODM1" 

# 4. फोर्स सब्सक्राइब के लिए चैनल
FORCE_SUB_CHANNELS = [
    {"chat_id": -1002599545967, "name": "Join 1", "invite_link": "https://t.me/+p2ErvvDmitZmYzdl"},
    {"chat_id": -1002391821078, "name": "Join 2", "invite_link": "https://t.me/+T4LO1ePja_I5NWQ1"}
]

# 5. आपकी सभी फाइलें, पैक, और सीरीज
# file_type: 'video', 'document', 'series'
FILE_DATA = {
    # --- सिंगल फाइल्स ---
    "Episode1": {
        "type": "video", 
        "id": "BAACAgUAAxkBAAMXaGpSqvDgq-0fAszJ6iItqfYpI7wAAroTAALdcVBXt_ZT-2d9Lno2BA", 
        "caption": "<b>Episode 1</b>",
        "buttons": [
            # पहली पंक्ति में 2 बटन
            [
                {"text": "🎬 Part 2", "url": "https://t.me/YourBotName?start=Episode2"},
                {"text": "👍 Like", "callback_data": "like_ep1"}
            ],
            # दूसरी पंक्ति में 1 बटन
            [
                {"text": "Join Our Channel", "url": "https://t.me/YourMainChannel"}
            ]
        ]
    },
    "Episode2": {
        "type": "video", 
        "id": "YOUR_EPISODE_2_ID_HERE", 
        "caption": "<b>Episode 2</b>"
    },
    "some_apk": {
        "type": "document", 
        "id": "YOUR_APK_FILE_ID_HERE",
        "caption": "Here is the latest version of the App."
    },

    # --- सीरीज/पैक का उदाहरण ---
    "Season1Pack": {
        "type": "series",
        "episodes": ["Episode1", "Episode2"] 
    }
}

# 6. डिलीट का समय (सेकंड में)
DELETE_DELAY = 900  # 15 मिनट
