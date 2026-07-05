"""Servizio gratuito A — Elementi.

Distribuzione di Fuoco, Terra, Aria e Acqua tra i corpi del tema più
l'Ascendente (11 punti, ogni punto vale 1). Regole, documentate anche in
contenuti/README.md:

- elemento **preponderante**: massimo unico con almeno PREPONDERANCE_MIN
  punti;
- elemento **carente**: minimo unico con al più LACK_MAX punti.

In caso di parità o soglie non raggiunte non viene indicato alcun
preponderante/carente (il tema è considerato equilibrato su quel fronte).
"""

from __future__ import annotations

from app import config
from app.astro.chart import Chart

PREPONDERANCE_MIN = 4
LACK_MAX = 1


def _extreme(counts: dict[str, int], *, largest: bool) -> str | None:
    """Elemento con conteggio massimo (o minimo) se unico e oltre soglia."""
    best = max(counts.values()) if largest else min(counts.values())
    winners = [e for e, c in counts.items() if c == best]
    if len(winners) != 1:
        return None
    if largest and best < PREPONDERANCE_MIN:
        return None
    if not largest and best > LACK_MAX:
        return None
    return winners[0]


def compute(chart: Chart) -> dict:
    points = list(chart.bodies)
    if chart.ascendant is not None:
        points.append(chart.ascendant)

    counts = {element: 0 for element in config.ELEMENTS}
    per_point = {}
    for point in points:
        counts[point.element] += 1
        per_point[point.id] = point.element

    preponderante = _extreme(counts, largest=True)
    carente = _extreme(counts, largest=False)

    return {
        "conteggi": counts,
        "totale_punti": len(points),
        "punti": per_point,
        "preponderante": preponderante,
        "carente": carente,
    }


def content_slugs(data: dict) -> list[str]:
    """Contenuti da allegare al risultato: descrizioni dei 4 elementi più
    i testi specifici per preponderanza/carenza rilevate."""
    slugs = [f"elementi/elemento-{element}" for element in config.ELEMENTS]
    if data["preponderante"]:
        slugs.append(f"elementi/{data['preponderante']}-preponderanza")
    if data["carente"]:
        slugs.append(f"elementi/{data['carente']}-carenza")
    return slugs


# Checklist di copertura: tutti i file che l'autore dei contenuti deve
# scrivere perché il servizio sia completo in una lingua.
REQUIRED_CONTENTS: list[str] = [
    *[f"elementi/elemento-{element}" for element in config.ELEMENTS],
    *[f"elementi/{element}-preponderanza" for element in config.ELEMENTS],
    *[f"elementi/{element}-carenza" for element in config.ELEMENTS],
]
