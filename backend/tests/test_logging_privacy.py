"""I dati di nascita non devono finire nei log.

La privacy policy dichiara che il server elabora i dati in memoria e non
li conserva. Oggi è vero *per assenza*: nel backend non c'è nessuna
chiamata di logging. Questi test rendono la promessa verificabile, così
che un `logger.info(payload)` aggiunto in futuro faccia fallire la CI
invece di passare inosservato.
"""

from __future__ import annotations

import logging

from fastapi.testclient import TestClient

from app.main import _StripQueryString, app

client = TestClient(app)

# Valori inventati e riconoscibili: se comparissero in un log li
# troveremmo per sottostringa senza rischio di falsi positivi.
PAYLOAD = {
    "date": "1911-02-17",
    "time": "03:47",
    "place": {
        "name": "Vattelapesca",
        "latitude": 44.4917,
        "longitude": 11.3428,
        "timezone": "Europe/Rome",
    },
}
SEGRETI = ["1911-02-17", "03:47", "Vattelapesca", "44.4917", "11.3428"]


def _record_di_accesso(path: str) -> logging.LogRecord:
    """Un record come quello che uvicorn emette per ogni richiesta."""
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:1234", "GET", path, "1.1", 200),
        exc_info=None,
    )


def test_il_filtro_toglie_la_query_string():
    record = _record_di_accesso("/api/geocode?q=Vattelapesca&lang=it")
    assert _StripQueryString().filter(record) is True
    assert record.args[2] == "/api/geocode"
    assert "Vattelapesca" not in record.getMessage()


def test_il_filtro_lascia_intatto_il_percorso():
    """Il conteggio per servizio è la nostra unica misura d'uso: non va perso."""
    record = _record_di_accesso("/api/services/elementi")
    _StripQueryString().filter(record)
    assert record.args[2] == "/api/services/elementi"


def _nessun_segreto(caplog) -> None:
    registrato = "\n".join(
        [r.getMessage() for r in caplog.records] + [str(r.args) for r in caplog.records]
    )
    for segreto in SEGRETI:
        assert segreto not in registrato, f"«{segreto}» è finito nei log"


def test_una_richiesta_valida_non_lascia_dati_nei_log(caplog):
    """Senza effemeridi installate la rotta risponde 503, ma il payload
    l'ha comunque attraversata: il test resta valido — e utile — anche
    dove i file delle effemeridi non ci sono."""
    with caplog.at_level(logging.DEBUG):
        response = client.post("/api/services/tema-natale", json=PAYLOAD)
    assert response.status_code in (200, 503)
    _nessun_segreto(caplog)


def test_un_errore_di_validazione_non_lascia_dati_nei_log(caplog):
    """Il caso più insidioso: gli errori Pydantic *contengono* i valori
    ricevuti. Vanno restituiti al client, non registrati."""
    payload = {**PAYLOAD, "place": {**PAYLOAD["place"], "latitude": 999}}
    with caplog.at_level(logging.DEBUG):
        response = client.post("/api/services/tema-natale", json=payload)
    assert response.status_code == 422
    _nessun_segreto(caplog)


def test_un_fuso_orario_mancante_non_lascia_dati_nei_log(caplog):
    """Percorso con `except Exception` in routes.py: verifichiamo che
    l'eccezione inghiottita non si porti dietro i dati nei log."""
    place = {k: v for k, v in PAYLOAD["place"].items() if k != "timezone"}
    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/api/services/tema-natale", json={**PAYLOAD, "place": place}
        )
    assert response.status_code == 422
    _nessun_segreto(caplog)
