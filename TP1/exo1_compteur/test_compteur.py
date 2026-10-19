"""Tests unitaires de l'application compteur.

Lancement (depuis ce dossier) :  python -m unittest -v test_compteur
Les tests utilisent le moteur graphique "offscreen" : aucune fenêtre n'est affichée.
"""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from compteur import FICHIER_QSS, VALEUR_MAX, VALEUR_MIN, Compteur

app = QApplication.instance() or QApplication([])


class TestCompteur(unittest.TestCase):
    def setUp(self):
        self.fenetre = Compteur()

    def test_valeur_initiale(self):
        self.assertEqual(self.fenetre.valeur, 0)
        self.assertEqual(self.fenetre.label.text(), "0")

    def test_clic_plus_incremente(self):
        self.fenetre.bouton_plus.click()
        self.fenetre.bouton_plus.click()
        self.assertEqual(self.fenetre.valeur, 2)
        self.assertEqual(self.fenetre.label.text(), "2")

    def test_clic_moins_decremente(self):
        for _ in range(5):
            self.fenetre.bouton_plus.click()
        self.fenetre.bouton_moins.click()
        self.assertEqual(self.fenetre.label.text(), "4")

    def test_borne_basse(self):
        self.fenetre.decrementer()
        self.assertEqual(self.fenetre.valeur, VALEUR_MIN)
        self.assertFalse(self.fenetre.bouton_moins.isEnabled())

    def test_borne_haute(self):
        for _ in range(VALEUR_MAX + 10):
            self.fenetre.incrementer()
        self.assertEqual(self.fenetre.valeur, VALEUR_MAX)
        self.assertEqual(self.fenetre.label.text(), "100")
        self.assertFalse(self.fenetre.bouton_plus.isEnabled())
        self.assertTrue(self.fenetre.bouton_moins.isEnabled())

    def test_boutons_reactives_apres_borne(self):
        self.fenetre.incrementer()
        self.assertTrue(self.fenetre.bouton_moins.isEnabled())
        self.fenetre.decrementer()
        self.assertFalse(self.fenetre.bouton_moins.isEnabled())
        self.assertTrue(self.fenetre.bouton_plus.isEnabled())


class TestStyle(unittest.TestCase):
    def test_qss_contient_hover_et_pressed(self):
        qss = FICHIER_QSS.read_text(encoding="utf-8")
        for bouton in ("boutonPlus", "boutonMoins"):
            self.assertIn(f"QPushButton#{bouton}:hover", qss)
            self.assertIn(f"QPushButton#{bouton}:pressed", qss)

    def test_qss_applicable(self):
        app.setStyleSheet(FICHIER_QSS.read_text(encoding="utf-8"))
        self.assertIn("QLabel#valeur", app.styleSheet())
        app.setStyleSheet("")


if __name__ == "__main__":
    unittest.main()
