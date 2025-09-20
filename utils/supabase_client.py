# ────────────────────────────────────────────────────────────────────────────────
# 📌 supabase_client.py — Initialisation du client Supabase
# Objectif : Fournir un client unique réutilisable dans tout le bot
# ────────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import os
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────
# 🔑 Chargement des variables d’environnement
# ──────────────────────────────────────────────────────────────
# Charge automatiquement .env si présent (utile en local)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ──────────────────────────────────────────────────────────────
# 🔌 Initialisation du client
# ──────────────────────────────────────────────────────────────
supabase = None

try:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL ou SUPABASE_KEY manquant")

    from supabase import create_client, Client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Client Supabase initialisé avec succès.")

except Exception as e:
    print(f"⚠️ Supabase désactivé : {e}")
