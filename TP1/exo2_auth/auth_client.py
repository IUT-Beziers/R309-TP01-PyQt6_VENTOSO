"""Client HTTP asynchrone du micro-service d'authentification (exercice 2.2).

Deux requêtes successives sont nécessaires :
  1. getToken()    : POST sur l'URL de login   -> obtient un TOKEN
  2. verifyToken() : GET  sur l'URL de vérification avec le TOKEN -> utilisateur

Si le micro-service du TD n° 02 attend d'autres noms de champs ou un autre
en-tête, il suffit de modifier les constantes ci-dessous.
"""
import asyncio
import logging

import aiohttp

# --- Format de dialogue avec le micro-service (à adapter si besoin) ---
CHAMP_UTILISATEUR = "user"
CHAMP_MOT_DE_PASSE = "password"
CHAMP_TOKEN = "token"
DELAI_MAX = 5  # secondes

journal = logging.getLogger("auth_client")


class ErreurAuth(Exception):
    """Erreur d'authentification (message lisible, affiché dans une boîte de dialogue)."""


async def get_token(url_login: str, nom: str, mot_de_passe: str) -> str:
    """Requête 1 : envoie les identifiants et retourne le TOKEN reçu."""
    journal.info("getToken()...\n  AUTH_URL: %s", url_login)
    donnees = {CHAMP_UTILISATEUR: nom, CHAMP_MOT_DE_PASSE: mot_de_passe}
    reponse = await _requete("POST", url_login, json=donnees)
    journal.info("  =>%s", reponse)
    token = reponse.get(CHAMP_TOKEN)
    if not token:
        raise ErreurAuth("Réponse inattendue du serveur (pas de token).")
    return token


async def verify_token(url_verif: str, token: str) -> dict:
    """Requête 2 : vérifie le TOKEN ; retourne {'valid': True, 'user': ...}."""
    journal.info("verifyToken()...\n  VERIF_URL: %s", url_verif)
    entetes = {"Authorization": f"Bearer {token}"}
    reponse = await _requete("GET", url_verif, headers=entetes)
    journal.info("  =>%s", reponse)
    if not reponse.get("valid"):
        raise ErreurAuth("Token invalide ou expiré.")
    return reponse


async def _requete(methode: str, url: str, **options) -> dict:
    """Effectue une requête et retourne le JSON ; convertit les erreurs en ErreurAuth."""
    delai = aiohttp.ClientTimeout(total=DELAI_MAX)
    try:
        async with aiohttp.ClientSession(timeout=delai) as session:
            async with session.request(methode, url, **options) as reponse:
                if reponse.status in (401, 403):
                    journal.info("  Erreur HTTP : %s pour %s", reponse.status, url)
                    raise ErreurAuth("Nom d'utilisateur, mot de passe ou token incorrect.")
                if reponse.status >= 400:
                    journal.info("  Erreur HTTP : %s pour %s", reponse.status, url)
                    raise ErreurAuth(f"Erreur HTTP {reponse.status} pour {url}.")
                return await reponse.json(content_type=None)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as erreur:
        journal.info("  Erreur réseau : %s", erreur)
        raise ErreurAuth(f"Serveur injoignable ({url}).") from erreur
