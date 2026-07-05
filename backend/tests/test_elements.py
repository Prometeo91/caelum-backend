from __future__ import annotations

from datetime import datetime, timezone

from app.astro.chart import Chart, Point
from app.services import elements


def make_point(pid: str, longitude: float) -> Point:
    from app.astro.chart import _make_point

    point = _make_point(pid, longitude)
    point.house = 1
    return point


def make_chart(body_longitudes: dict[str, float], asc: float) -> Chart:
    chart = Chart(
        utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
        julian_day_ut=0.0,
        latitude=0.0,
        longitude=0.0,
    )
    chart.bodies = [make_point(pid, lon) for pid, lon in body_longitudes.items()]
    chart.ascendant = make_point("ascendente", asc)
    return chart


FIRE, EARTH, AIR, WATER = 5.0, 35.0, 65.0, 95.0  # Ariete, Toro, Gemelli, Cancro


def test_counts_include_ascendant():
    chart = make_chart({"sole": FIRE, "luna": EARTH}, asc=WATER)
    data = elements.compute(chart)
    assert data["totale_punti"] == 3
    assert data["conteggi"] == {"fuoco": 1, "terra": 1, "aria": 0, "acqua": 1}
    assert data["punti"]["ascendente"] == "acqua"


def test_preponderance_and_lack():
    longs = {
        "sole": FIRE, "luna": FIRE + 120, "mercurio": FIRE + 240, "venere": FIRE,
        "marte": EARTH, "giove": EARTH, "saturno": AIR, "urano": AIR,
        "nettuno": WATER, "plutone": EARTH,
    }
    data = elements.compute(make_chart(longs, asc=FIRE))
    assert data["conteggi"]["fuoco"] == 5
    assert data["preponderante"] == "fuoco"
    assert data["carente"] == "acqua"


def test_tie_gives_no_preponderance():
    longs = {
        "sole": FIRE, "luna": FIRE, "mercurio": FIRE, "venere": FIRE,
        "marte": EARTH, "giove": EARTH, "saturno": EARTH, "urano": EARTH,
        "nettuno": AIR, "plutone": WATER,
    }
    data = elements.compute(make_chart(longs, asc=AIR))
    # fuoco=4 e terra=4: nessun preponderante unico.
    assert data["preponderante"] is None


def test_below_threshold_gives_no_preponderance():
    longs = {
        "sole": FIRE, "luna": FIRE, "mercurio": FIRE,
        "marte": EARTH, "giove": EARTH,
        "saturno": AIR, "urano": AIR,
        "nettuno": WATER, "plutone": WATER,
    }
    data = elements.compute(make_chart(longs, asc=WATER))
    # massimo = 3 (fuoco, acqua) < soglia 4 e non unico.
    assert data["preponderante"] is None


def test_lack_requires_unique_minimum():
    longs = {
        "sole": FIRE, "luna": FIRE, "mercurio": FIRE, "venere": FIRE,
        "marte": FIRE, "giove": EARTH, "saturno": AIR,
        "urano": EARTH, "nettuno": AIR, "plutone": FIRE,
    }
    data = elements.compute(make_chart(longs, asc=FIRE))
    # acqua=0 unico minimo -> carente; fuoco=7 -> preponderante.
    assert data["carente"] == "acqua"
    assert data["preponderante"] == "fuoco"


def test_content_slugs_composition():
    data = {"preponderante": "fuoco", "carente": "acqua"}
    slugs = elements.content_slugs(data)
    assert "elementi/elemento-fuoco" in slugs
    assert "elementi/fuoco-preponderanza" in slugs
    assert "elementi/acqua-carenza" in slugs
    assert len(slugs) == 6

    balanced = elements.content_slugs({"preponderante": None, "carente": None})
    assert len(balanced) == 4


def test_required_contents_checklist():
    assert len(elements.REQUIRED_CONTENTS) == 12
    assert "elementi/terra-preponderanza" in elements.REQUIRED_CONTENTS
    assert "elementi/aria-carenza" in elements.REQUIRED_CONTENTS
