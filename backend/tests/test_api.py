from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.astro import geocode
from app.astro.geocode import GeoResult
from app.main import app
from tests.conftest import requires_contents, requires_ephemeris

client = TestClient(app)

EINSTEIN_PAYLOAD = {
    "date": "1879-03-14",
    "time": "11:30",
    "place": {"name": "Ulm", "latitude": 48.4, "longitude": 10.0},
    "utc_offset_minutes": 40,
}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chart_requires_timezone_or_offset():
    payload = {
        "date": "1990-07-15",
        "time": "12:00",
        "place": {"latitude": 41.9, "longitude": 12.5},
    }
    response = client.post("/api/chart", json=payload)
    assert response.status_code == 422


@requires_ephemeris
def test_chart_einstein_endpoint():
    response = client.post("/api/chart", json=EINSTEIN_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    sun = next(p for p in body["bodies"] if p["id"] == "sole")
    assert sun["sign"] == "pesci"
    assert sun["house"] == 10
    assert sun["degrees_label"] == "23°30'"
    assert body["ascendant"]["sign"] == "cancro"
    assert len(body["house_cusps"]) == 12
    assert body["aspects"]


@requires_ephemeris
def test_chart_with_iana_timezone():
    payload = {
        "date": "1990-07-15",
        "time": "12:00",
        "place": {
            "name": "Roma",
            "latitude": 41.9,
            "longitude": 12.5,
            "timezone": "Europe/Rome",
        },
    }
    response = client.post("/api/chart", json=payload)
    assert response.status_code == 200
    assert response.json()["utc"].startswith("1990-07-15T10:00")


def test_services_catalog():
    response = client.get("/api/services")
    assert response.status_code == 200
    services = {s["id"]: s for s in response.json()}
    assert set(services) == {"tema-natale", "elementi", "emisferi"}
    assert services["elementi"]["free"] is True
    assert services["emisferi"]["free"] is True


def test_unknown_service_404():
    response = client.post("/api/services/inesistente", json=EINSTEIN_PAYLOAD)
    assert response.status_code == 404


@requires_ephemeris
@requires_contents
def test_elements_service_composes_contents():
    response = client.post("/api/services/elementi", json=EINSTEIN_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["totale_punti"] == 11
    assert sum(data["conteggi"].values()) == 11
    slugs = [c["slug"] for c in body["contents"]]
    # Sempre presenti le 4 descrizioni degli elementi.
    for element in ("fuoco", "terra", "aria", "acqua"):
        assert f"elementi/elemento-{element}" in slugs
    # I contenuti reali del repo sono caricati, non segnaposto.
    assert all(c["missing"] is False for c in body["contents"])
    assert all(c["title"] for c in body["contents"])


@requires_ephemeris
@requires_contents
def test_hemispheres_service_composes_contents():
    response = client.post("/api/services/emisferi", json=EINSTEIN_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["totale_punti"] == 10
    # Ogni corpo conta una volta per asse.
    assert data["conteggi"]["superiore"] + data["conteggi"]["inferiore"] == 10
    assert data["conteggi"]["orientale"] + data["conteggi"]["occidentale"] == 10
    # I contenuti allegati sono solo quelli delle concentrazioni rilevate.
    slugs = [c["slug"] for c in body["contents"]]
    expected = [
        f"emisferi/emisfero-{h}"
        for h in (data["verticale"], data["orizzontale"])
        if h
    ]
    assert slugs == expected
    assert all(c["missing"] is False for c in body["contents"])


@requires_ephemeris
def test_natal_chart_service_returns_chart_data():
    response = client.post("/api/services/tema-natale", json=EINSTEIN_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["service"]["id"] == "tema-natale"
    assert len(body["data"]["bodies"]) == 10
    # Le pagine di lettura hanno uno slug per pianeta nel segno e nella
    # casa, per gli angoli e per ogni aspetto; finché i testi non sono
    # scritti il loader risponde con segnaposto (missing = True).
    slugs = [c["slug"] for c in body["contents"]]
    assert "tema-natale/sole-in-pesci" in slugs
    assert "tema-natale/sole-in-casa-10" in slugs
    assert "tema-natale/ascendente-in-cancro" in slugs
    assert any(s.startswith("tema-natale/medio-cielo-in-") for s in slugs)
    assert len(slugs) == len(set(slugs)), "slug duplicati"
    aspect_count = len(body["data"]["aspects"])
    # 10 segni + 10 case + 2 angoli + aspetti.
    assert len(slugs) == 22 + aspect_count
    # A pagamento solo i pianeti nel segno da Mercurio a Plutone: otto
    # contenuti, mai case, aspetti o i tre pilastri gratuiti.
    paid = {c["slug"] for c in body["contents"] if c["paid"]}
    assert len(paid) == 8
    assert all("-in-" in slug and "-casa-" not in slug for slug in paid)
    free_prefixes = (
        "tema-natale/sole-in-",
        "tema-natale/luna-in-",
        "tema-natale/ascendente-in-",
    )
    assert not any(slug.startswith(free_prefixes) for slug in paid)


@requires_ephemeris
def test_now_returns_current_positions():
    response = client.get("/api/now")
    assert response.status_code == 200
    body = response.json()
    ids = [b["id"] for b in body["bodies"]]
    assert ids[0] == "sole" and ids[-1] == "plutone" and len(ids) == 10
    for point in body["bodies"]:
        # Senza luogo niente case; segno e gradi ci sono sempre.
        assert point["house"] is None
        assert 0 <= point["sign_degrees"] < 30
        assert point["degrees_label"]
    # L'istante è UTC esplicito.
    assert body["utc"].endswith("+00:00")


def test_paid_slug_rule():
    from app.services import natal_chart

    assert natal_chart.is_paid_slug("tema-natale/mercurio-in-ariete")
    assert natal_chart.is_paid_slug("tema-natale/plutone-in-pesci")
    # Pilastri gratuiti, case e aspetti fuori dal pacchetto.
    assert not natal_chart.is_paid_slug("tema-natale/sole-in-leone")
    assert not natal_chart.is_paid_slug("tema-natale/luna-in-scorpione")
    assert not natal_chart.is_paid_slug("tema-natale/ascendente-in-cancro")
    assert not natal_chart.is_paid_slug("tema-natale/mercurio-in-casa-3")
    assert not natal_chart.is_paid_slug("tema-natale/mercurio-trigono-plutone")


@requires_ephemeris
def test_chart_house_system_parameter():
    payload = {**EINSTEIN_PAYLOAD, "house_system": "W"}
    response = client.post("/api/chart", json=payload)
    assert response.status_code == 200
    body = response.json()
    # Segni interi: cuspidi sugli inizi esatti dei segni.
    assert all(c % 30 == 0 for c in body["house_cusps"])
    # I pianeti nei segni non cambiano.
    sun = next(p for p in body["bodies"] if p["id"] == "sole")
    assert sun["sign"] == "pesci"


def test_chart_unknown_house_system_422():
    payload = {**EINSTEIN_PAYLOAD, "house_system": "Z"}
    response = client.post("/api/chart", json=payload)
    assert response.status_code == 422


def test_geocode_endpoint(monkeypatch):
    async def fake_search(query, count=8, lang="it", client=None):
        assert query == "Ulm"
        return [
            GeoResult(
                name="Ulm",
                latitude=48.4,
                longitude=10.0,
                timezone="Europe/Berlin",
                country="Germania",
                admin1="Baden-Württemberg",
            )
        ]

    monkeypatch.setattr(geocode, "search_places", fake_search)
    response = client.get("/api/geocode", params={"q": "Ulm"})
    assert response.status_code == 200
    results = response.json()
    assert results[0]["timezone"] == "Europe/Berlin"


def test_geocode_unavailable_maps_to_503(monkeypatch):
    async def failing_search(query, count=8, lang="it", client=None):
        raise geocode.GeocodingUnavailable("down")

    monkeypatch.setattr(geocode, "search_places", failing_search)
    response = client.get("/api/geocode", params={"q": "Ulm"})
    assert response.status_code == 503


def test_nessun_header_cors_per_impostazione_predefinita():
    """Senza CAELUM_CORS_ORIGINS il backend non si lascia chiamare dalle
    pagine web altrui: con `allow_origins=["*"]` chiunque poteva usarlo
    come motore di calcolo gratuito a spese della nostra quota."""
    response = client.get("/health", headers={"Origin": "https://terzo.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
