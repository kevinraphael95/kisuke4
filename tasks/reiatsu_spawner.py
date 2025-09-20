# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu_spawner.py — Gestion du spawn des Reiatsu
# Objectif : Gérer l’apparition et la capture des Reiatsu sur les serveurs
# Catégorie : Reiatsu / RPG
# Accès : Tous
# Cooldown : Spawn auto toutes les X minutes (configurable par serveur)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
import random
import time
import asyncio
from datetime import datetime
from dateutil import parser
import json
from pathlib import Path

from discord.ext import commands, tasks
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_delete  # 🔒 utils protégés

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Paramètres globaux (facilement modifiables)
# ────────────────────────────────────────────────────────────────────────────────
CONFIG_PATH = Path("data/reiatsu_config.json")
with CONFIG_PATH.open("r", encoding="utf-8") as f:
    CONFIG = json.load(f)

SPAWN_LOOP_INTERVAL = CONFIG["SPAWN_LOOP_INTERVAL"]
SUPER_REIATSU_CHANCE = CONFIG["SUPER_REIATSU_CHANCE"]
SUPER_REIATSU_GAIN = CONFIG["SUPER_REIATSU_GAIN"]
NORMAL_REIATSU_GAIN = CONFIG["NORMAL_REIATSU_GAIN"]
SPAWN_SPEED_RANGES = CONFIG["SPAWN_SPEED_RANGES"]
DEFAULT_SPAWN_SPEED = CONFIG["DEFAULT_SPAWN_SPEED"]

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog : ReiatsuSpawner
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuSpawner(commands.Cog):
    """
    Gère le spawn automatique de Reiatsu et leur capture par les joueurs.
    Supporte un seul faux Reiatsu par serveur.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.locks = {}  # 🔒 locks par serveur pour éviter les races
        self.spawn_loop.start()
        self.bot.loop.create_task(self._check_on_startup())

    def cog_unload(self):
        """Arrêt de la loop au déchargement du cog."""
        self.spawn_loop.cancel()

    async def _check_on_startup(self):
        """Vérifie que les messages spawn encore marqués existent vraiment."""
        await self.bot.wait_until_ready()
        configs = supabase.table("reiatsu_config").select("*").execute()
        for conf in configs.data:
            if not conf.get("en_attente") or not conf.get("spawn_message_id"):
                continue
            guild = self.bot.get_guild(int(conf["guild_id"]))
            if not guild:
                continue
            channel = guild.get_channel(int(conf.get("channel_id") or 0))
            if not channel:
                continue
            try:
                await channel.fetch_message(int(conf["spawn_message_id"]))
            except Exception:
                supabase.table("reiatsu_config").update({
                    "en_attente": False,
                    "spawn_message_id": None,
                    "faux_en_attente": False
                }).eq("guild_id", conf["guild_id"]).execute()
                print(f"[RESET] Reiatsu fantôme nettoyé pour guild {conf['guild_id']}")

    @tasks.loop(seconds=SPAWN_LOOP_INTERVAL)
    async def spawn_loop(self):
        await self.bot.wait_until_ready()
        if not getattr(self.bot, "is_main_instance", True):
            return
        try:
            await self._spawn_tick()
        except Exception as e:
            print(f"[ERREUR spawn_loop] {e}")

    async def _spawn_tick(self):
        """Vérifie chaque config serveur pour savoir si un spawn doit apparaître."""
        now = int(time.time())
        configs = supabase.table("reiatsu_config").select("*").execute()
        for conf in configs.data:
            guild_id = conf["guild_id"]
            channel_id = conf.get("channel_id")
            en_attente = conf.get("en_attente", False)
            faux_en_attente = conf.get("faux_en_attente", False)
            spawn_speed = conf.get("spawn_speed") or DEFAULT_SPAWN_SPEED
            min_delay, max_delay = SPAWN_SPEED_RANGES.get(spawn_speed, SPAWN_SPEED_RANGES[DEFAULT_SPAWN_SPEED])
            delay = conf.get("spawn_delay") or random.randint(min_delay, max_delay)
            if not channel_id:
                continue
            last_spawn_str = conf.get("last_spawn_at")
            should_spawn = not last_spawn_str or (now - int(parser.parse(last_spawn_str).timestamp()) >= delay)
            if should_spawn and not en_attente:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    await self._spawn_message(channel, guild_id)
            # 🔹 Spawn d’un faux Reiatsu Illusionniste si aucun faux n’est actif
            if not faux_en_attente:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    await self._spawn_faux_reiatsu(guild_id, channel)

    async def _spawn_message(self, channel, guild_id):
        embed = discord.Embed(
            title="💠 Un Reiatsu sauvage apparaît !",
            description="Cliquez sur la réaction 💠 pour l'absorber.",
            color=discord.Color.purple()
        )
        message = await safe_send(channel, embed=embed)
        if not message:
            return
        try:
            await message.add_reaction("💠")
        except discord.HTTPException:
            pass
        supabase.table("reiatsu_config").update({
            "en_attente": True,
            "last_spawn_at": datetime.utcnow().isoformat(timespec="seconds"),
            "spawn_message_id": str(message.id)
        }).eq("guild_id", guild_id).execute()

    async def _spawn_faux_reiatsu(self, guild_id: str, channel: discord.TextChannel):
        """Spawn un faux Reiatsu si aucun faux n’est actif sur le serveur."""
        players = supabase.table("reiatsu").select("*").execute()
        for player in players.data:
            skill = player.get("active_skill")
            if skill and skill.get("type") == "faux" and skill.get("spawn_id") is None:
                embed = discord.Embed(
                    title="🎭 Un faux Reiatsu apparaît !",
                    description="Cliquez sur 💠 pour l'absorber… si vous osez !",
                    color=discord.Color.gold()
                )
                message = await safe_send(channel, embed=embed)
                if not message:
                    return
                try:
                    await message.add_reaction("💠")
                except discord.HTTPException:
                    pass
                skill["spawn_id"] = str(message.id)
                supabase.table("reiatsu").update({"active_skill": skill}).eq("user_id", player["user_id"]).execute()
                supabase.table("reiatsu_config").update({"faux_en_attente": True}).eq("guild_id", guild_id).execute()
                return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "💠" or payload.user_id == self.bot.user.id:
            return
        guild_id = str(payload.guild_id)
        if guild_id not in self.locks:
            self.locks[guild_id] = asyncio.Lock()
        async with self.locks[guild_id]:
            conf_data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
            if not conf_data.data:
                return
            conf = conf_data.data[0]
            guild = self.bot.get_guild(payload.guild_id)
            channel = guild.get_channel(payload.channel_id)
            user = guild.get_member(payload.user_id)
            if not channel or not user:
                return

            # 🔹 Vérification des faux Reiatsu
            user_list = supabase.table("reiatsu").select("*").execute()
            for u in user_list.data:
                skill = u.get("active_skill")
                if skill and skill.get("type") == "faux" and str(payload.message_id) == skill.get("spawn_id"):
                    owner_id = skill.get("owner_id")
                    owner = guild.get_member(int(owner_id))
                    if owner:
                        owner_data = supabase.table("reiatsu").select("points").eq("user_id", owner_id).single().execute()
                        if owner_data.data:
                            new_points = owner_data.data["points"] + 10
                            supabase.table("reiatsu").update({"points": new_points}).eq("user_id", owner_id).execute()
                        await safe_send(channel, f"🎭 Le faux Reiatsu a été absorbé par {user.mention}... {owner.mention} gagne **+10** points !")
                    supabase.table("reiatsu").update({"active_skill": None}).eq("user_id", u["user_id"]).execute()
                    supabase.table("reiatsu_config").update({"faux_en_attente": False}).eq("guild_id", guild_id).execute()
                    await safe_delete(await channel.fetch_message(payload.message_id))
                    return

            # 🔹 Reiatsu normal
            if not conf.get("en_attente") or str(payload.message_id) != conf.get("spawn_message_id"):
                return

            gain, is_super, bonus5, classe, new_total = self._calculate_gain(user.id)
            self._update_player(user, gain, bonus5, new_total, classe)
            await self._send_feedback(channel, user, gain, is_super, classe)

            spawn_speed = conf.get("spawn_speed") or DEFAULT_SPAWN_SPEED
            min_delay, max_delay = SPAWN_SPEED_RANGES.get(spawn_speed, SPAWN_SPEED_RANGES[DEFAULT_SPAWN_SPEED])
            new_delay = random.randint(min_delay, max_delay)
            supabase.table("reiatsu_config").update({
                "en_attente": False,
                "spawn_message_id": None,
                "spawn_delay": new_delay
            }).eq("guild_id", guild_id).execute()

            spawn_message_id = conf.get("spawn_message_id")
            if spawn_message_id:
                try:
                    message = await channel.fetch_message(int(spawn_message_id))
                    await safe_delete(message)
                except Exception:
                    pass

    def _calculate_gain(self, user_id):
        is_super = random.randint(1, 100) <= SUPER_REIATSU_CHANCE
        gain = SUPER_REIATSU_GAIN if is_super else NORMAL_REIATSU_GAIN
        user_data = supabase.table("reiatsu").select("classe", "points", "bonus5").eq("user_id", str(user_id)).execute()
        if user_data.data:
            classe = user_data.data[0].get("classe")
            current_points = user_data.data[0]["points"]
            bonus5 = user_data.data[0].get("bonus5", 0) or 0
        else:
            classe = "Travailleur"
            current_points = 0
            bonus5 = 0

        if not is_super:
            if classe == "Absorbeur":
                gain += 5
            elif classe == "Parieur":
                gain = 0 if random.random() < 0.5 else random.randint(5, 12)
            if classe == "Travailleur":
                bonus5 += 1
                if bonus5 >= 5:
                    gain = 6
                    bonus5 = 0
        else:
            bonus5 = 0
        return gain, is_super, bonus5, classe, current_points + gain

    def _update_player(self, user, gain, bonus5, new_total, classe):
        user_id = str(user.id)
        user_data = supabase.table("reiatsu").select("user_id").eq("user_id", user_id).execute()
        if user_data.data:
            supabase.table("reiatsu").update({"points": new_total, "bonus5": bonus5}).eq("user_id", user_id).execute()
        else:
            supabase.table("reiatsu").insert({
                "user_id": user_id,
                "username": user.name,
                "points": gain,
                "classe": classe,
                "bonus5": 1
            }).execute()

    async def _send_feedback(self, channel, user, gain, is_super, classe):
        if is_super:
            await safe_send(channel, f"🌟 {user.mention} a absorbé un **Super Reiatsu** et gagné **+{gain}** reiatsu !")
        else:
            if classe == "Parieur" and gain == 0:
                await safe_send(channel, f"🎲 {user.mention} a tenté d’absorber un reiatsu mais a raté (passif Parieur) !")
            else:
                await safe_send(channel, f"💠 {user.mention} a absorbé le Reiatsu et gagné **+{gain}** reiatsu !")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuSpawner(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
