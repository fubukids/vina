
import os, asyncio
import discord
from discord.ext import commands
from discord import app_commands
from utils import base_embed
from emojis import UI
# Slash auto-sync target guild (server-only economy). Set to your guild ID or None for global.
GUILD_ID = None  # e.g. 123456789012345678

INTENTS = discord.Intents.default()
INTENTS.guilds = True
INTENTS.members = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

# HELP command with dropdown
class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Economy", description="Money, Inventory, Sell, Upgrades"),
            discord.SelectOption(label="Hunt & Mine", description="Start & play hunting/mining"),
            discord.SelectOption(label="Shop", description="View and buy shop items"),
            discord.SelectOption(label="Minigames", description="Slots, Roulette, Blackjack, Coinflip, Horserace"),
            discord.SelectOption(label="Admin", description="Admin-only configuration"),
        ]
        super().__init__(placeholder="Pick a help category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        label = self.values[0]
        pages = {
            "Economy": "**/money** – show your balance\n"
                       "**/inventory** – show your items\n"
                       "**/sell** *type id qty* – sell item\n"
                       "**/sellall** *type* – sell all animals or stones\n"
                       "**/leveluparrow** – upgrade arrow\n"
                       "**/levelupaxe** – upgrade axe",
            "Hunt & Mine": "**/starthunt** – tutorial & enable hunting\n"
                           "**/hunt** – attempt a hunt (20s cd)\n"
                           "**/startmine** – tutorial & enable mining\n"
                           "**/mine** – attempt mining (20s cd)",
            "Shop": "**/shop** – view server shop\n"
                    "**/buyitem** *name* – buy & auto-use item",
            "Minigames": "**/slot** *bet*\n"
                         "**/roulette** *red/black bet*\n"
                         "**/coinflip** *heads/tails bet*\n"
                         "**/blackjack** *bet*\n"
                         "**/horserace** *horse bet*",
            "Admin": "**/setdailyreward** *amount*\n"
                     "**/setwork** *amount*\n"
                     "**/setmoneyuser** *member amount*\n"
                     "**/removemoneyuser** *member amount*\n"
                     "**/levelupprice** *tool from_tier price*\n"
                     "**/shopadd** *name price type [role]*\n"
                     "**/shopremove** *name*"
        }
        e = base_embed(f"{label} Help", pages[label])
        await interaction.response.edit_message(embed=e)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpSelect())

@bot.tree.command(name="help", description="Show bot help with dropdown")
async def help_cmd(interaction: discord.Interaction):
    e = base_embed("Weiz Economy Bot Help", "Pick a category below.")
    await interaction.response.send_message(embed=e, view=HelpView(), ephemeral=True)

async def load_cogs():
    await bot.load_extension("economy_cog")
    await bot.load_extension("hunt_mine_cog")
    await bot.load_extension("shop_cog")
    await bot.load_extension("admin_cog")
    await bot.load_extension("minigames_cog")

@bot.event
async def on_ready():
    try:
        await load_cogs()
    except Exception as e:
        print("Cog load error:", e)

    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            await bot.tree.sync(guild=guild)
            print(f"Synced slash commands to guild {GUILD_ID}")
        else:
            await bot.tree.sync()
            print("Globally synced slash commands.")
    except Exception as e:
        print("Sync error:", e)

    print(f"Logged in as {bot.user}")

def read_token():
    path = "token.txt"
    if not os.path.exists(path):
        raise RuntimeError("token.txt not found. Put your bot token inside token.txt")
    with open(path, "r") as f:
        return f.read().strip()

if __name__ == "__main__":
    token = read_token()
    bot.run(token)
