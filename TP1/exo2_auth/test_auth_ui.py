"""Tests de l'interface d'authentification (python -m unittest -v test_auth_ui)."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from auth_app import FICHIER_QSS, PAGE_LOGIN, PAGE_RESULT, FenetreAuth

app = QApplication.instance() or QApplication([])


class TestInterfaceAuth(unittest.TestCase):
    def setUp(self):
        self.fenetre = FenetreAuth()
        self.fenetre.show()
        self.login = self.fenetre.page_login
        self.result = self.fenetre.page_result

    def tearDown(self):
        self.fenetre.close()

    def saisir(self, nom, mot_de_passe):
        self.login.editUser.setText(nom)
        self.login.editPassword.setText(mot_de_passe)

    def test_page_initiale_et_proprietes(self):
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)
        self.assertEqual(self.fenetre.pile.count(), 2)
        self.assertEqual(self.login.editUser.placeholderText(), "Nom d'utilisateur")
        self.assertEqual(self.login.editPassword.placeholderText(), "Mot de passe")
        self.assertEqual(self.login.editPassword.echoMode(),
                         self.login.editPassword.EchoMode.Password)

    def test_bouton_desactive_tant_que_champs_vides(self):
        self.assertFalse(self.login.btnLogin.isEnabled())
        self.login.editUser.setText("alice")
        self.assertFalse(self.login.btnLogin.isEnabled())
        self.login.editPassword.setText("x")
        self.assertTrue(self.login.btnLogin.isEnabled())
        self.login.editUser.clear()
        self.assertFalse(self.login.btnLogin.isEnabled())

    def test_connexion_reussie_par_le_bouton(self):
        self.saisir("alice", "alice")
        self.login.btnLogin.click()
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_RESULT)
        self.assertEqual(self.result.lblBienvenue.text(), "Bienvenue alice !")

    def test_connexion_reussie_par_la_touche_entree(self):
        self.saisir("bob", "bob")
        QTest.keyClick(self.login.editPassword, Qt.Key.Key_Return)
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_RESULT)
        self.assertEqual(self.result.lblBienvenue.text(), "Bienvenue bob !")

    def test_entree_dans_utilisateur_passe_au_mot_de_passe(self):
        self.login.editUser.setText("alice")
        QTest.keyClick(self.login.editUser, Qt.Key.Key_Return)
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)
        self.assertIs(self.fenetre.focusWidget(), self.login.editPassword)

    def test_echec_affiche_une_boite_de_dialogue(self):
        self.saisir("alice", "mauvais")
        with patch("auth_app.QMessageBox.warning") as boite:
            self.login.btnLogin.click()
        boite.assert_called_once()
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)
        self.assertEqual(self.login.editPassword.text(), "")

    def test_deconnexion_revient_a_la_page_de_login(self):
        self.saisir("clark", "clark")
        self.login.btnLogin.click()
        self.result.btnLogout.click()
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)
        self.assertEqual(self.login.editUser.text(), "")
        self.assertEqual(self.login.editPassword.text(), "")

    def test_qss_charge_les_boutons_hover_pressed(self):
        qss = FICHIER_QSS.read_text(encoding="utf-8")
        self.assertIn("QPushButton:hover", qss)
        self.assertIn("QPushButton#btnLogout:pressed", qss)


if __name__ == "__main__":
    unittest.main()
