# R309 – TP n° 01 : PyQt6

Programmation évènementielle avec PyQt6.

## Contenu

| Dossier | Sujet |
|---|---|
| `TP1/exo1_compteur/` | Exercice 1 : application compteur (label 0 à 100, boutons `+` et `-`, QSS) |
| `TP1/exo2_auth/` | Exercice 2 : application d'authentification (Designer, QStackedWidget, qasync, QSettings, QToolBar) |
| `TP1/rapport/` | Rapport du TP |

Chaque question correspond à un tag Git : `tp1-exo1`, `tp1-exo2-1`, `tp1-exo2-2`, `tp1-exo2-3`, `tp1-exo2-4`.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancement

```bash
# Exercice 1
cd TP1/exo1_compteur && python3 compteur.py

# Exercice 2 (dans un premier terminal : le micro-service de test, port 4567)
cd TP1/exo2_auth && python3 serveur_test.py
# Exercice 2 (dans un second terminal : l'application)
cd TP1/exo2_auth && python3 auth_app.py          # authentification par le micro-service
cd TP1/exo2_auth && python3 auth_app.py --local  # vérification locale (users.sha256)
```

Utilisateurs de test : `alice`, `bob`, `clark` (le mot de passe est identique au nom).

## Tests unitaires

```bash
cd TP1/exo1_compteur && python3 -m unittest -v test_compteur
cd TP1/exo2_auth && python3 -m unittest -v test_auth_local test_auth_client test_parametres test_auth_ui
```

Les tests utilisent le moteur graphique `offscreen` : aucune fenêtre ne s'affiche.
