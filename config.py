# config.py (Corrected and Updated with Season Packs)

# 1. आपकी एडमिन ID
ADMIN_IDS = [6056915535] 

# 2. आपके मेन चैनल का लिंक
MAIN_CHANNEL_LINK = "https://t.me/+ngy1Guv8koBiODM1" 

# 3. लॉग चैनल की ID
LOG_CHANNEL_ID = -1002365365973

# 4. फोर्स सब्सक्राइब के लिए चैनल
FORCE_SUB_CHANNELS = [
    {"chat_id": -1002599545967, "name": "Jᴏɪɴ 1", "invite_link": "https://t.me/+p2ErvvDmitZmYzdl"},
    {"chat_id": -1002391821078, "name": "Jᴏɪɴ 2", "invite_link": "https://t.me/+T4LO1ePja_I5NWQ1"}
]

# 5. आपकी सभी फाइलें, पैक, और सीरीज
FILE_DATA = {
    # --- पहले सभी एपिसोड्स को अलग-अलग परिभाषित करें ---
    "Episode1": {
        "type": "video", 
        "id": "BAACAgUAAxkBAAMXaGpSqvDgq-0fAszJ6iItqfYpI7wAAroTAALdcVBXt_ZT-2d9Lno2BA", 
        "caption": "<b>Eᴘɪsᴏᴅᴇ 1</b>\nQᴜᴀʟɪᴛʏ: 1080p"
        # इस एपिसोड के साथ कोई बटन नहीं है
    },

    "Episode2": {
        "type": "video", 
        "id": "BAACAgUAAxkBAAMKaGpLylL2eBYyfy9tX8wqGoVV12gAAv0VAALdcVBXBhEhvub79Q02BA", 
        "caption": "<b>Eᴘɪsᴏᴅᴇ 2</b>",
        "buttons": [
            [{"text": "Wᴀᴛᴄʜ Pᴀʀᴛ 3", "url": "https://t.me/YourRossyBot?start=Episode3"}]
        ]
    },

    "Episode3": { # सीजन 2 के लिए
        "type": "video",
        "id": "BAACAgUAAxkBAANEaHW7EfEoyLY34V2h46PXRbDA_9oAAroTAALdcVBXIIL-uAu5A0Q2BA",
        "caption": "<b>S2 Eᴘɪsᴏᴅᴇ 1</b>"
    },

    "Episode4": { # सीजन 2 के लिए
        "type": "video",
        "id": "BAACAgUAAxkBAAOOaHtXCViOAAEOlcoWmydfao-TpaoNAAL9FQAC3XFQV6RvKzee8O2ANgQ",
        "caption": "<b>S2 Eᴘɪsᴏᴅᴇ 2</b>",
        "buttons": [
            [{"text": "Wᴀᴛᴄʜ Nᴇxᴛ Sᴇᴀsᴏɴ", "url": "https://t.me/YourMainChannel"}]
        ]
    },

    # --- अब सीरीज पैक बनाएं ---
    "Season1Pack": {
        "type": "series",
        "episodes": ["Episode1", "Episode2"] # यहाँ keys का इस्तेमाल करें
    },

    "Season2Pack": {
        "type": "series",
        "episodes": ["Episode3", "Episode4"] # यहाँ keys का इस्तेमाल करें
    }
}

# 6. डिलीट का समय (सेकंड में)
DELETE_DELAY = 900  # 15 मिनट
