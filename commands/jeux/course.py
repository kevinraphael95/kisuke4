# ────────────────────────────────────────────────────────────────────────────────
# 📌 animal_race.py — Mini-jeu de course d'animaux ultra-animé
# Objectif : Lancer une course animée entre plusieurs animaux avec mouvements fluides
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from utils.discord_utils import safe_send, safe_respond, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class AnimalRace(commands.Cog):
    """
    Commande /animal_race et !animal_race — Mini-jeu animé de course d'animaux avec mouvements fluides
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.animals = ["🐶", "🐱", "🐰", "🐢", "🐹", "🐴"]
        self.track_length = 20  # longueur de la piste

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne pour créer la piste
    # ────────────────────────────────────────────────────────────────────────────
    def render_track(self, positions):
        lines = []
        for animal, pos in positions.items():
            pos = min(pos, self.track_length)
            track = "─" * pos + animal + "─" * (self.track_length - pos) + " |🏁"
            lines.append(track)
        return "\n".join(lines)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne pour lancer la course
    # ────────────────────────────────────────────────────────────────────────────
    async def run_race(self, channel: discord.abc.Messageable):
        positions = {animal: 0 for animal in self.animals}
        speeds = {animal: random.uniform(0.5, 1.5) for animal in self.animals}  # vitesse initiale
        message = await safe_send(channel, "🏁 La course commence ! Préparez-vous...\n")
        winner = None

        while not winner:
            await asyncio.sleep(0.5)  # mouvement fluide
            for animal in self.animals:
                # chaque animal avance entre 1 et 3 cases, multiplié par sa vitesse
                advance = int(random.randint(1, 3) * speeds[animal])
                positions[animal] += advance
                if positions[animal] >= self.track_length and not winner:
                    winner = animal

            track_text = self.render_track(positions)
            await safe_edit(message, f"🏁 **Course en cours :**\n{track_text}")

        # Message final avec célébration
        celebration = {
            "🐶": "🎉 Le chien fonce vers la gloire !",
            "🐱": "🎉 Le chat agile remporte la victoire !",
            "🐰": "🎉 Le lapin bondissant gagne la course !",
            "🐢": "🎉 La tortue tenace franchit la ligne d’arrivée !",
            "🐹": "🎉 Le hamster rapide est le champion !",
            "🐴": "🎉 Le cheval puissant triomphe !"
        }
        await safe_edit(
            message,
            f"🏆 **Course terminée !** Le gagnant est **{winner}** !\n{celebration.get(winner, '')}"
        )

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="course",
        description="Lance une course animée entre plusieurs animaux et affiche le gagnant."
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.user.id))
    async def slash_animal_race(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self.run_race(interaction.channel)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /animal_race] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="course")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_animal_race(self, ctx: commands.Context):
        try:
            await self.run_race(ctx.channel)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !animal_race] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = AnimalRace(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
