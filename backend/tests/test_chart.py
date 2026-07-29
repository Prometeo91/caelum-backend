"""Test del motore astrologico su valori noti (tema di Einstein).

Einstein: 14/3/1879, 11:30 tempo medio locale (LMT = UTC+40min),
Ulm 48.4N 10.0E. Valori attesi:
- Sole 23°30' Pesci, in 10ª casa
- Luna ~14°30' Sagittario
- Ascendente 11°39' Cancro
"""

from __future__ import annotations

from datetime import date, time, timezone

import pytest

from app.astro import chart as chart_mod
from tests.conftest import requires_ephemeris

EINSTEIN_UTC = chart_mod.to_utc(
    date(1879, 3, 14), time(11, 30), utc_offset_minutes=40
)
ULM = {"latitude": 48.4, "longitude": 10.0}


def lon(sign_index: int, deg: int, minutes: int) -> float:
    return sign_index * 30 + deg + minutes / 60


def test_to_utc_with_explicit_offset():
    assert EINSTEIN_UTC.tzinfo == timezone.utc
    assert (EINSTEIN_UTC.hour, EINSTEIN_UTC.minute) == (10, 50)


def test_to_utc_with_iana_timezone():
    utc = chart_mod.to_utc(date(1990, 7, 15), time(12, 0), tz_name="Europe/Rome")
    # Luglio 1990: ora legale, UTC+2.
    assert (utc.hour, utc.minute) == (10, 0)


def test_to_utc_requires_reference():
    with pytest.raises(chart_mod.TimezoneRequired):
        chart_mod.to_utc(date(1990, 7, 15), time(12, 0))


@pytest.fixture(scope="module")
def einstein():
    return chart_mod.compute_chart(EINSTEIN_UTC, **ULM)


@requires_ephemeris
def test_einstein_sun(einstein):
    sun = next(p for p in einstein.bodies if p.id == "sole")
    assert sun.sign == "pesci"
    assert sun.longitude == pytest.approx(lon(11, 23, 30), abs=0.05)
    assert sun.house == 10


@requires_ephemeris
def test_einstein_moon(einstein):
    moon = next(p for p in einstein.bodies if p.id == "luna")
    assert moon.sign == "sagittario"
    assert moon.longitude == pytest.approx(lon(8, 14, 30), abs=0.5)


@requires_ephemeris
def test_einstein_ascendant(einstein):
    asc = einstein.ascendant
    assert asc.sign == "cancro"
    assert asc.longitude == pytest.approx(lon(3, 11, 39), abs=0.2)


@requires_ephemeris
def test_chart_structure(einstein):
    assert len(einstein.bodies) == 10
    assert len(einstein.house_cusps) == 12
    assert einstein.midheaven is not None
    for point in einstein.bodies:
        assert 1 <= point.house <= 12
        assert 0 <= point.longitude < 360
    # La 1ª cuspide Placidus coincide con l'Ascendente.
    assert einstein.house_cusps[0] == pytest.approx(
        einstein.ascendant.longitude, abs=1e-6
    )


@requires_ephemeris
def test_einstein_has_major_aspects(einstein):
    assert einstein.aspects, "un tema reale ha sempre qualche aspetto"
    valid_types = {"congiunzione", "sestile", "quadratura", "trigono", "opposizione"}
    for aspect in einstein.aspects:
        assert aspect.type in valid_types
        assert aspect.orb <= 10.0


@requires_ephemeris
def test_aspects_sorted_by_orb(einstein):
    """L'app mostra gli aspetti nell'ordine ricevuto: dal più stretto."""
    orbs = [a.orb for a in einstein.aspects]
    assert orbs == sorted(orbs)


@requires_ephemeris
def test_aspects_only_between_planets(einstein):
    """Niente aspetti con le cuspidi delle case (Ascendente e Medio
    Cielo compresi): si calcolano solo fra i corpi."""
    cusps = {"ascendente", "medio_cielo"}
    for aspect in einstein.aspects:
        assert aspect.point_a not in cusps
        assert aspect.point_b not in cusps


@requires_ephemeris
def test_house_system_changes_cusps_not_signs(einstein):
    """Cambiare domificazione ricalcola cuspidi e case, non i pianeti
    nei segni (è la promessa fatta nel foglio di domificazione)."""
    whole = chart_mod.compute_chart(EINSTEIN_UTC, **ULM, house_system="W")
    # Segni interi: ogni cuspide è l'inizio esatto di un segno.
    for cusp in whole.house_cusps:
        assert cusp % 30 == pytest.approx(0.0, abs=1e-6)
    for placidus_point, whole_point in zip(einstein.bodies, whole.bodies):
        assert placidus_point.sign == whole_point.sign
        assert placidus_point.longitude == pytest.approx(
            whole_point.longitude, abs=1e-9
        )
    # Con case diverse almeno un corpo cambia casa nel tema di Einstein.
    assert any(
        p.house != w.house for p, w in zip(einstein.bodies, whole.bodies)
    )


def test_unknown_house_system_rejected():
    with pytest.raises(ValueError):
        chart_mod.compute_chart(EINSTEIN_UTC, **ULM, house_system="X")


def test_house_of_wraparound():
    cusps = [350.0] + [350.0 + i * 30 for i in range(1, 12)]
    cusps = [c % 360 for c in cusps]
    assert chart_mod._house_of(355.0, cusps) == 1
    assert chart_mod._house_of(10.0, cusps) == 1
    assert chart_mod._house_of(21.0, cusps) == 2


def test_angular_separation():
    assert chart_mod.angular_separation(10, 350) == pytest.approx(20)
    assert chart_mod.angular_separation(0, 180) == pytest.approx(180)


def test_format_degrees():
    assert chart_mod.format_degrees(23.5) == "23°30'"
    assert chart_mod.format_degrees(0.999) == "1°00'"
    assert chart_mod.format_degrees(11.65) == "11°39'"
