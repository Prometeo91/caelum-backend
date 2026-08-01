"""Caricamento dei contenuti interpretativi (Markdown).

I contenuti vivono in `contenuti/<lingua>/<slug>.md` e sono scritti a mano
(nessuna generazione AI). Il formato di ogni file è documentato in
`contenuti/README.md`:

    # Titolo del contenuto

    Corpo in Markdown...

    ---

    **Titolo breve** (card): Titolo per le card dell'app

    **Teaser** (card): Sottotitolo/anteprima per le card

Se un contenuto manca nella lingua richiesta si ripiega su
`config.DEFAULT_LANG`; se manca anche lì il servizio non fallisce:
restituisce un segnaposto con `missing = True` e l'app mostra comunque
i dati calcolati.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app import config

_CARD_FIELD = re.compile(
    r"^\*\*(?P<key>Titolo breve|Short title|Título breve|Teaser)\*\*"
    r"\s*\(card\)\s*:\s*(?P<value>.+)$"
)

# Il marcatore del titolo card si scrive nella lingua del file: senza
# questa equivalenza un file inglese o spagnolo perderebbe il titolo in
# silenzio, senza che nulla fallisca. Aggiungendo una lingua va aggiunta
# qui la sua traduzione. («Teaser» resta invariato nelle tre lingue.)
_CARD_TITLE_KEYS = {"Titolo breve", "Short title", "Título breve"}


@dataclass
class Content:
    slug: str
    lang: str
    missing: bool = False
    title: str | None = None
    body: str = ""  # Markdown, senza titolo né metadati card
    card_title: str | None = None
    teaser: str | None = None
    # Impostato dalle rotte secondo il catalogo (ServiceDef.paid_contents):
    # l'app mostra chiusi i contenuti a pagamento non acquistati.
    paid: bool = False


@dataclass
class ContentBundle:
    """Contenuti richiesti da un servizio, con eventuali segnaposto."""

    items: list[Content] = field(default_factory=list)

    def as_dict_list(self) -> list[dict]:
        return [vars(item) for item in self.items]


def content_path(slug: str, lang: str = config.DEFAULT_LANG):
    return config.CONTENT_DIR / lang / f"{slug}.md"


def parse_markdown(slug: str, lang: str, text: str) -> Content:
    title: str | None = None
    card_title: str | None = None
    teaser: str | None = None
    body_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        match = _CARD_FIELD.match(stripped)
        if match:
            if match.group("key") in _CARD_TITLE_KEYS:
                card_title = match.group("value").strip()
            else:
                teaser = match.group("value").strip()
            continue
        if title is None and stripped.startswith("# "):
            title = stripped[2:].strip()
            continue
        body_lines.append(line)

    body = "\n".join(body_lines).strip()
    # Rimuove l'eventuale separatore finale che precedeva i metadati card.
    if body.endswith("---"):
        body = body[:-3].rstrip()

    return Content(
        slug=slug, lang=lang, title=title, body=body,
        card_title=card_title, teaser=teaser,
    )


def load_content(slug: str, lang: str = config.DEFAULT_LANG) -> Content:
    path = content_path(slug, lang)
    if not path.is_file() and lang != config.DEFAULT_LANG:
        # Finché una lingua non è tradotta serviamo la lingua di
        # riferimento: meglio un testo in italiano che nessun testo.
        lang = config.DEFAULT_LANG
        path = content_path(slug, lang)
    if not path.is_file():
        return Content(slug=slug, lang=lang, missing=True)
    return parse_markdown(slug, lang, path.read_text(encoding="utf-8"))


def load_bundle(slugs: list[str], lang: str = config.DEFAULT_LANG) -> ContentBundle:
    return ContentBundle(items=[load_content(slug, lang) for slug in slugs])
