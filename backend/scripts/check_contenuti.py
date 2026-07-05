#!/usr/bin/env python3
"""Checklist di copertura dei contenuti.

Confronta i file Markdown presenti in `contenuti/<lingua>/` con quelli
richiesti dai servizi del catalogo ed elenca i mancanti. Esce con codice 1
se mancano contenuti nella lingua di riferimento (italiano), così la CI
segnala i buchi di copertura.

Uso:
    python backend/scripts/check_contenuti.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from app.content.loader import content_path  # noqa: E402
from app.services.catalog import CATALOG  # noqa: E402


def languages() -> list[str]:
    if not config.CONTENT_DIR.is_dir():
        return [config.DEFAULT_LANG]
    langs = sorted(p.name for p in config.CONTENT_DIR.iterdir() if p.is_dir())
    return langs or [config.DEFAULT_LANG]


def main() -> int:
    missing_reference = 0
    for lang in languages():
        print(f"\n=== Lingua: {lang} ===")
        for service in CATALOG:
            if not service.required_contents:
                continue
            print(f"servizio '{service.id}':")
            for slug in service.required_contents:
                path = content_path(slug, lang)
                if path.is_file():
                    print(f"  [ok]       {slug}")
                else:
                    print(f"  [MANCANTE] {slug}  ->  {path}")
                    if lang == config.DEFAULT_LANG:
                        missing_reference += 1
    if missing_reference:
        print(
            f"\n{missing_reference} contenuti mancanti nella lingua di "
            f"riferimento ({config.DEFAULT_LANG})."
        )
        return 1
    print("\nCopertura completa nella lingua di riferimento.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
