# ────────────────────────────────────────────────────────────────────────────────
# 📌 eveil.py — Commande interactive /eveil et !eveil
# Objectif : Permet à un utilisateur de dépenser des points pour choisir un pouvoir
# Catégorie : RPG
# Accès : Public
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 💰 Coût de l'éveil (modifiable facilement)
# ────────────────────────────────────────────────────────────────────────────────
EVEIL_COST = 1

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu de sélection du pouvoir
# ────────────────────────────────────────────────────────────────────────────────
class EveilView(View):
    def __init__(self, user_id: str):
        super().__init__(timeout=120)
        self.user_id = user_id
        for pouvoir in ["Shinigami", "Hollow", "Quincy", "Fullbring"]:
            self.add_item(EveilButton(pouvoir, self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if hasattr(self, "message") and self.message:
            await self.message.edit(view=self)

class EveilButton(Button):
    def __init__(self, pouvoir, parent_view):
        super().__init__(label=pouvoir, style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.parent_view.user_id:
            return await interaction.response.send_message("❌ Tu ne peux pas utiliser ce bouton.", ephemeral=True)
        try:
            # Récupérer les données utilisateur dans la table 'reiatsu'
            user_data = supabase.table("reiatsu").select("*").eq("user_id", str(self.parent_view.user_id)).execute()
            if not user_data.data:
                return await safe_respond(interaction, "❌ Tu n'as pas de compte Reiatsu.", ephemeral=True)

            points = int(user_data.data[0]["points"])
            if points < EVEIL_COST:
                return await safe_respond(interaction, f"⛔ Tu n'as pas assez de points ({EVEIL_COST} requis).", ephemeral=True)

            # Déduire les points et enregistrer uniquement le pouvoir (sans toucher à 'classe')
            supabase.table("reiatsu").update({
                "points": points - EVEIL_COST,
                "pouvoir": self.label
            }).eq("user_id", str(self.parent_view.user_id)).execute()

            embed = discord.Embed(
                title="✨ Éveil réussi !",
                description=f"Tu as éveillé ton pouvoir : **{self.label}**.\n💰 Tu as dépensé {EVEIL_COST} reiatsu.",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            print(f"[ERREUR EveilButton] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Eveil(commands.Cog):
    """Commande /eveil et !eveil — Dépenser des points pour choisir un pouvoir"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_menu(self, ctx_or_interaction, user_id: str):
        view = EveilView(user_id)
        embed = discord.Embed(
            title="💠 Éveil",
            description=(
                f"Tu peux éveiller tes pouvoirs spirituels.\n"
                f"Choisis ton pouvoir. Coût : **{EVEIL_COST} points**."
            ),
            color=discord.Color.blue()
        )
        if isinstance(ctx_or_interaction, discord.Interaction):
            view.message = await ctx_or_interaction.response.send_message(embed=embed, view=view)
        else:
            view.message = await safe_send(ctx_or_interaction, embed=embed, view=view)

    @app_commands.command(name="eveil", description=f"💠 Dépenser {EVEIL_COST} points pour choisir un pouvoir")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_eveil(self, interaction: discord.Interaction):
        try:
            await self._send_menu(interaction, str(interaction.user.id))
        except Exception as e:
            print(f"[ERREUR /eveil] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="eveil")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def prefix_eveil(self, ctx: commands.Context):
        await self._send_menu(ctx, str(ctx.author.id))

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Eveil(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
