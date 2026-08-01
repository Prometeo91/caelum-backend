"""Modelli Pydantic delle richieste/risposte API."""

from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, Field, field_validator, model_validator

from app import config


class PlaceIn(BaseModel):
    name: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str | None = None  # fuso IANA, es. "Europe/Rome"


class BirthDataIn(BaseModel):
    """Dati di nascita. Il fuso IANA gestisce l'ora legale storica;
    `utc_offset_minutes` (es. 40 per LMT di Ulm) ha la precedenza e serve
    per nascite registrate in tempo medio locale."""

    date: date
    time: time
    place: PlaceIn
    utc_offset_minutes: int | None = Field(default=None, ge=-16 * 60, le=16 * 60)
    # Codice Swiss Ephemeris del sistema di domificazione (vedi
    # config.HOUSE_SYSTEMS): preferenza globale dell'app, non per-calcolo.
    house_system: str = "P"

    @field_validator("house_system")
    @classmethod
    def _known_house_system(cls, value: str) -> str:
        if value not in config.HOUSE_SYSTEMS:
            allowed = ", ".join(sorted(config.HOUSE_SYSTEMS))
            raise ValueError(
                f"Sistema di domificazione sconosciuto (ammessi: {allowed})."
            )
        return value

    @model_validator(mode="after")
    def _require_time_reference(self):
        if self.utc_offset_minutes is None and not self.place.timezone:
            raise ValueError(
                "Indicare place.timezone (IANA) oppure utc_offset_minutes."
            )
        return self


class PointOut(BaseModel):
    id: str
    longitude: float
    sign: str
    sign_index: int
    sign_degrees: float
    degrees_label: str  # es. "23°30'"
    element: str
    house: int | None
    retrograde: bool | None = None


class AspectOut(BaseModel):
    point_a: str
    point_b: str
    type: str
    angle: float
    orb: float
    separation: float


class ChartOut(BaseModel):
    utc: str
    julian_day_ut: float
    latitude: float
    longitude: float
    bodies: list[PointOut]
    ascendant: PointOut
    midheaven: PointOut
    house_cusps: list[float]
    aspects: list[AspectOut]


class ContentOut(BaseModel):
    slug: str
    lang: str
    missing: bool
    title: str | None = None
    body: str = ""
    card_title: str | None = None
    teaser: str | None = None
    paid: bool = False


class ServiceInfoOut(BaseModel):
    id: str
    version: int
    free: bool
    name_key: str


class ServiceResultOut(BaseModel):
    service: ServiceInfoOut
    data: dict
    contents: list[ContentOut]


class GeoResultOut(BaseModel):
    name: str
    latitude: float
    longitude: float
    timezone: str | None
    country: str | None
    admin1: str | None
