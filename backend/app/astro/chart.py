"""Calcolo del tema natale: posizioni, case Placidus, aspetti maggiori."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app import config
from app.astro.ephemeris import ephemeris_session


@dataclass
class Point:
    """Un punto del tema (corpo, Ascendente o Medio Cielo)."""

    id: str
    longitude: float  # longitudine eclittica 0–360
    sign: str
    sign_index: int
    sign_degrees: float  # gradi dentro il segno, 0–30
    element: str
    house: int | None = None
    speed: float | None = None  # gradi/giorno (solo corpi)
    retrograde: bool | None = None


@dataclass
class Aspect:
    point_a: str
    point_b: str
    type: str
    angle: float  # angolo esatto dell'aspetto (es. 120)
    orb: float  # scarto in gradi dall'angolo esatto
    separation: float  # distanza angolare effettiva


@dataclass
class Chart:
    utc: datetime
    julian_day_ut: float
    latitude: float
    longitude: float
    bodies: list[Point] = field(default_factory=list)
    ascendant: Point | None = None
    midheaven: Point | None = None
    house_cusps: list[float] = field(default_factory=list)  # 12 cuspidi, casa 1–12
    aspects: list[Aspect] = field(default_factory=list)

    def all_points(self) -> list[Point]:
        extra = [p for p in (self.ascendant, self.midheaven) if p is not None]
        return self.bodies + extra


class TimezoneRequired(ValueError):
    """Serve il fuso IANA oppure un offset UTC esplicito."""


def to_utc(
    birth_date: date,
    birth_time: time,
    tz_name: str | None = None,
    utc_offset_minutes: int | None = None,
) -> datetime:
    """Converte data/ora locali di nascita in UTC.

    `utc_offset_minutes`, se presente, ha la precedenza: serve per nascite
    registrate in tempo medio locale (LMT) o con offset noti non coperti
    da tzdata. Altrimenti si usa il fuso IANA, che gestisce l'ora legale
    storica tramite tzdata.
    """
    naive = datetime.combine(birth_date, birth_time)
    if utc_offset_minutes is not None:
        return (naive - timedelta(minutes=utc_offset_minutes)).replace(
            tzinfo=timezone.utc
        )
    if tz_name:
        return naive.replace(tzinfo=ZoneInfo(tz_name)).astimezone(timezone.utc)
    raise TimezoneRequired(
        "Indicare il fuso orario IANA oppure utc_offset_minutes."
    )


def _julian_day_ut(utc: datetime) -> float:
    hour = utc.hour + utc.minute / 60 + utc.second / 3600
    # swe.julday è puro calcolo di calendario, ma lo teniamo dentro la
    # sessione per uniformità d'uso della libreria.
    with ephemeris_session() as swe:
        return swe.julday(utc.year, utc.month, utc.day, hour)


def _make_point(point_id: str, lon: float, speed: float | None = None) -> Point:
    lon = lon % 360.0
    sign_index = int(lon // 30)
    return Point(
        id=point_id,
        longitude=lon,
        sign=config.SIGNS[sign_index],
        sign_index=sign_index,
        sign_degrees=lon % 30.0,
        element=config.ELEMENT_OF_SIGN[sign_index],
        speed=speed,
        retrograde=(speed < 0) if speed is not None else None,
    )


def _house_of(lon: float, cusps: list[float]) -> int:
    """Casa (1–12) che contiene la longitudine data."""
    lon = lon % 360.0
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if start <= end:
            inside = start <= lon < end
        else:  # la casa attraversa 0° Ariete
            inside = lon >= start or lon < end
        if inside:
            return i + 1
    return 12  # irraggiungibile, per completezza


def angular_separation(a: float, b: float) -> float:
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def _find_aspects(points: list[Point]) -> list[Aspect]:
    aspects: list[Aspect] = []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            pa, pb = points[i], points[j]
            # Un punto con restrizioni (oggi l'Ascendente, che fa solo
            # congiunzioni) la impone all'intera coppia.
            allowed = config.ASPECT_TYPES_ALLOWED.get(
                pa.id
            ) or config.ASPECT_TYPES_ALLOWED.get(pb.id)
            sep = angular_separation(pa.longitude, pb.longitude)
            for name, spec in config.ASPECTS.items():
                if allowed is not None and name not in allowed:
                    continue
                orb = abs(sep - spec["angle"])
                if orb <= spec["orb"]:
                    aspects.append(
                        Aspect(
                            point_a=pa.id,
                            point_b=pb.id,
                            type=name,
                            angle=spec["angle"],
                            orb=round(orb, 4),
                            separation=round(sep, 4),
                        )
                    )
                    break  # un solo aspetto per coppia
    # Dal più stretto al più largo: l'ordine che l'app mostra così com'è.
    aspects.sort(key=lambda a: a.orb)
    return aspects


def compute_chart(
    utc: datetime,
    latitude: float,
    longitude: float,
    bodies: list[tuple[str, int]] | None = None,
    house_system: str | None = None,
) -> Chart:
    """Calcola il tema natale completo per l'istante UTC e il luogo dati.

    `house_system` è un codice di config.HOUSE_SYSTEMS (predefinito
    Placidus): cambia cuspidi e posizioni nelle case, non i pianeti
    nei segni.
    """
    bodies = bodies if bodies is not None else config.BODIES
    if house_system is None:
        hsys = config.HOUSE_SYSTEM
    elif house_system in config.HOUSE_SYSTEMS:
        hsys = house_system.encode("ascii")
    else:
        raise ValueError(f"Sistema di domificazione sconosciuto: {house_system}")
    jd_ut = _julian_day_ut(utc)

    chart = Chart(
        utc=utc,
        julian_day_ut=jd_ut,
        latitude=latitude,
        longitude=longitude,
    )

    with ephemeris_session() as swe:
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        for body_id, swe_id in bodies:
            values, _retflags = swe.calc_ut(jd_ut, swe_id, flags)
            lon, _lat, _dist, lon_speed = values[0], values[1], values[2], values[3]
            chart.bodies.append(_make_point(body_id, lon, speed=lon_speed))

        cusps, ascmc = swe.houses(jd_ut, latitude, longitude, hsys)

    chart.house_cusps = [c % 360.0 for c in cusps[:12]]
    chart.ascendant = _make_point("ascendente", ascmc[0])
    chart.ascendant.house = 1
    chart.midheaven = _make_point("medio_cielo", ascmc[1])
    chart.midheaven.house = _house_of(chart.midheaven.longitude, chart.house_cusps)

    for point in chart.bodies:
        point.house = _house_of(point.longitude, chart.house_cusps)

    aspect_points = chart.bodies + [
        p
        for p in (chart.ascendant, chart.midheaven)
        if p is not None and p.id in config.ASPECT_EXTRA_POINTS
    ]
    chart.aspects = _find_aspects(aspect_points)
    return chart


def format_degrees(sign_degrees: float) -> str:
    """23.5 -> \"23°30'\" (per tabelle e log)."""
    deg = int(sign_degrees)
    minutes = round((sign_degrees - deg) * 60)
    if minutes == 60:
        deg, minutes = deg + 1, 0
    return f"{deg}°{minutes:02d}'"
