
import discord
from discord import app_commands
from discord.ext import commands
from data_manager import load_data, save_data, guild_profile, user_profile
from emojis import UI
from utils import base_embed, can_admin, money_fmt

class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="shop", description="Show the server shop.")
    async def shop(self, interaction: discord.Interaction):
        data = load_data()
        g = guild_profile(data, interaction.guild_id)
        items = g["config"]["shop_items"]
        e = base_embed("Server Shop", "Use `/buyitem name:<item>` to purchase.")
        if not items:
            e.add_field(name="Empty", value="Admins can add items with `/shopadd`.", inline=False)
        else:
            for name, info in items.items():
                line = f"Price: **{money_fmt(info['price'])}** | Type: `{info['type']}`"
                if info['type']=="role" and info.get("role_id"):
                    role = interaction.guild.get_role(info["role_id"])
                    if role:
                        line += f" | Role: {role.mention}"
                e.add_field(name=name, value=line, inline=False)
        e.set_thumbnail(url="https://em-content.zobj.net/source/microsoft-teams/363/shopping-cart_1f6d2-fe0f.png")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="buyitem", description="Buy an item from the shop (auto-used).")
    async def buyitem(self, interaction: discord.Interaction, name: str):
        data = load_data()
        g = guild_profile(data, interaction.guild_id)
        u = user_profile(data, interaction.guild_id, interaction.user.id)

        item = g["config"]["shop_items"].get(name)
        if not item:
            await interaction.response.send_message("Item not found.", ephemeral=True)
            return
        price = int(item["price"])
        if u["money"] < price:
            await interaction.response.send_message("Not enough money.", ephemeral=True)
            return
        u["money"] -= price

        # Auto-use
        applied = ""
        if item["type"] == "role" and item.get("role_id"):
            role = interaction.guild.get_role(item["role_id"])
            if role:
                try:
                    await interaction.user.add_roles(role, reason="Shop purchase")
                    applied = f"Role granted: {role.mention}"
                except discord.Forbidden:
                    applied = "Failed to grant role (missing permissions)."
        else:
            applied = "Item purchased!"

        save_data(data)
        e = base_embed("Purchase Complete", f"You bought **{name}** for **{money_fmt(price)}**.\n{applied}\nBalance: **{money_fmt(u['money'])}**")
        await interaction.response.send_message(embed=e)

    # Admin shop management
    @app_commands.command(name="shopadd", description="[Admin] Add an item to shop.")
    async def shopadd(self, interaction: discord.Interaction, name: str, price: int, type: str, role: discord.Role | None = None):
        if not can_admin(interaction):
            await interaction.response.send_message("Admin only.", ephemeral=True); return
        data = load_data()
        g = guild_profile(data, interaction.guild_id)
        g["config"]["shop_items"][name] = {"price": price, "type": type.lower(), "role_id": role.id if role else None}
        save_data(data)
        await interaction.response.send_message(embed=base_embed("Shop Updated", f"Added **{name}** for {money_fmt(price)}."))

    @app_commands.command(name="shopremove", description="[Admin] Remove an item from shop.")
    async def shopremove(self, interaction: discord.Interaction, name: str):
        if not can_admin(interaction):
            await interaction.response.send_message("Admin only.", ephemeral=True); return
        data = load_data()
        g = guild_profile(data, interaction.guild_id)
        if name in g["config"]["shop_items"]:
            g["config"]["shop_items"].pop(name)
            save_data(data)
            await interaction.response.send_message(embed=base_embed("Shop Updated", f"Removed **{name}**."))
        else:
            await interaction.response.send_message("Item not found.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ShopCog(bot))
