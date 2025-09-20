# ────────────────────────────────────────────────────────────────────────────────
# 📌 heartbeat_admin.py — Commande !heartbeat <pause|resume|status|set|unset>
# Objectif : Gérer tout le heartbeat via une seule commande
# Catégorie : Heartbeat
# Accès : Modérateur (permission admin requise)
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from utils.discord_utils import safe_send

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class HeartbeatAdmin(commands.Cog):
    """
    Commande !heartbeat — Gère le heartbeat automatique (pause, relance, statut, salon).
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.supabase = bot.supabase

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="heartbeat",
        aliases=["hb"],
        help="(Admin) Gère le heartbeat : pause, resume, status, set, unset.",
        description="Gère le heartbeat automatique (pause, relance, statut, salon)."
    )
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def heartbeat(self, ctx: commands.Context, action: str = None, channel: discord.TextChannel = None):
        """Commande préfixe pour gérer le heartbeat."""
        try:
            if not action:
                await safe_send(ctx, "❓ Utilisation : `!heartbeat pause|resume|status|set <#salon>|unset`")
                return

            action = action.lower()

            if action in ["pause", "p"]:
                self.supabase.table("bot_settings").upsert({
                    "key": "heartbeat_paused",
                    "value": "true"
                }).execute()
                await safe_send(ctx, "⏸️ Heartbeat mis en pause.")

            elif action in ["resume", "r"]:
                self.supabase.table("bot_settings").upsert({
                    "key": "heartbeat_paused",
                    "value": "false"
                }).execute()
                await safe_send(ctx, "▶️ Heartbeat relancé.")

            elif action in ["status", "stat", "s"]:
                res = self.supabase.table("bot_settings").select("value").eq("key", "heartbeat_paused").execute()
                paused = res.data and res.data[0]["value"].lower() == "true"
                status_msg = "🔴 Le heartbeat est **en pause**." if paused else "🟢 Le heartbeat est **actif**."
                await safe_send(ctx, status_msg)

            elif action == "set":
                if not channel:
                    await safe_send(ctx, "❌ Tu dois mentionner un salon. Exemple : `!heartbeat set #général`")
                    return
                self.supabase.table("bot_settings").upsert({
                    "key": "heartbeat_channel_id",
                    "value": str(channel.id)
                }).execute()
                heartbeat_cog = self.bot.get_cog("HeartbeatTask")
                if heartbeat_cog:
                    heartbeat_cog.heartbeat_channel_id = channel.id
                await safe_send(ctx, f"✅ Salon heartbeat défini : {channel.mention}")

            elif action == "unset":
                self.supabase.table("bot_settings").upsert({
                    "key": "heartbeat_channel_id",
                    "value": ""
                }).execute()
                heartbeat_cog = self.bot.get_cog("HeartbeatTask")
                if heartbeat_cog:
                    heartbeat_cog.heartbeat_channel_id = None
                await safe_send(ctx, "🗑️ Salon heartbeat supprimé.")

            else:
                await safe_send(ctx, "❌ Action inconnue. Utilise `pause`, `resume`, `status`, `set`, ou `unset`.")

        except commands.CommandOnCooldown as e:
            await safe_send(ctx, f"⏳ Attends encore {e.retry_after:.1f}s avant de réutiliser cette commande.")
        except Exception as e:
            print(f"[heartbeat:{action}] Erreur : {e}")
            await safe_send(ctx, "❌ Une erreur est survenue lors de l'action heartbeat.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HeartbeatAdmin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
