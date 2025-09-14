
import time, random
import discord
from emojis import UI, ARROWS, AXES
YELLOW = discord.Color.yellow()

FOOTER_TEXT = "weiz"

def base_embed(title=None, desc=None):
    e = discord.Embed(title=title or "", description=desc or "", color=YELLOW)
    e.set_footer(text=FOOTER_TEXT)
    return e

def can_admin(interaction: discord.Interaction) -> bool:
    m = interaction.user
    if isinstance(m, discord.Member):
        return m.guild_permissions.manage_guild
    return False

def cooldown_ok(user_data, action, seconds):
    now = time.time()
    cd = user_data["cooldowns"].get(action, 0)
    return now >= cd + seconds, max(0, int(cd + seconds - now))

def set_cooldown(user_data, action, seconds):
    user_data["cooldowns"][action] = time.time()

# Probabilities by tier (sum to 1 = chance of success; remaining chance = fail).
# On success, rarity distribution affects WHAT you get.
ARROW_SUCCESS = {
    "bronze": 0.25,
    "silver": 0.45,
    "gold": 0.65,
    "diamond": 0.80,
    "apex": 0.92
}

AXE_SUCCESS = {
    "bronze": 0.30,
    "silver": 0.50,
    "gold": 0.70,
    "diamond": 0.85,
    "apex": 0.95
}

RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]
RARITY_WEIGHTS = {
    "bronze": [70, 20, 8, 2, 0],
    "silver": [60, 25, 10, 4, 1],
    "gold":   [50, 28, 14, 6, 2],
    "diamond":[40, 30, 18, 9, 3],
    "apex":   [35, 32, 20, 10, 3]
}

# Sell prices by rarity
SELL_VALUES = {
    "common": 10,
    "uncommon": 25,
    "rare": 60,
    "epic": 150,
    "legendary": 400
}

def pick_rarity(tier: str):
    weights = RARITY_WEIGHTS[tier]
    return random.choices(RARITIES, weights=weights, k=1)[0]

def arrow_label(tier): return f"{ARROWS[tier]} `{tier.title()}`"
def axe_label(tier): return f"{AXES[tier]} `{tier.title()}`"

def money_fmt(n: int):
    return f"{UI['money']} {n:,}"

def blink_frames(item):
    return item["frames"]
