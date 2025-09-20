# ────────────────────────────────────────────────────────────────────────────────
# 📌 say_as.py — Commande interactive /say_as et !say_as
# Objectif : Faire répéter un message par le bot comme si c'était un autre membre (mention, ID ou pseudo)
# Catégorie : Administration
# Accès : Admin uniquement
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
class SayAs(commands.Cog):
    """Commande interactive /say_as et !say_as — Fait répéter un message par le bot comme si c'était un autre membre"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction utilitaire : résolution d’utilisateur
    # ────────────────────────────────────────────────────────────────────────────
    async def resolve_user(self, guild: discord.Guild, query: str):
        """Résout un membre ou utilisateur à partir d’une mention, d’un ID ou d’un pseudo"""
        member = None

        # Mention <@123456789>
        mention_match = re.match(r"<@!?(\d+)>", query)
        if mention_match:
            user_id = int(mention_match.group(1))
            member = guild.get_member(user_id)

        # ID numérique
        elif query.isdigit():
            member = guild.get_member(int(query))

        # Pseudo
        else:
            member = discord.utils.find(
                lambda m: m.name.lower() == query.lower() or m.display_name.lower() == query.lower(),
                guild.members
            )

        # Fallback API
        if member is None:
            try:
                member = await self.bot.fetch_user(int(query))
            except Exception:
                pass

        return member

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_as(self, channel: discord.TextChannel, target: discord.abc.User, message: str):
        """Envoie un message via webhook en utilisant le pseudo (serveur ou global) et avatar du membre cible"""
        message = (message or "").strip()
        if not message:
            return await safe_send(channel, "⚠️ Message vide.")

        # Remplacement des emojis custom du serveur 
        if hasattr(channel, "guild"):
            guild_emojis = {e.name.lower(): str(e) for e in channel.guild.emojis}

            def replace_emoji(match):
                return guild_emojis.get(match.group(1).lower(), match.group(0))

            message = re.sub(r":([a-zA-Z0-9_]+):", replace_emoji, message, flags=re.IGNORECASE)

        # Limite Discord
        if len(message) > 2000:
            message = message[:1997] + "..."

        # Création d'un webhook temporaire
        webhook = await channel.create_webhook(name=f"tmp-{target.name}")
        try:
            await webhook.send(
                content=message,
                username=target.display_name,
                avatar_url=target.display_avatar.url
            )
        finally:
            await webhook.delete()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="say_as",
        description="(Admin) Fait répéter un message par le bot comme si c'était un autre membre."
    )
    @app_commands.describe(user="Membre ciblé (mention, ID ou pseudo)", message="Message à répéter")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_say_as(self, interaction: discord.Interaction, user: str, *, message: str):
        try:
            await interaction.response.defer(ephemeral=True)
            target = await self.resolve_user(interaction.guild, user)
            if target is None:
                return await safe_respond(interaction, "❌ Membre introuvable.", ephemeral=True)

            await self._send_as(interaction.channel, target, message)
            await safe_respond(interaction, f"✅ Message envoyé en tant que **{target.display_name}**.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /say_as] {e}")
            await safe_respond(interaction, "❌ Impossible d’envoyer le message.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="say_as",
        aliases=["sa"],
        help="(Admin) Fait répéter un message par le bot comme si c'était un autre membre.\n"
             "Usage: !say_as <mention|id|pseudo> <message>"
    )
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_say_as(self, ctx: commands.Context, user: str, *, message: str):
        try:
            target = await self.resolve_user(ctx.guild, user)
            if target is None:
                return await safe_send(ctx.channel, "❌ Membre introuvable.")

            await self._send_as(ctx.channel, target, message)
        except Exception as e:
            print(f"[ERREUR !say_as] {e}")
            await safe_send(ctx.channel, "❌ Impossible d’envoyer le message.")
        finally:
            await safe_delete(ctx.message)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SayAs(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
