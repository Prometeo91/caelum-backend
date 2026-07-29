"""Servizio «Tema natale» — slug dei contenuti interpretativi.

Il calcolo del tema vive nello strato API (il tema è esso stesso il dato
del servizio); qui c'è solo la mappa dei contenuti da allegare per le
pagine di lettura del redesign «Specola»: pianeti nei segni, pianeti
nelle case, Ascendente e Medio Cielo nei segni, aspetti.

I file Markdown corrispondenti sono ancora da scrivere: finché mancano
il loader li segna `missing = True` e l'app mostra il segnaposto «testo
in preparazione». Restano fuori da REQUIRED_CONTENTS di proposito: la
checklist (e quindi la CI) segnala i buchi dei testi già promessi, non
un piano editoriale intero. Quando i testi verranno scritti, andranno
aggiunti qui a lotti (es. prima i pianeti nei segni).

Schema degli slug (nomi file in italiano, come da contenuti/README.md):

    tema-natale/sole-in-ariete            pianeta nel segno
    tema-natale/sole-in-casa-7            pianeta nella casa
    tema-natale/ascendente-in-vergine     Ascendente nel segno
    tema-natale/medio-cielo-in-gemelli    Medio Cielo nel segno
    tema-natale/sole-trigono-giove        aspetto (id in ordine di calcolo)
"""

from __future__ import annotations


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


# I testi del tema natale non sono ancora stati scritti (vedi sopra):
# checklist vuota finché il piano editoriale non parte.
REQUIRED_CONTENTS: list[str] = []
