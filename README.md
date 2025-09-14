
# Weiz Economy & Minigames Discord Bot (EN)

**Focus:** Server-only economy (per-guild), hunting & mining systems with arrows/axes tiers, shop, inventory, admin controls, and minigames.
**Embed color:** yellow, **Footer:** "weiz".
**Slash commands auto-sync** on startup.

## Quick Start
1. Create a bot at https://discord.com/developers/applications and invite it with bot+applications.commands scopes.
2. Put your bot token inside `token.txt` (just the token string).
3. (Optional) If you want to sync commands to only one guild, set `GUILD_ID` in `main.py` to your server ID. Otherwise keep it `None` for global sync.
4. Install deps: `pip install -r requirements.txt`
5. Run: `python main.py`

## Notes
- Data stored in `data/eco.json` per guild.
- Emojis are centralized in `emojis.py` for easy editing, including animals, stones, UI icons, and animated (blink) frames.
- Cooldowns: Hunt 20s, Mine 20s.
- Arrow tiers: bronze, silver, gold, diamond, apex (purple-gold).
- Axe tiers mirror arrow tiers.
- Admins: need `Manage Guild` permission for admin commands.
- Language: English responses.
- Host Tested: designed to be friendly for OrisHost free plan (simple file storage, no env vars).

## Files
- `main.py` – entry point, cogs load, slash autosync
- `emojis.py` – all pixel-ish emoji strings in one place
- `data_manager.py` – load/save helpers
- `utils.py` – shared helpers: embeds, checks, rng tables
- `hunt_mine_cog.py` – hunting & mining systems
- `economy_cog.py` – balance, inventory, selling, upgrading
- `shop_cog.py` – server shop & purchases
- `admin_cog.py` – admin config commands
- `minigames_cog.py` – slots, roulette, blackjack, coinflip, horserace
- `requirements.txt`, `token.txt` (you add), `README.md`
