"""Entry point FastAPI.

Avvio locale:
    cd backend
    python scripts/download_ephe.py   # una tantum
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging

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

# L'app mobile non ha bisogno di CORS; questa apertura serve solo per
# sviluppo/web preview. Da restringere quando ci sarà un dominio.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
