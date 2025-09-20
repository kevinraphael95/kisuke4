# ───────────────────────────────────────────────────────────────────────
# 📌 kido_command.py — Commande interactive !kido
# Objectif : Lancer un sort de Kidō avec animation et incantation
# Catégorie : Bleach
# Accès : Public
# ───────────────────────────────────────────────────────────────────────

# ───────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ───────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
import json, os

from utils.discord_utils import safe_send

# ───────────────────────────────────────────────
# 📂 Données Kidō
# ───────────────────────────────────────────────
KIDO_FILE = os.path.join("data", "kido.json")

def load_kido_data():
    with open(KIDO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ───────────────────────────────────────────────
# 🔁 Pagination
# ───────────────────────────────────────────────
class KidoPaginator(discord.ui.View):
    def __init__(self, user, pages):
        super().__init__(timeout=60)
        self.user = user
        self.pages = pages
        self.index = 0

    async def update_message(self, interaction):
        embed = self.pages[self.index]
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return await interaction.response.send_message("❌ Tu ne peux pas interagir avec cette pagination.", ephemeral=True)
        if self.index > 0:
            self.index -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return await interaction.response.send_message("❌ Tu ne peux pas interagir avec cette pagination.", ephemeral=True)
        if self.index < len(self.pages) - 1:
            self.index += 1
            await self.update_message(interaction)

# ───────────────────────────────────────────────
# 🧠 Cog principal
# ───────────────────────────────────────────────
class Kido(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ───────────────────────────────────────
    # 📌 Fonction unique commune
    # ───────────────────────────────────────
    async def _run_kido(self, target, type_kido: str = None, numero: int = None):
        try:
            data = load_kido_data()

            # ➤ Liste des sorts
            if type_kido is None and numero is None:
                all_sorts = []
                for kido_type, sorts in data.items():
                    for sort in sorts:
                        all_sorts.append(f"`{kido_type.title()} {sort['numero']}` — {sort['nom']}")

                pages = []
                for i in range(0, len(all_sorts), 15):
                    embed = discord.Embed(
                        title="📘 Liste des sorts de Kidō",
                        description="\n".join(all_sorts[i:i+15]),
                        color=discord.Color.teal()
                    )
                    embed.set_footer(text=f"Page {i//15+1}/{(len(all_sorts)-1)//15+1}")
                    pages.append(embed)

                view = KidoPaginator(target.user if isinstance(target, discord.Interaction) else target.author, pages)
                if isinstance(target, discord.Interaction):
                    await target.response.send_message(embed=pages[0], view=view)
                else:
                    await safe_send(target.channel, embed=pages[0], view=view)
                return

            # ➤ Validation
            type_kido = type_kido.lower()
            if type_kido not in data:
                msg = f"❌ Type de Kidō inconnu : `{type_kido}`."
                if isinstance(target, discord.Interaction):
                    await target.response.send_message(msg, ephemeral=True)
                else:
                    await safe_send(target.channel, msg)
                return

            sort = next((k for k in data[type_kido] if k["numero"] == numero), None)
            if not sort:
                msg = f"❌ Aucun sort {type_kido} numéro {numero} trouvé."
                if isinstance(target, discord.Interaction):
                    await target.response.send_message(msg, ephemeral=True)
                else:
                    await safe_send(target.channel, msg)
                return

            # ────────────────────────
            nom = sort["nom"]
            incantation = sort.get("incantation")
            image = sort.get("image")

            # Chemin image locale (ex: data/images/kido/1Sai.gif)
            local_img = os.path.join("data", "images", "kido", f"{numero}{nom.replace(' ', '')}.gif")

            files = None
            if os.path.exists(local_img):
                # Attache le fichier et l’associe à l’embed
                file = discord.File(local_img, filename=os.path.basename(local_img))
                files = [file]
                image_url = f"attachment://{os.path.basename(local_img)}"
            else:
                # Sinon utilise l’image définie dans kido.json (si présente)
                image_url = image

            # 📈 Embed final
            embed = discord.Embed(
                title=f"{type_kido.title()} #{numero} — {nom}",
                description=f"**📜 Incantation :**\n*{incantation or 'Aucune incantation connue'}*",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="🎼 Lancé par",
                value=target.user.mention if isinstance(target, discord.Interaction) else target.author.mention,
                inline=False
            )
            if image_url:
                embed.set_image(url=image_url)

            # Envoi final
            if isinstance(target, discord.Interaction):
                await target.response.send_message(embed=embed, files=files)
            else:
                await safe_send(target.channel, embed=embed, files=files)

        except FileNotFoundError:
            err = "❌ Le fichier `kido.json` est introuvable."
            if isinstance(target, discord.Interaction):
                await target.response.send_message(err, ephemeral=True)
            else:
                await safe_send(target.channel, err)
        except Exception as e:
            err = f"⚠️ Erreur : `{e}`"
            if isinstance(target, discord.Interaction):
                await target.response.send_message(err, ephemeral=True)
            else:
                await safe_send(target.channel, err)

    # ───────────────────────────────────────
    # Commande préfixe
    # ───────────────────────────────────────
    @commands.command(name="kido", help="🎼 Lance un sort de Kidō ! Exemple: `!!kido bakudo 61`")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kido_prefix(self, ctx, type_kido: str = None, numero: int = None):
        await self._run_kido(ctx, type_kido, numero)

    # ───────────────────────────────────────
    # Slash command
    # ───────────────────────────────────────
    @app_commands.command(name="kido", description="🎼 Lance un sort de Kidō (Bleach).")
    @app_commands.describe(type_kido="Type de Kidō (Hadō, Bakudō...)", numero="Numéro du sort")
    async def kido_slash(self, interaction: discord.Interaction, type_kido: str = None, numero: int = None):
        await self._run_kido(interaction, type_kido, numero)


# ───────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ───────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Kido(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
