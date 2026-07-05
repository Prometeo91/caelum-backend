from __future__ import annotations

from app import config
from app.content import loader
from app.services import elements
from tests.conftest import requires_contents

SAMPLE = """# Titolo di prova

Primo paragrafo con **grassetto**.

## Sezione

Altro testo.

---

**Titolo breve** (card): Titolo card

**Teaser** (card): Un teaser di prova.
"""


def test_parse_markdown_extracts_fields():
    content = loader.parse_markdown("x/y", "it", SAMPLE)
    assert content.title == "Titolo di prova"
    assert content.card_title == "Titolo card"
    assert content.teaser == "Un teaser di prova."
    assert "Primo paragrafo" in content.body
    assert "Titolo breve" not in content.body
    assert not content.body.endswith("---")
    assert content.missing is False


def test_missing_content_gives_placeholder():
    content = loader.load_content("elementi/non-esiste")
    assert content.missing is True
    assert content.slug == "elementi/non-esiste"
    assert content.body == ""


@requires_contents
def test_real_contents_are_complete_and_parse():
    """Checklist di copertura: i 12 file del servizio elementi esistono
    in italiano e hanno tutti titolo e metadati card."""
    for slug in elements.REQUIRED_CONTENTS:
        content = loader.load_content(slug, lang=config.DEFAULT_LANG)
        assert content.missing is False, f"manca {slug}"
        assert content.title, f"titolo mancante in {slug}"
        assert content.card_title, f"'Titolo breve (card)' mancante in {slug}"
        assert content.teaser, f"'Teaser (card)' mancante in {slug}"
        assert content.body.strip(), f"corpo vuoto in {slug}"
