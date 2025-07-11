# config.py (Correct Template)

# 1. आपकी एडमिन ID
ADMIN_IDS = [6056915535]

# 2. फोर्स सब्सक्राइब के लिए चैनल
FORCE_SUB_CHANNELS = [
    {"chat_id": -1002599545967, "name": "Join 1", "invite_link": "https://t.me/+p2ErvvDmitZmYzdl"},
    {"chat_id": -1002391821078, "name": "Join 2", "invite_link": "https://t.me/+T4LO1ePja_I5NWQ1"}
]

# 3. आपकी फाइलें और सीरीज
FILE_DATA = {

    "Episode1": {
        "type": "video", 
        "id": "BAACAgUAAxkBAAMXaGpSqvDgq-0fAszJ6iItqfYpI7wAAroTAALdcVBXt_ZT-2d9Lno2BA", 
        "caption": "<b>Episode 1</b>"
    }, # <-- हर ब्लॉक के बाद यह कॉमा ज़रूरी है

    "Episode2": {
        "type": "video", 
        "id": "BAACAgUAAxkBAAMKaGpLylL2eBYyfy9tX8wqGoVV12gAAv0VAALdcVBXBhEhvub79Q02BA", 
        "caption": "<b>Episode 2</b>"
    } # <-- आखिरी ब्लॉक के बाद कॉमा की ज़रूरत नहीं है
    
    # आप और भी फाइलें यहाँ जोड़ सकते हैं
}

# 4. डिलीट का समय (सेकंड में)
DELETE_DELAY = 900  # 15 मिनट
