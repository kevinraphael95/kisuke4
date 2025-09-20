# ────────────────────────────────────────────────────────────────────────────────
# 📌 drapeaux.py — Commande interactive /drapeaux et !drapeaux
# Objectif : Deviner le pays à partir d'un drapeau aléatoire (tous les pays)
# Modes : Solo (1 joueur, 2 minutes) et Multi (plusieurs joueurs, 2 minutes)
# Réponses : via bouton "Répondre" et formulaire (Modal)
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import random, asyncio, unicodedata

from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Liste complète des pays et codes ISO (inchangée)
# ────────────────────────────────────────────────────────────────────────────────
COUNTRIES = {
    "Afghanistan": "af", "Afrique du Sud": "za", "Albanie": "al", "Algérie": "dz",
    "Allemagne": "de", "Andorre": "ad", "Angola": "ao", "Antigua-et-Barbuda": "ag",
    "Arabie saoudite": "sa", "Argentine": "ar", "Arménie": "am", "Australie": "au",
    "Autriche": "at", "Azerbaïdjan": "az", "Bahamas": "bs", "Bahreïn": "bh",
    "Bangladesh": "bd", "Barbade": "bb", "Belgique": "be", "Belize": "bz",
    "Bénin": "bj", "Bhoutan": "bt", "Biélorussie": "by", "Birmanie": "mm",
    "Bolivie": "bo", "Bosnie-Herzégovine": "ba", "Botswana": "bw", "Brésil": "br",
    "Brunei": "bn", "Bulgarie": "bg", "Burkina Faso": "bf", "Burundi": "bi",
    "Cambodge": "kh", "Cameroun": "cm", "Canada": "ca", "Cap-Vert": "cv",
    "Chili": "cl", "Chine": "cn", "Chypre": "cy", "Colombie": "co",
    "Comores": "km", "Congo": "cg", "Corée du Nord": "kp", "Corée du Sud": "kr",
    "Costa Rica": "cr", "Croatie": "hr", "Cuba": "cu", "Danemark": "dk",
    "Djibouti": "dj", "Dominique": "dm", "Égypte": "eg", "Émirats arabes unis": "ae",
    "Équateur": "ec", "Érythrée": "er", "Espagne": "es", "Estonie": "ee",
    "Eswatini": "sz", "États-Unis": "us", "Éthiopie": "et", "Fidji": "fj",
    "Finlande": "fi", "France": "fr", "Gabon": "ga", "Gambie": "gm",
    "Géorgie": "ge", "Ghana": "gh", "Grèce": "gr", "Grenade": "gd",
    "Guatemala": "gt", "Guinée": "gn", "Guinée-Bissau": "gw", "Guinée équatoriale": "gq",
    "Guyana": "gy", "Haïti": "ht", "Honduras": "hn", "Hongrie": "hu",
    "Îles Marshall": "mh", "Îles Salomon": "sb", "Inde": "in", "Indonésie": "id",
    "Iran": "ir", "Irak": "iq", "Irlande": "ie", "Islande": "is",
    "Israël": "il", "Italie": "it", "Jamaïque": "jm", "Japon": "jp",
    "Jordanie": "jo", "Kazakhstan": "kz", "Kenya": "ke", "Kirghizistan": "kg",
    "Kiribati": "ki", "Koweït": "kw", "Laos": "la", "Lesotho": "ls",
    "Lettonie": "lv", "Liban": "lb", "Liberia": "lr", "Libye": "ly",
    "Liechtenstein": "li", "Lituanie": "lt", "Luxembourg": "lu", "Madagascar": "mg",
    "Malaisie": "my", "Malawi": "mw", "Maldives": "mv", "Mali": "ml",
    "Malte": "mt", "Maroc": "ma", "Maurice": "mu", "Mauritanie": "mr",
    "Mexique": "mx", "Micronésie": "fm", "Moldavie": "md", "Monaco": "mc",
    "Mongolie": "mn", "Monténégro": "me", "Mozambique": "mz", "Namibie": "na",
    "Nauru": "nr", "Népal": "np", "Nicaragua": "ni", "Niger": "ne",
    "Nigéria": "ng", "Norvège": "no", "Nouvelle-Zélande": "nz", "Oman": "om",
    "Ouganda": "ug", "Ouzbékistan": "uz", "Pakistan": "pk", "Palaos": "pw",
    "Panama": "pa", "Papouasie-Nouvelle-Guinée": "pg", "Paraguay": "py", "Pays-Bas": "nl",
    "Pérou": "pe", "Philippines": "ph", "Pologne": "pl", "Portugal": "pt",
    "Qatar": "qa", "République centrafricaine": "cf", "République dominicaine": "do",
    "République tchèque": "cz", "Roumanie": "ro", "Royaume-Uni": "gb", "Russie": "ru",
    "Rwanda": "rw", "Saint-Christophe-et-Niévès": "kn", "Sainte-Lucie": "lc",
    "Saint-Marin": "sm", "Saint-Vincent-et-les-Grenadines": "vc", "Salvador": "sv",
    "Samoa": "ws", "Sao Tomé-et-Principe": "st", "Sénégal": "sn", "Serbie": "rs",
    "Seychelles": "sc", "Sierra Leone": "sl", "Singapour": "sg", "Slovaquie": "sk",
    "Slovénie": "si", "Somalie": "so", "Soudan": "sd", "Soudan du Sud": "ss",
    "Sri Lanka": "lk", "Suède": "se", "Suisse": "ch", "Syrie": "sy",
    "Taïwan": "tw", "Tadjikistan": "tj", "Tanzanie": "tz", "Thaïlande": "th",
    "Timor oriental": "tl", "Togo": "tg", "Tonga": "to", "Trinité-et-Tobago": "tt",
    "Tunisie": "tn", "Turkménistan": "tm", "Turquie": "tr", "Tuvalu": "tv",
    "Ukraine": "ua", "Uruguay": "uy", "Vanuatu": "vu", "Vatican": "va",
    "Venezuela": "ve", "Viêt Nam": "vn", "Yémen": "ye", "Zambie": "zm",
    "Zimbabwe": "zw"
}


def get_flag_url(iso_code: str) -> str:
    return f"https://flagcdn.com/w320/{iso_code}.png"

def normalize_text(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    ).strip()

# ────────────────────────────────────────────────────────────────────────────────
# 📝 Modal (formulaire de réponse)
# ────────────────────────────────────────────────────────────────────────────────
class AnswerModal(discord.ui.Modal, title="🖊️ Devine le pays"):
    def __init__(self, country: str, winners: list, multi: bool, quiz_msg: discord.Message, view: discord.ui.View):
        super().__init__(timeout=None)
        self.country = country
        self.normalized_country = normalize_text(country)
        self.winners = winners
        self.multi = multi
        self.quiz_msg = quiz_msg
        self.view = view

        self.answer = discord.ui.TextInput(
            label="Entre le nom du pays",
            placeholder="Exemple : France",
            required=True,
            max_length=50
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        user_answer = normalize_text(self.answer.value)
        if user_answer == self.normalized_country:
            if interaction.user not in self.winners:
                self.winners.append(interaction.user)
            await interaction.response.send_message("✅ Bonne réponse !", ephemeral=True)

            # 💡 Si mode solo → fin immédiate du quiz
            if not self.multi and not getattr(self.view, "ended", False):
                self.view.ended = True  # ✅ On marque la partie comme terminée
                for child in self.view.children:
                    child.disabled = True
                embed = self.quiz_msg.embeds[0]
                embed.add_field(
                    name="🎉 Résultat",
                    value=f"✅ Réponse : **{self.country}**\n🏆 Gagnant : {interaction.user.mention}",
                    inline=False
                )
                await self.quiz_msg.edit(embed=embed, view=self.view)
                self.view.stop()
        else:
            await interaction.response.send_message("❌ Mauvaise réponse !", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue interactive — bouton "Répondre"
# ────────────────────────────────────────────────────────────────────────────────
class FlagQuizView(discord.ui.View):
    def __init__(self, country: str, winners: list, multi: bool, quiz_msg: discord.Message = None):
        super().__init__(timeout=None)
        self.country = country
        self.winners = winners
        self.multi = multi
        self.quiz_msg = quiz_msg
        self.ended = False  # ✅ Flag pour savoir si le quiz est terminé

    @discord.ui.button(label="Répondre", style=discord.ButtonStyle.primary, emoji="✍️")
    async def answer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnswerModal(self.country, self.winners, self.multi, self.quiz_msg, self))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Drapeaux(commands.Cog):
    """Commande /drapeaux et !drapeaux — Deviner le pays à partir d'un drapeau"""

    SOLO_TIME = 120  # ⏱ facilement modifiable (en secondes)
    MULTI_TIME = 120

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_quiz(self, channel, user=None, multi=False):
        country, iso_code = random.choice(list(COUNTRIES.items()))
        flag_url = get_flag_url(iso_code)
        winners = []

        embed = discord.Embed(
            title="🌍 Devine le pays !",
            description="Appuie sur **Répondre** pour envoyer ta proposition."
                        + ("\n⏳ **Mode Multi :** vous avez 2 minutes pour répondre." if multi else "\n⏳ **Mode Solo :** tu as 2 minutes pour répondre."),
            color=discord.Color.blurple()
        )
        embed.set_image(url=flag_url)

        view = FlagQuizView(country, winners, multi)
        quiz_msg = await safe_send(channel, embed=embed, view=view)
        view.quiz_msg = quiz_msg  # injection du message dans la vue

        try:
            await asyncio.sleep(self.MULTI_TIME if multi else self.SOLO_TIME)
        except asyncio.CancelledError:
            return

        # ✅ Si le quiz a déjà été terminé (solo), ne rien faire
        if view.ended:
            return

        embed = quiz_msg.embeds[0]
        if winners:
            embed.add_field(
                name="🎉 Résultat",
                value=f"✅ Réponse : **{country}**\n🏆 Gagnants : {', '.join(w.mention for w in set(winners))}",
                inline=False
            )
        else:
            embed.add_field(
                name="🎉 Résultat",
                value=f"❌ Personne n'a trouvé. C'était **{country}**.",
                inline=False
            )

        for child in view.children:
            child.disabled = True

        await quiz_msg.edit(embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="drapeaux", description="Devine le pays à partir d'un drapeau")
    @app_commands.describe(mode="Tapez 'm' ou 'multi' pour le mode multijoueur")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def slash_drapeaux(self, interaction: discord.Interaction, mode: str = None):
        try:
            await interaction.response.defer()
            if mode is None:
                await self._send_quiz(interaction.channel, interaction.user, multi=False)
            elif mode.lower() in ["m", "multi"]:
                await self._send_quiz(interaction.channel, interaction.user, multi=True)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /drapeaux] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────
    @commands.command(name="drapeaux")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_drapeaux(self, ctx: commands.Context, *, arg: str = None):
        try:
            if arg is None:
                await self._send_quiz(ctx.channel, ctx.author, multi=False)
            elif arg.lower() in ["m", "multi"]:
                await self._send_quiz(ctx.channel, ctx.author, multi=True)
        except Exception as e:
            print(f"[ERREUR !drapeaux] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Drapeaux(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
