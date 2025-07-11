# database.py
import json
import os

DB_FILE = 'bot_database.json'

def load_db():
    """डेटाबेस फाइल को लोड करता है, अगर मौजूद नहीं है तो नई बनाता है।"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    else:
        # नई डेटाबेस की संरचना
        return {
            "users": {}, # { "user_id": {"referrals": 0, "points": 0, "last_daily": "YYYY-MM-DD"} }
            "banned_users": []
        }

def save_db(data):
    """डेटाबेस को फाइल में सेव करता है।"""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# शुरू में डेटाबेस लोड करें
db = load_db()

def add_user(user_id):
    """डेटाबेस में एक नए यूजर को जोड़ता है।"""
    if str(user_id) not in db["users"]:
        db["users"][str(user_id)] = {
            "referrals": 0,
            "points": 10, # स्वागत बोनस
            "last_daily": None
        }
        save_db(db)
        return True
    return False

def ban_user(user_id):
    """एक यूजर को बैन करता है।"""
    if user_id not in db["banned_users"]:
        db["banned_users"].append(user_id)
        save_db(db)
        return True
    return False

def unban_user(user_id):
    """एक यूजर को अनबैन करता है।"""
    if user_id in db["banned_users"]:
        db["banned_users"].remove(user_id)
        save_db(db)
        return True
    return False