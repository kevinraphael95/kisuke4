# ────────────────────────────────────────────────────────────────────────────────
# 📌 skill.py — Commande simple /skill et !skill
# Objectif : Utiliser la compétence active de la classe du joueur avec cooldown
# Catégorie : Reiatsu
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import random
from datetime import datetime, timezone, timedelta
import discord
from discord import app_commands
from discord.ext import commands
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_followup

# Cooldowns par classe (en secondes)
CLASS_CD = {
    "Travailleur": 0,
    "Voleur": 12 * 3600,
    "Absorbeur": 12 * 3600,
    "Illusionniste": 8 * 3600,
    "Parieur": 12 * 3600
}

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Skill(commands.Cog):
    """
    Commande /skill et !skill — Active la compétence spécifique de la classe du joueur avec cooldown
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("[COG LOAD] Skill cog chargé ✅")

    # 🔹 Fonction interne commune
    async def _execute_skill(self, user_id: str, ctx_or_interaction=None):
        try:
            response = supabase.table("reiatsu").select("*").eq("user_id", user_id).single().execute()
            data = getattr(response, "data", None)
        except Exception as e:
            print(f"[ERREUR SUPABASE] {e}")
            return "❌ Impossible de récupérer les données."

        if not data:
            return "❌ Tu n'as pas encore commencé l'aventure. Utilise `!start`."

        classe = data.get("classe", "Travailleur")
        reiatsu = data.get("points", 0)
        last_skill = data.get("last_skill")
        skill_cd = data.get("skill_cd", 0)
        now = datetime.now(timezone.utc)

        # ⏳ Cooldown
        if last_skill:
            elapsed = (now - datetime.fromisoformat(last_skill)).total_seconds()
            if elapsed < skill_cd:
                remaining = timedelta(seconds=int(skill_cd - elapsed))
                return f"⏳ Compétence encore en recharge ! Temps restant : **{remaining}**"

        updated_fields = {}
        result_message = ""

        # ────── Gestion des compétences par classe ──────
        if classe == "Travailleur":
            result_message = "💼 Tu es Travailleur : pas de compétence active."
            new_cd = 0

        elif classe == "Voleur":
            updated_fields["vol_garanti"] = True
            result_message = "🥷 Ton prochain vol sera garanti."
            new_cd = CLASS_CD["Voleur"]

        elif classe == "Absorbeur":
            updated_fields["prochain_reiatsu"] = 100
            result_message = "🌀 Ton prochain Reiatsu absorbé sera un Super Reiatsu (100 points)."
            new_cd = CLASS_CD["Absorbeur"]

        elif classe == "Illusionniste":
            # Marquer en DB qu’un faux Reiatsu doit être créé par le spawner
            updated_fields["active_skill"] = {
                "type": "faux",
                "owner_id": user_id,
                "spawn_id": None,
                "created_at": now.isoformat()
            }
            updated_fields["faux_block_user"] = user_id
            result_message = "🎭 Ton pouvoir Illusionniste est activé ! Un faux Reiatsu apparaîtra bientôt..."
            new_cd = CLASS_CD["Illusionniste"]

            # Supprimer le message de commande pour effacer les traces
            if ctx_or_interaction:
                try:
                    if isinstance(ctx_or_interaction, commands.Context):
                        await ctx_or_interaction.message.delete()
                    elif isinstance(ctx_or_interaction, discord.Interaction):
                        if ctx_or_interaction.response.is_done():
                            await ctx_or_interaction.delete_original_response()
                        else:
                            await ctx_or_interaction.response.defer()
                            await ctx_or_interaction.delete_original_response()
                except Exception:
                    pass

        elif classe == "Parieur":
            if reiatsu < 10:
                return "❌ Tu n'as pas assez de Reiatsu pour parier (10 requis)."
            new_points = reiatsu - 10
            if random.random() < 0.5:
                new_points += 30
                result_message = "🎲 Tu as misé 10 Reiatsu et gagné 30 !"
            else:
                result_message = "🎲 Tu as misé 10 Reiatsu et perdu."
            updated_fields["points"] = new_points
            new_cd = CLASS_CD["Parieur"]

        # Ajout cooldown
        updated_fields["last_skill"] = now.isoformat()
        updated_fields["skill_cd"] = new_cd

        # 🔹 Update sécurisé Supabase
        try:
            response = supabase.table("reiatsu").upsert({**data, **updated_fields}, on_conflict="user_id").execute()
            if getattr(response, "status_code", 200) >= 400:
                return "❌ Impossible de mettre à jour les données (Supabase a renvoyé une erreur)."
        except Exception as e:
            print(f"[ERREUR SUPABASE UPDATE] {e}")
            return "❌ Impossible de mettre à jour les données."

        return result_message

    # 🔹 Commande SLASH
    @app_commands.command(
        name="skill",
        description="Active la compétence spécifique de ta classe avec cooldown."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_skill(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            message = await self._execute_skill(str(interaction.user.id), interaction)
            await safe_followup(interaction, message)
        except app_commands.CommandOnCooldown as e:
            await safe_followup(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /skill] {e}")
            await safe_followup(interaction, "❌ Une erreur est survenue.")

    # 🔹 Commande PREFIX
    @commands.command(name="skill")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_skill(self, ctx: commands.Context):
        try:
            message = await self._execute_skill(str(ctx.author.id), ctx)
            await safe_send(ctx.channel, message)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !skill] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Skill(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
    print("[COG SETUP] Skill cog ajouté ✅")
