# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Il progetto è in italiano: commenti, commit e documentazione seguono la
lingua del repository.

## Questo repository è un mirror in sola lettura

**Non sviluppare qui.** Questo repo è una copia pubblicata del backend
di Caelum, il cui sorgente di verità vive in un monorepo privato
insieme all'app Flutter e ai testi interpretativi. Esiste perché
pyswisseph (Swiss Ephemeris) è AGPL-3.0 e impone di pubblicare il
sorgente del servizio in produzione.

Le modifiche fatte qui verrebbero sovrascritte al prossimo
riallineamento: la cartella `backend/` viene ricopiata per intero dal
monorepo. I file alla radice (questo, `README.md`, `LICENSE`,
`.gitignore`, `docs/`) sono invece specifici del mirror e sopravvivono
alle sincronizzazioni.

Per correzioni o segnalazioni: apri una issue, oppure porta la modifica
nel monorepo privato e riallinea il mirror.

## Cosa manca qui, di proposito

- **`contenuti/`** — i testi interpretativi sono dati proprietari, non
  codice, e restano privati. Il backend li legge da una cartella
  esterna indicata da `CONTENUTI_DIR`; se non ci sono, le API
  restituiscono segnaposto con `missing=true` invece di fallire.
- **`backend/ephe/`** — le effemeridi si scaricano con
  `python scripts/download_ephe.py`, non sono committate.

Di conseguenza molti test **si saltano da soli** (marcatori
`requires_contents` e `requires_ephemeris`): non sono rotti e non vanno
"riparati".

## Comandi

```bash
cd backend
pip install -e ".[dev]"
python scripts/download_ephe.py        # effemeridi, una tantum
python -m pytest                       # test (alcuni si saltano, vedi sopra)
python -m pytest tests/test_chart.py -q # un solo file
uvicorn app.main:app --reload          # API su :8000, documentazione su /docs
```

## Architettura

- **`app/config.py`** è l'unica fonte dei valori regolabili (corpi
  calcolati, orbi degli aspetti, sistema di case, percorsi): la logica
  li legge da lì e non li ridefinisce altrove.
- **Catalogo dei servizi** (`app/services/catalog.py`): ogni servizio
  dichiara `compute(chart)`, `content_slugs(data)` e
  `REQUIRED_CONTENTS`. Quest'ultima è la checklist di copertura usata
  dai test e da `scripts/check_contenuti.py`.
- **Contenuti** (`app/content/loader.py`): Markdown in
  `contenuti/<lingua>/<slug>.md`. Gli **slug restano in italiano in
  tutte le lingue** — li genera il codice dagli id di elementi ed
  emisferi. L'italiano è la lingua di riferimento: una lingua non
  ancora tradotta ripiega sull'italiano invece di restituire testo
  vuoto. Marcatori card: `**Titolo breve** (card):` in italiano,
  `**Short title** (card):` in inglese.
- Il parametro `lang` arriva dall'app via query string e segue la
  lingua del dispositivo dell'utente.
- **Nessuna persistenza**: ogni richiesta si elabora in memoria e non
  viene salvato nulla. È una promessa fatta agli utenti nella scheda
  dello store, non un dettaglio implementativo: va preservata.
