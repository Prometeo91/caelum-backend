"""Entry point FastAPI.

Avvio locale:
    cd backend
    python scripts/download_ephe.py   # una tantum
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router


class _StripQueryString(logging.Filter):
    """Toglie la query string dal log di accesso di uvicorn.

    I dati di nascita viaggiano nel corpo delle POST e non sono mai
    registrati, ma `GET /api/geocode?q=Roma` lascerebbe il luogo cercato
    nei log della piattaforma, insieme a indirizzo IP e orario: una
    conservazione che la privacy policy dichiara di non fare.

    Il **percorso** resta intatto, quindi restano leggibili i conteggi
    per servizio (`/api/services/elementi` e simili), che sono l'unica
    misura d'uso di cui disponiamo senza analytics nell'app.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # uvicorn passa (client_addr, method, full_path, http_version, status).
        args = record.args
        if isinstance(args, tuple) and len(args) == 5:
            path = args[2]
            if isinstance(path, str) and "?" in path:
                record.args = (*args[:2], path.split("?", 1)[0], *args[3:])
        return True


# I filtri sopravvivono alla configurazione del logging fatta da uvicorn
# all'avvio: `dictConfig` sostituisce gli handler, non i filtri.
logging.getLogger("uvicorn.access").addFilter(_StripQueryString())

app = FastAPI(
    title="Caelum backend",
    version="0.1.0",
    description=(
        "Calcolo del tema natale (Swiss Ephemeris) e composizione dei "
        "servizi interpretativi. Nessun dato di nascita viene salvato: "
        "il backend è stateless, i dati restano sul dispositivo. "
        "Codice sorgente (AGPL-3.0): "
        "https://github.com/Prometeo91/caelum-backend"
    ),
)

# CORS chiuso: l'app mobile parla in HTTP nativo e il CORS non la
# riguarda: è una regola dei browser. Con `["*"]` qualunque sito poteva
# usare questo backend come motore di calcolo gratuito dalle pagine dei
# propri visitatori, a spese della nostra quota su Render.
#
# Non è una difesa contro l'abuso in generale (uno script o un curl
# passano comunque), ma toglie la via più comoda.
#
# CAELUM_CORS_ORIGINS, separate da virgola, riapre a origini specifiche:
# serve per lo sviluppo web locale o se un domani ci sarà un sito.
_origins = [o.strip() for o in os.getenv("CAELUM_CORS_ORIGINS", "").split(",") if o.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(router)
