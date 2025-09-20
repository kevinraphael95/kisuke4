# ────────────────────────────────────────────────────────────────────────────────
# 📌 steamkey.py — Commande interactive /steamkey et !steamkey
# Objectif : Miser des points Reiatsu pour tenter de gagner une clé Steam
# Catégorie : Général
# Accès : Public
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
REIATSU_COST = 1
WIN_CHANCE = 0.5  # 0.5 = 50% de chance de gagner

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — View avec bouton miser
# ────────────────────────────────────────────────────────────────────────────────
class SteamKeyView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.value = None
        self.last_interaction = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await safe_respond(interaction, "❌ Ce bouton n'est pas pour toi.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label=f"Miser {REIATSU_COST} Reiatsu", style=discord.ButtonStyle.green)
    async def bet_button(self, interaction: discord.Interaction, button: Button):
        button.disabled = True
        await interaction.response.edit_message(view=self)
        self.value = True
        self.last_interaction = interaction
        self.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — View de confirmation (uniquement en cas de gain)
# ────────────────────────────────────────────────────────────────────────────────
class ConfirmKeyView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=30)
        self.author_id = author_id
        self.confirmed = None
        self.refresh = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="✅ Oui, je veux la clé", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="🔄 Autre jeu", style=discord.ButtonStyle.blurple)
    async def refresh_button(self, interaction: discord.Interaction, button: Button):
        self.refresh = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="❌ Non, laisse la clé", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        self.confirmed = False
        await interaction.response.defer()
        self.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class SteamKey(commands.Cog):
    """Commande /steamkey et !steamkey — Miser des Reiatsu pour tenter de gagner une clé Steam"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ─────────── Fonctions internes accès Supabase ───────────
    async def _get_reiatsu(self, user_id: str) -> int:
        resp = supabase.table("reiatsu").select("points").eq("user_id", user_id).single().execute()
        return resp.data["points"] if resp.data else 0

    async def _update_reiatsu(self, user_id: str, new_points: int):
        supabase.table("reiatsu").update({"points": new_points}).eq("user_id", user_id).execute()

    async def _get_one_steam_key(self):
        resp = supabase.table("steam_keys").select("*").eq("won", False).limit(1).execute()
        if resp.data and len(resp.data) > 0:
            return resp.data[0]
        return None

    async def _mark_steam_key_won(self, key_id: int, winner: str):
        supabase.table("steam_keys").update({"won": True, "winner": winner}).eq("id", key_id).execute()

    # ─────────── Logique du jeu ───────────
    async def _try_win_key(self, interaction_or_ctx):
        user_id = str(interaction_or_ctx.user.id)
        reiatsu_points = await self._get_reiatsu(user_id)

        if reiatsu_points < REIATSU_COST:
            msg = f"❌ Tu n'as pas assez de Reiatsu (il te faut {REIATSU_COST})."
            if isinstance(interaction_or_ctx, discord.Interaction):
                await interaction_or_ctx.followup.send(msg, ephemeral=True)
            else:
                await safe_send(interaction_or_ctx.channel, msg)
            return

        await self._update_reiatsu(user_id, reiatsu_points - REIATSU_COST)

        if random.random() <= WIN_CHANCE:
            key = await self._get_one_steam_key()
            if not key:
                embed = discord.Embed(title="🎮 Jeu Steam Key", description="🎉 Gagné ! Mais plus de clés 😢", color=discord.Color.gold())
                await self._send(interaction_or_ctx, embed)
                return

            # Embed avec options (clé, refresh, refus)
            embed = discord.Embed(title="🎉 Félicitations !", description="Tu as gagné une clé Steam !", color=discord.Color.green())
            embed.add_field(name="Jeu", value=key["game_name"], inline=True)
            embed.add_field(name="Lien Steam", value=f"[Voir sur Steam]({key['steam_url']})", inline=True)
            embed.set_footer(text="Choisis si tu veux la clé ou tirer un autre jeu.")

            view = ConfirmKeyView(interaction_or_ctx.user.id)
            msg = await self._send(interaction_or_ctx, embed, view)
            await view.wait()

            if view.refresh:
                # Relance un nouveau jeu sans consommer de Reiatsu
                await safe_edit(msg, embed=discord.Embed(title="🔄 Nouveau jeu en cours...", color=discord.Color.blurple()), view=None)
                await self._try_win_key(interaction_or_ctx)
                return

            if view.confirmed:
                await self._mark_steam_key_won(key["id"], interaction_or_ctx.user.name)
                try:
                    await interaction_or_ctx.user.send(f"🎁 **Clé Steam pour {key['game_name']}**\n`{key['steam_key']}`")
                    await safe_edit(msg, embed=discord.Embed(title="✅ Clé envoyée en DM !", color=discord.Color.green()), view=None)
                except discord.Forbidden:
                    await safe_edit(msg, embed=discord.Embed(title="⚠️ Impossible d'envoyer un DM. Active-les et réessaie.", color=discord.Color.orange()), view=None)
            else:
                await safe_edit(msg, embed=discord.Embed(title="🔄 Clé laissée dispo pour les autres joueurs.", color=discord.Color.blurple()), view=None)

        else:
            # Si perdu → pas de bouton, juste un embed rouge
            await self._send(interaction_or_ctx, discord.Embed(
                title="Dommage !",
                description="❌ Tu n'as pas gagné cette fois, retente ta chance !",
                color=discord.Color.red()
            ))

    async def _send(self, interaction_or_ctx, embed, view=None):
        if isinstance(interaction_or_ctx, discord.Interaction):
            return await interaction_or_ctx.followup.send(embed=embed, view=view)
        return await safe_send(interaction_or_ctx.channel, embed=embed, view=view)

    # ─────────── Commande SLASH ───────────
    @app_commands.command(name="steamkey", description="Miser des Reiatsu pour tenter de gagner une clé Steam")
    async def slash_steamkey(self, interaction: discord.Interaction):
        try:
            view = await self._send_menu(interaction.channel, interaction.user.id)
            await view.wait()
            if view.value:
                await self._try_win_key(view.last_interaction)
            else:
                for child in view.children:
                    child.disabled = True
                msg = await interaction.original_response()
                await safe_edit(msg, view=view)
                await safe_respond(interaction, "⏰ Temps écoulé.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /steamkey] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ─────────── Commande PREFIX ───────────
    @commands.command(name="steamkey", aliases=["sk"])
    async def prefix_steamkey(self, ctx: commands.Context):
        try:
            view = await self._send_menu(ctx.channel, ctx.author.id)
            await view.wait()
            if view.value:
                class DummyInteraction:
                    def __init__(self, user, channel): self.user, self.channel = user, channel
                await self._try_win_key(DummyInteraction(ctx.author, ctx.channel))
            else:
                await safe_send(ctx.channel, "⏰ Temps écoulé.")
        except Exception as e:
            print(f"[ERREUR !steamkey] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

    async def _send_menu(self, channel, user_id: int):
        keys_resp = supabase.table("steam_keys").select("game_name").eq("won", False).execute()
        nb_keys = len(keys_resp.data) if keys_resp.data else 0
        games = set(k["game_name"] for k in keys_resp.data) if keys_resp.data else set()

        if nb_keys == 0:
            embed = discord.Embed(title="🎮 Jeu Steam Key", description="❌ Aucun jeu disponible pour le moment.", color=discord.Color.red())
            await safe_send(channel, embed=embed)
            return SteamKeyView(user_id)

        embed = discord.Embed(title="🎮 Jeu Steam Key", description=f"Miser {REIATSU_COST} Reiatsu pour une chance de gagner une clé Steam.", color=discord.Color.blurple())
        embed.add_field(name="Probabilité de gagner", value="50%", inline=False)
        embed.add_field(name="Clés restantes", value=str(nb_keys), inline=False)
        embed.add_field(name="Jeux dispo", value=", ".join(games) if games else "Aucun", inline=True)
        embed.set_footer(text="Vous avez 2 minutes pour miser.")
        view = SteamKeyView(user_id)
        await safe_send(channel, embed=embed, view=view)
        return view

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SteamKey(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
