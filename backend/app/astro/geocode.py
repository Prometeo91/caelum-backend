"""Ricerca del luogo di nascita con l'API gratuita di Open-Meteo.

L'API restituisce anche il fuso orario IANA del luogo, che usiamo poi per
convertire l'ora locale di nascita in UTC (ora legale storica inclusa,
via tzdata).
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app import config


@dataclass
class GeoResult:
    name: str
    latitude: float
    longitude: float
    timezone: str | None
    country: str | None
    admin1: str | None  # regione/provincia, per disambiguare


class GeocodingUnavailable(RuntimeError):
    """Il servizio di geocoding non è raggiungibile o ha risposto male."""


async def search_places(
    query: str,
    count: int = 8,
    lang: str = config.DEFAULT_LANG,
    client: httpx.AsyncClient | None = None,
) -> list[GeoResult]:
    params = {"name": query, "count": count, "language": lang, "format": "json"}
    own_client = client is None
    client = client or httpx.AsyncClient(timeout=10)
    try:
        response = await client.get(config.GEOCODING_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise GeocodingUnavailable(str(exc)) from exc
    finally:
        if own_client:
            await client.aclose()

    results = []
    for item in payload.get("results", []):
        results.append(
            GeoResult(
                name=item.get("name", query),
                latitude=item["latitude"],
                longitude=item["longitude"],
                timezone=item.get("timezone"),
                country=item.get("country"),
                admin1=item.get("admin1"),
            )
        )
    return results
