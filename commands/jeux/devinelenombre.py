# ────────────────────────────────────────────────────────────────────────────────
# 📌 devinelenombre.py — Commande interactive /devinelenombre et !devinelenombre
# Objectif : Deviner un nombre entre 0 et 100
# Modes : Solo (1 joueur) et Multi (plusieurs joueurs)
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
from discord.ui import View, Button, TextInput, Modal
import random
import asyncio
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Modal pour proposer un nombre
# ────────────────────────────────────────────────────────────────────────────────
class DevinelenombreModal(Modal):
    def __init__(self, parent_view):
        super().__init__(title="Propose un nombre")
        self.parent_view = parent_view
        self.number_input = TextInput(
            label="Nombre entre 0 et 100",
            placeholder="Exemple : 42",
            required=True,
            max_length=3,
            min_length=1
        )
        self.add_item(self.number_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            guess = int(self.number_input.value.strip())
        except ValueError:
            return await interaction.response.send_message("❌ Ce n'est pas un nombre valide.", ephemeral=True)
        await self.parent_view.process_guess(interaction, guess)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue principale avec boutons
# ────────────────────────────────────────────────────────────────────────────────
class DevinelenombreView(View):
    SOLO_TIME = 120
    MULTI_TIME = 120

    def __init__(self, target: int, multi: bool = False, author_id: int | None = None):
        super().__init__(timeout=None)
        self.target = target
        self.multi = multi
        self.max_attempts = 10
        self.attempts: list[int] = []
        self.message = None
        self.finished = False
        self.author_id = author_id
        self.add_item(ProposeNombreButton(self))

    def build_embed(self) -> discord.Embed:
        mode_text = "Multi" if self.multi else "Solo"
        embed = discord.Embed(
            title=f"🎯 Devinelenombre - Mode {mode_text}",
            description="Devine le nombre entre 0 et 100\nAppuie sur **Proposer un nombre** pour participer.",
            color=discord.Color.orange()
        )
        if self.attempts:
            lines = []
            for idx, val in enumerate(self.attempts, 1):
                if val < self.target:
                    symbol = "⬆️ Trop bas"
                elif val > self.target:
                    symbol = "⬇️ Trop haut"
                else:
                    symbol = "✅ Exact !"
                lines.append(f"{idx}. {val} → {symbol}")
            embed.add_field(name=f"Essais ({len(self.attempts)}/{self.max_attempts})", value="\n".join(lines), inline=False)
        else:
            embed.add_field(name="Essais", value="*(Aucun essai pour l’instant)*", inline=False)

        if self.finished:
            if self.attempts and self.attempts[-1] == self.target:
                embed.color = discord.Color.green()
                embed.set_footer(text="🎉 Bravo ! Tu as trouvé le nombre.")
            else:
                embed.color = discord.Color.red()
                embed.set_footer(text=f"💀 Partie terminée. Le nombre était {self.target}.")
        else:
            embed.set_footer(text=f"⏳ Temps restant : {self.SOLO_TIME if not self.multi else self.MULTI_TIME} secondes")

        return embed

    async def process_guess(self, interaction: discord.Interaction, guess: int):
        if self.finished:
            return await safe_respond(interaction, "⚠️ La partie est terminée.", ephemeral=True)
        if not (0 <= guess <= 100):
            return await safe_respond(interaction, "⚠️ Le nombre doit être entre 0 et 100.", ephemeral=True)
        self.attempts.append(guess)
        if guess == self.target or len(self.attempts) >= self.max_attempts:
            self.finished = True
            for child in self.children:
                child.disabled = True
        await safe_edit(self.message, embed=self.build_embed(), view=self)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def start_timer(self):
        try:
            await asyncio.sleep(self.MULTI_TIME if self.multi else self.SOLO_TIME)
        except asyncio.CancelledError:
            return
        if not self.finished:
            self.finished = True
            for child in self.children:
                child.disabled = True
            embed = self.build_embed()
            embed.color = discord.Color.red()
            embed.set_footer(text=f"⏳ Temps écoulé ! Le nombre était {self.target}.")
            await safe_edit(self.message, embed=embed, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Bouton Proposer
# ────────────────────────────────────────────────────────────────────────────────
class ProposeNombreButton(Button):
    def __init__(self, parent_view: DevinelenombreView):
        super().__init__(label="Proposer un nombre", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.author_id and interaction.user.id != self.parent_view.author_id:
            return await interaction.response.send_message("❌ Seul le lanceur peut proposer un nombre.", ephemeral=True)
        await interaction.response.send_modal(DevinelenombreModal(self.parent_view))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Devinelenombre(commands.Cog):
    """Commande /devinelenombre et !devinelenombre — Deviner un nombre entre 0 et 100"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _start_game(self, channel: discord.abc.Messageable, user_id: int, multi: bool = False):
        target = random.randint(0, 100)
        author_filter = None if multi else user_id
        view = DevinelenombreView(target, multi=multi, author_id=author_filter)
        embed = view.build_embed()
        view.message = await safe_send(channel, embed=embed, view=view)
        asyncio.create_task(view.start_timer())

    # 🔹 Commande SLASH
    @app_commands.command(name="devinelenombre", description="Devine un nombre entre 0 et 100")
    @app_commands.describe(mode="Tapez 'm' ou 'multi' pour le mode multijoueur")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_devinelenombre(self, interaction: discord.Interaction, mode: str = None):
        try:
            await interaction.response.defer()
            multi = mode and mode.lower() in ("m", "multi")
            await self._start_game(interaction.channel, user_id=interaction.user.id, multi=multi)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /devinelenombre] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # 🔹 Commande PREFIX
    @commands.command(name="devinelenombre", help="Devine un nombre entre 0 et 100 (multi = plusieurs joueurs)")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_devinelenombre(self, ctx: commands.Context, mode: str = None):
        try:
            multi = mode and mode.lower() in ("m", "multi")
            await self._start_game(ctx.channel, user_id=ctx.author.id, multi=multi)
        except Exception as e:
            print(f"[ERREUR !devinelenombre] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Devinelenombre(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)



