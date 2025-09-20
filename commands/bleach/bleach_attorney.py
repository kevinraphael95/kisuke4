# ────────────────────────────────────────────────────────────────────────────────
# 📌 bleach_attorney.py — Mini-jeu interactif complet Ace Attorney version Bleach
# Objectif : Jeu complet avec dialogues, indices, témoignages, contradictions et objections
# Catégorie : Bleach
# Accès : Tous
# Cooldown : 1 utilisation / 15 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import json
import os

from utils.discord_utils import safe_send, safe_edit, safe_respond, safe_delete

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des histoires JSON
# ────────────────────────────────────────────────────────────────────────────────
STORIES_JSON_PATH = os.path.join("data", "ace_bleach_stories.json")

def load_stories():
    try:
        with open(STORIES_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {STORIES_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Sélection d'histoire et gameplay
# ────────────────────────────────────────────────────────────────────────────────
class StorySelectionView(View):
    def __init__(self, bot, stories):
        super().__init__(timeout=120)
        self.bot = bot
        self.stories = stories
        self.message = None
        for title in stories.keys():
            self.add_item(StoryButton(self, title))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)

class StoryButton(Button):
    def __init__(self, parent_view: StorySelectionView, story_title):
        super().__init__(label=story_title, style=discord.ButtonStyle.primary)
        self.parent_view = parent_view
        self.story_title = story_title

    async def callback(self, interaction: discord.Interaction):
        story_data = self.parent_view.stories[self.story_title]
        first_scene_id = story_data['scenes'][0]['id']
        await self.parent_view.bot.get_cog('AceBleach')._start_scene(interaction.channel, story_data, first_scene_id)
        await safe_edit(interaction.message, content=f"📚 Histoire choisie : **{self.story_title}**", embed=None, view=None)

# ────────────────────────────────────────────────────────────────────────────────
class GameButtonView(View):
    def __init__(self, bot, story_data, current_scene_id, evidence=[]):
        super().__init__(timeout=300)
        self.bot = bot
        self.story_data = story_data
        self.current_scene_id = current_scene_id
        self.message = None
        self.evidence = evidence
        self.add_scene_buttons()

    def add_scene_buttons(self):
        self.clear_items()
        scene = self.story_data['scenes'][self.current_scene_id]
        for choice in scene.get('choices', []):
            self.add_item(SceneChoiceButton(self, choice))
        for objection in scene.get('objections', []):
            self.add_item(ObjectionButton(self, objection))
        if self.evidence:
            self.add_item(ExamineEvidenceButton(self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)

class SceneChoiceButton(Button):
    def __init__(self, parent_view: GameButtonView, choice_data):
        super().__init__(label=choice_data['text'], style=discord.ButtonStyle.primary)
        self.parent_view = parent_view
        self.choice_data = choice_data

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.current_scene_id = self.choice_data['next_scene']
        await self.parent_view.show_scene(interaction)

class ObjectionButton(Button):
    def __init__(self, parent_view: GameButtonView, objection_data):
        super().__init__(label=f"Objection: {objection_data['text']}", style=discord.ButtonStyle.danger)
        self.parent_view = parent_view
        self.objection_data = objection_data

    async def callback(self, interaction: discord.Interaction):
        valid = self.objection_data.get('valid', False)
        content = "✅ Objection réussie !" if valid else "❌ Objection échouée !"
        next_scene_id = self.objection_data.get('next_scene', self.parent_view.current_scene_id)
        self.parent_view.current_scene_id = next_scene_id
        await safe_edit(interaction.message, content=content, embed=None, view=self.parent_view)

class ExamineEvidenceButton(Button):
    def __init__(self, parent_view: GameButtonView):
        super().__init__(label="Examiner preuves", style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        evidences = self.parent_view.evidence
        if not evidences:
            await safe_respond(interaction, "❌ Aucune preuve à examiner.", ephemeral=True)
            return
        text = "\n".join(f"• {ev}" for ev in evidences)
        await safe_respond(interaction, f"📂 Preuves disponibles :\n{text}", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class AceBleach(commands.Cog):
    """Mini-jeu complet Ace Attorney avec dialogues, preuves, objections et scènes interactives."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_story_selection(self, channel: discord.abc.Messageable):
        stories = load_stories()
        if not stories:
            await safe_send(channel, "❌ Aucune histoire disponible.")
            return
        view = StorySelectionView(self.bot, stories)
        view.message = await safe_send(channel, "📚 Choisis ton histoire Bleach :", view=view)

    async def _start_scene(self, channel, story_data, scene_id):
        scene = story_data['scenes'][scene_id]
        embed = discord.Embed(
            title=f"📖 {scene.get('character', '???')}",
            description=scene.get('dialogue', ''),
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Expression: {scene.get('expression', 'neutre')}")
        evidence = story_data.get('evidence', [])
        view = GameButtonView(self.bot, story_data, scene_id, evidence)
        view.message = await safe_send(channel, embed=embed, view=view)

        async def show_scene(interaction):
            scene = story_data['scenes'][view.current_scene_id]
            embed = discord.Embed(
                title=f"📖 {scene.get('character', '???')}",
                description=scene.get('dialogue', ''),
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"Expression: {scene.get('expression', 'neutre')}")
            view.add_scene_buttons()
            await safe_edit(interaction.message, embed=embed, view=view)

        view.show_scene = show_scene

    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="bleach_attorney", description="Lance le mini-jeu Ace Attorney version Bleach.")
    @app_commands.checks.cooldown(1, 15.0, key=lambda i: (i.user.id))
    async def slash_ace_bleach(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._send_story_selection(interaction.channel)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /ace_bleach] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="bleach_attorney", aliases=["bleach attorney", "ba"])
    @commands.cooldown(1, 15.0, commands.BucketType.user)
    async def prefix_ace_bleach(self, ctx: commands.Context):
        try:
            await self._send_story_selection(ctx.channel)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !ace_bleach] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = AceBleach(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
