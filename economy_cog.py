
import discord
from discord import app_commands
from discord.ext import commands
from data_manager import load_data, save_data, user_profile, guild_profile
from emojis import UI, ARROWS, AXES, ANIMALS, STONES
from utils import base_embed, money_fmt, arrow_label, axe_label, SELL_VALUES

class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # BALANCE
    @app_commands.command(name="money", description="Show your money balance.")
    async def money(self, interaction: discord.Interaction):
        data = load_data()
        u = user_profile(data, interaction.guild_id, interaction.user.id)
        e = base_embed("Balance", f"{interaction.user.mention} has **{money_fmt(u['money'])}**.")
        await interaction.response.send_message(embed=e)

    # INVENTORY
    @app_commands.command(name="inventory", description="Show your inventory.")
    async def inventory(self, interaction: discord.Interaction):
        data = load_data()
        u = user_profile(data, interaction.guild_id, interaction.user.id)

        animals_total = sum(u["animals"].values())
        stones_total  = sum(u["stones"].values())

        e = base_embed("Inventory")
        e.add_field(name="Money", value=money_fmt(u["money"]), inline=False)
        e.add_field(name="Arrow", value=arrow_label(u["arrow_tier"]), inline=True)
        e.add_field(name="Axe", value=axe_label(u["axe_tier"]), inline=True)

        # Animal summary
        if animals_total:
            lines = []
            for key, qty in sorted(u["animals"].items(), key=lambda kv: kv[0]):
                item = ANIMALS.get(key)
                if not item: continue
                icon = item["frames"][0].replace("✦","").replace("✧","")
                lines.append(f"{icon} **{item['name']}** × **{qty}**")
            e.add_field(name="Animals", value="\n".join(lines)[:1024], inline=False)
        else:
            e.add_field(name="Animals", value="None", inline=False)

        # Stone summary
        if stones_total:
            lines = []
            for key, qty in sorted(u["stones"].items(), key=lambda kv: kv[0]):
                item = STONES.get(key)
                if not item: continue
                icon = item["frames"][0].replace("✦","").replace("✧","")
                lines.append(f"{icon} **{item['name']}** × **{qty}**")
            e.add_field(name="Stones", value="\n".join(lines)[:1024], inline=False)
        else:
            e.add_field(name="Stones", value="None", inline=False)
        await interaction.response.send_message(embed=e)

    # SELL single
    @app_commands.command(name="sell", description="Sell items (animal/stone) to earn money.")
    @app_commands.describe(item_type="animal or stone", item_id="e.g. 'rabbit' or 'gold'", quantity="amount or 'all'")
    async def sell(self, interaction: discord.Interaction, item_type: str, item_id: str, quantity: str):
        item_type = item_type.lower()
        if item_type not in ("animal", "stone"):
            await interaction.response.send_message("Type must be 'animal' or 'stone'.", ephemeral=True)
            return

        data = load_data()
        u = user_profile(data, interaction.guild_id, interaction.user.id)
        bag = u["animals"] if item_type=="animal" else u["stones"]
        if item_id not in bag or bag[item_id] <= 0:
            await interaction.response.send_message("You don't have that item.", ephemeral=True)
            return

        to_sell = bag[item_id] if quantity.lower()=="all" else max(1, min(int(quantity), bag[item_id]))
        # Compute price: rarity derived heuristically from name mapping (simple demo: map by item_id length to rarity)
        # For better accuracy, we embed rarity in stored key as "item_id|rarity". But to keep simple, use base value of 'rare-ish' by id pattern.
        # We'll assume mid-value for animals, ore have higher base if precious.
        base = 20
        if item_type=="animal":
            if item_id in ("lion","tiger","elephant","rhino","eagle","shark","panda"): base = 150
            elif item_id in ("wolf","bear","owl","fox","boar","deer","bison","buffalo","croc"): base = 60
            else: base = 25
        else:
            if item_id in ("diamond","ruby","emerald","sapphire","amethyst"): base = 200
            elif item_id in ("gold","silver"): base = 100
            elif item_id in ("iron","copper"): base = 35
            else: base = 20

        earn = base * to_sell
        bag[item_id] -= to_sell
        if bag[item_id] <= 0:
            bag.pop(item_id, None)
        u["money"] += earn
        save_data(data)
        e = base_embed("Sold!", f"You sold **{to_sell}×** `{item_id}` for **{money_fmt(earn)}**.\nNew balance: **{money_fmt(u['money'])}**.")
        await interaction.response.send_message(embed=e)

    # MASS SELL (bulk by type)
    @app_commands.command(name="sellall", description="Sell all animals or all stones.")
    @app_commands.describe(item_type="animal or stone")
    async def sellall(self, interaction: discord.Interaction, item_type: str):
        item_type = item_type.lower()
        if item_type not in ("animal", "stone"):
            await interaction.response.send_message("Type must be 'animal' or 'stone'.", ephemeral=True)
            return
        data = load_data()
        u = user_profile(data, interaction.guild_id, interaction.user.id)
        bag = u["animals"] if item_type=="animal" else u["stones"]
        total_qty = sum(bag.values())
        if total_qty == 0:
            await interaction.response.send_message("Nothing to sell.", ephemeral=True)
            return
        # approximate pricing
        earn = 0
        for k, q in list(bag.items()):
            base = 20
            if item_type=="animal":
                if k in ("lion","tiger","elephant","rhino","eagle","shark","panda"): base = 150
                elif k in ("wolf","bear","owl","fox","boar","deer","bison","buffalo","croc"): base = 60
                else: base = 25
            else:
                if k in ("diamond","ruby","emerald","sapphire","amethyst"): base = 200
                elif k in ("gold","silver"): base = 100
                elif k in ("iron","copper"): base = 35
                else: base = 20
            earn += base * q
            bag[k] = 0
        u["money"] += earn
        u[item_type + "s"] = {}
        save_data(data)
        e = base_embed("Sold All", f"Sold **{total_qty}** {item_type}s for **{money_fmt(earn)}**.\nNew balance: **{money_fmt(u['money'])}**.")
        await interaction.response.send_message(embed=e)

    # UPGRADE ARROW / AXE
    @app_commands.command(name="leveluparrow", description="Upgrade your Arrow tier.")
    async def leveluparrow(self, interaction: discord.Interaction):
        data = load_data()
        g = guild_profile(data, interaction.guild_id)
        u = user_profile(data, interaction.guild_id, interaction.user.id)
        tiers = ["bronze","silver","gold","diamond","apex"]
        cur = u["arrow_tier"]
        if cur == "apex":
            await interaction.response.send_message("Your Arrow is already at max tier.", ephemeral=True)
            return
        idx = tiers.index(cur)
        nxt = tiers[idx+1]
        cost = g["config"]["arrow_prices"][cur]
        if u["money"] < cost:
            await interaction.response.send_message(f"Need {money_fmt(cost)} to upgrade to {nxt.title()}.", ephemeral=True)
            return
        u["money"] -= cost
        u["arrow_tier"] = nxt
        save_data(data)
        e = base_embed("Arrow Upgraded", f"{interaction.user.mention} upgraded to {nxt.title()}!\nBalance: {money_fmt(u['money'])}")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="levelupaxe", description="Upgrade your Axe tier.")
    async def levelupaxe(self, interaction: discord.Interaction):
        data = load_data()
        g = guild_profile(data, interaction.guild_id)
        u = user_profile(data, interaction.guild_id, interaction.user.id)
        tiers = ["bronze","silver","gold","diamond","apex"]
        cur = u["axe_tier"]
        if cur == "apex":
            await interaction.response.send_message("Your Axe is already at max tier.", ephemeral=True)
            return
        idx = tiers.index(cur)
        nxt = tiers[idx+1]
        cost = g["config"]["axe_prices"][cur]
        if u["money"] < cost:
            await interaction.response.send_message(f"Need {money_fmt(cost)} to upgrade to {nxt.title()}.", ephemeral=True)
            return
        u["money"] -= cost
        u["axe_tier"] = nxt
        save_data(data)
        e = base_embed("Axe Upgraded", f"{interaction.user.mention} upgraded to {nxt.title()}!\nBalance: {money_fmt(u['money'])}")
        await interaction.response.send_message(embed=e)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
