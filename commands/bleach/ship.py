# ────────────────────────────────────────────────────────────────
# 📌 ship.py — Commande interactive /ship et !ship
# Objectif : Tester la compatibilité entre deux personnages de Bleach
# Catégorie : Bleach
# Accès : Public
# Cooldown : 1 utilisation / 3 secondes / utilisateur
# ────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, button
import json
import hashlib
import random
import asyncio

from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────
# 🧮 Fonction : Calcul du score de compatibilité
# ────────────────────────────────────────────────────────────────
def calculer_score(p1, p2):
    noms_ordonnes = sorted([p1["nom"], p2["nom"]])
    clef = f"{noms_ordonnes[0]}+{noms_ordonnes[1]}"
    hash_bytes = hashlib.md5(clef.encode()).digest()
    score = int.from_bytes(hash_bytes, 'big') % 101

    if p1.get("genre") != p2.get("genre"):
        score += 5

    races_p1 = set(p1.get("races", []))
    races_p2 = set(p2.get("races", []))
    if not races_p1 & races_p2:
        score -= 10

    stats1 = list(p1["stats"].values())
    stats2 = list(p2["stats"].values())
    avg1 = sum(stats1) / len(stats1)
    avg2 = sum(stats2) / len(stats2)
    diff = abs(avg1 - avg2)

    if diff <= 2:
        score += 5
    elif diff >= 6:
        score -= 10

    return max(0, min(score, 100))

# ────────────────────────────────────────────────────────────────
# 🎛️ Vue interactive : Bouton Nouveau Ship
# ────────────────────────────────────────────────────────────────
class ShipView(View):
    def __init__(self, persos, message=None):
        super().__init__(timeout=60)
        self.persos = persos
        self.message = message

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await safe_edit(self.message, view=self)
            except Exception:
                pass

    @button(label="💘 Nouveau ship", style=discord.ButtonStyle.blurple)
    async def nouveau_ship(self, interaction: discord.Interaction, button: discord.ui.Button):
        p1, p2 = random.sample(self.persos, 2)
        await self._send_result(interaction, p1, p2)

    async def _send_result(self, interaction, p1, p2):
        score = calculer_score(p1, p2)

        if score >= 90:
            reaction = "âmes sœurs 💞"
            color = discord.Color.magenta()
        elif score >= 70:
            reaction = "une excellente alchimie spirituelle ! 🔥"
            color = discord.Color.red()
        elif score >= 50:
            reaction = "une belle entente possible 🌸"
            color = discord.Color.orange()
        elif score >= 30:
            reaction = "relation instable... mais pas impossible 😬"
            color = discord.Color.yellow()
        else:
            reaction = "aucune chance... ils sont de mondes opposés 💔"
            color = discord.Color.blue()

        embed = discord.Embed(
            title="💘 Test de compatibilité 💘",
            color=color
        )
        embed.add_field(name="👩‍❤️‍👨 Couple", value=f"**{p1['nom']}** ❤️ **{p2['nom']}**", inline=False)
        embed.add_field(name="🔢 Taux d’affinité", value=f"`{score}%`", inline=True)
        embed.add_field(name="💬 Verdict", value=f"*{reaction}*", inline=False)

        if "image" in p1:
            embed.set_thumbnail(url=p1["image"])
        if "image" in p2:
            embed.set_image(url=p2["image"])

        await interaction.response.edit_message(embed=embed, view=self)

# ────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────
class ShipCommand(commands.Cog):
    """
    Commande /ship et !ship — Tire au sort deux personnages de Bleach et calcule leur compatibilité
    """
    def __init__(self, bot):
        self.bot = bot

    async def _send_ship(self, channel: discord.abc.Messageable, user=None):
        try:
            with open("data/bleach_personnages.json", "r", encoding="utf-8") as f:
                persos = json.load(f)

            if len(persos) < 2:
                await safe_send(channel, "❌ Il faut au moins **deux personnages** pour créer une romance.")
                return

            p1, p2 = random.sample(persos, 2)
            score = calculer_score(p1, p2)

            if score >= 90:
                reaction = "âmes sœurs 💞"
                color = discord.Color.magenta()
            elif score >= 70:
                reaction = "une excellente alchimie spirituelle ! 🔥"
                color = discord.Color.red()
            elif score >= 50:
                reaction = "une belle entente possible 🌸"
                color = discord.Color.orange()
            elif score >= 30:
                reaction = "relation instable... mais pas impossible 😬"
                color = discord.Color.yellow()
            else:
                reaction = "aucune chance... ils sont de mondes opposés 💔"
                color = discord.Color.blue()

            # Animation d'analyse
            barre = ["⏳", "💞"]
            loading_msg = await safe_send(channel, "Analyse en cours... " + barre[0])
            for emoji in barre[1:]:
                await asyncio.sleep(1)
                await safe_edit(loading_msg, content=f"Analyse en cours... {emoji}")
            await asyncio.sleep(1.5)

            embed = discord.Embed(
                title="💘 Test de compatibilité 💘",
                color=color
            )
            embed.add_field(name="👩‍❤️‍👨 Couple", value=f"**{p1['nom']}** ❤️ **{p2['nom']}**", inline=False)
            embed.add_field(name="🔢 Taux d’affinité", value=f"`{score}%`", inline=True)
            embed.add_field(name="💬 Verdict", value=f"*{reaction}*", inline=False)

            if "image" in p1:
                embed.set_thumbnail(url=p1["image"])
            if "image" in p2:
                embed.set_image(url=p2["image"])

            view = ShipView(persos)
            message = await safe_edit(loading_msg, content=None, embed=embed, view=view)
            view.message = message

        except FileNotFoundError:
            await safe_send(channel, "❌ Le fichier `bleach_personnages.json` est introuvable. Impossible de procéder au *shipping*.")
        except Exception as e:
            await safe_send(channel, f"⚠️ Une erreur est survenue : `{e}`")

    # ──────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ──────────────────────────────────────────────────────────
    @app_commands.command(
        name="ship",
        description="💘 Teste la compatibilité entre deux personnages de Bleach."
    )
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def slash_ship(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._send_ship(interaction.channel, user=interaction.user)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /ship] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ──────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="ship"
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def prefix_ship(self, ctx: commands.Context):
        try:
            await self._send_ship(ctx.channel, user=ctx.author)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !ship] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ShipCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
