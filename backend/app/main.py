"""Entry point FastAPI.

Avvio locale:
    cd backend
    python scripts/download_ephe.py   # una tantum
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

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
