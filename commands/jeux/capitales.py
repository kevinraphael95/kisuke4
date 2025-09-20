# ────────────────────────────────────────────────────────────────────────────────
# 📌 capitales.py — Commande interactive /capitales et !capitales
# Objectif : Deviner la capitale d'un pays
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
from discord.ui import View, Modal, TextInput, Button
import random, asyncio, unicodedata
from utils.discord_utils import safe_send, safe_respond, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Liste des pays et leurs capitales
# ────────────────────────────────────────────────────────────────────────────────
CAPITALS = {
    "Afghanistan": "Kaboul",
    "Afrique du Sud": "Pretoria",
    "Albanie": "Tirana",
    "Algérie": "Alger",
    "Allemagne": "Berlin",
    "Andorre": "Andorre-la-Vieille",
    "Angola": "Luanda",
    "Antigua-et-Barbuda": "Saint-Jean",
    "Arabie saoudite": "Riyad",
    "Argentine": "Buenos Aires",
    "Arménie": "Erevan",
    "Australie": "Canberra",
    "Autriche": "Vienne",
    "Azerbaïdjan": "Bakou",
    "Bahamas": "Nassau",
    "Bahreïn": "Manama",
    "Bangladesh": "Dacca",
    "Barbade": "Bridgetown",
    "Belgique": "Bruxelles",
    "Belize": "Belmopan",
    "Bénin": "Porto-Novo",
    "Bhoutan": "Thimphou",
    "Biélorussie": "Minsk",
    "Birmanie": "Naypyidaw",
    "Bolivie": "Sucre",
    "Bosnie-Herzégovine": "Sarajevo",
    "Botswana": "Gaborone",
    "Brésil": "Brasília",
    "Brunei": "Bandar Seri Begawan",
    "Bulgarie": "Sofia",
    "Burkina Faso": "Ouagadougou",
    "Burundi": "Gitega",
    "Cambodge": "Phnom Penh",
    "Cameroun": "Yaoundé",
    "Canada": "Ottawa",
    "Cap-Vert": "Praia",
    "Chili": "Santiago",
    "Chine": "Pékin",
    "Chypre": "Nicosie",
    "Colombie": "Bogotá",
    "Comores": "Moroni",
    "Congo": "Brazzaville",
    "Corée du Nord": "Pyongyang",
    "Corée du Sud": "Séoul",
    "Costa Rica": "San José",
    "Croatie": "Zagreb",
    "Cuba": "La Havane",
    "Danemark": "Copenhague",
    "Djibouti": "Djibouti",
    "Dominique": "Roseau",
    "Égypte": "Le Caire",
    "Émirats arabes unis": "Abou Dabi",
    "Équateur": "Quito",
    "Érythrée": "Asmara",
    "Espagne": "Madrid",
    "Estonie": "Tallinn",
    "Eswatini": "Mbabane",
    "États-Unis": "Washington, D.C.",
    "Éthiopie": "Addis-Abeba",
    "Fidji": "Suva",
    "Finlande": "Helsinki",
    "France": "Paris",
    "Gabon": "Libreville",
    "Gambie": "Banjul",
    "Géorgie": "Tbilissi",
    "Ghana": "Accra",
    "Grèce": "Athènes",
    "Grenade": "Saint-Georges",
    "Guatemala": "Guatemala",
    "Guinée": "Conakry",
    "Guinée-Bissau": "Bissau",
    "Guinée équatoriale": "Malabo",
    "Guyana": "Georgetown",
    "Haïti": "Port-au-Prince",
    "Honduras": "Tegucigalpa",
    "Hongrie": "Budapest",
    "Îles Marshall": "Majuro",
    "Îles Salomon": "Honiara",
    "Inde": "New Delhi",
    "Indonésie": "Jakarta",
    "Iran": "Téhéran",
    "Irak": "Bagdad",
    "Irlande": "Dublin",
    "Islande": "Reykjavik",
    "Israël": "Jérusalem",
    "Italie": "Rome",
    "Jamaïque": "Kingston",
    "Japon": "Tokyo",
    "Jordanie": "Amman",
    "Kazakhstan": "Noursoultan",
    "Kenya": "Nairobi",
    "Kirghizistan": "Bichkek",
    "Kiribati": "Tarawa",
    "Koweït": "Koweït",
    "Laos": "Vientiane",
    "Lesotho": "Maseru",
    "Lettonie": "Riga",
    "Liban": "Beyrouth",
    "Liberia": "Monrovia",
    "Libye": "Tripoli",
    "Liechtenstein": "Vaduz",
    "Lituanie": "Vilnius",
    "Luxembourg": "Luxembourg",
    "Madagascar": "Antananarivo",
    "Malaisie": "Kuala Lumpur",
    "Malawi": "Lilongwe",
    "Maldives": "Malé",
    "Mali": "Bamako",
    "Malte": "La Valette",
    "Maroc": "Rabat",
    "Maurice": "Port-Louis",
    "Mauritanie": "Nouakchott",
    "Mexique": "Mexico",
    "Micronésie": "Palikir",
    "Moldavie": "Chișinău",
    "Monaco": "Monaco",
    "Mongolie": "Oulan-Bator",
    "Monténégro": "Podgorica",
    "Mozambique": "Maputo",
    "Namibie": "Windhoek",
    "Nauru": "Yaren",
    "Népal": "Katmandou",
    "Nicaragua": "Managua",
    "Niger": "Niamey",
    "Nigéria": "Abuja",
    "Norvège": "Oslo",
    "Nouvelle-Zélande": "Wellington",
    "Oman": "Mascate",
    "Ouganda": "Kampala",
    "Ouzbékistan": "Tachkent",
    "Pakistan": "Islamabad",
    "Palaos": "Ngerulmud",
    "Panama": "Panama",
    "Papouasie-Nouvelle-Guinée": "Port-Moresby",
    "Paraguay": "Asuncion",
    "Pays-Bas": "Amsterdam",
    "Pérou": "Lima",
    "Philippines": "Manille",
    "Pologne": "Varsovie",
    "Portugal": "Lisbonne",
    "Qatar": "Doha",
    "République centrafricaine": "Bangui",
    "République dominicaine": "Saint-Domingue",
    "République tchèque": "Prague",
    "Roumanie": "Bucarest",
    "Royaume-Uni": "Londres",
    "Russie": "Moscou",
    "Rwanda": "Kigali",
    "Saint-Christophe-et-Niévès": "Basseterre",
    "Saint-Marin": "Saint-Marin",
    "Saint-Vincent-et-les-Grenadines": "Kingstown",
    "Salvador": "San Salvador",
    "Samoa": "Apia",
    "Sao Tomé-et-Principe": "São Tomé",
    "Sénégal": "Dakar",
    "Serbie": "Belgrade",
    "Seychelles": "Victoria",
    "Sierra Leone": "Freetown",
    "Singapour": "Singapour",
    "Slovaquie": "Bratislava",
    "Slovénie": "Ljubljana",
    "Somalie": "Mogadiscio",
    "Soudan": "Khartoum",
    "Soudan du Sud": "Djouba",
    "Sri Lanka": "Sri Jayawardenepura Kotte",
    "Suède": "Stockholm",
    "Suisse": "Berne",
    "Syrie": "Damas",
    "Taïwan": "Taipei",
    "Tadjikistan": "Douchanbé",
    "Tanzanie": "Dodoma",
    "Thaïlande": "Bangkok",
    "Timor oriental": "Dili",
    "Togo": "Lomé",
    "Tonga": "Nukuʻalofa",
    "Trinité-et-Tobago": "Port-d'Espagne",
    "Tunisie": "Tunis",
    "Turkménistan": "Achgabat",
    "Turquie": "Ankara",
    "Tuvalu": "Funafuti",
    "Ukraine": "Kiev",
    "Uruguay": "Montevideo",
    "Vanuatu": "Port-Vila",
    "Vatican": "Cité du Vatican",
    "Venezuela": "Caracas",
    "Viêt Nam": "Hanoï",
    "Yémen": "Sanaa",
    "Zambie": "Lusaka",
    "Zimbabwe": "Harare"
}

def normalize_text(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    ).strip()

# ────────────────────────────────────────────────────────────────────────────────
# 📝 Modal (formulaire de réponse)
# ────────────────────────────────────────────────────────────────────────────────
class AnswerModal(Modal, title="🖊️ Devine la capitale"):
    def __init__(self, country: str, winners: list, multi: bool, quiz_msg: discord.Message, view: View):
        super().__init__(timeout=None)
        self.country = country
        self.capital = normalize_text(CAPITALS[country])
        self.winners = winners
        self.multi = multi
        self.quiz_msg = quiz_msg
        self.view = view
        self.answer = TextInput(
            label="Entre la capitale",
            placeholder="Exemple : Paris",
            required=True,
            max_length=50
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        user_answer = normalize_text(self.answer.value)
        if user_answer == self.capital:
            if interaction.user not in self.winners:
                self.winners.append(interaction.user)
            await interaction.response.send_message("✅ Bonne réponse !", ephemeral=True)

            if not self.multi and not getattr(self.view, "ended", False):
                self.view.ended = True
                for child in self.view.children:
                    child.disabled = True
                embed = self.quiz_msg.embeds[0]
                embed.add_field(
                    name="🎉 Résultat",
                    value=f"✅ Réponse : **{self.capital}**\n🏆 Gagnant : {interaction.user.mention}",
                    inline=False
                )
                await self.quiz_msg.edit(embed=embed, view=self.view)
                self.view.stop()
        else:
            await interaction.response.send_message("❌ Mauvaise réponse !", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue interactive
# ────────────────────────────────────────────────────────────────────────────────
class CapitalQuizView(View):
    def __init__(self, country: str, winners: list, multi: bool, quiz_msg: discord.Message = None):
        super().__init__(timeout=None)
        self.country = country
        self.winners = winners
        self.multi = multi
        self.quiz_msg = quiz_msg
        self.ended = False

    @discord.ui.button(label="Répondre", style=discord.ButtonStyle.primary, emoji="✍️")
    async def answer_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(AnswerModal(self.country, self.winners, self.multi, self.quiz_msg, self))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Capitales(commands.Cog):
    """Commande /capitales et !capitales — Deviner la capitale d'un pays"""
    SOLO_TIME = 120
    MULTI_TIME = 120

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🔹 Fonction interne commune
    async def _send_quiz(self, channel, user=None, multi=False):
        country = random.choice(list(CAPITALS.keys()))
        capital = CAPITALS[country]
        winners = []

        title = "Devine la Capitale - Mode Multijoueur 🌍" if multi else "Devine la Capitale - Mode Solo 🧍‍♂️"
        footer_text = f"⏱️ Temps : {self.MULTI_TIME if multi else self.SOLO_TIME} secondes"

        embed = discord.Embed(
            title=title,
            description=f"Quel est la capitale de **{country}** ?\nAppuie sur **Répondre** pour proposer ta réponse.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=footer_text)

        view = CapitalQuizView(country, winners, multi)
        quiz_msg = await safe_send(channel, embed=embed, view=view)
        view.quiz_msg = quiz_msg

        try:
            await asyncio.sleep(self.MULTI_TIME if multi else self.SOLO_TIME)
        except asyncio.CancelledError:
            return

        if view.ended:
            return

        embed = quiz_msg.embeds[0]
        if winners:
            embed.add_field(
                name="🎉 Résultat",
                value=f"✅ Réponse : **{capital}**\n🏆 Gagnants : {', '.join(w.mention for w in set(winners))}",
                inline=False
            )
        else:
            embed.add_field(
                name="🎉 Résultat",
                value=f"❌ Personne n'a trouvé. C'était **{capital}**.",
                inline=False
            )

        for child in view.children:
            child.disabled = True
        await quiz_msg.edit(embed=embed, view=view)

    # 🔹 Commande SLASH
    @app_commands.command(name="capitales", description="Devine la capitale d'un pays")
    @app_commands.describe(mode="Tapez 'm' ou 'multi' pour le mode multijoueur")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def slash_capitales(self, interaction: discord.Interaction, mode: str = None):
        try:
            await interaction.response.defer()
            multi = mode is not None and mode.lower() in ["m", "multi"]
            await self._send_quiz(interaction.channel, interaction.user, multi=multi)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /capitales] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # 🔹 Commande PREFIX
    @commands.command(name="capitales")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_capitales(self, ctx: commands.Context, *, arg: str = None):
        try:
            multi = arg is not None and arg.lower() in ["m", "multi"]
            await self._send_quiz(ctx.channel, ctx.author, multi=multi)
        except Exception as e:
            print(f"[ERREUR !capitales] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Capitales(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
