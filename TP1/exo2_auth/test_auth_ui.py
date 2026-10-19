"""Tests de l'interface d'authentification (python -m unittest -v test_auth_ui).

Les tests utilisent le moteur "offscreen" de Qt et une boucle qasync.
Le mode réseau est testé face au micro-service de test (serveur_test.py).
"""
import asyncio
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from aiohttp.test_utils import TestServer
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from auth_app import FICHIER_QSS, PAGE_LOGIN, PAGE_RESULT, FenetreAuth
from parametres import Parametres
from serveur_test import creer_application

app = QApplication.instance() or QApplication([])
boucle = QEventLoop(app)
asyncio.set_event_loop(boucle)


def parametres_jetables(cas_de_test):
    """Parametres écrivant dans un .ini temporaire (le vrai fichier n'est pas touché)."""
    dossier = tempfile.TemporaryDirectory()
    cas_de_test.addCleanup(dossier.cleanup)
    reglages = QSettings(str(Path(dossier.name) / "test.ini"), QSettings.Format.IniFormat)
    return Parametres(reglages)


def executer(coroutine):
    """Exécute une coroutine dans la boucle qasync et attend son résultat."""
    return boucle.run_until_complete(coroutine)


def laisser_tourner():
    """Laisse la boucle traiter les tâches lancées par un clic (asyncSlot)."""
    executer(asyncio.sleep(0.05))


class TestModeLocal(unittest.TestCase):
    """Vérification locale avec users.sha256 (exercice 2.1)."""

    def setUp(self):
        self.fenetre = FenetreAuth(parametres_jetables(self), mode_local=True)
        self.fenetre.show()
        self.login = self.fenetre.page_login
        self.result = self.fenetre.page_result

    def tearDown(self):
        self.fenetre.close()

    def fermer_boite(self):
        if self.fenetre.boite_erreur is not None:
            self.fenetre.boite_erreur.close()

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
        self.login.btnLogin.click()
        laisser_tourner()
        boite = self.fenetre.boite_erreur
        self.assertIsNotNone(boite)
        self.assertTrue(boite.isVisible())
        self.assertIn("incorrect", boite.text())
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)
        self.assertEqual(self.login.editPassword.text(), "")
        self.fermer_boite()
        self.assertIsNone(self.fenetre.boite_erreur)

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
        self.parametres = parametres_jetables(self)
        self.parametres.login_url = str(self.serveur.make_url("/login"))
        self.parametres.verif_url = str(self.serveur.make_url("/verify"))
        self.fenetre = FenetreAuth(self.parametres)
        self.fenetre.show()
        self.login = self.fenetre.page_login
        self.result = self.fenetre.page_result

    def tearDown(self):
        if self.fenetre.boite_erreur is not None:
            self.fenetre.boite_erreur.close()
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
        self.connecter("alice", "faux")
        self.assertIsNotNone(self.fenetre.boite_erreur)
        self.assertIn("incorrect", self.fenetre.boite_erreur.text())
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)
        self.assertIsNone(self.fenetre.token)

    def test_serveur_injoignable(self):
        self.parametres.login_url = "http://127.0.0.1:9/login"
        self.connecter("alice", "alice")
        self.assertIn("injoignable", self.fenetre.boite_erreur.text())
        self.assertEqual(self.fenetre.pile.currentIndex(), PAGE_LOGIN)

    def test_formulaire_reactive_apres_echec(self):
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
        self.assertIsNotNone(self.parametres.token)  # toujours présent dans les réglages


if __name__ == "__main__":
    unittest.main()
