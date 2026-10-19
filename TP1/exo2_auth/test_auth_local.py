"""Tests unitaires de la validation locale (python -m unittest -v test_auth_local)."""
import tempfile
import unittest
from pathlib import Path

from auth_local import charger_utilisateurs, hacher, verifier_identifiants

FICHIER = Path(__file__).resolve().parent / "users.sha256"


class TestAuthLocal(unittest.TestCase):
    def setUp(self):
        self.utilisateurs = charger_utilisateurs(FICHIER)

    def test_hacher_valeur_connue(self):
        self.assertEqual(
            hacher("alice"),
            "2bd806c97f0e00af1a1fc3328fa763a9269723c8db8fac4f93af71db186d6e90")

    def test_chargement_des_trois_utilisateurs(self):
        self.assertEqual(set(self.utilisateurs), {"alice", "bob", "clark"})

    def test_identifiants_valides(self):
        for nom in ("alice", "bob", "clark"):
            self.assertTrue(verifier_identifiants(self.utilisateurs, nom, nom))

    def test_mauvais_mot_de_passe(self):
        self.assertFalse(verifier_identifiants(self.utilisateurs, "alice", "bob"))

    def test_utilisateur_inconnu(self):
        self.assertFalse(verifier_identifiants(self.utilisateurs, "eve", "eve"))

    def test_champs_vides(self):
        self.assertFalse(verifier_identifiants(self.utilisateurs, "", ""))

    def test_lignes_vides_ignorees(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "u.sha256"
            chemin.write_text(f"\nzoe:{hacher('pwd')}\n\n", encoding="utf-8")
            self.assertEqual(charger_utilisateurs(chemin), {"zoe": hacher("pwd")})


if __name__ == "__main__":
    unittest.main()
