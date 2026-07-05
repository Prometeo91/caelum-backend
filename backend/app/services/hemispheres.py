"""Servizio gratuito B — Emisferi.

Distribuzione dei dieci corpi classici nei quattro emisferi del tema.
L'Ascendente e il Medio Cielo definiscono gli assi e non vengono
conteggiati. Regole, documentate anche in contenuti/README.md:

- asse dell'orizzonte (Ascendente–Discendente): emisfero **superiore** =
  case 7–12, emisfero **inferiore** = case 1–6;
- asse del meridiano (Medio Cielo–Fondo Cielo): emisfero **orientale** =
  case 10, 11, 12, 1, 2, 3, emisfero **occidentale** = case 4–9;
- su ciascun asse viene segnalata una concentrazione quando almeno
  CONCENTRATION_MIN corpi cadono nello stesso emisfero.
"""

from __future__ import annotations

from app.astro.chart import Chart

CONCENTRATION_MIN = 7

VERTICAL = ("superiore", "inferiore")
HORIZONTAL = ("orientale", "occidentale")
HEMISPHERES: list[str] = [*VERTICAL, *HORIZONTAL]

SUPERIOR_HOUSES = frozenset(range(7, 13))
EASTERN_HOUSES = frozenset({10, 11, 12, 1, 2, 3})


def _concentration(counts: dict[str, int], pair: tuple[str, str]) -> str | None:
    """Emisfero della coppia con almeno CONCENTRATION_MIN corpi, se c'è."""
    for hemisphere in pair:
        if counts[hemisphere] >= CONCENTRATION_MIN:
            return hemisphere
    return None


def compute(chart: Chart) -> dict:
    bodies = [p for p in chart.bodies if p.house is not None]

    counts = {hemisphere: 0 for hemisphere in HEMISPHERES}
    per_point = {}
    for point in bodies:
        vertical = "superiore" if point.house in SUPERIOR_HOUSES else "inferiore"
        horizontal = "orientale" if point.house in EASTERN_HOUSES else "occidentale"
        counts[vertical] += 1
        counts[horizontal] += 1
        per_point[point.id] = {"verticale": vertical, "orizzontale": horizontal}

    return {
        "conteggi": counts,
        "totale_punti": len(bodies),
        "punti": per_point,
        "verticale": _concentration(counts, VERTICAL),
        "orizzontale": _concentration(counts, HORIZONTAL),
    }


def content_slugs(data: dict) -> list[str]:
    """Contenuti da allegare: solo i testi delle concentrazioni rilevate."""
    slugs = []
    if data["verticale"]:
        slugs.append(f"emisferi/emisfero-{data['verticale']}")
    if data["orizzontale"]:
        slugs.append(f"emisferi/emisfero-{data['orizzontale']}")
    return slugs


# Checklist di copertura: tutti i file che l'autore dei contenuti deve
# scrivere perché il servizio sia completo in una lingua.
REQUIRED_CONTENTS: list[str] = [
    f"emisferi/emisfero-{hemisphere}" for hemisphere in HEMISPHERES
]
