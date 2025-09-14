
import json, os

DATA_FILE = os.path.join("data", "eco.json")

def _ensure():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)

def load_data():
    _ensure()
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    _ensure()
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def guild_profile(data, guild_id):
    g = data.setdefault(str(guild_id), {
        "users": {},
        "config": {
            "daily_reward": 100,
            "work_reward": 100,
            "arrow_prices": { # upgrade from tier -> next tier cost
                "bronze": 500,
                "silver": 2500,
                "gold": 10000,
                "diamond": 50000
            },
            "axe_prices": {
                "bronze": 500,
                "silver": 2500,
                "gold": 10000,
                "diamond": 50000
            },
            "shop_items": {} # name -> {"price": int, "type": "role"/"item", "role_id": int | None}
        }
    })
    return g

def user_profile(data, guild_id, user_id):
    g = guild_profile(data, guild_id)
    u = g["users"].setdefault(str(user_id), {
        "money": 0,
        "arrow_tier": "bronze",
        "axe_tier": "bronze",
        "animals": {},  # item_id -> count
        "stones": {},   # item_id -> count
        "cooldowns": {}, # action -> ts
        "flags": {
            "hunt_started": False,
            "mine_started": False
        }
    })
    return u
