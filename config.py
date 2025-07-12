# config.py (Final with Series/Pack Example)
# config.py के अंदर
LOG_CHANNEL_ID = -1002365365973  # <-- यहाँ अपने प्राइवेट लॉग चैनल की ID डालें
# 1. आपकी एडमिन ID
ADMIN_IDS = [6056915535]

# 2. आपके मेन चैनल का लिंक (डायरेक्ट /start के लिए)
MAIN_CHANNEL_LINK = "https://t.me/+ngy1Guv8koBiODM1" 

# 3. फोर्स सब्सक्राइब के लिए चैनल
FORCE_SUB_CHANNELS = [
    {"chat_id": -1002599545967, "name": "Join 1", "invite_link": "https://t.me/+p2ErvvDmitZmYzdl"},
    {"chat_id": -1002391821078, "name": "Join 2", "invite_link": "https://t.me/+T4LO1ePja_I5NWQ1"}
]

# 4. आपकी फाइलें, पैक, और सीरीज
# file_type: 'video', 'document', 'series'
FILE_DATA = {
    # --- सिंगल फाइल्स ---
    # config.py

FILE_DATA = {
    "Episode1": {
        "type": "video", 
        "id": "...", 
        "caption": "<b>Episode 1</b>",
        "buttons": [
            # पहली पंक्ति में 2 बटन
            [
                {"text": "🎬 Part 2", "url": "https://t.me/YourBot?start=Episode2"},
                {"text": "👍 Like", "callback_data": "like_ep1"}
            ],
            # दूसरी पंक्ति में 1 बटन
            [
                {"text": "Join Our Channel", "url": "https://t.me/YourChannel"}
            ]
        ]
    },
    "Episode2": {
        "type": "video", 
        "id": "...", 
        "caption": "<b>Episode 2</b>"
        # इस एपिसोड के लिए कोई बटन नहीं है, तो यह खाली रहेगा
    }
}
    },
    "some_apk": {
        "type": "document", 
        "id": "YOUR_APK_FILE_ID_HERE", # .apk फाइल की ID यहाँ डालें
        "caption": "Here is the latest version of the App."
    },

    # --- सीरीज/पैक का उदाहरण ---
    "Season1Pack": {
        "type": "series",
        # इस लिस्ट में उन सभी एपिसोड की 'key' डालें जिन्हें आप भेजना चाहते हैं
        "episodes": ["Episode1", "Episode2"] 
        # आप और भी जोड़ सकते हैं, जैसे: ["Episode1", "Episode2", "Episode3", ...]
    }
}

# 5. डिलीट का समय (सेकंड में)
DELETE_DELAY = 900  # 15 मिनट
