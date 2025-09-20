# ────────────────────────────────────────────────────────────────────────────────
# 📌 help.py — Commande interactive !help
# Objectif : Afficher dynamiquement l’aide des commandes avec menu et pagination
# Catégorie : Général
# Accès : Public
# Cooldown : 1 utilisation / 5 sec / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Select, Button
from bot import get_prefix
import math
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Sélecteur de catégorie
# ────────────────────────────────────────────────────────────────────────────────
class HelpCategoryView(View):
    def __init__(self, bot, categories, prefix):
        super().__init__(timeout=None)
        self.bot = bot
        self.categories = categories
        self.prefix = prefix
        self.add_item(HelpCategorySelect(self))

class HelpCategorySelect(Select):
    def __init__(self, parent_view: HelpCategoryView):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label=cat, description=f"{len(cmds)} commande(s)")
            for cat, cmds in sorted(self.parent_view.categories.items())
        ]
        super().__init__(placeholder="Sélectionne une catégorie", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        selected_cat = self.values[0]
        commands_in_cat = sorted(self.parent_view.categories[selected_cat], key=lambda c: c.name)
        paginator = HelpPaginatorView(self.parent_view.bot, selected_cat, commands_in_cat, self.parent_view.prefix, self.parent_view)
        await safe_edit(
            interaction.message,
            content=f"📂 Catégorie sélectionnée : **{selected_cat}**",
            embed=paginator.create_embed(),
            view=paginator
        )

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Pagination des commandes
# ────────────────────────────────────────────────────────────────────────────────
class HelpPaginatorView(View):
    def __init__(self, bot, category, commands_list, prefix, parent_view):
        super().__init__(timeout=None)
        self.bot = bot
        self.category = category
        self.commands = commands_list
        self.prefix = prefix
        self.parent_view = parent_view
        self.page = 0
        self.per_page = 10
        self.total_pages = max(1, math.ceil(len(self.commands) / self.per_page))
        if self.total_pages > 1:
            self.add_item(PrevButton(self))
            self.add_item(NextButton(self))
        self.add_item(HelpCategorySelect(self.parent_view))

    def create_embed(self):
        embed = discord.Embed(
            title=f"📂 {self.category} — Page {self.page + 1}/{self.total_pages}",
            color=discord.Color.blurple()
        )
        start, end = self.page * self.per_page, (self.page + 1) * self.per_page
        for cmd in self.commands[start:end]:
            embed.add_field(name=f"`{self.prefix}{cmd.name}`", value=cmd.help or "Pas de description.", inline=False)
        embed.set_footer(text=f"Utilise {self.prefix}help <commande> pour plus de détails.")
        return embed

class PrevButton(Button):
    def __init__(self, paginator):
        super().__init__(label="◀️", style=discord.ButtonStyle.primary)
        self.paginator = paginator

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.paginator.page > 0:
            self.paginator.page -= 1
            await safe_edit(interaction.message, embed=self.paginator.create_embed(), view=self.paginator)

class NextButton(Button):
    def __init__(self, paginator):
        super().__init__(label="▶️", style=discord.ButtonStyle.primary)
        self.paginator = paginator

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.paginator.page < self.paginator.total_pages - 1:
            self.paginator.page += 1
            await safe_edit(interaction.message, embed=self.paginator.create_embed(), view=self.paginator)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class HelpCommand(commands.Cog):
    """Commande !help — Affiche les commandes du bot par catégories avec menu interactif"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h"], help="Affiche la liste des commandes ou une commande spécifique.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def help_func(self, ctx: commands.Context, commande: str = None):
        prefix = get_prefix(self.bot, ctx.message)

        # 🔍 Aide pour commande spécifique
        if commande:
            cmd = self.bot.get_command(commande)
            if not cmd:
                return await safe_send(ctx.channel, f"❌ La commande `{commande}` n'existe pas.")

            embed = discord.Embed(title=f"ℹ️ Aide pour `{prefix}{cmd.name}`", color=discord.Color.green())
            embed.add_field(name="📄 Description", value=cmd.help or "Pas de description.", inline=False)
            if cmd.aliases:
                embed.add_field(name="🔁 Alias", value=", ".join(f"`{a}`" for a in cmd.aliases), inline=False)
            embed.set_footer(text="📌 Syntaxe : <obligatoire> [optionnel]")
            return await safe_send(ctx.channel, embed=embed)

        # 📜 Liste des commandes par catégorie
        categories = {}
        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
            cat = getattr(cmd, "category", "Autres")
            categories.setdefault(cat, []).append(cmd)

        view = HelpCategoryView(self.bot, categories, prefix)
        await safe_send(ctx.channel, "📌 Sélectionne une catégorie pour voir ses commandes :", view=view)

    def cog_load(self):
        self.help_func.category = "Général"

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HelpCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
    print("✅ Cog chargé : HelpCommand (catégorie = Général)")
