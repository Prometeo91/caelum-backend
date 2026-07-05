#!/usr/bin/env python3
"""Scarica i file effemeridi Swiss Ephemeris (NON vanno committati).

I file coprono gli anni 1800–2399 e pesano ~2 MB in totale:

    sepl_18.se1  pianeti
    semo_18.se1  Luna
    seas_18.se1  asteroidi principali (per usi futuri)

Fonte: https://raw.githubusercontent.com/aloistr/swisseph (repo ufficiale
Astrodienst su GitHub). Destinazione: backend/ephe (o $EPHE_PATH).

⚠️ Licenza Swiss Ephemeris: AGPL oppure licenza commerciale Astrodienst.
Da risolvere prima di un'eventuale pubblicazione a codice chiuso.
"""

from __future__ import annotations

import http.client
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from app.astro.ephemeris import REQUIRED_FILES  # noqa: E402

BASE_URL = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe"
RETRIES = 4


def _download(url: str, target: Path) -> None:
    """Scarica su file temporaneo e rinomina solo a download completo,
    così un'interruzione non lascia mai un file parziale al posto giusto."""
    tmp = target.with_suffix(target.suffix + ".part")
    last_error: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(url) as resp, open(tmp, "wb") as out:
                out.write(resp.read())
            tmp.replace(target)
            return
        except (OSError, http.client.HTTPException) as exc:
            last_error = exc
            wait = 2**attempt
            print(f"  tentativo {attempt} fallito ({exc}); riprovo tra {wait}s")
            time.sleep(wait)
    tmp.unlink(missing_ok=True)
    raise SystemExit(f"download fallito per {url}: {last_error}")


def main() -> int:
    dest = config.EPHE_PATH
    dest.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_FILES:
        target = dest / name
        if target.is_file():
            print(f"già presente: {target}")
            continue
        url = f"{BASE_URL}/{name}"
        print(f"scarico {url} -> {target}")
        _download(url, target)
    print("fatto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
