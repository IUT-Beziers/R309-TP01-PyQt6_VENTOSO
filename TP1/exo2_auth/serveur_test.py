"""Micro-service d'authentification de TEST (exercice 2.2).

Il imite le micro-service du TD n° 02 pour pouvoir travailler et lancer les
tests sans dépendre d'une machine distante :

    POST /login   corps JSON {"user": "...", "password": "..."}
                  -> 200 {"token": "<jeton signé>"}   ou   401
    GET  /verify  en-tête  Authorization: Bearer <jeton>
                  -> 200 {"valid": true, "user": "..."}   ou   401

Lancement manuel :   python serveur_test.py        (port 4567)
"""
import base64
import hashlib
import hmac
import json
import time
from pathlib import Path

from aiohttp import web

from auth_local import charger_utilisateurs, verifier_identifiants

DOSSIER = Path(__file__).resolve().parent
PORT = 4567
CLE_UTILISATEURS = web.AppKey("utilisateurs", dict)
SECRET = b"secret-de-test-r309"
DUREE_JETON = 3600  # secondes


def _b64(donnees: bytes) -> str:
    return base64.urlsafe_b64encode(donnees).rstrip(b"=").decode()


def _signature(corps: str) -> str:
    return _b64(hmac.new(SECRET, corps.encode(), hashlib.sha256).digest())


def creer_jeton(nom: str, duree: int = DUREE_JETON) -> str:
    """Jeton de type JWT (HS256) : en-tête.charge_utile.signature."""
    en_tete = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    maintenant = int(time.time())
    charge = _b64(json.dumps({"user": nom, "iat": maintenant,
                              "exp": maintenant + duree}).encode())
    corps = f"{en_tete}.{charge}"
    return f"{corps}.{_signature(corps)}"


def lire_jeton(jeton: str):
    """Retourne la charge utile si le jeton est valide et non expiré, sinon None."""
    try:
        en_tete, charge, signature = jeton.split(".")
        if not hmac.compare_digest(signature, _signature(f"{en_tete}.{charge}")):
            return None
        donnees = json.loads(base64.urlsafe_b64decode(charge + "=" * (-len(charge) % 4)))
    except (ValueError, UnicodeDecodeError):
        return None
    return donnees if donnees.get("exp", 0) > time.time() else None


async def login(requete: web.Request) -> web.Response:
    try:
        corps = await requete.json()
        nom, mot_de_passe = corps["user"], corps["password"]
    except (ValueError, KeyError, TypeError):
        return web.json_response({"error": "requête invalide"}, status=400)
    if verifier_identifiants(requete.app[CLE_UTILISATEURS], nom, mot_de_passe):
        return web.json_response({"token": creer_jeton(nom)})
    return web.json_response({"error": "identifiants incorrects"}, status=401)


async def verify(requete: web.Request) -> web.Response:
    entete = requete.headers.get("Authorization", "")
    charge = lire_jeton(entete[7:]) if entete.startswith("Bearer ") else None
    if charge is None:
        return web.json_response({"valid": False}, status=401)
    return web.json_response({"valid": True, "user": charge["user"]})


def creer_application(fichier_utilisateurs=DOSSIER / "users.sha256") -> web.Application:
    app = web.Application()
    app[CLE_UTILISATEURS] = charger_utilisateurs(fichier_utilisateurs)
    app.router.add_post("/login", login)
    app.router.add_get("/verify", verify)
    return app


if __name__ == "__main__":
    print(f"Micro-service de test actif sur le port {PORT}")
    web.run_app(creer_application(), port=PORT, print=None)
