"""Servizio «Tema natale» — slug dei contenuti interpretativi.

Il calcolo del tema vive nello strato API (il tema è esso stesso il dato
del servizio); qui c'è solo la mappa dei contenuti da allegare per le
pagine di lettura del redesign «Specola»: pianeti nei segni, pianeti
nelle case, Ascendente nei segni, aspetti.

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
    tema-natale/sole-trigono-giove        aspetto (id in ordine di calcolo)
    pilastri/sole-ariete-ascendente-toro  il ritratto: Sole + Ascendente

L'ultimo è il testo combinato della scheda «Ritratto» (144 combinazioni
per lingua): vive nella cartella `pilastri/` ma viaggia nella risposta
di questo servizio, così l'app lo riceve con la stessa chiamata del tema.
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
    angle = data.get("ascendant")
    if angle:
        slugs.append(
            f"tema-natale/{_slug_id(angle['id'])}-in-{angle['sign']}"
        )
    # Il ritratto: la lettura combinata di Sole e Ascendente.
    sun = next(
        (body for body in data.get("bodies", []) if body.get("id") == "sole"),
        None,
    )
    if sun and angle:
        slugs.append(f"pilastri/sole-{sun['sign']}-ascendente-{angle['sign']}")
    for aspect in data.get("aspects", []):
        slugs.append(
            "tema-natale/"
            f"{_slug_id(aspect['point_a'])}-{aspect['type']}"
            f"-{_slug_id(aspect['point_b'])}"
        )
    return slugs


# Lotti editoriali già scritti: i tre pilastri nei dodici segni (36
# file), poi tutti i pianeti da Mercurio a Plutone (84). I prossimi
# lotti (Medio Cielo, case, congiunzioni con l'Ascendente) si aggiungono
# qui man mano che i testi esistono.
#
# Tutte le letture dei pianeti nei segni sono gratuite: l'idea di
# metterle dietro lo sblocco unico è stata accantonata (l'eventuale
# pagamento riguarderà servizi complessi futuri, come sinastria e
# oroscopi periodici). L'infrastruttura resta pronta: basta passare
# un predicato a `ServiceDef.paid_contents` e l'app rimette i
# lucchetti, senza aggiornamenti lato client.
# Aspetti che la geometria rende impossibili: Mercurio non si allontana
# dal Sole più di 28° e Venere più di 48°, quindi con il Sole fanno solo
# la congiunzione; fra loro due non superano i 76°, quindi niente oltre
# il sestile. Per queste coppie non si scrive il resto.
_POSSIBLE_ASPECTS: dict[tuple[str, str], tuple[str, ...]] = {
    ("sole", "mercurio"): ("congiunzione",),
    ("sole", "venere"): ("congiunzione",),
    ("mercurio", "venere"): ("congiunzione", "sestile"),
}

_BODY_IDS = [body_id for body_id, _ in config.BODIES]
# Tutte le coppie dei dieci corpi hanno i loro testi (45 coppie).
_ASPECT_PAIRS = [
    (a, b) for i, a in enumerate(_BODY_IDS) for b in _BODY_IDS[i + 1:]
]

REQUIRED_CONTENTS: list[str] = [
    f"tema-natale/{point}-in-{sign}"
    for point in (
        "sole",
        "luna",
        "ascendente",
        "mercurio",
        "venere",
        "marte",
        "giove",
        "saturno",
        "urano",
        "nettuno",
        "plutone",
    )
    for sign in config.SIGNS
] + [
    # Il ritratto: Sole × Ascendente, 144 combinazioni per lingua.
    f"pilastri/sole-{sun}-ascendente-{asc}"
    for sun in config.SIGNS
    for asc in config.SIGNS
] + [
    # Gli aspetti fra i dieci corpi. La coppia
    # segue l'ordine di config.BODIES, come nel calcolo.
    f"tema-natale/{a}-{kind}-{b}"
    for a, b in _ASPECT_PAIRS
    for kind in _POSSIBLE_ASPECTS.get((a, b), config.ASPECTS)
]
