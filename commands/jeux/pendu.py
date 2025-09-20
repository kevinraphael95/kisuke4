# ────────────────────────────────────────────────────────────────────────────────
# 📌 pendu.py — Commande interactive !pendu
# Objectif : Jeu du pendu interactif avec propositions par message
# Catégorie : Jeux
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import aiohttp
from utils.discord_utils import safe_send, safe_edit, safe_respond  # ✅ Utilisation safe_

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Constantes et ASCII
# ────────────────────────────────────────────────────────────────────────────────
PENDU_ASCII = [
    "`     \n     \n     \n     \n     \n=========`",
    "`     +---+\n     |   |\n         |\n         |\n         |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n         |\n         |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n     |   |\n         |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n    /|   |\n         |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n    /|\\  |\n         |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n    /|\\  |\n    /    |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n    /|\\  |\n    / \\  |\n     =========`",
]

MAX_ERREURS = 7

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Classe PenduGame
# ────────────────────────────────────────────────────────────────────────────────
class PenduGame:
    def __init__(self, mot: str, mode: str = "solo"):
        self.mot = mot.lower()
        self.trouve = set()
        self.rate = set()
        self.terminee = False
        self.mode = mode
        self.max_erreurs = min(len(mot) + 1, MAX_ERREURS)

    def get_display_word(self) -> str:
        return " ".join([l if l in self.trouve else "_" for l in self.mot])

    def get_pendu_ascii(self) -> str:
        return PENDU_ASCII[min(len(self.rate), self.max_erreurs)]

    def get_lettres_tentees(self) -> str:
        lettres_tentees = sorted(self.trouve | self.rate)
        return ", ".join(lettres_tentees) if lettres_tentees else "Aucune"

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🕹️ Jeu du Pendu — mode {self.mode.capitalize()}",
            description=f"```\n{self.get_pendu_ascii()}\n```",
            color=discord.Color.blue()
        )
        embed.add_field(name="Mot", value=f"`{self.get_display_word()}`", inline=False)
        embed.add_field(name="Erreurs", value=f"`{len(self.rate)} / {self.max_erreurs}`", inline=False)
        embed.add_field(name="Lettres tentées", value=f"`{self.get_lettres_tentees()}`", inline=False)
        embed.set_footer(text="✉️ Propose une lettre en répondant par un message contenant UNE lettre.")
        return embed

    def propose_lettre(self, lettre: str):
        lettre = lettre.lower()
        if lettre in self.trouve or lettre in self.rate:
            return None
        if lettre in self.mot:
            self.trouve.add(lettre)
        else:
            self.rate.add(lettre)
        if all(l in self.trouve for l in set(self.mot)):
            self.terminee = True
            return "gagne"
        if len(self.rate) >= self.max_erreurs:
            self.terminee = True
            return "perdu"
        return "continue"

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Classe PenduSession (pour solo et multi)
# ────────────────────────────────────────────────────────────────────────────────
class PenduSession:
    def __init__(self, game: PenduGame, message: discord.Message, mode: str = "solo", author_id: int = None):
        self.game = game
        self.message = message
        self.mode = mode  # "solo" ou "multi"
        if mode == "multi":
            self.players = set()
            if author_id:
                self.players.add(author_id)
        else:
            self.player_id = author_id  # solo : stocke juste le joueur qui a lancé la partie

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Pendu(commands.Cog):
    """
    Commande !pendu — Jeu du pendu interactif, mode solo ou multi.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions = {}  # dict channel_id -> PenduSession
        self.http_session = aiohttp.ClientSession()

    @commands.command(
        name="pendu",
        help="Démarre une partie du jeu du pendu.",
        description="Lance une partie, puis propose des lettres par message."
    )
    async def pendu_cmd(self, ctx: commands.Context, mode: str = ""):
        mode = mode.lower()
        if mode not in ("multi", "m"):
            mode = "solo"

        channel_id = ctx.channel.id
        if channel_id in self.sessions:
            await safe_send(ctx.channel, "❌ Une partie est déjà en cours dans ce salon.")
            return

        mot = await self._fetch_random_word()
        if not mot:
            await safe_send(ctx.channel, "❌ Impossible de récupérer un mot, réessaie plus tard.")
            return

        game = PenduGame(mot, mode=mode)
        embed = game.create_embed()
        message = await safe_send(ctx.channel, embed=embed)

        if mode == "multi":
            session = PenduSession(game, message, mode="multi", author_id=ctx.author.id)
        else:
            session = PenduSession(game, message, mode="solo", author_id=ctx.author.id)

        self.sessions[channel_id] = session

    async def _fetch_random_word(self) -> str | None:
        url = "https://trouve-mot.fr/api/random/1"
        try:
            async with self.http_session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return data[0]["name"].lower()
        except Exception:
            return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        channel_id = message.channel.id
        session: PenduSession = self.sessions.get(channel_id)
        if not session:
            return

        # Solo : uniquement le joueur qui a lancé la partie
        if session.mode == "solo" and message.author.id != session.player_id:
            return

        # Multi : tous les joueurs peuvent proposer
        if session.mode == "multi" and session.players is not None and message.author.id not in session.players:
            session.players.add(message.author.id)  # ajoute le joueur si nouveau

        content = message.content.strip().lower()
        if len(content) != 1 or not content.isalpha():
            return

        game = session.game
        resultat = game.propose_lettre(content)

        if resultat is None:
            await safe_send(message.channel, f"❌ Lettre `{content}` déjà proposée.", delete_after=5)
            await message.delete()
            return

        embed = game.create_embed()
        try:
            await safe_edit(session.message, embed=embed)
        except discord.NotFound:
            del self.sessions[channel_id]
            await safe_send(message.channel, "❌ Partie annulée car le message du jeu a été supprimé.")
            return

        await message.delete()

        if resultat == "gagne":
            await safe_send(message.channel, f"🎉 Bravo {message.author.mention}, le mot `{game.mot}` a été deviné !")
            del self.sessions[channel_id]
            return

        if resultat == "perdu":
            await safe_send(message.channel, f"💀 Partie terminée ! Le mot était `{game.mot}`.")
            del self.sessions[channel_id]
            return

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Pendu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
