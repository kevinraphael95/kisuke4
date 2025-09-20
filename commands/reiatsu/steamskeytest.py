# ────────────────────────────────────────────────────────────────────────────────
# 📌 steamkey.py — Commande interactive /steamkey et !steamkey
# Objectif : Miser des points Reiatsu pour tenter de gagner une clé Steam
# Catégorie : Reiatsu
# Accès : Public
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────
#
# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Constantes
# ────────────────────────────────────────────────────────────────────────────────
REIATSU_COST = Z00
WIN_CHANCE = 0.1  # 10% de chance de gagner

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — View avec bouton Miser
# ────────────────────────────────────────────────────────────────────────────────
class SteamKeyView(View):
    def __init__(self, author_id: int, message: discord.Message = None):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.value = None
        self.last_interaction = None
        self.message = message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await safe_respond(interaction, "❌ Ce bouton n'est pas pour toi.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            embed = self.message.embeds[0]
            embed.set_footer(text="⏳ Temps écoulé. Relance /steamkey pour retenter ta chance.")
            await safe_edit(self.message, embed=embed, view=self)

    @discord.ui.button(label=f"Miser {REIATSU_COST} Reiatsu", style=discord.ButtonStyle.green)
    async def bet_button(self, interaction: discord.Interaction, button: Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.value = True
        self.last_interaction = interaction
        self.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Confirmation + choix de jeu
# ────────────────────────────────────────────────────────────────────────────────
class ConfirmKeyView(View):
    def __init__(self, author_id: int, keys_dispo: list, message: discord.Message, current_index: int = 0):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.keys_dispo = keys_dispo
        self.index = current_index
        self.message = message
        self.choice = None
        self.switch_count = 0
        self.max_switches = 3

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @property
    def current_key(self):
        return self.keys_dispo[self.index]

    def build_embed(self):
        embed = discord.Embed(
            title="🎉 Tu as gagné une clé Steam !",
            description="Choisis la clé qui te convient le mieux.\n⚠️ Tu peux cliquer sur **Autre jeu** jusqu’à 3 fois.",
            color=discord.Color.green()
        )
        embed.add_field(name="🎮 Jeu", value=self.current_key["game_name"], inline=False)
        embed.add_field(name="🔗 Lien Steam", value=f"[Voir sur Steam]({self.current_key['steam_url']})", inline=False)
        embed.set_footer(text=f"✅ : Prendre | 🎲 : Autre jeu ({self.switch_count}/{self.max_switches}) | ❌ : Refuser")
        return embed

    async def refresh_embed(self, interaction: discord.Interaction):
        await safe_edit(self.message, embed=self.build_embed(), view=self)
        await interaction.response.defer()

    @discord.ui.button(label="✅ Prendre cette clé", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.choice = "accept"
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="🎲 Autre jeu", style=discord.ButtonStyle.blurple)
    async def other_game(self, interaction: discord.Interaction, button: Button):
        self.switch_count += 1
        if self.switch_count >= self.max_switches:
            button.disabled = True
        self.index = (self.index + 1) % len(self.keys_dispo)
        await self.refresh_embed(interaction)

    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        self.choice = "reject"
        await interaction.response.defer()
        self.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class SteamKey(commands.Cog):
    """Commande /steamkey et !steamkey — Miser des Reiatsu pour tenter de gagner une clé Steam"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_reiatsu(self, user_id: str) -> int:
        try:
            resp = supabase.table("reiatsu").select("points").eq("user_id", user_id).single().execute()
            return resp.data["points"] if resp.data else 0
        except Exception as e:
            print(f"[ERREUR Supabase _get_reiatsu] {e}")
            return 0

    async def _update_reiatsu(self, user_id: str, new_points: int):
        try:
            supabase.table("reiatsu").update({"points": new_points}).eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[ERREUR Supabase _update_reiatsu] {e}")

    async def _get_all_steam_keys(self):
        try:
            resp = supabase.table("steam_keys").select("*").eq("won", False).execute()
            return resp.data or []
        except Exception as e:
            print(f"[ERREUR Supabase _get_all_steam_keys] {e}")
            return []

    async def _mark_steam_key_won(self, key_id: int, winner: str):
        try:
            supabase.table("steam_keys").update({"won": True, "winner": winner}).eq("id", key_id).execute()
        except Exception as e:
            print(f"[ERREUR Supabase _mark_steam_key_won] {e}")

    async def _try_win_key(self, interaction_or_ctx):
        keys_dispo = await self._get_all_steam_keys()
        if not keys_dispo:
            return await self._send(interaction_or_ctx, discord.Embed(
                title="⛔ Pas de clé dispo",
                description="Aucune clé n'est disponible pour le moment.",
                color=discord.Color.orange()
            ))

        user_id = str(interaction_or_ctx.user.id)
        reiatsu_points = await self._get_reiatsu(user_id)

        if reiatsu_points < REIATSU_COST:
            msg = f"❌ Pas assez de Reiatsu ! Il te faut {REIATSU_COST}."
            return await (interaction_or_ctx.followup.send(msg, ephemeral=True)
                         if isinstance(interaction_or_ctx, discord.Interaction)
                         else safe_send(interaction_or_ctx.channel, msg))

        await self._update_reiatsu(user_id, reiatsu_points - REIATSU_COST)

        if random.random() <= WIN_CHANCE:
            msg = await self._send(interaction_or_ctx, discord.Embed(
                title="🎁 Recherche d'une clé en cours...", color=discord.Color.blurple()
            ))
            view = ConfirmKeyView(interaction_or_ctx.user.id, keys_dispo, msg, 0)
            await safe_edit(msg, embed=view.build_embed(), view=view)
            await view.wait()

            if view.choice == "accept":
                chosen = view.current_key
                await self._mark_steam_key_won(chosen["id"], interaction_or_ctx.user.name)
                try:
                    await interaction_or_ctx.user.send(
                        f"🎁 **Clé Steam pour {chosen['game_name']}**\n`{chosen['steam_key']}`"
                    )
                    await safe_edit(msg, embed=discord.Embed(title="✅ Clé envoyée en DM !", color=discord.Color.green()), view=None)
                except discord.Forbidden:
                    await safe_edit(msg, embed=discord.Embed(title="⚠️ Impossible d'envoyer un DM.", color=discord.Color.orange()), view=None)

            elif view.choice == "reject":
                await safe_edit(msg, embed=discord.Embed(title="🔄 Clé remise en jeu pour les autres joueurs.", color=discord.Color.blurple()), view=None)

        else:
            await self._send(interaction_or_ctx, discord.Embed(
                title="😢 Dommage !",
                description="❌ Tu n'as pas gagné cette fois. Retente ta chance !",
                color=discord.Color.red()
            ))

    async def _send(self, interaction_or_ctx, embed, view=None):
        if isinstance(interaction_or_ctx, discord.Interaction):
            return await interaction_or_ctx.followup.send(embed=embed, view=view)
        return await safe_send(interaction_or_ctx.channel, embed=embed, view=view)

    async def _send_menu(self, channel, user, user_id: int):
        reiatsu_points = await self._get_reiatsu(user_id)
        keys_dispo = await self._get_all_steam_keys()

        jeux = ", ".join([k["game_name"] for k in keys_dispo[:5]]) or "Aucun"
        if len(keys_dispo) > 5:
            jeux += "…"

        embed = discord.Embed(
            title="🎮 Loto Clé Steam",
            description="Mise du Reiatsu pour tenter de gagner une clé Steam !",
            color=discord.Color.blurple()
        )
        embed.add_field(name="💠 Reiatsu possédé", value=f"**{reiatsu_points}**", inline=False)
        embed.add_field(name="💸 Prix d'une tentative", value=f"**{REIATSU_COST}**", inline=False)
        embed.add_field(name="🎰 Chance de gagner une clé", value=f"**{int(WIN_CHANCE * 100)}%**", inline=False)
        embed.add_field(name="🔑 Nombre de clés à gagner", value=f"**{len(keys_dispo)}**", inline=False)
        embed.add_field(name="🎮 Jeux gagnables", value=jeux, inline=False)

        view = SteamKeyView(user_id)
        message = await safe_send(channel, embed=embed, view=view)
        view.message = message
        return view

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="steamkey", description="Miser des Reiatsu pour tenter de gagner une clé Steam")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.user.id))
    async def slash_steamkey(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            view = await self._send_menu(interaction.channel, interaction.user, interaction.user.id)
            await view.wait()
            if view.value:
                await self._try_win_key(view.last_interaction)
        except Exception as e:
            print(f"[ERREUR /steamkey] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="steamkey", aliases=["skey"])
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_steamkey(self, ctx: commands.Context):
        try:
            view = await self._send_menu(ctx.channel, ctx.author, ctx.author.id)
            await view.wait()
            if view.value:
                class DummyInteraction:
                    def __init__(self, user, channel):
                        self.user, self.channel = user, channel
                await self._try_win_key(DummyInteraction(ctx.author, ctx.channel))
        except Exception as e:
            print(f"[ERREUR !steamkey] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SteamKey(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
