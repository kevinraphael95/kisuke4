# ────────────────────────────────────────────────────────────────────────────────
# 📌 volreiatsu.py — Commande interactive /volreiatsu et !volreiatsu
# Objectif : Permet de voler 10% du Reiatsu d’un autre joueur avec probabilité de réussite
# Catégorie : Reiatsu
# Accès : Public
# Cooldown : 1 utilisation / 24h / utilisateur (persistant via Supabase)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond  
import random

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuVol(commands.Cog):
    """
    Commande /volreiatsu et !volreiatsu — Tente de voler du Reiatsu à un autre joueur
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _volreiatsu_logic(self, voleur: discord.Member, cible: discord.Member, channel: discord.abc.Messageable):
        voleur_id = str(voleur.id)
        cible_id = str(cible.id)

        # 📥 Récupération des données voleur
        voleur_data = supabase.table("reiatsu").select("*").eq("user_id", voleur_id).execute()
        if not voleur_data.data:
            await safe_send(channel, "⚠️ Données introuvables pour toi.")
            return
        voleur_data = voleur_data.data[0]

        voleur_classe = voleur_data.get("classe")
        voleur_cd = voleur_data.get("steal_cd", 24)
        now = datetime.utcnow()
        dernier_vol_str = voleur_data.get("last_steal_attempt")

        if dernier_vol_str:
            dernier_vol = datetime.fromisoformat(dernier_vol_str)
            prochain_vol = dernier_vol + timedelta(hours=voleur_cd)
            if now < prochain_vol:
                restant = prochain_vol - now
                j = restant.days
                h, m = divmod(restant.seconds // 60, 60)
                await safe_send(channel, f"⏳ Tu dois encore attendre **{j}j {h}h{m}m** avant de retenter.")
                return

        # 📥 Récupération des données cible
        cible_data = supabase.table("reiatsu").select("*").eq("user_id", cible_id).execute()
        if not cible_data.data:
            await safe_send(channel, "⚠️ Données introuvables pour la cible.")
            return
        cible_data = cible_data.data[0]

        voleur_points = voleur_data.get("points", 0)
        cible_points = cible_data.get("points", 0)
        cible_classe = cible_data.get("classe")

        if cible_points == 0:
            await safe_send(channel, f"⚠️ {cible.mention} n’a pas de Reiatsu à voler.")
            return
        if voleur_points == 0:
            await safe_send(channel, "⚠️ Tu dois avoir au moins **1 point** de Reiatsu pour tenter un vol.")
            return

        # 🎲 Calcul du vol
        montant = max(1, cible_points // 10)  # 10%

        # 🔹 Si voleur a activé son skill → vol garanti
        skill_actif = voleur_data.get("vol_garanti", False)

        if skill_actif:
            succes = True
            # On désactive le skill après utilisation
            supabase.table("reiatsu").update({"vol_garanti": False}).eq("user_id", voleur_id).execute()
        else:
            # Voleur normal
            if voleur_classe == "Voleur":
                succes = random.random() < 0.67
                if random.random() < 0.15:  # 15% de chance de doubler le gain
                    montant *= 2
            else:
                succes = random.random() < 0.25

        # Préparation du payload voleur
        payload_voleur = {"last_steal_attempt": now.isoformat()}

        if succes:
            payload_voleur["points"] = voleur_points + montant
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()

            if cible_classe == "Illusionniste" and random.random() < 0.5:
                await safe_send(channel, f"🩸 {voleur.mention} a volé **{montant}** points à {cible.mention}... mais c'était une illusion, {cible.mention} n'a rien perdu !")
            else:
                supabase.table("reiatsu").update({
                    "points": max(0, cible_points - montant)
                }).eq("user_id", cible_id).execute()
                await safe_send(channel, f"🩸 {voleur.mention} a réussi à voler **{montant}** points de Reiatsu à {cible.mention} !")
        else:
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()
            await safe_send(channel, f"😵 {voleur.mention} a tenté de voler {cible.mention}... mais a échoué !")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="reiatsuvol",
        description="💠 Tente de voler 10% du Reiatsu d’un autre membre (25% de réussite). Cooldown : 24h."
    )
    async def slash_volreiatsu(self, interaction: discord.Interaction, cible: discord.Member):
        """Commande slash pour voler du Reiatsu."""
        try:
            await interaction.response.defer()
            if interaction.user.id == cible.id:
                await safe_respond(interaction, "❌ Tu ne peux pas te voler toi-même.", ephemeral=True)
                return
            await self._volreiatsu_logic(interaction.user, cible, interaction.channel)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /reiatsuvol] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="reiatsuvol",
        aliases=["rtsv", "volreiatsu", "vrts"],
        help="💠 Tente de voler 10% du Reiatsu d’un autre membre. 25% de réussite. Cooldown : 24h."
    )
    async def prefix_volreiatsu(self, ctx: commands.Context, cible: discord.Member = None):
        """Commande préfixe pour voler du Reiatsu."""
        try:
            if not cible:
                await safe_send(ctx.channel, "ℹ️ Utilisation : `!reiatsuvol @membre`")
                return
            if ctx.author.id == cible.id:
                await safe_send(ctx.channel, "❌ Tu ne peux pas te voler toi-même.")
                return
            await self._volreiatsu_logic(ctx.author, cible, ctx.channel)
        except Exception as e:
            print(f"[ERREUR !reiatsuvol] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuVol(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
