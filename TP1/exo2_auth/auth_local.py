"""Validation locale des identifiants (exercice 2.1).

Le fichier users.sha256 contient une ligne par utilisateur au format :
    utilisateur:sha256(mot_de_passe)
"""
import hashlib
import hmac
from pathlib import Path


def hacher(mot_de_passe: str) -> str:
    """Retourne l'empreinte SHA-256 (hexadécimale) du mot de passe."""
    return hashlib.sha256(mot_de_passe.encode("utf-8")).hexdigest()


def charger_utilisateurs(chemin: Path) -> dict[str, str]:
    """Lit le fichier et retourne un dictionnaire {utilisateur: empreinte}."""
    utilisateurs = {}
    for ligne in Path(chemin).read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ":" not in ligne:
            continue
        nom, empreinte = ligne.split(":", 1)
        utilisateurs[nom.strip()] = empreinte.strip().lower()
    return utilisateurs


def verifier_identifiants(utilisateurs: dict[str, str], nom: str, mot_de_passe: str) -> bool:
    """Vrai si le nom existe et si l'empreinte du mot de passe correspond."""
    attendu = utilisateurs.get(nom)
    if attendu is None:
        return False
    # compare_digest évite les comparaisons qui s'arrêtent au premier octet différent
    return hmac.compare_digest(attendu, hacher(mot_de_passe))
