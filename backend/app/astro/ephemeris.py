"""Accesso serializzato e thread-safe a Swiss Ephemeris.

pyswisseph conserva il percorso delle effemeridi in storage thread-local:
`swe.set_ephe_path` va richiamato in OGNI thread che usa la libreria
(FastAPI esegue gli endpoint sincroni in un pool di thread). Inoltre le
funzioni di calcolo non sono rientranti, quindi tutte le chiamate passano
da un unico lock globale.

Usare sempre `ephemeris_session()` attorno alle chiamate a swe.*.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager

import swisseph as swe

from app import config

_lock = threading.Lock()
_tls = threading.local()

# I file minimi per i dieci corpi classici (1800–2399) più il file
# asteroidi, per usi futuri. Scaricati da scripts/download_ephe.py.
REQUIRED_FILES = ["sepl_18.se1", "semo_18.se1", "seas_18.se1"]


class EphemerisNotInstalled(RuntimeError):
    """File effemeridi assenti: eseguire backend/scripts/download_ephe.py."""


def _ensure_thread_initialized() -> None:
    if not getattr(_tls, "initialized", False):
        missing = [
            name for name in REQUIRED_FILES
            if not (config.EPHE_PATH / name).is_file()
        ]
        if missing:
            raise EphemerisNotInstalled(
                "File effemeridi mancanti in "
                f"{config.EPHE_PATH}: {', '.join(missing)}. "
                "Eseguire: python backend/scripts/download_ephe.py"
            )
        swe.set_ephe_path(str(config.EPHE_PATH))
        _tls.initialized = True


@contextmanager
def ephemeris_session():
    """Serializza l'uso di swe.* e garantisce set_ephe_path nel thread."""
    with _lock:
        _ensure_thread_initialized()
        yield swe
