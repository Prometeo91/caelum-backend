# caelum-backend

Backend di calcolo di **Caelum**, app mobile di astrologia (tema
natale e servizi interpretativi). FastAPI + [Swiss
Ephemeris](https://www.astro.com/swisseph/) via `pyswisseph`.

Questo repository è il **sorgente del servizio in produzione**,
pubblicato in adempimento della licenza **AGPL-3.0** di Swiss
Ephemeris (vedi [LICENSE](LICENSE)). L'app mobile e i testi
interpretativi non fanno parte di quest'opera: comunicano col backend
via API e restano proprietari.

## Cosa fa

- Calcola il tema natale (posizioni dei 10 corpi classici, case
  Placidus, aspetti maggiori) con Swiss Ephemeris.
- Compone i servizi interpretativi (tema natale, elementi, emisferi)
  allegando testi Markdown letti da una cartella `contenuti/`
  esterna (non inclusa qui: i testi sono dati, non codice).
- È **stateless**: nessun dato di nascita viene salvato; ogni
  richiesta è elaborata in memoria.
- Geocoding dei luoghi via [Open-Meteo](https://open-meteo.com/).

## Avvio

```bash
cd backend
pip install -e ".[dev]"
python scripts/download_ephe.py   # scarica i file effemeridi (una tantum)
python -m pytest                  # i test sui contenuti reali si saltano se assenti
uvicorn app.main:app --reload     # API su http://127.0.0.1:8000 (docs su /docs)
```

Variabili d'ambiente: `EPHE_PATH` (cartella effemeridi),
`CONTENUTI_DIR` (cartella dei testi interpretativi), `GEOCODING_URL`.

## Privacy

Il servizio non conserva alcun dato: vedi la
[privacy policy](docs/privacy-policy.md) dell'app Caelum.

## Licenza

[GNU Affero General Public License v3.0](LICENSE) — come richiesto
dall'uso di Swiss Ephemeris (© Astrodienst AG).
