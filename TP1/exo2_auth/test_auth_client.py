"""Tests du client HTTP asynchrone, face au micro-service de test.

Lancement :  python -m unittest -v test_auth_client
"""
import unittest

from aiohttp.test_utils import TestServer

import auth_client
from auth_client import ErreurAuth, get_token, verify_token
from serveur_test import creer_application, creer_jeton


class TestClientAuth(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.serveur = TestServer(creer_application())
        await self.serveur.start_server()
        self.url_login = str(self.serveur.make_url("/login"))
        self.url_verif = str(self.serveur.make_url("/verify"))

    async def asyncTearDown(self):
        await self.serveur.close()

    async def test_get_token_identifiants_valides(self):
        token = await get_token(self.url_login, "alice", "alice")
        self.assertEqual(token.count("."), 2)  # forme d'un JWT

    async def test_get_token_mauvais_mot_de_passe(self):
        with self.assertRaises(ErreurAuth):
            await get_token(self.url_login, "alice", "faux")

    async def test_get_token_utilisateur_inconnu(self):
        with self.assertRaises(ErreurAuth):
            await get_token(self.url_login, "eve", "eve")

    async def test_verify_token_valide(self):
        token = await get_token(self.url_login, "bob", "bob")
        reponse = await verify_token(self.url_verif, token)
        self.assertEqual(reponse, {"valid": True, "user": "bob"})

    async def test_verify_token_falsifie(self):
        token = await get_token(self.url_login, "bob", "bob")
        with self.assertRaises(ErreurAuth):
            await verify_token(self.url_verif, token[:-3] + "xyz")

    async def test_verify_token_expire(self):
        with self.assertRaises(ErreurAuth):
            await verify_token(self.url_verif, creer_jeton("bob", duree=-10))

    async def test_serveur_injoignable(self):
        with self.assertRaises(ErreurAuth) as contexte:
            await get_token("http://127.0.0.1:9/login", "alice", "alice")
        self.assertIn("injoignable", str(contexte.exception))

    async def test_delai_depasse(self):
        ancien = auth_client.DELAI_MAX
        auth_client.DELAI_MAX = 0.001
        try:
            with self.assertRaises(ErreurAuth):
                await get_token(self.url_login, "alice", "alice")
        finally:
            auth_client.DELAI_MAX = ancien


if __name__ == "__main__":
    unittest.main()
