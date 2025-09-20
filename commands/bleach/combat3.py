# ────────────────────────────────────────────────────────────────────────────────
# 📌 combat.py — Commande interactive !combat
# Objectif : Simule un combat entre 2 personnages de Bleach avec stats, énergie et effets.
# Catégorie : Bleach
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import random
import json
import os

# Import des fonctions utilitaires safe_send
from utils.discord_utils import safe_send

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des personnages
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_personnages.json")

def load_personnages():
    """Charge les personnages depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Fonctions utilitaires du combat
# ────────────────────────────────────────────────────────────────────────────────
def init_personnage(p: dict):
    """Initialise les champs nécessaires pour le combat."""
    p["vie"] = p.get("stats", {}).get("vie", 100)
    p["energie"] = p.get("stats", {}).get("energie", 100)
    p["bouclier"] = 0
    p["status"] = None
    p["status_duree"] = 0
    for attaque in p.get("attaques", []):
        attaque["utilisé"] = False
    return p

def formater_etat(p: dict) -> str:
    """Retourne une ligne formatée avec les PV et énergie."""
    return f"**{p['nom']}** — ❤️ {p['vie']} PV | 🔋 {p['energie']} Énergie | 🛡️ {p['bouclier']}"

def infliger_degats(cible: dict, degats: int, log: str) -> str:
    """Applique des dégâts en tenant compte du bouclier."""
    if cible["bouclier"] > 0:
        absorption = min(cible["bouclier"], degats)
        cible["bouclier"] -= absorption
        degats -= absorption
        log += f"🛡️ Bouclier absorbe {absorption} dégâts.\n"
    if degats > 0:
        cible["vie"] -= degats
        log += f"💢 {cible['nom']} subit {degats} dégâts (PV restants: {cible['vie']}).\n"
    return log

def appliquer_soin(cible: dict, quantite: int, log: str) -> str:
    """Soigne la cible d’un certain montant."""
    cible["vie"] += quantite
    log += f"✨ {cible['nom']} récupère {quantite} PV !\n"
    return log

def appliquer_bouclier(cible: dict, quantite: int, log: str) -> str:
    """Ajoute un bouclier à la cible."""
    cible["bouclier"] += quantite
    log += f"🛡️ {cible['nom']} gagne un bouclier de {quantite} !\n"
    return log

def appliquer_effet(attaque: dict, cible: dict, log: str) -> str:
    """Applique l’effet spécial de l’attaque."""
    effet = attaque.get("effet", "").lower()
    if effet == "soin":
        return appliquer_soin(cible, attaque.get("puissance", 20), log)
    elif effet == "bouclier":
        return appliquer_bouclier(cible, attaque.get("puissance", 20), log)
    elif effet == "poison":
        cible["status"] = "poison"
        cible["status_duree"] = 3
        log += f"☠️ {cible['nom']} est empoisonné pour 3 tours !\n"
    elif effet == "gel":
        cible["status"] = "gel"
        cible["status_duree"] = 1
        log += f"❄️ {cible['nom']} est gelé et perd son prochain tour !\n"
    elif effet == "confusion":
        cible["status"] = "confusion"
        cible["status_duree"] = 2
        log += f"💫 {cible['nom']} est confus !\n"
    return log

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Combat3Command(commands.Cog):
    """Commande !combat3 — Simule un combat entre 2 personnages de Bleach avec stats, énergie et effets."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="combat3",
        help="Simule un combat entre 2 personnages de Bleach.",
        description="Lance un combat automatisé sur 5 tours entre 2 personnages tirés au hasard."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def combat(self, ctx: commands.Context):
        """Commande principale simulant un combat."""
        try:
            personnages = load_personnages()

            if len(personnages) < 2:
                return await safe_send(ctx.channel, "❌ Pas assez de personnages dans le fichier.")

            p1, p2 = random.sample(personnages, 2)
            p1, p2 = init_personnage(p1), init_personnage(p2)

            nom1, nom2 = p1["nom"], p2["nom"]

            # Détermine l'ordre des tours
            tour_order = sorted([p1, p2], key=lambda p: p["stats"]["mobilité"] + random.randint(0, 10), reverse=True)
            log = ""

            for tour in range(1, 6):
                log += f"**🌀 __Tour {tour}__ 🌀**\n{formater_etat(p1)}\n{formater_etat(p2)}\n\n"
                for attaquant in tour_order:
                    defenseur = p2 if attaquant == p1 else p1
                    if attaquant["vie"] <= 0 or defenseur["vie"] <= 0:
                        continue

                    # gestion des statuts
                    if attaquant["status"] == "gel":
                        log += f"❄️ {attaquant['nom']} est gelé et passe son tour.\n\n"
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None
                        continue
                    if attaquant["status"] == "confusion" and random.random() < 0.4:
                        log += f"💫 {attaquant['nom']} est confus et se blesse (10 PV) !\n\n"
                        attaquant["vie"] -= 10
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None
                        continue
                    if attaquant["status"] == "poison":
                        log += f"☠️ {attaquant['nom']} perd 5 PV à cause du poison.\n"
                        attaquant["vie"] -= 5
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None

                    # attaques possibles
                    possibles = [
                        a for a in attaquant["attaques"]
                        if a["cout"] <= attaquant["energie"] and (a["type"] != "ultime" or not a["utilisé"])
                    ]
                    if not possibles:
                        attaque = {"nom": "Attaque simple", "degats": attaquant["stats"]["force"] // 2, "cout": 0, "effet": ""}
                    else:
                        attaque = random.choice(possibles)
                        if attaque["type"] == "ultime":
                            attaque["utilisé"] = True

                    # esquive
                    esquive_chance = min(defenseur["stats"]["mobilité"] / 40 + random.uniform(0, 0.2), 0.5)
                    tentative = random.random()
                    cout_esquive = 50 if attaque["type"] == "ultime" else 10
                    if tentative < esquive_chance and defenseur["energie"] >= cout_esquive:
                        defenseur["energie"] -= cout_esquive
                        log += f"💨 {defenseur['nom']} esquive {attaque['nom']} !\n\n"
                        continue

                    # dégâts
                    base = attaque["degats"]
                    bonus = attaquant["stats"]["attaque"] + attaquant["stats"]["force"] - defenseur["stats"]["défense"]
                    total = base + max(0, bonus)
                    if random.random() < min(0.1 + attaquant["stats"]["force"] / 50, 0.4):
                        total = int(total * 1.5)
                        log += "**Coup critique !**\n"
                    attaquant["energie"] -= attaque["cout"]

                    log += f"💥 {attaquant['nom']} utilise {attaque['nom']}\n"
                    log = infliger_degats(defenseur, total, log)

                    # effets
                    if attaque.get("effet") in ["soin", "bouclier"]:
                        log = appliquer_effet(attaque, attaquant, log)
                    else:
                        log = appliquer_effet(attaque, defenseur, log)

                    if defenseur["vie"] <= 0:
                        log += f"\n🏆 {attaquant['nom']} remporte le combat par KO !"
                        return await self.send_embed_log(ctx, log, nom1, nom2)
                    log += "\n"

            gagnant = p1 if p1["vie"] > p2["vie"] else p2
            log += f"🏁 Fin du combat, vainqueur : **{gagnant['nom']}** !"
            await self.send_embed_log(ctx, log, nom1, nom2)

        except Exception as e:
            import traceback; traceback.print_exc()
            await safe_send(ctx.channel, f"❌ Erreur dans !combat3 : `{e}`")

    async def send_embed_log(self, ctx, log: str, nom1: str, nom2: str):
        """Envoie le log dans un embed, tronqué si trop long."""
        if len(log) > 6000:
            log = log[:5950] + "\n...[log tronqué]..."
        embed = discord.Embed(
            title=f"🗡️ {nom1} vs {nom2}",
            description=log,
            color=discord.Color.red()
        )
        await safe_send(ctx.channel, embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Combat3Command(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
