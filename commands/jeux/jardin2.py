# ────────────────────────────────────────────────────────────────────────────────
# 📌 jardin2.py — Jardin interactif (alternative)
# Objectif : Version alternative du jardin avec boutons pour chaque case (type calculatrice)
# Catégorie : Jeux
# Accès : Public
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import datetime
import random
import json

from utils.supabase_client import supabase
from utils.discord_utils import safe_send

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Config & Données
# ────────────────────────────────────────────────────────────────────────────────
with open("data/jardin_config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

DEFAULT_GRID = CONFIG["DEFAULT_GRID"]
FLEUR_EMOJIS = CONFIG["FLEUR_EMOJIS"]
FERTILIZE_PROBABILITY = CONFIG["FERTILIZE_PROBABILITY"]
FERTILIZE_COOLDOWN = datetime.timedelta(minutes=CONFIG["FERTILIZE_COOLDOWN_MINUTES"])
TABLE_NAME = "gardens"

# ────────────────────────────────────────────────────────────────────────────────
# 🛠️ Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
async def get_or_create_garden(user_id: int, username: str):
    """Récupère ou crée un jardin pour l’utilisateur"""
    res = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).execute()
    if res.data:
        return res.data[0]

    new_garden = {
        "user_id": user_id,
        "username": username,
        "garden_grid": DEFAULT_GRID.copy(),
        "inventory": {f: 0 for f in FLEUR_EMOJIS},
        "argent": 0,
        "armee": "",
        "last_fertilize": None
    }
    supabase.table(TABLE_NAME).insert(new_garden).execute()
    return new_garden


def pousser_fleurs(grid: list[str]) -> list[str]:
    """Fait pousser aléatoirement des fleurs sur la grille"""
    new_grid = []
    for line in grid:
        new_line = ""
        for c in line:
            if c == "🌱" and random.random() < FERTILIZE_PROBABILITY:
                _, emoji = random.choice(list(FLEUR_EMOJIS.items()))
                new_line += emoji
            else:
                new_line += c
        new_grid.append(new_line)
    return new_grid


# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Vue Jardin2
# ────────────────────────────────────────────────────────────────────────────────
class Jardin2View(discord.ui.View):
    def __init__(self, garden: dict, user_id: int):
        super().__init__(timeout=300)
        self.garden = garden
        self.user_id = user_id

        # 🔹 Boutons de la grille
        for row_idx, row in enumerate(self.garden["garden_grid"]):
            cells = [row[i:i+2] for i in range(0, len(row), 2)]
            for col_idx, cell in enumerate(cells):
                self.add_item(FlowerButton(row_idx, col_idx, cell, self))

        # 🔹 Ligne des commandes globales
        self.add_item(GlobalButton("💩", "engrais", self))
        self.add_item(GlobalButton("✂️", "couper", self))
        self.add_item(GlobalButton("🛍️", "inventaire", self))
        self.add_item(GlobalButton("⚗️", "alchimie", self))
        self.add_item(GlobalButton("💵", "magasin", self))

    # 🆕 Ajout des méthodes manquantes
    async def refresh(self, interaction: discord.Interaction):
        """Recharge le jardin avec une nouvelle vue"""
        new_view = Jardin2View(self.garden, self.user_id)
        await interaction.response.edit_message(
            content=self.format_garden(),
            view=new_view
        )

    def format_garden(self) -> str:
        """Affiche le jardin au format ASCII"""
        grid_display = "\n".join(
            "[" + "][".join([row[i:i+2] for i in range(0, len(row), 2)]) + "]"
            for row in self.garden["garden_grid"]
        )
        return (
            f"**🏡 Jardin de {self.garden['username']}**\n"
            "💩:engrais, ✂️:couper, 🛍️:inventaire, ⚗️:alchimie, 💵:magasin"
        )


# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Boutons individuels
# ────────────────────────────────────────────────────────────────────────────────
class FlowerButton(discord.ui.Button):
    def __init__(self, row: int, col: int, emoji: str, parent_view: Jardin2View):
        super().__init__(label=emoji, style=discord.ButtonStyle.secondary, row=row)
        self.row = row
        self.col = col
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        current = self.parent_view.garden["garden_grid"][self.row]
        char = current[self.col]

        # Couper une fleur (si ≠ 🌱)
        if char != "🌱":
            inv = self.parent_view.garden["inventory"]
            inv[char] = inv.get(char, 0) + 1
            row_list = list(current)
            row_list[self.col] = "🌱"
            self.parent_view.garden["garden_grid"][self.row] = "".join(row_list)

            supabase.table(TABLE_NAME).update({
                "garden_grid": self.parent_view.garden["garden_grid"],
                "inventory": self.parent_view.garden["inventory"]
            }).eq("user_id", self.parent_view.user_id).execute()

        await self.parent_view.refresh(interaction)


class GlobalButton(discord.ui.Button):
    def __init__(self, emoji: str, action: str, parent_view: Jardin2View):
        super().__init__(label=emoji, style=discord.ButtonStyle.green, row=4)
        self.action = action
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        if self.action == "engrais":
            now = datetime.datetime.now(datetime.timezone.utc)
            last = self.parent_view.garden.get("last_fertilize")
            if last and now < datetime.datetime.fromisoformat(last) + FERTILIZE_COOLDOWN:
                return await interaction.response.send_message("⏳ Engrais en cooldown !", ephemeral=True)

            self.parent_view.garden["garden_grid"] = pousser_fleurs(self.parent_view.garden["garden_grid"])
            self.parent_view.garden["last_fertilize"] = now.isoformat()
            supabase.table(TABLE_NAME).update({
                "garden_grid": self.parent_view.garden["garden_grid"],
                "last_fertilize": self.parent_view.garden["last_fertilize"]
            }).eq("user_id", self.parent_view.user_id).execute()

        # TODO : inventaire, alchimie, magasin

        await self.parent_view.refresh(interaction)


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Jardin2Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="jardin2")
    async def prefix_jardin2(self, ctx: commands.Context):
        garden = await get_or_create_garden(ctx.author.id, ctx.author.name)
        view = Jardin2View(garden, ctx.author.id)
        await safe_send(ctx.channel, content=view.format_garden(), view=view)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Jardin2Cog(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
