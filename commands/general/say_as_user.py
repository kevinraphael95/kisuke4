# ────────────────────────────────────────────────────────────────────────────────
# 📌 say_as_user.py — Commande interactive /say_as_user et !say_as_user
# Objectif : Faire répéter un message par le bot comme si c'était l'utilisateur
# Catégorie : Général
# Accès : Public
# Cooldown : 1 utilisation / 5 sec / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
import re
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_delete, safe_respond  

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class SayAsUser(commands.Cog):
    """Commande interactive /say_as_user et !say_as_user — Fait répéter un message par le bot comme si c'était l'utilisateur"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_as_user(self, channel: discord.TextChannel, user: discord.User, message: str):
        """Envoie un message via webhook en utilisant le pseudo et avatar de l'utilisateur"""
        message = (message or "").strip()
        if not message:
            return await safe_send(channel, "⚠️ Message vide.")

        # Remplacement des emojis custom du serveur (case-insensible)
        if hasattr(channel, "guild"):
            guild_emojis = {e.name.lower(): str(e) for e in channel.guild.emojis}

            def replace_emoji(match):
                return guild_emojis.get(match.group(1).lower(), match.group(0))

            message = re.sub(r":([a-zA-Z0-9_]+):", replace_emoji, message, flags=re.IGNORECASE)


        # Limite Discord
        if len(message) > 2000:
            message = message[:1997] + "..."

        # Création d'un webhook temporaire
        webhook = await channel.create_webhook(name=f"tmp-{user.name}")
        try:
            await webhook.send(
                content=message,
                username=user.display_name,
                avatar_url=user.display_avatar.url
            )
        finally:
            await webhook.delete()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="say_as_user",
        description="Fait répéter un message par le bot comme si c'était vous."
    )
    @app_commands.describe(message="Message à répéter")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_say_as_user(self, interaction: discord.Interaction, *, message: str):
        try:
            await interaction.response.defer()
            await self._send_as_user(interaction.channel, interaction.user, message)
            await safe_respond(interaction, "✅ Message envoyé !", ephemeral=True)
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /say_as_user] {e}")
            await safe_respond(interaction, "❌ Impossible d’envoyer le message.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="say_as_user",
        aliases=["sau"],
        help="Fait répéter un message par le bot comme si c'était vous."
    )
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_say_as_user(self, ctx: commands.Context, *, message: str):
        try:
            await self._send_as_user(ctx.channel, ctx.author, message)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !say_as_user] {e}")
            await safe_send(ctx.channel, "❌ Impossible d’envoyer le message.")
        finally:
            await safe_delete(ctx.message)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SayAsUser(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
