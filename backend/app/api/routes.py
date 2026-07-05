"""Rotte API del backend."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app import config
from app.api import schemas
from app.astro import chart as chart_mod
from app.astro import geocode
from app.astro.ephemeris import EphemerisNotInstalled
from app.content import loader
from app.services.catalog import CATALOG, ServiceDef, get_service

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/api/geocode", response_model=list[schemas.GeoResultOut])
async def geocode_place(
    q: str = Query(min_length=2, max_length=100),
    count: int = Query(default=8, ge=1, le=20),
    lang: str = Query(default=config.DEFAULT_LANG, min_length=2, max_length=5),
):
    try:
        results = await geocode.search_places(q, count=count, lang=lang)
    except geocode.GeocodingUnavailable:
        raise HTTPException(
            status_code=503, detail="Servizio di ricerca luoghi non disponibile."
        )
    return [schemas.GeoResultOut(**vars(r)) for r in results]


def _point_out(point: chart_mod.Point) -> schemas.PointOut:
    return schemas.PointOut(
        id=point.id,
        longitude=round(point.longitude, 4),
        sign=point.sign,
        sign_index=point.sign_index,
        sign_degrees=round(point.sign_degrees, 4),
        degrees_label=chart_mod.format_degrees(point.sign_degrees),
        element=point.element,
        house=point.house,
        retrograde=point.retrograde,
    )


def _chart_out(chart: chart_mod.Chart) -> schemas.ChartOut:
    return schemas.ChartOut(
        utc=chart.utc.isoformat(),
        julian_day_ut=chart.julian_day_ut,
        latitude=chart.latitude,
        longitude=chart.longitude,
        bodies=[_point_out(p) for p in chart.bodies],
        ascendant=_point_out(chart.ascendant),
        midheaven=_point_out(chart.midheaven),
        house_cusps=[round(c, 4) for c in chart.house_cusps],
        aspects=[schemas.AspectOut(**vars(a)) for a in chart.aspects],
    )


def _compute_chart(birth: schemas.BirthDataIn) -> chart_mod.Chart:
    try:
        utc = chart_mod.to_utc(
            birth.date,
            birth.time,
            tz_name=birth.place.timezone,
            utc_offset_minutes=birth.utc_offset_minutes,
        )
    except chart_mod.TimezoneRequired as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=422, detail="Fuso orario non valido.")
    try:
        return chart_mod.compute_chart(
            utc, birth.place.latitude, birth.place.longitude
        )
    except EphemerisNotInstalled as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/api/chart", response_model=schemas.ChartOut)
def compute_chart(birth: schemas.BirthDataIn):
    return _chart_out(_compute_chart(birth))


@router.get("/api/services", response_model=list[schemas.ServiceInfoOut])
def list_services():
    return [_service_info(s) for s in CATALOG]


def _service_info(service: ServiceDef) -> schemas.ServiceInfoOut:
    return schemas.ServiceInfoOut(
        id=service.id,
        version=service.version,
        free=service.free,
        name_key=service.name_key,
    )


@router.post("/api/services/{service_id}", response_model=schemas.ServiceResultOut)
def run_service(
    service_id: str,
    birth: schemas.BirthDataIn,
    lang: str = Query(default=config.DEFAULT_LANG, min_length=2, max_length=5),
):
    service = get_service(service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Servizio inesistente.")

    chart = _compute_chart(birth)
    data = service.compute(chart)
    if service.id == "tema-natale":
        data = _chart_out(chart).model_dump()

    bundle = loader.load_bundle(service.content_slugs(data), lang=lang)
    return schemas.ServiceResultOut(
        service=_service_info(service),
        data=data,
        contents=[schemas.ContentOut(**vars(c)) for c in bundle.items],
    )
