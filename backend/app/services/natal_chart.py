"""Servizio «Tema natale» — slug dei contenuti interpretativi.

Il calcolo del tema vive nello strato API (il tema è esso stesso il dato
del servizio); qui c'è solo la mappa dei contenuti da allegare per le
pagine di lettura del redesign «Specola»: pianeti nei segni, pianeti
nelle case, Ascendente e Medio Cielo nei segni, aspetti.

I file Markdown si scrivono a lotti: il primo (Sole, Luna e Ascendente
nei dodici segni — i «tre pilastri» del redesign) è in REQUIRED_CONTENTS
e quindi sorvegliato dalla checklist e dalla CI. Per gli slug non ancora
coperti il loader risponde `missing = True` e l'app mostra il segnaposto
«testo in preparazione»; i lotti successivi (altri pianeti nei segni,
case, aspetti) vanno aggiunti qui man mano che i testi esistono.

Schema degli slug (nomi file in italiano, come da contenuti/README.md):

    tema-natale/sole-in-ariete            pianeta nel segno
    tema-natale/sole-in-casa-7            pianeta nella casa
    tema-natale/ascendente-in-vergine     Ascendente nel segno
    tema-natale/medio-cielo-in-gemelli    Medio Cielo nel segno
    tema-natale/sole-trigono-giove        aspetto (id in ordine di calcolo)
"""

from __future__ import annotations

from app import config


def _slug_id(point_id: str) -> str:
    """`medio_cielo` -> `medio-cielo`: negli slug si usano i trattini."""
    return point_id.replace("_", "-")


def content_slugs(data: dict) -> list[str]:
    """Slug per il tema calcolato (`data` è il ChartOut serializzato)."""
    slugs: list[str] = []
    for body in data.get("bodies", []):
        slugs.append(f"tema-natale/{_slug_id(body['id'])}-in-{body['sign']}")
        if body.get("house"):
            slugs.append(
                f"tema-natale/{_slug_id(body['id'])}-in-casa-{body['house']}"
            )
    for angle_key in ("ascendant", "midheaven"):
        angle = data.get(angle_key)
        if angle:
            slugs.append(
                f"tema-natale/{_slug_id(angle['id'])}-in-{angle['sign']}"
            )
    for aspect in data.get("aspects", []):
        slugs.append(
            "tema-natale/"
            f"{_slug_id(aspect['point_a'])}-{aspect['type']}"
            f"-{_slug_id(aspect['point_b'])}"
        )
    return slugs


# Primo lotto editoriale: i tre pilastri nei dodici segni (36 file).
REQUIRED_CONTENTS: list[str] = [
    f"tema-natale/{point}-in-{sign}"
    for point in ("sole", "luna", "ascendente")
    for sign in config.SIGNS
]
