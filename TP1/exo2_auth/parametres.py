"""Paramètres persistants de l'application (exercice 2.3) avec QSettings.

Valeurs conservées d'un lancement à l'autre :
    auth/login_url   URL du service d'authentification (obtention du TOKEN)
    auth/verif_url   URL du service de vérification du TOKEN
    auth/token       dernier TOKEN obtenu (s'il existe)

Sous Linux, le fichier est ~/.config/R309/Authentification.ini
"""
from urllib.parse import urlparse

from PyQt6.QtCore import QSettings

ORGANISATION = "R309"
APPLICATION = "Authentification"

URL_LOGIN_PAR_DEFAUT = "http://localhost:4567/login"
URL_VERIF_PAR_DEFAUT = "http://localhost:4567/verify"

CLE_LOGIN = "auth/login_url"
CLE_VERIF = "auth/verif_url"
CLE_TOKEN = "auth/token"


def url_valide(url: str) -> bool:
    """Vrai pour une URL http(s) avec un nom de machine, ex. http://localhost:4567/login."""
    try:
        analyse = urlparse(url.strip())
        return analyse.scheme in ("http", "https") and bool(analyse.hostname)
    except ValueError:
        return False


class Parametres:
    """Petite façade au-dessus d'un objet QSettings."""

    def __init__(self, reglages=None):
        # Un QSettings peut être fourni (tests) ; sinon fichier .ini de l'utilisateur
        self._reglages = reglages or QSettings(
            QSettings.Format.IniFormat, QSettings.Scope.UserScope,
            ORGANISATION, APPLICATION)

    @property
    def login_url(self) -> str:
        return self._reglages.value(CLE_LOGIN, URL_LOGIN_PAR_DEFAUT, type=str)

    @login_url.setter
    def login_url(self, valeur: str):
        self._reglages.setValue(CLE_LOGIN, valeur)
        self._reglages.sync()

    @property
    def verif_url(self) -> str:
        return self._reglages.value(CLE_VERIF, URL_VERIF_PAR_DEFAUT, type=str)

    @verif_url.setter
    def verif_url(self, valeur: str):
        self._reglages.setValue(CLE_VERIF, valeur)
        self._reglages.sync()

    @property
    def token(self):
        """Le TOKEN mémorisé, ou None s'il n'existe pas."""
        valeur = self._reglages.value(CLE_TOKEN, "", type=str)
        return valeur or None

    @token.setter
    def token(self, valeur):
        if valeur:
            self._reglages.setValue(CLE_TOKEN, valeur)
        else:
            self._reglages.remove(CLE_TOKEN)
        self._reglages.sync()
