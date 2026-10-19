"""TP1 - Exercice 2.1 : application d'authentification (PyQt6 + Designer).

Deux pages créées avec Qt Designer (login.ui et result.ui) sont placées
dans un QStackedWidget. Les identifiants sont vérifiés localement grâce au
fichier users.sha256 (format  utilisateur:sha256(mot_de_passe)).
"""
import sys
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget

DOSSIER = Path(__file__).resolve().parent
FICHIER_QSS = DOSSIER / "style-auth.qss"


class FenetreAuth(QMainWindow):
    """Fenêtre principale : une pile de pages (connexion / résultat)."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Authentification")
        self.resize(420, 320)

        # Chargement des deux interfaces dessinées avec Designer
        self.page_login = uic.loadUi(DOSSIER / "login.ui")
        self.page_result = uic.loadUi(DOSSIER / "result.ui")

        self.pile = QStackedWidget()
        self.pile.addWidget(self.page_login)    # index 0
        self.pile.addWidget(self.page_result)   # index 1
        self.setCentralWidget(self.pile)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(FICHIER_QSS.read_text(encoding="utf-8"))
    fenetre = FenetreAuth()
    fenetre.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
