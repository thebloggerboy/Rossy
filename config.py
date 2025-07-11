# config.py (Corrected)

# 1. आपकी एडमिन ID
ADMIN_IDS = [6056915535]

# 2. फोर्स सब्सक्राइब के लिए चैनल
FORCE_SUB_CHANNELS = [
    {"chat_id": -1002599545967, "name": "Join 1", "invite_link": "https://t.me/+p2ErvvDmitZmYzdl"},
    {"chat_id": -1002391821078, "name": "Join 2", "invite_link": "https://t.me/+T4LO1ePja_I5NWQ1"}
]

# 3. आपकी फाइलें
FILE_DATA = {
    "Episode1": {
        "type": "video", 
        "id": "YOUR_NEW_EPISODE_1_ID_HERE", # <-- यहाँ hanny bot से निकली नई ID डालें
        "caption": "<b>Episode 1</b>"
    },
    "Episode2": {
        "type": "video", 
        "id": "YOUR_NEW_EPISODE_2_ID_HERE",
        "caption": "<b>Episode 2</b>"
    }
}

# 4. डिलीट का समय (सेकंड में)
DELETE_DELAY = 900  # 15 मिनट
