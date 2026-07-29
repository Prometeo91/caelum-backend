"""Configurazione centralizzata del backend.

Tutti i valori regolabili (corpi calcolati, orbi degli aspetti, percorsi)
vivono qui: la logica di calcolo li legge da questo modulo e non li
ridefinisce altrove.
"""

from __future__ import annotations

import os
from pathlib import Path

import swisseph as swe

BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/
REPO_DIR = BACKEND_DIR.parent

# Percorso dei file effemeridi (scaricati, mai committati).
EPHE_PATH = Path(os.environ.get("EPHE_PATH", BACKEND_DIR / "ephe"))

# Radice dei contenuti interpretativi (Markdown, per lingua).
CONTENT_DIR = Path(os.environ.get("CONTENUTI_DIR", REPO_DIR / "contenuti"))

# Lingua di riferimento: i contenuti devono esistere almeno in questa lingua.
DEFAULT_LANG = "it"

# Endpoint di geocoding (API gratuita di Open-Meteo).
GEOCODING_URL = os.environ.get(
    "GEOCODING_URL", "https://geocoding-api.open-meteo.com/v1/search"
)

# I dieci corpi classici, in ordine. Lista configurabile: per aggiungere
# un corpo basta una voce (id stabile usato nelle API e nei test).
BODIES: list[tuple[str, int]] = [
    ("sole", swe.SUN),
    ("luna", swe.MOON),
    ("mercurio", swe.MERCURY),
    ("venere", swe.VENUS),
    ("marte", swe.MARS),
    ("giove", swe.JUPITER),
    ("saturno", swe.SATURN),
    ("urano", swe.URANUS),
    ("nettuno", swe.NEPTUNE),
    ("plutone", swe.PLUTO),
]

# Sistema di case predefinito: Placidus.
HOUSE_SYSTEM = b"P"

# Sistemi di domificazione selezionabili dall'app (codici Swiss Ephemeris).
# L'elenco rispecchia il foglio di domificazione del redesign «Specola»;
# le etichette visibili sono tradotte nell'app, qui servono solo ai log
# e alla validazione.
HOUSE_SYSTEMS: dict[str, str] = {
    "P": "Placido",
    "W": "Segni interi",
    "E": "Case uguali",
    "K": "Koch",
    "R": "Regiomontano",
    "C": "Campano",
    "O": "Porfirio",
    "T": "Topocentrico (Polich-Page)",
    "I": "Pullen SR",
}

# Aspetti maggiori: angolo e orbo (in gradi), entrambi configurabili.
ASPECTS: dict[str, dict[str, float]] = {
    "congiunzione": {"angle": 0.0, "orb": 10.0},
    "sestile": {"angle": 60.0, "orb": 4.0},
    "quadratura": {"angle": 90.0, "orb": 6.0},
    "trigono": {"angle": 120.0, "orb": 8.0},
    "opposizione": {"angle": 180.0, "orb": 10.0},
}

# Punti inclusi nel calcolo degli aspetti oltre ai corpi (id speciali).
# Vuoto per scelta editoriale: gli aspetti si calcolano solo fra pianeti,
# non con le cuspidi delle case (Ascendente e Medio Cielo compresi).
ASPECT_EXTRA_POINTS: list[str] = []

# Segni zodiacali (indice 0 = Ariete) e loro elemento.
SIGNS: list[str] = [
    "ariete", "toro", "gemelli", "cancro", "leone", "vergine",
    "bilancia", "scorpione", "sagittario", "capricorno", "acquario", "pesci",
]

ELEMENT_OF_SIGN: list[str] = [
    "fuoco", "terra", "aria", "acqua",
    "fuoco", "terra", "aria", "acqua",
    "fuoco", "terra", "aria", "acqua",
]

ELEMENTS: list[str] = ["fuoco", "terra", "aria", "acqua"]
