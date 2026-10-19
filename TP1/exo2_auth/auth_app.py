"""TP1 - Exercice 2.1 : application d'authentification (PyQt6 + Designer).

Deux pages créées avec Qt Designer (login.ui et result.ui) sont placées
dans un QStackedWidget. Les identifiants sont vérifiés localement grâce au
fichier users.sha256 (format  utilisateur:sha256(mot_de_passe)).
"""
import sys
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                             QStackedWidget)

from auth_local import charger_utilisateurs, verifier_identifiants

DOSSIER = Path(__file__).resolve().parent
FICHIER_UTILISATEURS = DOSSIER / "users.sha256"
FICHIER_QSS = DOSSIER / "style-auth.qss"

PAGE_LOGIN = 0
PAGE_RESULT = 1


class FenetreAuth(QMainWindow):
    """Fenêtre principale : une pile de pages (connexion / résultat)."""

    def __init__(self, fichier_utilisateurs=FICHIER_UTILISATEURS):
        super().__init__()
        self.setWindowTitle("Authentification")
        self.resize(420, 320)
        self.utilisateurs = charger_utilisateurs(fichier_utilisateurs)

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

    def on_login(self):
        login = self.page_login
        nom = login.editUser.text().strip()
        mot_de_passe = login.editPassword.text()
        if verifier_identifiants(self.utilisateurs, nom, mot_de_passe):
            self.afficher_resultat(nom)
        else:
            login.editPassword.clear()
            QMessageBox.warning(self, "Échec de l'authentification",
                                "Nom d'utilisateur ou mot de passe incorrect.")
            login.editPassword.setFocus()

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
    app = QApplication(sys.argv)
    app.setStyleSheet(FICHIER_QSS.read_text(encoding="utf-8"))
    fenetre = FenetreAuth()
    fenetre.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
