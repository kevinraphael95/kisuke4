# ────────────────────────────────────────────────────────────────────────────────
# 📌 tools_requirements.py — Commande simple /requirements et !requirements
# Objectif : Génère automatiquement un fichier requirements.txt minimal avec les packages utilisés et l'envoie sur Discord
# Catégorie : Admin
# Accès : Administrateurs seulement
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond
import tempfile
import os
import ast
import pkg_resources

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ToolsRequirements(commands.Cog):
    """
    Commande /requirements et !requirements — Crée un requirements.txt minimal et l'envoie sur Discord
    Accessible uniquement aux administrateurs.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Récupère les packages externes réellement utilisés
    # ────────────────────────────────────────────────────────────────────────────
    def _get_used_packages(self, directory="."):
        stdlib_modules = {
            "os", "sys", "json", "time", "datetime", "re", "math", "random", "pathlib",
            "subprocess", "tempfile", "collections", "itertools", "functools", "typing"
        }

        used_packages = set()
        local_modules = set()

        # Récupère tous les modules locaux pour les exclure
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    local_modules.add(os.path.splitext(file)[0])

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                            tree = ast.parse(f.read(), filename=file)
                    except Exception:
                        continue
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                pkg = alias.name.split(".")[0]
                                if pkg not in stdlib_modules and pkg not in local_modules:
                                    used_packages.add(pkg)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                pkg = node.module.split(".")[0]
                                if pkg not in stdlib_modules and pkg not in local_modules:
                                    used_packages.add(pkg)
        return used_packages

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Génère et envoie requirements.txt minimal
    # ────────────────────────────────────────────────────────────────────────────
    async def _generate_requirements(self, channel: discord.abc.Messageable):
        try:
            used_packages = self._get_used_packages()
            installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}

            # Exclut les dépendances indirectes connues
            exclude = {
                "certifi", "idna", "urllib3", "charset_normalizer",
                "multidict", "yarl", "h11", "h2", "hpack", "hyperframe",
                "frozenlist", "aiosignal", "sniffio", "markupsafe",
                "blinker", "itsdangerous", "jinja2", "werkzeug"
            }

            minimal_requirements = []
            for pkg in used_packages:
                key = pkg.lower()
                if key in installed_packages and key not in exclude:
                    minimal_requirements.append(f"{pkg}=={installed_packages[key]}")

            minimal_requirements = sorted(set(minimal_requirements))

            # Création d’un fichier temporaire
            with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as tmp_file:
                tmp_file.write("\n".join(minimal_requirements))
                tmp_file_path = tmp_file.name

            await channel.send(file=discord.File(tmp_file_path, filename="requirements.txt"))

        except Exception as e:
            print(f"[ERREUR generate_requirements] {e}")
            await safe_send(channel, "❌ Impossible de générer requirements.txt.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH (admin seulement)
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        name="requirements",
        description="Génère et envoie un fichier requirements.txt minimal avec les packages utilisés"
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def slash_requirements(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._generate_requirements(interaction.channel)
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /requirements] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX (admin seulement)
    # ────────────────────────────────────────────────────────────────────────────
    @commands.has_permissions(administrator=True)
    @commands.command(name="requirements")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_requirements(self, ctx: commands.Context):
        await self._generate_requirements(ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ToolsRequirements(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
