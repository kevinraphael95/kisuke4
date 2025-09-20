# ──────────────────────────────────────────────────────────────
# 📌 reiatsu.py — Commande principale Reiatsu
# Objectif : Afficher les points et infos Reiatsu d’un joueur
# Catégorie : RPG
# ──────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
from utils.supabase_client import supabase
from utils.discord_utils import safe_send

class Reiatsu(commands.Cog):
    """Affiche et gère le Reiatsu d’un joueur."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reiatsu")
    async def reiatsu_cmd(self, ctx):
        """Affiche les points Reiatsu de l'utilisateur."""
        try:
            data = supabase.table("reiatsu").select("*").eq("user_id", ctx.author.id).execute()
            if not data.data:
                await safe_send(ctx.channel, f"⚠️ {ctx.author.mention}, tu n’as pas encore de Reiatsu !")
                return

            user = data.data[0]
            points = user["points"]
            classe = user["classe"]
            await safe_send(ctx.channel, f"💠 **{ctx.author.display_name}** — Classe : {classe} | Reiatsu : **{points}**")
        except Exception as e:
            print(f"[ERREUR REIATSU] {e}")
            await safe_send(ctx.channel, "❌ Impossible de récupérer ton Reiatsu pour le moment.")

async def setup(bot):
    await bot.add_cog(Reiatsu(bot))
