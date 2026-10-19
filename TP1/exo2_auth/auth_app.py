"""TP1 - Exercice 2.1 : application d'authentification (PyQt6 + Designer).

Deux pages créées avec Qt Designer (login.ui et result.ui) sont placées
dans un QStackedWidget. Les identifiants sont vérifiés par un micro-service
HTTP, de façon asynchrone (asyncio + qasync) : une première requête obtient
un TOKEN, une seconde requête vérifie ce TOKEN.
"""
import asyncio
import logging
import sys
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                             QStackedWidget)
from qasync import QEventLoop, asyncSlot

from auth_client import ErreurAuth, get_token, verify_token

DOSSIER = Path(__file__).resolve().parent
URL_LOGIN = "http://localhost:4567/login"
URL_VERIF = "http://localhost:4567/verify"
FICHIER_QSS = DOSSIER / "style-auth.qss"

PAGE_LOGIN = 0
PAGE_RESULT = 1


class FenetreAuth(QMainWindow):
    """Fenêtre principale : une pile de pages (connexion / résultat)."""

    def __init__(self, url_login=URL_LOGIN, url_verif=URL_VERIF):
        super().__init__()
        self.setWindowTitle("Authentification")
        self.resize(420, 320)
        self.url_login = url_login
        self.url_verif = url_verif
        self.token = None

        # Chargement des deux interfaces dessinées avec Designer
        self.page_login = uic.loadUi(DOSSIER / "login.ui")
        self.page_result = uic.loadUi(DOSSIER / "result.ui")

        self.pile = QStackedWidget()
        self.pile.addWidget(self.page_login)    # index 0
        self.pile.addWidget(self.page_result)   # index 1
        self.setCentralWidget(self.pile)

        # Signaux / slots
        login = self.page_login
        login.editUser.textChanged.connect(self.maj_bouton_login)
        login.editPassword.textChanged.connect(self.maj_bouton_login)
        login.editUser.returnPressed.connect(self.entree_dans_utilisateur)
        login.editPassword.returnPressed.connect(login.btnLogin.click)
        login.btnLogin.clicked.connect(self.on_login)
        self.page_result.btnLogout.clicked.connect(self.on_logout)

        login.editUser.setFocus()

    # ----- Page de connexion -----
    def maj_bouton_login(self):
        """Le bouton n'est actif que si les deux champs sont remplis."""
        login = self.page_login
        remplis = bool(login.editUser.text().strip() and login.editPassword.text())
        login.btnLogin.setEnabled(remplis)

    def entree_dans_utilisateur(self):
        """Entrée dans le champ utilisateur : on passe au mot de passe."""
        login = self.page_login
        if login.editPassword.text():
            login.btnLogin.click()
        else:
            login.editPassword.setFocus()

    @asyncSlot()
    async def on_login(self):
        """Slot du bouton : lance la connexion sans bloquer l'interface."""
        await self.connecter()

    async def connecter(self):
        """Requête 1 (getToken) puis requête 2 (verifyToken)."""
        login = self.page_login
        nom = login.editUser.text().strip()
        mot_de_passe = login.editPassword.text()
        self.activer_saisie(False)
        try:
            token = await get_token(self.url_login, nom, mot_de_passe)
            reponse = await verify_token(self.url_verif, token)
        except ErreurAuth as erreur:
            login.editPassword.clear()
            QMessageBox.warning(self, "Échec de l'authentification", str(erreur))
        else:
            self.token = token
            self.afficher_resultat(reponse.get("user", nom))
        finally:
            self.activer_saisie(True)

    def activer_saisie(self, actif):
        """Bloque ou débloque le formulaire pendant les requêtes réseau."""
        login = self.page_login
        login.editUser.setEnabled(actif)
        login.editPassword.setEnabled(actif)
        if actif:
            self.maj_bouton_login()
            login.editPassword.setFocus()
        else:
            login.btnLogin.setEnabled(False)

    # ----- Page de résultat -----
    def afficher_resultat(self, nom):
        self.page_login.editUser.clear()
        self.page_login.editPassword.clear()
        self.page_result.lblBienvenue.setText(f"Bienvenue {nom} !")
        self.pile.setCurrentIndex(PAGE_RESULT)

    def on_logout(self):
        self.pile.setCurrentIndex(PAGE_LOGIN)
        self.page_login.editUser.setFocus()


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app = QApplication(sys.argv)
    app.setStyleSheet(FICHIER_QSS.read_text(encoding="utf-8"))

    # qasync : la boucle asyncio est fusionnée avec la boucle d'évènements de Qt
    boucle = QEventLoop(app)
    asyncio.set_event_loop(boucle)
    fin = asyncio.Event()
    app.aboutToQuit.connect(fin.set)

    fenetre = FenetreAuth()
    fenetre.show()
    with boucle:
        boucle.run_until_complete(fin.wait())


if __name__ == "__main__":
    main()
