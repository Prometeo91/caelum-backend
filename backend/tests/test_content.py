from __future__ import annotations

from app import config
from app.content import loader
from app.services import elements, hemispheres, natal_chart
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
def test_untranslated_language_falls_back_to_default():
    """Una lingua senza contenuti serve la lingua di riferimento invece
    di lasciare l'app senza testo."""
    slug = elements.REQUIRED_CONTENTS[0]
    # 'zz' non esiste di proposito: le lingue tradotte vanno servite
    # nella loro lingua, non dalla riserva.
    content = loader.load_content(slug, lang="zz")
    assert content.missing is False
    assert content.lang == config.DEFAULT_LANG
    assert content.body.strip()


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


@requires_contents
def test_translated_contents_are_well_formed():
    """I file presenti in una lingua diversa da quella di riferimento
    devono essere completi come gli originali: la riserva nasconderebbe
    altrimenti una traduzione a metà."""
    required = [
        *elements.REQUIRED_CONTENTS,
        *hemispheres.REQUIRED_CONTENTS,
        *natal_chart.REQUIRED_CONTENTS,
    ]
    for lang_dir in sorted(config.CONTENT_DIR.iterdir()):
        if not lang_dir.is_dir() or lang_dir.name == config.DEFAULT_LANG:
            continue
        lang = lang_dir.name
        for slug in required:
            if not loader.content_path(slug, lang).is_file():
                continue  # traduzione incompleta: interviene la riserva
            content = loader.load_content(slug, lang=lang)
            assert content.lang == lang, f"{lang}/{slug} servito dalla riserva"
            assert content.title, f"titolo mancante in {lang}/{slug}"
            assert content.card_title, f"titolo card mancante in {lang}/{slug}"
            assert content.teaser, f"teaser mancante in {lang}/{slug}"
            assert content.body.strip(), f"corpo vuoto in {lang}/{slug}"
