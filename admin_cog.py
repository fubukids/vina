
import discord
from discord import app_commands
from discord.ext import commands
from data_manager import load_data, save_data, guild_profile, user_profile
from utils import base_embed, can_admin, money_fmt

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setdailyreward", description="[Admin] Set daily reward amount (default 100).")
    async def setdailyreward(self, interaction: discord.Interaction, amount: int):
        if not can_admin(interaction):
            await interaction.response.send_message("Admin only.", ephemeral=True); return
        data = load_data()
        g = guild_profile(data, interaction.guild_id)
        g["config"]["daily_reward"] = max(0, amount)
        save_data(data)
        await interaction.response.send_message(embed=base_embed("Config Updated", f"Daily reward set to {money_fmt(amount)}"))

    @app_commands.command(name="setwork", description="[Admin] Set work income (default 100).")
    async def setwork(self, interaction: discord.Interaction, amount: int):
        if not can_admin(interaction):
            await interaction.response.send_message("Admin only.", ephemeral=True); return
        data = load_data()
        g = guild_profile(data, interaction.guild_id)
        g["config"]["work_reward"] = max(0, amount)
        save_data(data)
        await interaction.response.send_message(embed=base_embed("Config Updated", f"Work reward set to {money_fmt(amount)}"))

    @app_commands.command(name="setmoneyuser", description="[Admin] Set a user's money to an amount.")
    async def setmoneyuser(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if not can_admin(interaction):
            await interaction.response.send_message("Admin only.", ephemeral=True); return
        data = load_data()
        u = user_profile(data, interaction.guild_id, member.id)
        u["money"] = max(0, amount)
        save_data(data)
        await interaction.response.send_message(embed=base_embed("Money Set", f"{member.mention} now has {money_fmt(u['money'])}"))

    @app_commands.command(name="removemoneyuser", description="[Admin] Remove money from a user.")
    async def removemoneyuser(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if not can_admin(interaction):
            await interaction.response.send_message("Admin only.", ephemeral=True); return
        data = load_data()
        u = user_profile(data, interaction.guild_id, member.id)
        u["money"] = max(0, u["money"] - max(0, amount))
        save_data(data)
        await interaction.response.send_message(embed=base_embed("Money Removed", f"{member.mention} now has {money_fmt(u['money'])}"))

    @app_commands.command(name="levelupprice", description="[Admin] Set upgrade price tiers for arrows/axes.")
    @app_commands.describe(tool="arrow or axe", from_tier="bronze/silver/gold/diamond", price="cost to upgrade from this tier to the next")
    async def levelupprice(self, interaction: discord.Interaction, tool: str, from_tier: str, price: int):
        if not can_admin(interaction):
            await interaction.response.send_message("Admin only.", ephemeral=True); return
        tool = tool.lower()
        from_tier = from_tier.lower()
        if tool not in ("arrow","axe") or from_tier not in ("bronze","silver","gold","diamond"):
            await interaction.response.send_message("Invalid inputs.", ephemeral=True); return
        data = load_data()
        g = guild_profile(data, interaction.guild_id)
        key = "arrow_prices" if tool=="arrow" else "axe_prices"
        g["config"][key][from_tier] = max(0, price)
        save_data(data)
        await interaction.response.send_message(embed=base_embed("Prices Updated", f"{tool.title()} upgrade from {from_tier.title()} now costs {money_fmt(price)}"))

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
