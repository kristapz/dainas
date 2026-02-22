# Flask search app

A simple Flask UI that queries the Solr index from this repo and provides
full-text search + volume filters, plus a Latvian artisan sourcing directory.

## Prereqs
- Solr running with the `latcore` core loaded (see repo root `docker-compose.yml`).
- Python 3.8+ recommended. (Your current base Python is 3.6, which will struggle with newer wheels.)

## Run (venv)
```bash
cd /Users/kristapszilgalvis/Desktop/latviandainas
python -m venv .venv
source .venv/bin/activate
pip install -r flask-app/requirements.txt
python flask-app/app.py
```

Then open: http://127.0.0.1:5000

## Run (conda)
```bash
conda create -n dainas python=3.10 -y
conda activate dainas
pip install -r /Users/kristapszilgalvis/Desktop/latviandainas/flask-app/requirements.txt
python /Users/kristapszilgalvis/Desktop/latviandainas/flask-app/app.py
```

## Env vars
- `SOLR_URL` (default: `http://localhost:8983/solr/latcore/select`)
- `CONTENT_BASE_URL` (default: `http://127.0.0.1:5000/dainas`)
- `ROWS` (default: 50)
- `FACET_LIMIT` (default: 20)

By default the app serves the static TEI HTML pages itself under `/dainas/...`.
If you prefer to use the nginx container, set:

```bash
export CONTENT_BASE_URL="http://localhost"
```

Then daina links will point to the nginx server instead.

## Artisan data
The artisan directory is loaded from:
`/Users/kristapszilgalvis/Desktop/latviandainas/flask-app/data/latvian_artisan_sourcing.csv`
