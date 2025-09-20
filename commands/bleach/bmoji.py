# ────────────────────────────────────────────────────────────────────────────────
# 📌 bmoji.py — Commande interactive !bmoji + /bmoji
# Objectif : Deviner quel personnage Bleach se cache derrière un emoji
# Catégorie : Bleach
# Accès : Public
# Cooldown : 1 utilisation / 5s / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
import json, random, os
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_emojis.json")

def load_characters():
    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON bmoji] {e}")
        return []

# ────────────────────────────────────────────────────────────────────────────────
# ⚔️ Fonction commune
# ────────────────────────────────────────────────────────────────────────────────
async def _run_bmoji(target):
    try:
        characters = load_characters()
        if not characters:
            msg = "⚠️ Le fichier d'emojis est vide ou introuvable."
            if isinstance(target, discord.Interaction):
                return await safe_respond(target, msg, ephemeral=True)
            return await safe_send(target.channel, msg)

        perso = random.choice(characters)
        nom = perso["nom"]
        emojis = random.sample(perso["emojis"], k=min(3, len(perso["emojis"])))

        distracteurs = random.sample([c["nom"] for c in characters if c["nom"] != nom], 3)
        options = distracteurs + [nom]
        random.shuffle(options)

        lettres = ["🇦", "🇧", "🇨", "🇩"]
        bonne = lettres[options.index(nom)]

        # ─────────────── Embed ───────────────
        embed = discord.Embed(
            title="Bmoji",
            description="Devine le personnage de Bleach derrière ces emojis !",
            color=discord.Color.purple()
        )
        embed.add_field(
            name=" ".join(emojis),
            value="\n".join(f"{lettres[i]} : {options[i]}" for i in range(4)),
            inline=False
        )

        # ─────────────── Boutons ───────────────
        class PersoButton(discord.ui.Button):
            def __init__(self, emoji, idx):
                super().__init__(emoji=emoji, style=discord.ButtonStyle.secondary)
                self.idx = idx

            async def callback(self, inter_button):
                user_ok = False
                if isinstance(target, discord.Interaction):
                    user_ok = inter_button.user == target.user
                else:
                    user_ok = inter_button.user == target.author

                if not user_ok:
                    return await safe_respond(inter_button, "❌ Ce défi ne t'est pas destiné.", ephemeral=True)

                view.success = (lettres[self.idx] == bonne)
                view.stop()
                await inter_button.response.defer()

        view = discord.ui.View(timeout=30)
        for i in range(4):
            view.add_item(PersoButton(lettres[i], i))
        view.success = False

        # ─────────────── Envoi embed ───────────────
        if isinstance(target, discord.Interaction):
            await target.response.send_message(embed=embed, view=view)
            msg = await target.original_response()
        else:
            msg = await safe_send(target.channel, embed=embed, view=view)

        view.message = msg
        await view.wait()

        # ─────────────── Résultat ───────────────
        result_msg = "✅ Bonne réponse !" if view.success else f"❌ Mauvaise réponse (c'était {nom})"
        if isinstance(target, discord.Interaction):
            await target.followup.send(result_msg)
        else:
            await safe_send(target.channel, result_msg)

    except Exception as e:
        print(f"[ERREUR bmoji] {e}")
        err = "⚠️ Une erreur est survenue."
        if isinstance(target, discord.Interaction):
            await safe_respond(target, err, ephemeral=True)
        else:
            await safe_send(target.channel, err)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class BMojiCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Préfixe
    @commands.command(name="bmoji", help="Devine quel personnage Bleach se cache derrière ces emojis.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def bmoji_prefix(self, ctx: commands.Context):
        await _run_bmoji(ctx)

    # Slash
    @app_commands.command(name="bmoji", description="Devine quel personnage Bleach se cache derrière ces emojis.")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def bmoji_slash(self, interaction: discord.Interaction):
        await _run_bmoji(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = BMojiCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
