# ────────────────────────────────────────────────────────────────────────────────
# 📌 couleur.py — Commande interactive !couleur et /couleur
# Objectif : Afficher une couleur aléatoire avec ses codes HEX et RGB dans un embed Discord
# Catégorie : 🎨 Fun&Random
# Accès : Public
# Cooldown : 1 utilisation / 3 sec / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import random
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue interactive avec bouton "Nouvelle couleur"
# ────────────────────────────────────────────────────────────────────────────────
class CouleurView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author
        self.message = None

    def generer_embed(self):
        """Génère un embed avec une couleur aléatoire et son aperçu visuel."""
        code_hex = random.randint(0, 0xFFFFFF)
        hex_str = f"#{code_hex:06X}"
        r = (code_hex >> 16) & 0xFF
        g = (code_hex >> 8) & 0xFF
        b = code_hex & 0xFF
        rgb_str = f"({r}, {g}, {b})"
        image_url = f"https://dummyimage.com/700x200/{code_hex:06x}/{code_hex:06x}.png&text=+"
        embed = discord.Embed(
            title="🌈 Couleur aléatoire",
            description=f"🔹 **Code HEX** : `{hex_str}`\n🔸 **Code RGB** : `{rgb_str}`",
            color=code_hex
        )
        embed.set_image(url=image_url)
        return embed

    @discord.ui.button(label="🔁 Nouvelle couleur", style=discord.ButtonStyle.primary)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Tu ne peux pas utiliser ce bouton.", ephemeral=True)
            return
        try:
            new_embed = self.generer_embed()
            await safe_edit(interaction.message, embed=new_embed, view=self)
            await interaction.response.defer()
        except Exception as e:
            await safe_edit(interaction, content=f"❌ Erreur : {e}", view=None)

    async def on_timeout(self):
        """Désactive le bouton quand le délai est écoulé."""
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await safe_edit(self.message, view=self)
            except Exception:
                pass

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CouleurCommand(commands.Cog):
    """Commande !couleur et /couleur — Génère et affiche une couleur aléatoire avec codes HEX et RGB."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="couleur",
        description="Affiche une couleur aléatoire avec un aperçu visuel et ses codes HEX & RGB."
    )
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: (i.user.id))  # cooldown : 1 fois / 3s / utilisateur
    async def slash_couleur(self, interaction: discord.Interaction):
        try:
            view = CouleurView(interaction.user)
            embed = view.generer_embed()
        

            # Répond directement à l'interaction
            await interaction.response.send_message(embed=embed, view=view)
            view.message = await interaction.original_response()
        except Exception as e:
            print(f"[ERREUR /couleur] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue lors de la génération de la couleur.", ephemeral=True)


    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="couleur",
        help="🎨 Affiche une couleur aléatoire avec ses codes HEX et RGB.",
        description="Affiche une couleur aléatoire avec un aperçu visuel et ses codes HEX & RGB."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def prefix_couleur(self, ctx: commands.Context):
        try:
            view = CouleurView(ctx.author)
            embed = view.generer_embed()
 
            view.message = await safe_send(ctx, embed=embed, view=view)
        except Exception as e:
            print(f"[ERREUR !couleur] {e}")
            await safe_send(ctx, "❌ Une erreur est survenue lors de la génération de la couleur.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CouleurCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun&Random"
    await bot.add_cog(cog)
