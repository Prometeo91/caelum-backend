from __future__ import annotations

import pytest

from app import config
from app.astro.ephemeris import REQUIRED_FILES

requires_ephemeris = pytest.mark.skipif(
    any(not (config.EPHE_PATH / f).is_file() for f in REQUIRED_FILES),
    reason=(
        "File effemeridi assenti: eseguire "
        "'python backend/scripts/download_ephe.py' prima dei test"
    ),
)

# I testi interpretativi non sono distribuiti col backend open source:
# i test che verificano la composizione dei contenuti reali si saltano
# se la cartella non c'è (es. nel repo pubblico del solo backend).
requires_contents = pytest.mark.skipif(
    not (config.CONTENT_DIR / config.DEFAULT_LANG).is_dir(),
    reason=f"Contenuti assenti in {config.CONTENT_DIR}",
)
