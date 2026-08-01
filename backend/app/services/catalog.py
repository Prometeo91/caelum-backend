"""Catalogo dei servizi: dati, non codice sparso.

Ogni servizio è una voce di questo catalogo. Per aggiungerne uno nuovo
(anche a pagamento) servono solo:

1. un modulo con la funzione di calcolo `compute(chart) -> dict`
   (ed eventualmente `content_slugs(data)` e `REQUIRED_CONTENTS`);
2. una voce `ServiceDef` qui sotto;
3. i file Markdown in `contenuti/<lingua>/...`.

Nessun'altra parte del backend va toccata: le rotte API e la checklist di
copertura leggono il catalogo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from app.astro.chart import Chart
from app.services import elements, hemispheres, natal_chart


@dataclass(frozen=True)
class ServiceDef:
    id: str
    version: int
    free: bool
    # Chiave i18n: nome e descrizione visibili sono tradotti nell'app.
    name_key: str
    compute: Callable[[Chart], dict]
    # Dati calcolati -> slug dei contenuti da allegare alla risposta.
    content_slugs: Callable[[dict], list[str]] = lambda data: []
    # Checklist di copertura per gli autori dei contenuti.
    required_contents: list[str] = field(default_factory=list)
    # Slug -> il contenuto è a pagamento? Il flag arriva all'app, che
    # mostra chiuso ciò che non è stato acquistato (lo sblocco è un
    # acquisto in-app; lo stato vive nello store, non nel backend).
    paid_contents: Callable[[str], bool] = lambda slug: False


def _chart_passthrough(chart: Chart) -> dict:
    # Il tema natale è esso stesso il "dato" del servizio: la
    # serializzazione completa avviene nello strato API.
    return {}


CATALOG: list[ServiceDef] = [
    ServiceDef(
        id="tema-natale",
        version=1,
        free=True,
        name_key="serviceNatalChart",
        compute=_chart_passthrough,
        content_slugs=natal_chart.content_slugs,
        required_contents=natal_chart.REQUIRED_CONTENTS,
        paid_contents=natal_chart.is_paid_slug,
    ),
    ServiceDef(
        id="elementi",
        version=1,
        free=True,
        name_key="serviceElements",
        compute=elements.compute,
        content_slugs=elements.content_slugs,
        required_contents=elements.REQUIRED_CONTENTS,
    ),
    ServiceDef(
        id="emisferi",
        version=1,
        free=True,
        name_key="serviceHemispheres",
        compute=hemispheres.compute,
        content_slugs=hemispheres.content_slugs,
        required_contents=hemispheres.REQUIRED_CONTENTS,
    ),
]


def get_service(service_id: str) -> ServiceDef | None:
    for service in CATALOG:
        if service.id == service_id:
            return service
    return None
