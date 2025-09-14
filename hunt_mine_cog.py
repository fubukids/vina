
import asyncio, random, time
import discord
from discord import app_commands
from discord.ext import commands
from data_manager import load_data, save_data, user_profile
from emojis import UI, ARROWS, AXES, ANIMALS, STONES, BLINK
from utils import base_embed, cooldown_ok, set_cooldown, ARROW_SUCCESS, AXE_SUCCESS, pick_rarity, blink_frames

HUNT_CD = 20
MINE_CD = 20

class StartHuntView(discord.ui.View):
    def __init__(self, author_id: int, timeout=60):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value = False

    @discord.ui.button(label="I agree. Start Hunting!", style=discord.ButtonStyle.success, emoji="✅")
    async def agree(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        self.value = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

class StartMineView(discord.ui.View):
    def __init__(self, author_id: int, timeout=60):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value = False

    @discord.ui.button(label="I agree. Start Mining!", style=discord.ButtonStyle.success, emoji="✅")
    async def agree(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return
        self.value = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

class HuntMineCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="starthunt", description="Learn how hunting works and start it.")
    async def starthunt(self, interaction: discord.Interaction):
        data = load_data()
        u = user_profile(data, interaction.guild_id, interaction.user.id)
        e = base_embed("Hunting Tutorial",
            "Hunting rules:\n"
            "• Use `/hunt` to attempt catching an animal.\n"
            "• You start with **Bronze Arrow** (low success rate).\n"
            "• Better arrows increase success chance & rarer animals.\n"
            f"• Cooldown: **{HUNT_CD}s**.\n"
            "• Click ✅ to accept and start. You'll receive a Bronze Arrow.")
        view = StartHuntView(interaction.user.id)
        await interaction.response.send_message(embed=e, view=view)
        await view.wait()
        if view.value:
            u["flags"]["hunt_started"] = True
            # ensure bronze
            u["arrow_tier"] = "bronze"
            save_data(data)
            done = base_embed("Hunting Enabled", "You can now use `/hunt`. Good luck!")
            await interaction.followup.send(embed=done)

    @app_commands.command(name="startmine", description="Learn how mining works and start it.")
    async def startmine(self, interaction: discord.Interaction):
        data = load_data()
        u = user_profile(data, interaction.guild_id, interaction.user.id)
        e = base_embed("Mining Tutorial",
            "Mining rules:\n"
            "• Use `/mine` to attempt getting stones/gems.\n"
            "• You start with **Bronze Axe** (low success rate).\n"
            "• Better axes increase success chance & rarer stones.\n"
            f"• Cooldown: **{MINE_CD}s**.\n"
            "• Click ✅ to accept and start. You'll receive a Bronze Axe.")
        view = StartMineView(interaction.user.id)
        await interaction.response.send_message(embed=e, view=view)
        await view.wait()
        if view.value:
            u["flags"]["mine_started"] = True
            u["axe_tier"] = "bronze"
            save_data(data)
            done = base_embed("Mining Enabled", "You can now use `/mine`. Swing away!")
            await interaction.followup.send(embed=done)

    @app_commands.command(name="hunt", description="Go hunting for animals with your Arrow.")
    async def hunt(self, interaction: discord.Interaction):
        data = load_data()
        u = user_profile(data, interaction.guild_id, interaction.user.id)
        if not u["flags"]["hunt_started"]:
            await interaction.response.send_message("Use `/starthunt` first.", ephemeral=True)
            return

        ok, remain = cooldown_ok(u, "hunt", HUNT_CD)
        if not ok:
            await interaction.response.send_message(f"Cooldown {remain}s.", ephemeral=True)
            return

        tier = u["arrow_tier"]
        success_chance = ARROW_SUCCESS[tier]
        frames = ["✦","✧","✦","✧","✦"]
        e = base_embed("Hunting...", f"{ARROWS[tier]} Searching the wilds {frames[0]}")
        msg = await interaction.response.send_message(embed=e)
        msg = await interaction.original_response()

        # simple animation
        for i in range(1, len(frames)):
            await asyncio.sleep(0.6)
            e = base_embed("Hunting...", f"{ARROWS[tier]} Searching the wilds {frames[i]}")
            await msg.edit(embed=e)

        # resolve
        set_cooldown(u, "hunt", HUNT_CD)
        if random.random() <= success_chance:
            # choose animal weighted by rarity
            rarity = pick_rarity(tier)
            key = random.choice(list(ANIMALS.keys()))
            u["animals"][key] = u["animals"].get(key, 0) + 1
            save_data(data)

            icon = ANIMALS[key]["frames"][random.randint(0,1)]
            e = base_embed("Hunt Success!", f"You caught **{icon} {ANIMALS[key]['name']}** [{rarity.title()}].")
            await msg.edit(embed=e)
        else:
            save_data(data)
            e = base_embed("Hunt Failed", "The trail went cold... Better luck next time!")
            await msg.edit(embed=e)

    @app_commands.command(name="mine", description="Mine stones with your Axe.")
    async def mine(self, interaction: discord.Interaction):
        data = load_data()
        u = user_profile(data, interaction.guild_id, interaction.user.id)
        if not u["flags"]["mine_started"]:
            await interaction.response.send_message("Use `/startmine` first.", ephemeral=True)
            return

        ok, remain = cooldown_ok(u, "mine", MINE_CD)
        if not ok:
            await interaction.response.send_message(f"Cooldown {remain}s.", ephemeral=True)
            return

        tier = u["axe_tier"]
        success_chance = AXE_SUCCESS[tier]
        frames = ["＊","﹡","＊","﹡","＊"]
        e = base_embed("Mining...", f"{AXES[tier]} Swinging {frames[0]}")
        await interaction.response.send_message(embed=e)
        msg = await interaction.original_response()
        for i in range(1, len(frames)):
            await asyncio.sleep(0.6)
            e = base_embed("Mining...", f"{AXES[tier]} Swinging {frames[i]}")
            await msg.edit(embed=e)

        set_cooldown(u, "mine", MINE_CD)
        if random.random() <= success_chance:
            rarity = pick_rarity(tier)
            key = random.choice(list(STONES.keys()))
            u["stones"][key] = u["stones"].get(key, 0) + 1
            save_data(data)
            icon = STONES[key]["frames"][random.randint(0,1)]
            e = base_embed("Mining Success!", f"You mined **{icon} {STONES[key]['name']}** [{rarity.title()}].")
            await msg.edit(embed=e)
        else:
            save_data(data)
            e = base_embed("Mining Failed", "The vein collapsed... You found nothing.")
            await msg.edit(embed=e)

async def setup(bot):
    await bot.add_cog(HuntMineCog(bot))
