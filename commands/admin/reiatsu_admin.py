# ──────────────────────────────────────────────────────────────
# 📌 ReiatsuAdmin.py — Commande interactive !ReiatsuAdmin / !rtsa
# Objectif : Gérer les paramètres Reiatsu (définir, supprimer un salon, ou modifier les points d’un membre)
# Catégorie : Reiatsu
# Accès : Administrateur
# Cooldown : 1 utilisation / 5 secondes / utilisateur (sauf spawn : 3s)
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
import asyncio
import random
import json
from datetime import datetime
from discord.ext import commands
from discord import ui
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_reply, safe_edit, safe_delete

# ──────────────────────────────────────────────────────────────
# 🔧 Chargement config globale Reiatsu (JSON)
# ──────────────────────────────────────────────────────────────
with open("data/reiatsu_config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

SPAWN_SPEED_RANGES = CONFIG.get("SPAWN_SPEED_RANGES", {})
DEFAULT_SPAWN_SPEED = CONFIG.get("DEFAULT_SPAWN_SPEED", "Normal")

# ──────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ──────────────────────────────────────────────────────────────
class ReiatsuAdmin(commands.Cog):
    """
    Commande !ReiatsuAdmin / !rtsa — Gère Reiatsu : set, unset, change, spawn, speed
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────
    # 🔹 Commande principale (groupe)
    # ──────────────────────────────────────────────────────────
    @commands.group(
        name="reiatsuadmin",
        aliases=["rtsa"],
        invoke_without_command=True,
        help="(Admin) Gère le Reiatsu : set, unset, change, spawn, speed."
    )
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def reiatsuadmin(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🧪 Commande Reiatsu Admin",
            description=(
                "Voici les sous-commandes disponibles :\n\n"
                "`!!rtsa set` — Définit le salon de spawn de Reiatsu\n"
                "`!!rtsa unset` — Supprime le salon configuré\n"
                "`!!rtsa change @membre <points>` — Modifie les points d’un membre\n"
                "`!!rtsa spawn` — Force le spawn immédiat d’un Reiatsu\n"
                "`!!rtsa speed` — Gère la vitesse du spawn"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Réservé aux administrateurs")
        await safe_send(ctx, embed=embed)

    # ──────────────────────────────────────────────────────────
    # 🔹 Sous-commande : SET
    # ──────────────────────────────────────────────────────────
    @reiatsuadmin.command(name="set")
    @commands.has_permissions(administrator=True)
    async def set_reiatsu(self, ctx: commands.Context):
        try:
            guild_id = str(ctx.guild.id)
            channel_id = str(ctx.channel.id)
            now_iso = datetime.utcnow().isoformat()

            # Choix delay par rapport à la vitesse par défaut
            min_delay, max_delay = SPAWN_SPEED_RANGES.get(DEFAULT_SPAWN_SPEED, [1800, 3600])
            delay = random.randint(min_delay, max_delay)

            data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
            if data.data:
                # Mise à jour existante
                supabase.table("reiatsu_config").update({
                    "channel_id": channel_id,
                    "last_spawn_at": now_iso,
                    "spawn_delay": delay,
                    "spawn_speed": DEFAULT_SPAWN_SPEED,
                    "en_attente": False,
                    "spawn_message_id": None
                }).eq("guild_id", guild_id).execute()
            else:
                # Nouveau serveur
                supabase.table("reiatsu_config").insert({
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "last_spawn_at": now_iso,
                    "spawn_delay": delay,
                    "spawn_speed": DEFAULT_SPAWN_SPEED,
                    "en_attente": False,
                    "spawn_message_id": None
                }).execute()

            await safe_send(ctx, f"✅ Le salon {ctx.channel.mention} est désormais configuré pour le spawn de Reiatsu avec vitesse par défaut **{DEFAULT_SPAWN_SPEED}**.")
        except Exception as e:
            await safe_send(ctx, f"❌ Une erreur est survenue lors de la configuration : `{e}`")

    # (UNSET, CHANGE, SPAWN identiques à ton code d’origine → je n’y touche pas)

    # ──────────────────────────────────────────────────────────
    # 🔹 Sous-commande : SPEED
    # ──────────────────────────────────────────────────────────
    @reiatsuadmin.command(name="speed")
    @commands.has_permissions(administrator=True)
    async def speed_reiatsu(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        res = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()

        if not res.data:
            await safe_send(ctx, "❌ Aucun salon Reiatsu configuré pour ce serveur.")
            return

        config = res.data[0]
        current_delay = config.get("spawn_delay", SPAWN_SPEED_RANGES[DEFAULT_SPAWN_SPEED][1])

        # Déterminer la vitesse actuelle
        current_speed_name = DEFAULT_SPAWN_SPEED
        for name, (min_delay, max_delay) in SPAWN_SPEED_RANGES.items():
            if min_delay <= current_delay <= max_delay:
                current_speed_name = name
                break

        # Création de l'embed
        embed = discord.Embed(
            title="⚡ Vitesse du spawn de Reiatsu",
            description=f"**Vitesse actuelle :** {current_speed_name} ({current_delay} sec)",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="Vitesses possibles",
            value="\n".join([f"{name} → {min_delay}-{max_delay} sec" for name, (min_delay, max_delay) in SPAWN_SPEED_RANGES.items()]),
            inline=False
        )

        # Création de boutons
        class SpeedView(ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                for name in SPAWN_SPEED_RANGES:
                    if name != current_speed_name:
                        self.add_item(ui.Button(label=name, style=discord.ButtonStyle.primary, custom_id=f"speed_{name}"))

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                return interaction.user == ctx.author

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True

        view = SpeedView()
        message = await safe_send(ctx, embed=embed, view=view)

        # Callback des boutons
        async def button_listener(interaction: discord.Interaction):
            new_speed_name = interaction.data["custom_id"].split("_", 1)[1]
            min_delay, max_delay = SPAWN_SPEED_RANGES[new_speed_name]
            new_delay = random.randint(min_delay, max_delay)
            supabase.table("reiatsu_config").update({
                "spawn_delay": new_delay,
                "spawn_speed": new_speed_name
            }).eq("guild_id", guild_id).execute()
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="✅ Vitesse du spawn modifiée",
                    description=f"Nouvelle vitesse : **{new_speed_name}** ({new_delay} sec)",
                    color=discord.Color.green()
                ),
                view=None
            )

        for child in view.children:
            if isinstance(child, ui.Button):
                child.callback = button_listener

        self.bot.add_view(view)

# ──────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ──────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuAdmin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
