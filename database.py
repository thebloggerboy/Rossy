# database.py (Phase 2 - Upgraded)
import json
import os

DB_FILE = 'bot_database.json'

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # अगर फाइल खाली या खराब है
                return {"users": {}, "banned_users": []}
    else:
        return {"users": {}, "banned_users": []}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

db = load_db()

def add_user(user_id):
    user_id_str = str(user_id)
    if user_id_str not in db["users"]:
        db["users"][user_id_str] = {} # भविष्य के लिए खाली डिक्शनरी
        save_db(db)
        return True
    return False

def get_all_user_ids():
    """सभी यूज़र IDs की एक लिस्ट देता है।"""
    return list(db["users"].keys())

def ban_user(user_id):
    """एक यूजर को बैन करता है।"""
    user_id_int = int(user_id)
    if user_id_int not in db["banned_users"]:
        db["banned_users"].append(user_id_int)
        save_db(db)
        return True
    return False

def unban_user(user_id):
    """एक यूजर को अनबैन करता है।"""
    user_id_int = int(user_id)
    if user_id_int in db["banned_users"]:
        db["banned_users"].remove(user_id_int)
        save_db(db)
        return True
    return False
