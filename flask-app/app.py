import csv
import math
import os
from pathlib import Path
from urllib.parse import urlencode

import requests
from flask import Flask, request, render_template, send_from_directory, abort

app = Flask(__name__)

SOLR_URL = os.environ.get("SOLR_URL", "http://localhost:8983/solr/latcore/select")
CONTENT_BASE_URL = os.environ.get(
    "CONTENT_BASE_URL", "http://127.0.0.1:5000/dainas"
).rstrip("/")
DEFAULT_ROWS = int(os.environ.get("ROWS", "50"))
MAX_ROWS = 200
FACET_LIMIT = int(os.environ.get("FACET_LIMIT", "20"))

BASE_DIR = Path(__file__).resolve().parent
STATIC_CONTENT_DIR = BASE_DIR.parent / "static-content"
ARTISAN_DATA_PATH = BASE_DIR / "data" / "latvian_artisan_sourcing.csv"

VOLUME_ROMAN = {
    "latv01": "I",
    "latv02": "II",
    "latv03": "III",
    "latv04": "IV",
    "latv05": "V",
    "latv06": "VI",
    "latv07": "VII",
    "latv08": "VIII",
    "latv09": "IX",
    "latv10": "X",
    "latv11": "XI",
    "latv12": "XII",
}

REGIONS = ["Riga", "Vidzeme", "Kurzeme", "Zemgale", "Latgale"]

KEYWORD_CATEGORY_MAP = {
    "saule": ["Textiles", "Metalwork", "Jewelry"],
    "mēness": ["Metalwork", "Jewelry"],
    "zvaig": ["Metalwork", "Jewelry"],
    "josta": ["Textiles"],
    "lina": ["Textiles"],
    "lin": ["Textiles"],
    "māls": ["Pottery"],
    "keram": ["Pottery"],
    "katls": ["Pottery"],
    "sakta": ["Jewelry"],
    "dzintar": ["Jewelry"],
    "kokle": ["Woodwork"],
    "koks": ["Woodwork"],
    "medus": ["Food"],
    "alus": ["Food"],
    "maize": ["Food"],
}


def _first(value):
    if isinstance(value, list):
        return value[0] if value else ""
    return value if value is not None else ""


def _text(value):
    if isinstance(value, list):
        return " ".join(str(item) for item in value if item is not None)
    return value if value is not None else ""


def _parse_facet_list(items):
    if not items:
        return []
    parsed = []
    it = iter(items)
    for name, count in zip(it, it):
        if count:
            parsed.append((name, count))
    return parsed


def _doc_link(doc):
    volume_id = _first(doc.get("volume_id"))
    parent_id = _first(doc.get("parent_id"))
    fallback_id = _first(doc.get("id"))
    div_id = parent_id or volume_id or fallback_id
    return f"{CONTENT_BASE_URL}/tei.{volume_id}.xml?lang=eng&div_id={div_id}"


def _snippet(text, limit=260):
    text = _text(text)
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _normalize_doc(doc):
    normalized = dict(doc)
    for key in ("id", "volume_id", "parent_head", "parent_id", "lg_head"):
        normalized[key] = _first(doc.get(key))
    normalized["fulltext"] = _text(doc.get("fulltext"))
    return normalized


def _build_params(q, volume_id, page, rows):
    rows = max(1, min(rows, MAX_ROWS))
    page = max(1, page)

    params = {
        "q": q or "*:*",
        "defType": "edismax",
        "qf": "fulltext^2 lg_head parent_head",
        "rows": rows,
        "start": (page - 1) * rows,
        "facet": "true",
        "facet.field": ["volume_id"],
        "facet.limit": FACET_LIMIT,
        "facet.sort": "count",
        "facet.mincount": 1,
        "hl": "true",
        "hl.fl": "fulltext",
        "hl.snippets": 1,
        "hl.fragsize": 160,
        "hl.simple.pre": "<mark>",
        "hl.simple.post": "</mark>",
    }

    if volume_id:
        params["fq"] = [f"volume_id:{volume_id}"]

    return params


def _query_string(base_args, **overrides):
    args = {**base_args, **overrides}
    clean = {k: v for k, v in args.items() if v not in (None, "")}
    return urlencode(clean, doseq=True)


def _apply_highlights(docs, highlight_map):
    for doc in docs:
        doc_id = doc.get("id")
        snippet = None
        if doc_id:
            snippet_list = highlight_map.get(doc_id, {}).get("fulltext")
            if snippet_list:
                snippet = snippet_list[0]
        doc["snippet"] = snippet or _snippet(doc.get("fulltext"))
    return docs


def _parse_region(location):
    location = (location or "").lower()
    for region in REGIONS:
        if region.lower() in location:
            return region
    return ""


def _ships_flag(value):
    value = (value or "").strip().lower()
    return value not in ("", "no", "n")


def _load_artisans(path):
    artisans = []
    if not path.exists():
        return artisans
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            artisan = {
                "name": (row.get("Name") or "").strip(),
                "category": (row.get("Category") or "").strip(),
                "sub_category": (row.get("Sub-Category") or "").strip(),
                "location": (row.get("Location") or "").strip(),
                "website": (row.get("Website") or "").strip(),
                "etsy": (row.get("Etsy") or "").strip(),
                "instagram": (row.get("Instagram") or "").strip(),
                "ships_international": (row.get("Ships Internationally") or "").strip(),
                "notes": (row.get("Notes") or "").strip(),
            }
            artisan["region"] = _parse_region(artisan["location"])
            artisan["ships_flag"] = _ships_flag(artisan["ships_international"])
            artisans.append(artisan)
    return artisans


ARTISANS = _load_artisans(ARTISAN_DATA_PATH)


def _filter_artisans(artisans, query, category, region, shipping):
    query = (query or "").strip().lower()
    category = (category or "").strip()
    region = (region or "").strip()
    shipping = (shipping or "").strip().lower()

    filtered = []
    for artisan in artisans:
        if category and artisan["category"] != category:
            continue
        if region and artisan["region"] != region:
            continue
        if shipping == "yes" and not artisan["ships_flag"]:
            continue

        if query:
            haystack = " ".join(
                [
                    artisan["name"],
                    artisan["category"],
                    artisan["sub_category"],
                    artisan["location"],
                    artisan["notes"],
                ]
            ).lower()
            if query not in haystack:
                continue

        filtered.append(artisan)

    return filtered


def _artisan_facets(artisans):
    categories = sorted({a["category"] for a in artisans if a["category"]})
    regions = sorted({a["region"] for a in artisans if a["region"]})
    return categories, regions


def _suggested_categories(query):
    query = (query or "").lower()
    if not query:
        return []
    found = []
    for key, categories in KEYWORD_CATEGORY_MAP.items():
        if key in query:
            for cat in categories:
                if cat not in found:
                    found.append(cat)
    return found


@app.get("/")
def search():
    q = request.args.get("q", "").strip()
    volume_id = request.args.get("volume_id")

    craft_category = request.args.get("craft_category")
    craft_region = request.args.get("craft_region")
    craft_shipping = request.args.get("craft_shipping")

    try:
        rows = int(request.args.get("rows", DEFAULT_ROWS))
    except ValueError:
        rows = DEFAULT_ROWS
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    rows = max(1, min(rows, MAX_ROWS))
    page = max(1, page)

    params = _build_params(q, volume_id, page, rows)

    error = None
    data = None
    try:
        resp = requests.get(SOLR_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        error = f"Solr request failed: {exc}"

    docs = []
    num_found = 0
    facets = {"volume_id": []}
    if data:
        response = data.get("response", {})
        docs = [_normalize_doc(doc) for doc in response.get("docs", [])]
        num_found = int(response.get("numFound", 0))

        raw_facets = data.get("facet_counts", {}).get("facet_fields", {})
        facets["volume_id"] = _parse_facet_list(raw_facets.get("volume_id"))

        highlight_map = data.get("highlighting", {})
        docs = _apply_highlights(docs, highlight_map)

    artisan_categories, artisan_regions = _artisan_facets(ARTISANS)
    suggested_categories = _suggested_categories(q)
    artisans = _filter_artisans(ARTISANS, q, craft_category, craft_region, craft_shipping)

    total_pages = max(1, int(math.ceil(num_found / float(rows or 1))))

    base_args = {
        "q": q,
        "volume_id": volume_id,
        "rows": rows,
        "craft_category": craft_category,
        "craft_region": craft_region,
        "craft_shipping": craft_shipping,
    }

    return render_template(
        "search.html",
        q=q,
        docs=docs,
        num_found=num_found,
        page=page,
        rows=rows,
        total_pages=total_pages,
        facets=facets,
        base_args=base_args,
        volume_roman=VOLUME_ROMAN,
        doc_link=_doc_link,
        query_string=_query_string,
        error=error,
        artisans=artisans,
        artisan_categories=artisan_categories,
        artisan_regions=artisan_regions,
        craft_category=craft_category,
        craft_region=craft_region,
        craft_shipping=craft_shipping,
        suggested_categories=suggested_categories,
    )


@app.get("/dainas/tei.<volume>.xml")
def serve_tei(volume):
    lang = request.args.get("lang", "eng")
    div_id = request.args.get("div_id")
    if not div_id:
        abort(404)
    filename = f"tei.{volume}.xml?lang={lang}&div_id={div_id}.html"
    file_path = STATIC_CONTENT_DIR / filename
    if not file_path.exists():
        fallback = f"tei.{volume}.xml?lang={lang}&div_id={volume}.html"
        fallback_path = STATIC_CONTENT_DIR / fallback
        if fallback_path.exists():
            filename = fallback
        else:
            abort(404)
    return send_from_directory(STATIC_CONTENT_DIR, filename)


@app.get("/dainas/<path:filename>")
def serve_dainas_file(filename):
    return send_from_directory(STATIC_CONTENT_DIR, filename)


@app.get("/favicon.ico")
def favicon():
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
