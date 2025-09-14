
import asyncio, random
import discord
from discord import app_commands
from discord.ext import commands
from data_manager import load_data, save_data, user_profile, guild_profile
from utils import base_embed, money_fmt
from emojis import UI

class MinigamesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # SLOTS
    @app_commands.command(name="slot", description="Spin the slot machine.")
    async def slot(self, interaction: discord.Interaction, bet: int):
        if bet <= 0: 
            await interaction.response.send_message("Bet must be positive.", ephemeral=True); return
        data = load_data()
        u = user_profile(data, interaction.guild_id, interaction.user.id)
        if u["money"] < bet:
            await interaction.response.send_message("Not enough balance.", ephemeral=True); return
        u["money"] -= bet
        save_data(data)

        reels = ["🍒","🍋","🍇","⭐","💎"]
        e = base_embed("Slots", "Spinning...")
        await interaction.response.send_message(embed=e)
        msg = await interaction.original_response()
        slot = ["⬛","⬛","⬛"]
        for i in range(6):
            slot = [random.choice(reels) for _ in range(3)]
            e = base_embed("Slots", f"[ {slot[0]} | {slot[1]} | {slot[2]} ]")
            await asyncio.sleep(0.5)
            await msg.edit(embed=e)

        payout = 0
        if len(set(slot)) == 1:
            sym = slot[0]
            mult = {"🍒":3,"🍋":4,"🍇":5,"⭐":8,"💎":15}[sym]
            payout = bet * mult
        elif slot.count("💎") == 2:
            payout = int(bet * 2.5)
        elif slot.count("⭐") == 2:
            payout = int(bet * 2.0)

        u["money"] += payout
        save_data(data)
        result = "You lost."
        if payout>0: result = f"You won **{money_fmt(payout)}**!"
        end = base_embed("Slots Result", f"[ {slot[0]} | {slot[1]} | {slot[2]} ]\n{result}\nBalance: {money_fmt(u['money'])}")
        await msg.edit(embed=end)

    # ROULETTE (red/black)
    @app_commands.command(name="roulette", description="Bet on red or black.")
    async def roulette(self, interaction: discord.Interaction, color: str, bet: int):
        color = color.lower()
        if color not in ("red","black"):
            await interaction.response.send_message("Pick 'red' or 'black'.", ephemeral=True); return
        if bet <= 0: 
            await interaction.response.send_message("Bet must be positive.", ephemeral=True); return
        data = load_data()
        u = user_profile(data, interaction.guild_id, interaction.user.id)
        if u["money"] < bet:
            await interaction.response.send_message("Not enough balance.", ephemeral=True); return
        u["money"] -= bet; save_data(data)

        e = base_embed("Roulette", f"Betting on **{color}**...")
        await interaction.response.send_message(embed=e)
        msg = await interaction.original_response()
        await asyncio.sleep(1.5)
        outcome = random.choice(["red","black","green"])  # green = 0
        payout = 0
        if outcome == color:
            payout = bet * 2
        elif outcome == "green":
            payout = 0
        u["money"] += payout; save_data(data)
        end = base_embed("Roulette Result", f"Ball landed on **{outcome}**.\n{'You won!' if payout else 'You lost.'}\nBalance: {money_fmt(u['money'])}")
        await msg.edit(embed=end)

    # COINFLIP
    @app_commands.command(name="coinflip", description="Coinflip heads/tails.")
    async def coinflip(self, interaction: discord.Interaction, side: str, bet: int):
        side = side.lower()
        if side not in ("heads","tails"):
            await interaction.response.send_message("Pick heads or tails.", ephemeral=True); return
        if bet <= 0:
            await interaction.response.send_message("Bet must be positive.", ephemeral=True); return
        data = load_data(); u = user_profile(data, interaction.guild_id, interaction.user.id)
        if u["money"] < bet: 
            await interaction.response.send_message("Not enough balance.", ephemeral=True); return
        u["money"] -= bet; save_data(data)
        e = base_embed("Coinflip", "Flipping...")
        await interaction.response.send_message(embed=e)
        msg = await interaction.original_response()
        await asyncio.sleep(0.8)
        res = random.choice(["heads","tails"])
        payout = bet*2 if res==side else 0
        u["money"] += payout; save_data(data)
        end = base_embed("Coinflip Result", f"It's **{res}**. {'You won!' if payout else 'You lost.'}\nBalance: {money_fmt(u['money'])}")
        await msg.edit(embed=end)

    # BLACKJACK (simple)
    @app_commands.command(name="blackjack", description="Play blackjack against dealer.")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        if bet <= 0:
            await interaction.response.send_message("Bet must be positive.", ephemeral=True); return
        data = load_data(); u = user_profile(data, interaction.guild_id, interaction.user.id)
        if u["money"] < bet:
            await interaction.response.send_message("Not enough balance.", ephemeral=True); return

        # game state
        deck = [r+s for r in list("A23456789TJQK") for s in "♠♥♦♣"] * 4
        random.shuffle(deck)
        def val(hand):
            total, aces = 0, 0
            for c in hand:
                r=c[0]
                if r in "TJQK": total += 10
                elif r=="A": total += 11; aces += 1
                else: total += int(r)
            while total>21 and aces>0:
                total -= 10; aces -= 1
            return total
        def fmt(hand):
            return " ".join(hand) + f" (={val(hand)})"

        u["money"] -= bet; save_data(data)

        player = [deck.pop(), deck.pop()]
        dealer = [deck.pop(), deck.pop()]

        view = discord.ui.View()
        hit_btn = discord.ui.Button(label="Hit", style=discord.ButtonStyle.primary, emoji="🃏")
        stand_btn = discord.ui.Button(label="Stand", style=discord.ButtonStyle.secondary, emoji="🛑")
        finished = asyncio.Event()

        async def update_msg(msg):
            e = base_embed("Blackjack", f"Your hand: **{fmt(player)}**\nDealer shows: `{dealer[0]}` `??`")
            await msg.edit(embed=e, view=view)

        async def end_game(msg, outcome):
            payout = 0
            if outcome=="win": payout = bet*2
            elif outcome=="push": payout = bet
            u["money"] += payout; save_data(data)
            e = base_embed("Blackjack Result",
                           f"Your hand: **{fmt(player)}**\nDealer: **{fmt(dealer)}**\n"
                           f"Outcome: **{outcome.upper()}**\nBalance: {money_fmt(u['money'])}")
            for c in view.children: c.disabled = True
            await msg.edit(embed=e, view=view)
            finished.set()

        async def on_hit(interaction_btn: discord.Interaction):
            if interaction_btn.user.id != interaction.user.id:
                await interaction_btn.response.send_message("This is not your game.", ephemeral=True); return
            player.append(deck.pop())
            if val(player) > 21:
                await end_game(msg_ref, "lose")
            else:
                await update_msg(msg_ref)
                await interaction_btn.response.defer()

        async def on_stand(interaction_btn: discord.Interaction):
            if interaction_btn.user.id != interaction.user.id:
                await interaction_btn.response.send_message("This is not your game.", ephemeral=True); return
            # dealer plays
            while val(dealer) < 17:
                dealer.append(deck.pop()); await asyncio.sleep(0.6)
            pv, dv = val(player), val(dealer)
            if dv>21 or pv>dv: await end_game(msg_ref, "win")
            elif pv==dv: await end_game(msg_ref, "push")
            else: await end_game(msg_ref, "lose")

        hit_btn.callback = on_hit
        stand_btn.callback = on_stand
        view.add_item(hit_btn); view.add_item(stand_btn)

        e = base_embed("Blackjack", "Dealing cards...")
        await interaction.response.send_message(embed=e, view=view)
        msg_ref = await interaction.original_response()
        await update_msg(msg_ref)

        try:
            await asyncio.wait_for(finished.wait(), timeout=120)
        except asyncio.TimeoutError:
            for c in view.children: c.disabled=True
            e = base_embed("Blackjack Timeout", "Game ended due to inactivity.")
            await msg_ref.edit(embed=e, view=view)

    # HORSE RACE
    @app_commands.command(name="horserace", description="Bet on a horse (1-4) and watch the race!")
    async def horserace(self, interaction: discord.Interaction, horse: int, bet: int):
        if horse not in (1,2,3,4):
            await interaction.response.send_message("Pick horse 1-4.", ephemeral=True); return
        if bet <= 0:
            await interaction.response.send_message("Bet must be positive.", ephemeral=True); return
        data = load_data(); u = user_profile(data, interaction.guild_id, interaction.user.id)
        if u["money"] < bet:
            await interaction.response.send_message("Not enough balance.", ephemeral=True); return
        u["money"] -= bet; save_data(data)

        track_len = 20
        pos = [0,0,0,0]
        icons = ["🐎","🐴","🦄","🏇"]
        e = base_embed("Horse Race", "They're off!")
        await interaction.response.send_message(embed=e)
        msg = await interaction.original_response()
        winner = None

        for _ in range(40):
            for i in range(4):
                pos[i] += random.choice([0,1,1,2])  # small random progress
                if pos[i] >= track_len and winner is None:
                    winner = i+1
            lines = []
            for i in range(4):
                bar = "·"*max(0, track_len - pos[i])
                lines.append(f"{i+1} {icons[i]} |{'—'*pos[i]}{icons[i] if pos[i]<track_len else '🏁'}{bar}")
            e = base_embed("Horse Race", "\n".join(lines))
            await msg.edit(embed=e)
            await asyncio.sleep(0.4)
            if winner is not None: break

        payout = bet*4 if winner==horse else 0
        u["money"] += payout; save_data(data)
        end = base_embed("Race Result", f"Winner: **Horse {winner}**\n{'You won!' if payout else 'You lost.'}\nBalance: {money_fmt(u['money'])}")
        await msg.edit(embed=end)

async def setup(bot):
    await bot.add_cog(MinigamesCog(bot))
