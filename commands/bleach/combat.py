# ────────────────────────────────────────────────────────────────────────────────
# 📌 bleach_pokemon_combat.py — Mini-jeu interactif style Pokémon / Bleach
# Objectif : Duel interactif avec choix de perso, stats, types, attaques et ultimes
# Catégorie : Jeu / Combat
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
import json
import os
import random

from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Fichier JSON des persos
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "combat.json")

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Charger les persos
# ────────────────────────────────────────────────────────────────────────────────
def load_characters():
    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {DATA_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Type chart (faiblesses / forces)
# ────────────────────────────────────────────────────────────────────────────────
TYPE_CHART = {
    "Shinigami": {"strong": ["Quincy"], "weak": ["Arrancar"]},
    "Arrancar": {"strong": ["Shinigami"], "weak": ["Quincy"]},
    "Quincy": {"strong": ["Arrancar"], "weak": ["Shinigami"]},
    "Hollow": {"strong": ["Shinigami"], "weak": ["Quincy"]}
}

def type_modifier(attack_type, target_type):
    if target_type in TYPE_CHART.get(attack_type, {}).get("strong", []):
        return 1.5
    elif target_type in TYPE_CHART.get(attack_type, {}).get("weak", []):
        return 0.5
    return 1.0

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Sélection de personnage
# ────────────────────────────────────────────────────────────────────────────────
class CharacterSelectView(View):
    def __init__(self, bot, user):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user
        self.message = None
        self.selected = None
        characters = load_characters()
        options = [discord.SelectOption(label=name) for name in characters.keys()]
        self.add_item(CharacterSelect(options, self))

class CharacterSelect(Select):
    def __init__(self, options, parent_view):
        self.parent_view = parent_view
        super().__init__(placeholder="Choisis ton personnage", options=options)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected = self.values[0]
        await safe_edit(interaction.message, content=f"🎮 {interaction.user.name} a choisi **{self.values[0]}**!", view=None)
        # Lance le duel automatiquement après sélection
        await self.parent_view.bot.get_cog('BleachPokemonCombat')._start_duel(interaction.channel, interaction.user.name, self.values[0])

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Menu combat interactif
# ────────────────────────────────────────────────────────────────────────────────
class AttackSelectView(View):
    def __init__(self, bot, player, enemy):
        super().__init__(timeout=120)
        self.bot = bot
        self.player = player
        self.enemy = enemy
        self.message = None
        self.add_item(AttackSelect(self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)

class AttackSelect(Select):
    def __init__(self, parent_view: AttackSelectView):
        self.parent_view = parent_view
        options = []
        for atk_name, atk_data in parent_view.player["moves"].items():
            desc = f"Type: {atk_data['type']}, Power: {atk_data.get('power',0)}"
            if atk_data.get('cooldown'):
                desc += ", Ultime"
            options.append(discord.SelectOption(label=atk_name, description=desc))
        super().__init__(placeholder="Choisis ton attaque", options=options)

    async def callback(self, interaction: discord.Interaction):
        player = self.parent_view.player
        enemy = self.parent_view.enemy
        atk_name = self.values[0]
        atk = player["moves"][atk_name]

        # IA choisit son attaque
        enemy_atk_name, enemy_atk = self.choose_ai_attack(enemy, player)

        # Calcul dégâts
        dmg_to_enemy = max(int((atk.get('power',0) + player['stats'].get('REI',0)) * type_modifier(atk['type'], enemy['type'])) - enemy['stats'].get('TEC',0),0)
        dmg_to_player = max(int((enemy_atk.get('power',0) + enemy['stats'].get('REI',0)) * type_modifier(enemy_atk['type'], player['type'])) - player['stats'].get('TEC',0),0)

        enemy['stats']['HP'] -= dmg_to_enemy
        player['stats']['HP'] -= dmg_to_player

        embed = discord.Embed(title=f"💥 Combat : {player['name']} VS {enemy['name']}", color=discord.Color.purple())
        embed.add_field(name=f"{player['name']} utilise", value=f"{atk_name} (-{dmg_to_enemy} HP)", inline=False)
        embed.add_field(name=f"{enemy['name']} utilise", value=f"{enemy_atk_name} (-{dmg_to_player} HP)", inline=False)
        embed.add_field(name="HP Restant", value=f"{player['name']}: {player['stats']['HP']} | {enemy['name']}: {enemy['stats']['HP']}", inline=False)

        # Fin combat
        if player['stats']['HP'] <=0 and enemy['stats']['HP']<=0:
            embed.title += " - ⚔️ Égalité !"
            self.stop()
        elif player['stats']['HP'] <=0:
            embed.title += f" - 💀 {player['name']} a perdu !"
            self.stop()
        elif enemy['stats']['HP'] <=0:
            embed.title += f" - 🏆 {player['name']} a gagné !"
            self.stop()

        await safe_edit(interaction.message, embed=embed, view=self if self._running else None)

    def choose_ai_attack(self, enemy, player):
        moves_list = list(enemy['moves'].items())
        ult = [m for m in moves_list if m[1].get('cooldown')]
        if enemy['stats']['HP'] < 50 and ult:
            return ult[0]
        return random.choice(moves_list)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class BleachPokemonCombat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="choose_character")
    @commands.cooldown(1, 15.0, commands.BucketType.user)
    async def prefix_choose_character(self, ctx: commands.Context):
        view = CharacterSelectView(self.bot, ctx.author)
        view.message = await ctx.send(f"🎮 {ctx.author.name}, choisis ton personnage :", view=view)

    async def _start_duel(self, channel: discord.abc.Messageable, player_name: str, player_key: str):
        characters = load_characters()
        if not characters:
            await safe_send(channel, "❌ Impossible de charger les personnages.")
            return

        player = characters[player_key]
        player['name'] = player_name

        enemy_key = random.choice([k for k in characters.keys() if k!=player_key])
        enemy = characters[enemy_key]
        enemy['name'] = enemy_key

        view = AttackSelectView(self.bot, player, enemy)
        embed = discord.Embed(title=f"💥 Duel : {player['name']} VS {enemy['name']}" , color=discord.Color.green())
        embed.add_field(name="Combat", value="Choisis ton attaque !", inline=False)
        view.message = await safe_send(channel, embed=embed, view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = BleachPokemonCombat(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
