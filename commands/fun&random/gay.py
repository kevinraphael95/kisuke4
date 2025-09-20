# ────────────────────────────────────────────────────────────────────────────────
# 📌 gay.py — Commande simple /gay et !gay
# Objectif : Calcule un taux de gaytitude fixe et fun pour un utilisateur Discord
# Catégorie : 🌈 Fun&Random
# Accès : Tous
# Cooldown : 1 utilisation / 3 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import hashlib
import random
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonction utilitaire pour calculer le score et générer l'embed
# ────────────────────────────────────────────────────────────────────────────────
def calculer_gaytitude_embed(member: discord.Member) -> discord.Embed:
    user_id = str(member.id).encode()
    hash_val = hashlib.md5(user_id).digest()
    score = int.from_bytes(hash_val, "big") % 101

    filled = "█" * (score // 10)
    empty = "░" * (10 - (score // 10))
    bar = f"`{filled}{empty}`"

    niveaux = [
        {"min": 90, "emoji": "🌈", "titre": "Légende arc-en-ciel", "couleur": discord.Color.magenta(), "descriptions": [
            "Ton aura pourrait repeindre une Pride entière.",
            "Tu transformes chaque salle en comédie musicale.",
            "Ta playlist est légalement un drapeau."
        ]},
        {"min": 70, "emoji": "💖", "titre": "Icône de style", "couleur": discord.Color.pink(), "descriptions": [
            "Tu portes plus de motifs que Zara.",
            "Tu brilles sans filtre.",
            "Ton regard déclenche des coming-outs."
        ]},
        {"min": 50, "emoji": "🌀", "titre": "Curieux·se affirmé·e", "couleur": discord.Color.blurple(), "descriptions": [
            "Tu es une énigme en glitter.",
            "Explorateur·rice de toutes les vibes.",
            "Ton cœur a plus de bissections qu’un shōnen."
        ]},
        {"min": 30, "emoji": "🤔", "titre": "Questionnement doux", "couleur": discord.Color.gold(), "descriptions": [
            "Tu dis ‘non’ mais ton historique dit ‘peut-être’.",
            "Un mojito et tout peut basculer.",
            "T’as déjà dit ‘je suis fluide, genre dans l’humour’."
        ]},
        {"min": 0, "emoji": "📏", "titre": "Straight mode activé", "couleur": discord.Color.dark_gray(), "descriptions": [
            "Tu joues à FIFA et ça te suffit.",
            "Ton placard contient 50 tee-shirts gris.",
            "Même ton Wi-Fi est en ligne droite."
        ]}
    ]

    niveau = next(n for n in niveaux if score >= n["min"])
    commentaire = random.choice(niveau["descriptions"])

    embed = discord.Embed(
        title=f"{niveau['emoji']} {niveau['titre']}",
        description=commentaire,
        color=niveau["couleur"]
    )
    embed.set_author(name=f"Taux de gaytitude de {member.display_name}", icon_url=member.display_avatar.url)
    embed.add_field(name="📊 Pourcentage", value=f"**{score}%**", inline=True)
    embed.add_field(name="📈 Niveau", value=bar, inline=False)
    embed.set_footer(text="✨ C’est scientifique. Enfin presque.")

    return embed

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class GayCommand(commands.Cog):
    """Commande /gay et !gay — Calcule un taux de gaytitude fixe et fun."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="gay",
        description="🌈 Calcule ton taux de gaytitude."
    )
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)  # Cooldown 3s par utilisateur
    @app_commands.describe(member="Utilisateur pour qui calculer la gaytitude (optionnel)")
    async def slash_gay(self, interaction: discord.Interaction, member: discord.Member = None):
        try:
            member = member or interaction.user
            embed = calculer_gaytitude_embed(member)
            embed.timestamp = interaction.created_at
            await safe_respond(interaction, embed=embed)
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /gay] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="gay",
        help="🌈 Calcule ton taux de gaytitude."
    )
    @commands.cooldown(1, 3, commands.BucketType.user)  # Cooldown 3s par utilisateur
    async def prefix_gay(self, ctx: commands.Context, member: discord.Member = None):
        try:
            member = member or ctx.author
            embed = calculer_gaytitude_embed(member)
            embed.timestamp = ctx.message.created_at
            await safe_send(ctx, embed=embed)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !gay] {e}")
            await safe_send(ctx, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = GayCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun&Random"
    await bot.add_cog(cog)
