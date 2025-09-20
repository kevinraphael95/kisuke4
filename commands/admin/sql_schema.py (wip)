# ────────────────────────────────────────────────────────────────────────────────
# 📌 tools_sqlschema.py — Commande /sqlschema et !sqlschema
# Objectif : Analyse le code du bot, détecte les tables Supabase utilisées et génère un SQL CREATE TABLE détaillé
# Catégorie : Admin
# Accès : Administrateurs seulement
# Cooldown : 1 utilisation / 20 secondes / utilisateur
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
import re
import ast

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ToolsSQLSchema(commands.Cog):
    """
    Commande /sqlschema et !sqlschema — Génère un schéma SQL détaillé pour les tables Supabase utilisées
    Accessible uniquement aux administrateurs.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Détection des types SQL depuis les valeurs
    # ────────────────────────────────────────────────────────────────────────────
    def _infer_sql_type(self, value):
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float8"
        elif isinstance(value, (list, dict)):
            return "jsonb"
        elif value is None:
            return "text"
        else:
            return "text"

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Analyse le code et récupère toutes les colonnes par table
    # ────────────────────────────────────────────────────────────────────────────
    def _get_tables_and_columns(self, directory="."):
        tables = {}
        supabase_pattern = re.compile(r'supabase\.(?:table|from_)\(["\'](\w+)["\']\)')

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                            source = f.read()
                        tree = ast.parse(source, filename=file)
                    except Exception:
                        continue

                    # Détection des noms de tables
                    for match in supabase_pattern.findall(source):
                        if match not in tables:
                            tables[match] = {}

                    # Analyse AST pour insert, update, select, eq...
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                            func_name = node.func.attr
                            target = node.func.value

                            # ── insert / update (dict)
                            if func_name in {"insert", "update"} and node.args:
                                arg = node.args[0]
                                if isinstance(arg, ast.Dict):
                                    table_name = None
                                    if isinstance(target, ast.Call) and isinstance(target.func, ast.Attribute):
                                        if target.func.attr in {"table", "from_"} and target.args:
                                            if isinstance(target.args[0], ast.Constant):
                                                table_name = target.args[0].value
                                    if table_name:
                                        if table_name not in tables:
                                            tables[table_name] = {}
                                        for key, val in zip(arg.keys, arg.values):
                                            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                                col = key.value
                                                value = None
                                                try:
                                                    value = ast.literal_eval(val)
                                                except Exception:
                                                    pass
                                                sql_type = self._infer_sql_type(value)
                                                tables[table_name][col] = sql_type

                            # ── select("col1, col2,...")
                            elif func_name == "select" and node.args:
                                if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                                    cols = [c.strip() for c in node.args[0].value.split(",")]
                                    table_name = None
                                    if isinstance(target, ast.Call) and isinstance(target.func, ast.Attribute):
                                        if target.func.attr in {"table", "from_"} and target.args:
                                            if isinstance(target.args[0], ast.Constant):
                                                table_name = target.args[0].value
                                    if table_name:
                                        if table_name not in tables:
                                            tables[table_name] = {}
                                        for col in cols:
                                            if col and col not in tables[table_name]:
                                                tables[table_name][col] = "text"

                            # ── filtres eq("col", value), lt, gt...
                            elif func_name in {"eq", "lt", "gt", "gte", "lte"} and len(node.args) >= 2:
                                if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                                    col = node.args[0].value
                                    value = None
                                    try:
                                        value = ast.literal_eval(node.args[1])
                                    except Exception:
                                        pass
                                    sql_type = self._infer_sql_type(value)
                                    table_name = None
                                    if isinstance(target, ast.Call) and isinstance(target.func, ast.Attribute):
                                        if target.func.attr in {"table", "from_"} and target.args:
                                            if isinstance(target.args[0], ast.Constant):
                                                table_name = target.args[0].value
                                    if table_name:
                                        if table_name not in tables:
                                            tables[table_name] = {}
                                        tables[table_name][col] = sql_type

        return tables

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Génère schema.sql et l'envoie
    # ────────────────────────────────────────────────────────────────────────────
    async def _generate_sqlschema(self, channel: discord.abc.Messageable):
        try:
            tables = self._get_tables_and_columns()

            if not tables:
                await safe_send(channel, "ℹ️ Aucune table Supabase trouvée dans le code.")
                return

            sql_lines = ["-- Généré automatiquement depuis le bot\n"]
            for table, cols in tables.items():
                sql_lines.append(f"CREATE TABLE IF NOT EXISTS {table} (")
                sql_lines.append("    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),")
                for i, (col, sql_type) in enumerate(cols.items()):
                    comma = "," if i < len(cols) - 1 else ""
                    sql_lines.append(f"    {col} {sql_type}{comma}")
                sql_lines.append(");\n")

            with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".sql") as tmp_file:
                tmp_file.write("\n".join(sql_lines))
                tmp_file_path = tmp_file.name

            await channel.send(file=discord.File(tmp_file_path, filename="schema.sql"))

        except Exception as e:
            print(f"[ERREUR generate_sqlschema] {e}")
            await safe_send(channel, "❌ Impossible de générer schema.sql.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH (admin seulement)
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        name="sqlschema",
        description="Analyse le code et génère un schéma SQL détaillé pour les tables Supabase utilisées"
    )
    @app_commands.checks.cooldown(1, 20.0, key=lambda i: i.user.id)
    async def slash_sqlschema(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._generate_sqlschema(interaction.channel)
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /sqlschema] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX (admin seulement)
    # ────────────────────────────────────────────────────────────────────────────
    @commands.has_permissions(administrator=True)
    @commands.command(name="sqlschema")
    @commands.cooldown(1, 20.0, commands.BucketType.user)
    async def prefix_sqlschema(self, ctx: commands.Context):
        await self._generate_sqlschema(ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ToolsSQLSchema(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
