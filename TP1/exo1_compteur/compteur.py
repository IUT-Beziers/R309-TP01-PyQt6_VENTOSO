"""TP1 - Exercice 1 : application compteur (PyQt6).

Un label affiche une valeur comprise entre 0 et 100.
Le bouton "+" l'incrémente, le bouton "-" la décrémente.
"""
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
                             QVBoxLayout, QWidget)

VALEUR_MIN = 0
VALEUR_MAX = 100


class Compteur(QWidget):
    """Fenêtre du compteur : un label et deux boutons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compteur")
        self._valeur = VALEUR_MIN

        self.label = QLabel(str(self._valeur))
        self.label.setObjectName("valeur")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.bouton_moins = QPushButton("-")
        self.bouton_moins.setObjectName("boutonMoins")
        self.bouton_plus = QPushButton("+")
        self.bouton_plus.setObjectName("boutonPlus")
        for bouton in (self.bouton_moins, self.bouton_plus):
            bouton.setCursor(Qt.CursorShape.PointingHandCursor)

        boutons = QHBoxLayout()
        boutons.addWidget(self.bouton_moins)
        boutons.addWidget(self.bouton_plus)

        disposition = QVBoxLayout(self)
        disposition.addWidget(self.label)
        disposition.addLayout(boutons)

        # Programmation évènementielle : on relie les signaux aux slots.
        self.bouton_plus.clicked.connect(self.incrementer)
        self.bouton_moins.clicked.connect(self.decrementer)

        self._maj_affichage()

    @property
    def valeur(self) -> int:
        return self._valeur

    def incrementer(self):
        """Slot du bouton "+" : ajoute 1 sans dépasser VALEUR_MAX."""
        if self._valeur < VALEUR_MAX:
            self._valeur += 1
            self._maj_affichage()

    def decrementer(self):
        """Slot du bouton "-" : retire 1 sans passer sous VALEUR_MIN."""
        if self._valeur > VALEUR_MIN:
            self._valeur -= 1
            self._maj_affichage()

    def _maj_affichage(self):
        """Met à jour le label et l'état (actif/inactif) des boutons."""
        self.label.setText(str(self._valeur))
        self.bouton_plus.setEnabled(self._valeur < VALEUR_MAX)
        self.bouton_moins.setEnabled(self._valeur > VALEUR_MIN)


def main():
    app = QApplication(sys.argv)
    fenetre = Compteur()
    fenetre.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
