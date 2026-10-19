"""TP1 - Exercice 2 : application d'authentification (PyQt6 + Designer).

Trois pages créées avec Qt Designer (login.ui, result.ui et settings.ui) sont
placées dans un QStackedWidget. Les identifiants sont vérifiés par un
micro-service HTTP, de façon asynchrone (asyncio + qasync) : une première
requête obtient un TOKEN, une seconde requête vérifie ce TOKEN.
Les URL et le TOKEN sont mémorisés avec QSettings ; une barre d'outils permet
de modifier les URL. Avec l'option --local, on retrouve la vérification locale
de l'exercice 2.1.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                             QStackedWidget, QStyle, QToolBar)
from qasync import QEventLoop, asyncSlot

from auth_client import ErreurAuth, ErreurReseau, get_token, verify_token
from auth_local import charger_utilisateurs, verifier_identifiants
from parametres import Parametres, url_valide

DOSSIER = Path(__file__).resolve().parent
FICHIER_UTILISATEURS = DOSSIER / "users.sha256"
FICHIER_QSS = DOSSIER / "style-auth.qss"

PAGE_LOGIN = 0
PAGE_RESULT = 1
PAGE_SETTINGS = 2


class FenetreAuth(QMainWindow):
    """Fenêtre principale : une pile de pages (connexion / résultat)."""

    def __init__(self, parametres=None, mode_local=False,
                 fichier_utilisateurs=FICHIER_UTILISATEURS):
        super().__init__()
        self.setWindowTitle("Authentification")
        self.resize(420, 320)
        self.parametres = parametres or Parametres()
        self.boite_erreur = None
        self.mode_local = mode_local
        self.utilisateurs = charger_utilisateurs(fichier_utilisateurs) if mode_local else {}

        # Chargement des deux interfaces dessinées avec Designer
        self.page_login = uic.loadUi(DOSSIER / "login.ui")
        self.page_result = uic.loadUi(DOSSIER / "result.ui")
        self.page_settings = uic.loadUi(DOSSIER / "settings.ui")

        self.pile = QStackedWidget()
        self.pile.addWidget(self.page_login)      # index 0
        self.pile.addWidget(self.page_result)     # index 1
        self.pile.addWidget(self.page_settings)   # index 2
        self.setCentralWidget(self.pile)
        self.page_avant_settings = PAGE_LOGIN

        # Barre d'outils : une action (cochable) qui affiche/masque la page des URL
        icone = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.action_settings = QAction(icone, "Paramètres des URL", self)
        self.action_settings.setCheckable(True)
        self.action_settings.setToolTip("Modifier les URL d'authentification")
        self.barre_outils = QToolBar("Outils")
        self.barre_outils.addAction(self.action_settings)
        self.addToolBar(self.barre_outils)

        # Signaux / slots
        login = self.page_login
        login.editUser.textChanged.connect(self.maj_bouton_login)
        login.editPassword.textChanged.connect(self.maj_bouton_login)
        login.editUser.returnPressed.connect(self.entree_dans_utilisateur)
        login.editPassword.returnPressed.connect(login.btnLogin.click)
        login.btnLogin.clicked.connect(self.on_login)
        self.page_result.btnLogout.clicked.connect(self.on_logout)

        self.page_result.btnVerify.clicked.connect(self.on_verify)
        self.action_settings.toggled.connect(self.basculer_settings)
        self.page_settings.btnValider.clicked.connect(self.on_valider_settings)
        for champ in (self.page_settings.editLoginUrl, self.page_settings.editVerifUrl):
            champ.returnPressed.connect(self.page_settings.btnValider.click)

        # Un TOKEN mémorisé lors d'un lancement précédent ?
        if self.token and not self.mode_local:
            self.afficher_token_existant()
        else:
            login.editUser.setFocus()

    @property
    def token(self):
        """Le TOKEN est mémorisé dans les paramètres (QSettings)."""
        return self.parametres.token

    @token.setter
    def token(self, valeur):
        self.parametres.token = valeur

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
            token, utilisateur = await self.authentifier(nom, mot_de_passe)
        except ErreurAuth as erreur:
            login.editPassword.clear()
            self.afficher_erreur(str(erreur))
        else:
            if token:  # pas de token en mode local : on ne touche pas au TOKEN mémorisé
                self.token = token
            self.afficher_resultat(utilisateur)
        finally:
            self.activer_saisie(True)

    async def authentifier(self, nom, mot_de_passe):
        """Retourne (token, utilisateur) ou lève ErreurAuth."""
        if self.mode_local:
            if not verifier_identifiants(self.utilisateurs, nom, mot_de_passe):
                raise ErreurAuth("Nom d'utilisateur ou mot de passe incorrect.")
            return None, nom
        token = await get_token(self.parametres.login_url, nom, mot_de_passe)
        reponse = await verify_token(self.parametres.verif_url, token)
        return token, reponse.get("user", nom)

    def activer_saisie(self, actif):
        """Bloque ou débloque le formulaire pendant les requêtes réseau."""
        login = self.page_login
        login.editUser.setEnabled(actif)
        login.editPassword.setEnabled(actif)
        self.action_settings.setEnabled(actif)
        if actif:
            self.maj_bouton_login()
            login.editPassword.setFocus()
        else:
            login.btnLogin.setEnabled(False)

    def afficher_erreur(self, message, titre="Échec de l'authentification"):
        """Boîte de dialogue d'erreur NON bloquante.

        QMessageBox.warning() lance une boucle d'évènements imbriquée, ce qui
        gêne asyncio/qasync quand on l'appelle depuis une coroutine : on utilise
        donc open(), qui affiche la boîte (modale pour la fenêtre) et rend la main.
        """
        boite = QMessageBox(QMessageBox.Icon.Warning, titre, message, QMessageBox.StandardButton.Ok, self)
        boite.setWindowModality(Qt.WindowModality.WindowModal)
        boite.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        boite.finished.connect(self.boite_fermee)
        boite.open()
        self.boite_erreur = boite

    def boite_fermee(self):
        self.boite_erreur = None

    # ----- Page de résultat -----
    def afficher_resultat(self, nom):
        self.page_login.editUser.clear()
        self.page_login.editPassword.clear()
        resultat = self.page_result
        resultat.lblBienvenue.setText(f"Bienvenue {nom} !")
        # hide()/show() : la case n'a de sens que s'il existe un TOKEN
        resultat.btnVerify.hide()
        resultat.btnLogout.show()
        if self.token:
            resultat.chkDeleteToken.show()
        else:
            resultat.chkDeleteToken.hide()
        self.pile.setCurrentIndex(PAGE_RESULT)

    def afficher_token_existant(self):
        """Un TOKEN est mémorisé : on propose de le vérifier ou de s'en débarrasser."""
        resultat = self.page_result
        resultat.lblBienvenue.setText("Token exists")
        resultat.btnVerify.show()
        resultat.chkDeleteToken.show()
        resultat.btnLogout.show()
        self.pile.setCurrentIndex(PAGE_RESULT)

    @asyncSlot()
    async def on_verify(self):
        await self.verifier_token_memorise()

    async def verifier_token_memorise(self):
        """Vérifie le TOKEN mémorisé auprès du serveur (une seule requête)."""
        bouton = self.page_result.btnVerify
        bouton.setEnabled(False)
        self.action_settings.setEnabled(False)
        try:
            reponse = await verify_token(self.parametres.verif_url, self.token)
        except ErreurReseau as erreur:
            self.afficher_erreur(str(erreur))          # le TOKEN est conservé
        except ErreurAuth as erreur:
            self.token = None                           # TOKEN refusé : on l'efface
            self.afficher_erreur(f"{erreur} Il a été supprimé.")
            self.pile.setCurrentIndex(PAGE_LOGIN)
            self.page_login.editUser.setFocus()
        else:
            self.afficher_resultat(reponse.get("user", "?"))
        finally:
            bouton.setEnabled(True)
            self.action_settings.setEnabled(True)

    def on_logout(self):
        if not self.mode_local and self.page_result.chkDeleteToken.isChecked():
            self.token = None
        self.pile.setCurrentIndex(PAGE_LOGIN)
        self.page_login.editUser.setFocus()

    # ----- Page des paramètres (3e interface) -----
    def basculer_settings(self, afficher):
        """Action de la barre d'outils : affiche la page des URL ou revient à la page précédente."""
        if afficher:
            self.page_avant_settings = self.pile.currentIndex()
            self.page_settings.editLoginUrl.setText(self.parametres.login_url)
            self.page_settings.editVerifUrl.setText(self.parametres.verif_url)
            self.pile.setCurrentIndex(PAGE_SETTINGS)
            self.page_settings.editLoginUrl.setFocus()
        else:
            self.pile.setCurrentIndex(self.page_avant_settings)

    def on_valider_settings(self):
        """Bouton Valider : contrôle les deux URL, les mémorise et ferme la page."""
        url_login = self.page_settings.editLoginUrl.text().strip()
        url_verif = self.page_settings.editVerifUrl.text().strip()
        if not (url_valide(url_login) and url_valide(url_verif)):
            self.afficher_erreur("Les deux URL doivent commencer par http:// ou https://.",
                                 "URL invalide")
            return
        self.parametres.login_url = url_login
        self.parametres.verif_url = url_verif
        self.action_settings.setChecked(False)   # déclenche le retour à la page précédente


def main():
    analyseur = argparse.ArgumentParser(description="Application d'authentification")
    analyseur.add_argument("--local", action="store_true",
                           help="vérifier les identifiants avec users.sha256 (sans réseau)")
    options, restants = analyseur.parse_known_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app = QApplication([sys.argv[0]] + restants)
    app.setStyleSheet(FICHIER_QSS.read_text(encoding="utf-8"))

    # qasync : la boucle asyncio est fusionnée avec la boucle d'évènements de Qt
    boucle = QEventLoop(app)
    asyncio.set_event_loop(boucle)
    fin = asyncio.Event()
    app.aboutToQuit.connect(fin.set)

    fenetre = FenetreAuth(mode_local=options.local)
    fenetre.show()
    with boucle:
        boucle.run_until_complete(fin.wait())


if __name__ == "__main__":
    main()
