"""Tests de l'interface d'authentification (python -m unittest -v test_auth_ui).

Les tests utilisent le moteur "offscreen" de Qt et une boucle qasync.
Le mode réseau est testé face au micro-service de test (serveur_test.py).
"""
import asyncio
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from aiohttp.test_utils import TestServer
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from auth_app import FICHIER_QSS, PAGE_LOGIN, PAGE_RESULT, FenetreAuth
from serveur_test import creer_application

app = QApplication.instance() or QApplication([])
boucle = QEventLoop(app)
asyncio.set_event_loop(boucle)


def executer(coroutine):
    """Exécute une coroutine dans la boucle qasync et attend son résultat."""
    return boucle.run_until_complete(coroutine)


def laisser_tourner():
    """Laisse la boucle traiter les tâches lancées par un clic (asyncSlot)."""
    executer(asyncio.sleep(0.05))


class TestModeLocal(unittest.TestCase):
    """Vérification locale avec users.sha256 (exercice 2.1)."""

    def setUp(self):
        self.fenetre = FenetreAuth(mode_local=True)
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
        laisser_tourner()
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_RESULT)
        self.assertEqual(self.result.lblBienvenue.text(), "Bienvenue alice !")

    def test_connexion_reussie_par_la_touche_entree(self):
        self.saisir("bob", "bob")
        QTest.keyClick(self.login.editPassword, Qt.Key.Key_Return)
        laisser_tourner()
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_RESULT)
        self.assertEqual(self.result.lblBienvenue.text(), "Bienvenue bob !")

    def test_entree_dans_utilisateur_passe_au_mot_de_passe(self):
        self.login.editUser.setText("alice")
        QTest.keyClick(self.login.editUser, Qt.Key.Key_Return)
        laisser_tourner()
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)
        self.assertIs(self.fenetre.focusWidget(), self.login.editPassword)

    def test_echec_affiche_une_boite_de_dialogue(self):
        self.saisir("alice", "mauvais")
        with patch("auth_app.QMessageBox.warning") as boite:
            self.login.btnLogin.click()
            laisser_tourner()
        boite.assert_called_once()
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)
        self.assertEqual(self.login.editPassword.text(), "")

    def test_deconnexion_revient_a_la_page_de_login(self):
        self.saisir("clark", "clark")
        self.login.btnLogin.click()
        laisser_tourner()
        self.result.btnLogout.click()
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)
        self.assertEqual(self.login.editUser.text(), "")
        self.assertEqual(self.login.editPassword.text(), "")

    def test_case_token_cachee_en_mode_local(self):
        self.saisir("alice", "alice")
        self.login.btnLogin.click()
        laisser_tourner()
        self.assertTrue(self.result.chkDeleteToken.isHidden())

    def test_qss_contient_hover_et_pressed(self):
        qss = FICHIER_QSS.read_text(encoding="utf-8")
        self.assertIn("QPushButton:hover", qss)
        self.assertIn("QPushButton#btnLogout:pressed", qss)


class TestModeReseau(unittest.TestCase):
    """Vérification par le micro-service HTTP (exercice 2.2)."""

    def setUp(self):
        self.serveur = TestServer(creer_application())
        executer(self.serveur.start_server())
        self.fenetre = FenetreAuth(
            url_login=str(self.serveur.make_url("/login")),
            url_verif=str(self.serveur.make_url("/verify")))
        self.fenetre.show()
        self.login = self.fenetre.page_login
        self.result = self.fenetre.page_result

    def tearDown(self):
        self.fenetre.close()
        executer(self.serveur.close())

    def connecter(self, nom, mot_de_passe):
        self.login.editUser.setText(nom)
        self.login.editPassword.setText(mot_de_passe)
        executer(self.fenetre.connecter())

    def test_connexion_reussie(self):
        self.connecter("alice", "alice")
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_RESULT)
        self.assertEqual(self.result.lblBienvenue.text(), "Bienvenue alice !")
        self.assertIsNotNone(self.fenetre.token)
        self.assertFalse(self.result.chkDeleteToken.isHidden())

    def test_connexion_par_le_bouton_asynchrone(self):
        self.login.editUser.setText("bob")
        self.login.editPassword.setText("bob")
        self.login.btnLogin.click()
        executer(asyncio.sleep(0.3))
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_RESULT)
        self.assertEqual(self.result.lblBienvenue.text(), "Bienvenue bob !")

    def test_mauvais_mot_de_passe(self):
        with patch("auth_app.QMessageBox.warning") as boite:
            self.connecter("alice", "faux")
        boite.assert_called_once()
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)
        self.assertIsNone(self.fenetre.token)

    def test_serveur_injoignable(self):
        self.fenetre.url_login = "http://127.0.0.1:9/login"
        with patch("auth_app.QMessageBox.warning") as boite:
            self.connecter("alice", "alice")
        self.assertIn("injoignable", boite.call_args.args[2])
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)

    def test_formulaire_reactive_apres_echec(self):
        with patch("auth_app.QMessageBox.warning"):
            self.connecter("alice", "faux")
        self.assertTrue(self.login.editUser.isEnabled())
        self.assertTrue(self.login.editPassword.isEnabled())
        self.assertFalse(self.login.btnLogin.isEnabled())  # mot de passe vidé

    def test_deconnexion_avec_case_cochee_efface_le_token(self):
        self.connecter("alice", "alice")
        self.result.chkDeleteToken.setChecked(True)
        self.result.btnLogout.click()
        self.assertIsNone(self.fenetre.token)
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)

    def test_deconnexion_case_decochee_garde_le_token(self):
        self.connecter("alice", "alice")
        self.result.chkDeleteToken.setChecked(False)
        self.result.btnLogout.click()
        self.assertIsNotNone(self.fenetre.token)


if __name__ == "__main__":
    unittest.main()
