# config.py

# 1. आपकी एडमिन ID
ADMIN_IDS = [6056915535]

# 2. फोर्स सब्सक्राइब के लिए चैनल
# चैनल ID निकालने के लिए, चैनल से कोई मैसेज @userinfobot को फॉरवर्ड करें।
FORCE_SUB_CHANNELS = [
    {"chat_id": -1002599545967, "name": "Join 1", "invite_link": "https://t.me/+p2ErvvDmitZmYzdl"},
    {"chat_id": -1002391821078, "name": "Join 2", "invite_link": "https://t.me/+T4LO1ePja_I5NWQ1"}
]

# 3. आपकी फाइलें और सीरीज
# file_type: 'video', 'document', 'series'
FILE_DATA = {
    # सिंगल फाइल्स
    "Episode1": {"type": "video", "id": "BAACAgUAAxkBAAMXaGpSqvDgq-0fAszJ6iItqfYpI7wAAroTAALdcVBXt_ZT-2d9Lno2BA", "caption": "<b>Episode 1</b>"},
    "Episode2": {"type": "video", "id": "BAACAgUAAxkBAAMKaGpLylL2eBYyfy9tX8wqGoVV12gAAv0VAALdcVBXBhEhvub79Q02BA", "caption": "<b>Episode 2</b>"},
    "some_apk": {"type": "document", "id": "YOUR_APK_FILE_ID", "caption": "Here is the APK file."},

    # सीरीज पैक
    "Season1Pack": {
        "type": "series",
        "episodes": ["Episode1", "Episode2"] # यहाँ उन सभी keys को डालें जिन्हें भेजना है
    }
}

# 4. डिलीट का समय (सेकंड में)
DELETE_DELAY = 900  # 15 मिनट