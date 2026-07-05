from __future__ import annotations

from datetime import datetime, timezone

from app.astro.chart import Chart, _make_point
from app.services import hemispheres


def make_chart(body_houses: dict[str, int]) -> Chart:
    chart = Chart(
        utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
        julian_day_ut=0.0,
        latitude=0.0,
        longitude=0.0,
    )
    for pid, house in body_houses.items():
        point = _make_point(pid, 0.0)
        point.house = house
        chart.bodies.append(point)
    return chart


def test_counts_by_house():
    chart = make_chart({"sole": 1, "luna": 7, "mercurio": 10, "venere": 4})
    data = hemispheres.compute(chart)
    assert data["totale_punti"] == 4
    assert data["conteggi"] == {
        "superiore": 2,  # case 7 e 10
        "inferiore": 2,  # case 1 e 4
        "orientale": 2,  # case 1 e 10
        "occidentale": 2,  # case 7 e 4
    }
    assert data["punti"]["sole"] == {
        "verticale": "inferiore",
        "orizzontale": "orientale",
    }
    assert data["punti"]["venere"] == {
        "verticale": "inferiore",
        "orizzontale": "occidentale",
    }


def test_concentration_detected_on_both_axes():
    # 8 corpi in casa 12 (superiore + orientale), 2 in casa 5.
    houses = {f"corpo{i}": 12 for i in range(8)}
    houses |= {"nettuno": 5, "plutone": 5}
    data = hemispheres.compute(make_chart(houses))
    assert data["conteggi"]["superiore"] == 8
    assert data["verticale"] == "superiore"
    assert data["orizzontale"] == "orientale"


def test_below_threshold_gives_no_concentration():
    # 6 sopra e 4 sotto l'orizzonte: sotto la soglia di 7.
    houses = {f"corpo{i}": 9 for i in range(6)}
    houses |= {f"altro{i}": 2 for i in range(4)}
    data = hemispheres.compute(make_chart(houses))
    assert data["conteggi"]["superiore"] == 6
    assert data["verticale"] is None
    # Est/ovest: 4 orientali (casa 2) e 6 occidentali (casa 9).
    assert data["orizzontale"] is None


def test_points_without_house_are_skipped():
    chart = make_chart({"sole": 1})
    chart.bodies[0].house = None
    data = hemispheres.compute(chart)
    assert data["totale_punti"] == 0
    assert data["verticale"] is None


def test_content_slugs_composition():
    both = hemispheres.content_slugs(
        {"verticale": "inferiore", "orizzontale": "occidentale"}
    )
    assert both == [
        "emisferi/emisfero-inferiore",
        "emisferi/emisfero-occidentale",
    ]
    assert hemispheres.content_slugs({"verticale": None, "orizzontale": None}) == []


def test_required_contents_checklist():
    assert len(hemispheres.REQUIRED_CONTENTS) == 4
    assert "emisferi/emisfero-orientale" in hemispheres.REQUIRED_CONTENTS
