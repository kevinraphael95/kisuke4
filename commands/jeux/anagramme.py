# ────────────────────────────────────────────────────────────────────────────────
# 📌 anagramme.py — Commande interactive /anagramme et !anagramme
# Objectif : Jeu de l'anagramme avec embed, tentatives limitées et feedback
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Modal, TextInput, Button
import random, aiohttp, unicodedata
from spellchecker import SpellChecker
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🌐 Initialisation du spellchecker français
# ────────────────────────────────────────────────────────────────────────────────
spell = SpellChecker(language='fr')

# ────────────────────────────────────────────────────────────────────────────────
# 🌐 Fonction pour récupérer un mot français aléatoire
# ────────────────────────────────────────────────────────────────────────────────
async def get_random_french_word(length: int | None = None) -> str:
    """Récupère un mot français aléatoire depuis l'API trouve-mot.fr"""
    url = "https://trouve-mot.fr/api/random"
    if length:
        url += f"?size={length}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]["name"].upper()
    except Exception as e:
        print(f"[ERREUR API Anagramme] {e}")
    return "PYTHON"

# ────────────────────────────────────────────────────────────────────────────────
# 🌐 Fonction pour vérifier qu’un mot existe via SpellChecker
# ────────────────────────────────────────────────────────────────────────────────
def is_valid_word(word: str) -> bool:
    """Retourne True si le mot est reconnu par SpellChecker"""
    return word.lower() in spell.word_frequency

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Modal pour proposer un mot
# ────────────────────────────────────────────────────────────────────────────────
class AnagrammeModal(Modal):
    def __init__(self, parent_view):
        super().__init__(title="🖊️ Propose un mot")
        self.parent_view = parent_view
        self.word_input = TextInput(
            label="Mot",
            placeholder=f"Reconstitue le mot de {self.parent_view.display_length} lettres",
            required=True,
            max_length=self.parent_view.display_length,
            min_length=self.parent_view.display_length
        )
        self.add_item(self.word_input)

    async def on_submit(self, interaction: discord.Interaction):
        guess = self.word_input.value.strip().upper()
        await self.parent_view.process_guess(interaction, guess)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue principale avec boutons (Proposer + Indice)
# ────────────────────────────────────────────────────────────────────────────────
class AnagrammeView(View):
    def __init__(self, target_word: str, max_attempts: int | None = None, author_id: int | None = None):
        super().__init__(timeout=180)
        normalized = target_word.replace("Œ", "OE").replace("œ", "oe")
        self.target_word = normalized.upper()
        self.display_word = ''.join(random.sample(self.target_word, len(self.target_word)))
        self.display_length = len([c for c in self.target_word if c.isalpha()])
        base_attempts = max(self.display_length, 5)
        self.max_attempts = max_attempts if max_attempts else base_attempts
        self.attempts: list[dict] = []
        self.message = None
        self.finished = False
        self.author_id = author_id
        self.hinted_indices: set[int] = set()

        # Boutons
        self.add_item(AnagrammeButton(self))
        self.hint_button = HintButtonAnagramme(self)
        self.add_item(self.hint_button)

    # ───────────── Helper pour enlever accents ─────────────
    def remove_accents(self, text: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        ).upper()

    # ───────────── Feedback visuel ─────────────
    def create_feedback_line(self, entry: dict) -> str:
        word = entry['word']
        is_hint = entry.get('hint', False)
        colors = []
        for i, c in enumerate(word):
            if i < len(self.target_word) and self.remove_accents(c) == self.remove_accents(self.target_word[i]):
                colors.append("🟩")
            elif c in self.target_word:
                colors.append("🟨")
            else:
                colors.append("⬛")
        return f"{' '.join(word)}\n{' '.join(colors)}"

    def build_embed(self) -> discord.Embed:
        mode_text = "Solo 🧍‍♂️" if self.author_id else "Multi 🌍"
        embed = discord.Embed(
            title=f"🔀 Anagramme - {mode_text}",
            description=f"Mot mélangé : **{' '.join(self.display_word)}**",
            color=discord.Color.orange()
        )

        if self.attempts:
            tries_text = "\n\n".join(self.create_feedback_line(entry) for entry in self.attempts)
            embed.add_field(name=f"Essais ({len(self.attempts)}/{self.max_attempts})", value=tries_text, inline=False)
        else:
            embed.add_field(name="Essais", value="*(Aucun essai pour l’instant)*", inline=False)

        if self.finished:
            last_word = self.attempts[-1]['word'] if self.attempts else ""
            if self.remove_accents(last_word) == self.remove_accents(self.target_word):
                embed.color = discord.Color.green()
                embed.set_footer(text="🎉 Bravo ! Tu as trouvé le mot.")
            else:
                embed.color = discord.Color.red()
                embed.set_footer(text=f"💀 Partie terminée. Le mot était {self.target_word}.")
        else:
            embed.set_footer(text=f"⏳ Temps restant : 180 secondes")

        return embed

    async def process_guess(self, interaction: discord.Interaction, guess: str):
        if self.finished:
            return await safe_respond(interaction, "⚠️ La partie est terminée.", ephemeral=True)

        filtered_guess = guess.replace("-", "")
        if len(filtered_guess) != self.display_length:
            return await safe_respond(interaction, f"⚠️ Le mot doit faire {self.display_length} lettres.", ephemeral=True)

        if not is_valid_word(filtered_guess):
            return await safe_respond(interaction, f"❌ `{guess}` n’est pas reconnu comme un mot valide.", ephemeral=True)

        self.attempts.append({'word': guess.upper(), 'hint': False})

        if self.remove_accents(filtered_guess) == self.remove_accents(self.target_word) or len(self.attempts) >= self.max_attempts:
            self.finished = True
            for child in self.children:
                child.disabled = True

        await safe_edit(self.message, embed=self.build_embed(), view=self)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def on_timeout(self):
        if self.finished:
            return
        self.finished = True
        for child in self.children:
            child.disabled = True
        embed = self.build_embed()
        embed.color = discord.Color.red()
        embed.set_footer(text=f"⏳ Temps écoulé ! Le mot était {self.target_word}.")
        await safe_edit(self.message, embed=embed, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Boutons
# ────────────────────────────────────────────────────────────────────────────────
class AnagrammeButton(Button):
    def __init__(self, parent_view: AnagrammeView):
        super().__init__(label="Proposer un mot", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.author_id and interaction.user.id != self.parent_view.author_id:
            return await interaction.response.send_message("❌ Seul le lanceur peut proposer un mot.", ephemeral=True)
        await interaction.response.send_modal(AnagrammeModal(self.parent_view))

class HintButtonAnagramme(Button):
    def __init__(self, parent_view: AnagrammeView):
        super().__init__(label="Indice", style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        pv = self.parent_view
        if pv.author_id and interaction.user.id != pv.author_id:
            return await interaction.response.send_message("❌ Seul le lanceur peut utiliser l'indice.", ephemeral=True)
        if pv.finished:
            return await interaction.response.send_message("⚠️ La partie est déjà terminée.", ephemeral=True)
        available_indices = [i for i in range(len(pv.target_word)) if i not in pv.hinted_indices]
        if not available_indices:
            return await interaction.response.send_message("ℹ️ Aucune lettre restante à révéler.", ephemeral=True)
        idx = random.choice(available_indices)
        hint_word = ["_" for _ in range(len(pv.target_word))]
        hint_word[idx] = pv.target_word[idx]
        pv.attempts.append({'word': "".join(hint_word), 'hint': True})
        pv.hinted_indices.add(idx)
        self.disabled = True
        if len(pv.attempts) >= pv.max_attempts:
            pv.finished = True
            for child in pv.children:
                child.disabled = True
        await safe_edit(pv.message, embed=pv.build_embed(), view=pv)
        await interaction.response.send_message(f"🔎 Indice utilisé — lettre **{pv.target_word[idx]}** révélée.", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Anagramme(commands.Cog):
    """Commande /anagramme et !anagramme — Lance une partie d'Anagramme"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _start_game(self, channel: discord.abc.Messageable, author_id: int, mode: str = "solo"):
        length = random.choice(range(5, 9))
        target_word = await get_random_french_word(length=length)
        author_filter = None if mode.lower() in ("multi", "m") else author_id
        view = AnagrammeView(target_word, max_attempts=None, author_id=author_filter)
        embed = view.build_embed()
        view.message = await safe_send(channel, embed=embed, view=view)

    # 🔹 Commande SLASH
    @app_commands.command(name="anagramme", description="Lance une partie d'Anagramme (multi = tout le monde peut jouer)")
    @app_commands.describe(mode="Mode de jeu : solo ou multi")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_anagramme(self, interaction: discord.Interaction, mode: str = "solo"):
        try:
            await interaction.response.defer()
            await self._start_game(interaction.channel, author_id=interaction.user.id, mode=mode)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /anagramme] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # 🔹 Commande PREFIX
    @commands.command(name="anagramme", help="Lance une partie d'Anagramme. anagramme multi ou m pour jouer en multi.")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_anagramme(self, ctx: commands.Context, mode: str = "solo"):
        try:
            await self._start_game(ctx.channel, author_id=ctx.author.id, mode=mode)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !anagramme] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Anagramme(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)




