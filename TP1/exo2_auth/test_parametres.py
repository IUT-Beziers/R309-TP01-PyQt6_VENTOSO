"""Tests des paramètres persistants (python -m unittest -v test_parametres)."""
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QSettings

from parametres import (URL_LOGIN_PAR_DEFAUT, URL_VERIF_PAR_DEFAUT, Parametres,
                        url_valide)


def reglages_temporaires(dossier: str) -> QSettings:
    """QSettings écrivant dans un fichier .ini jetable (pas dans ~/.config)."""
    return QSettings(str(Path(dossier) / "test.ini"), QSettings.Format.IniFormat)


class TestParametres(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier.cleanup)

    def nouveaux(self) -> Parametres:
        return Parametres(reglages_temporaires(self.dossier.name))

    def test_valeurs_par_defaut(self):
        p = self.nouveaux()
        self.assertEqual(p.login_url, URL_LOGIN_PAR_DEFAUT)
        self.assertEqual(p.verif_url, URL_VERIF_PAR_DEFAUT)
        self.assertIsNone(p.token)

    def test_persistance_entre_deux_lancements(self):
        premier = self.nouveaux()
        premier.login_url = "http://10.42.227.111:4567/login"
        premier.verif_url = "http://10.42.227.111:4567/verify"
        premier.token = "abc.def.ghi"
        deuxieme = self.nouveaux()  # simule un nouveau lancement
        self.assertEqual(deuxieme.login_url, "http://10.42.227.111:4567/login")
        self.assertEqual(deuxieme.verif_url, "http://10.42.227.111:4567/verify")
        self.assertEqual(deuxieme.token, "abc.def.ghi")

    def test_effacement_du_token(self):
        p = self.nouveaux()
        p.token = "abc"
        p.token = None
        self.assertIsNone(self.nouveaux().token)

    def test_fichier_ini_cree(self):
        p = self.nouveaux()
        p.token = "xyz"
        contenu = (Path(self.dossier.name) / "test.ini").read_text(encoding="utf-8")
        self.assertIn("token=xyz", contenu)


class TestUrlValide(unittest.TestCase):
    def test_urls_acceptees(self):
        for url in ("http://localhost:4567/login", "https://exemple.fr/verify",
                    "http://10.42.227.111:4567/login", " http://localhost:4567/x "):
            self.assertTrue(url_valide(url), url)

    def test_urls_refusees(self):
        for url in ("", "localhost:4567/login", "ftp://localhost/login",
                    "http://", "n'importe quoi", "http://[::1"):
            self.assertFalse(url_valide(url), url)


if __name__ == "__main__":
    unittest.main()
