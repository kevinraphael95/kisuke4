# ────────────────────────────────────────────────────────────────
# 📌 kluboutside.py — Commande interactive /kluboutside et !kluboutside / !ko
# Objectif : Afficher une question Klub Outside par numéro, aléatoire ou paginer toutes
# Catégorie : Bleach
# Accès : Public
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View
import json
import os
import random

from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────
KO_DATA_PATH = os.path.join("data", "ko.json")
KO_IMAGE_DIR = os.path.join("data", "images", "kluboutside")

def load_data():
    """Charge le fichier JSON contenant les questions Klub Outside."""
    try:
        with open(KO_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {KO_DATA_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────
# 🎛️ UI — Pagination interactive
# ────────────────────────────────────────────────────────────────
class KlubPaginator(View):
    def __init__(self, user, data):
        super().__init__(timeout=60)
        self.user = user
        self.data = data
        self.keys = list(data.get("Questions", {}).keys())
        self.index = 0

    async def send_embed(self, interaction: discord.Interaction):
        key = self.keys[self.index]
        question = self.data["Questions"][key]

        embed = discord.Embed(
            title=f"📓 Question Klub Outside n°{key}",
            color=discord.Color.dark_green()
        )
        embed.add_field(name="📅 Date", value=question.get("date", "?"), inline=False)
        embed.add_field(name="❓ Question", value=question.get("question", "?"), inline=False)
        embed.add_field(name="💬 Réponse", value=question.get("réponse", "?"), inline=False)
        embed.set_footer(text=f"{self.index+1} / {len(self.keys)}")

        image_path = self._find_image_file(key)
        if image_path:
            file = discord.File(image_path, filename=os.path.basename(image_path))
            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
            await interaction.response.edit_message(embed=embed, view=self, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    def _find_image_file(self, key):
        for ext in ["png", "jpg", "jpeg", "webp"]:
            path = os.path.join(KO_IMAGE_DIR, f"ko{key}.{ext}")
            if os.path.exists(path):
                return path
        return None

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return await interaction.response.send_message("❌ Ce défi ne t'est pas destiné.", ephemeral=True)
        if self.index > 0:
            self.index -= 1
            await self.send_embed(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return await interaction.response.send_message("❌ Ce défi ne t'est pas destiné.", ephemeral=True)
        if self.index < len(self.keys) - 1:
            self.index += 1
            await self.send_embed(interaction)

    @discord.ui.button(label="🔀 Aléatoire", style=discord.ButtonStyle.primary)
    async def random_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return await interaction.response.send_message("❌ Ce défi ne t'est pas destiné.", ephemeral=True)
        self.index = random.randint(0, len(self.keys) - 1)
        await self.send_embed(interaction)

# ────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────
class KlubOutside(commands.Cog):
    """
    Commande /kluboutside et !kluboutside / !ko — Affiche une question de la FAQ du Klub Outside
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ──────────────────────────────────────────────────────────
    async def _send_menu(self, channel: discord.abc.Messageable, user=None, argument: str = None):
        data = load_data()
        if not data or "Questions" not in data:
            await safe_send(channel, "❌ Impossible de charger les questions.")
            return

        keys = list(data["Questions"].keys())
        if not keys:
            await safe_send(channel, "❌ Aucune question disponible.")
            return

        # Déterminer l'index de départ
        if argument is None:
            start_index = 0
        elif argument.lower() == "random":
            start_index = random.randint(0, len(keys) - 1)
        elif argument.isdigit():
            numero = argument
            if numero not in keys:
                await safe_send(channel, f"❌ Aucune question trouvée pour le numéro {numero}.")
                return
            start_index = keys.index(numero)
        else:
            await safe_send(channel, f"❌ Argument non reconnu : `{argument}`. Utilise un numéro ou `random`.")
            return

        view = KlubPaginator(user or channel, data)
        view.index = start_index
        key = view.keys[start_index]
        question = data["Questions"][key]

        embed = discord.Embed(
            title=f"📓 Question Klub Outside n°{key}",
            color=discord.Color.dark_green()
        )
        embed.add_field(name="📅 Date", value=question.get("date", "?"), inline=False)
        embed.add_field(name="❓ Question", value=question.get("question", "?"), inline=False)
        embed.add_field(name="💬 Réponse", value=question.get("réponse", "?"), inline=False)
        embed.set_footer(text=f"{start_index+1} / {len(view.keys)}")

        image_path = view._find_image_file(key)
        if image_path:
            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
            file = discord.File(image_path, filename=os.path.basename(image_path))
            await safe_send(channel, embed=embed, view=view, file=file)
        else:
            await safe_send(channel, embed=embed, view=view)

    # ──────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ──────────────────────────────────────────────────────────
    @app_commands.command(
        name="kluboutside",
        description="Affiche une question de la FAQ du Klub Outside."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_kluboutside(self, interaction: discord.Interaction, argument: str = None):
        try:
            await interaction.response.defer()
            await self._send_menu(interaction.channel, user=interaction.user, argument=argument)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /kluboutside] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ──────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="kluboutside",
        aliases=["ko"]
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def prefix_kluboutside(self, ctx: commands.Context, *, argument: str = None):
        try:
            await self._send_menu(ctx.channel, user=ctx.author, argument=argument)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !kluboutside] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = KlubOutside(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
