#!/usr/bin/env python3
"""
Alternance Industrie - fetch_offres.py

Interroge l'API publique "La Bonne Alternance" (api.apprentissage.beta.gouv.fr)
pour chaque secteur défini dans sectors.yaml, dédoublonne les résultats et
maintient une archive JSON consommée par le site statique (docs/data/offres.json).

Variables d'environnement attendues :
    LBA_API_TOKEN   - jeton Bearer personnel (obligatoire)
    DEBUG_LBA       - si défini (n'importe quelle valeur), affiche la structure
                      brute de la première réponse de chaque secteur (diagnostic)
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parent.parent
SECTORS_FILE = ROOT / "sectors.yaml"
ARCHIVE_FILE = ROOT / "docs" / "data" / "offres.json"

API_BASE = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"
PAUSE_BETWEEN_CALLS = 1.1  # secondes - limite API : 60 appels/minute
REQUEST_TIMEOUT = 30

DEBUG = bool(os.environ.get("DEBUG_LBA"))


def log(*args):
    print(*args, file=sys.stderr, flush=True)


def load_sectors():
    with open(SECTORS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["sectors"]


def load_archive():
    if ARCHIVE_FILE.exists():
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"generated_at": None, "offres": []}


def save_archive(archive):
    ARCHIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)


def _as_date_string(value):
    """La Bonne Alternance renvoie parfois une date sous forme de dict
    (ex: {"$date": "..."}) plutôt qu'une chaîne simple. On normalise ici."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("$date", "value", "date"):
            if key in value:
                return _as_date_string(value[key])
        return None
    return str(value)


def fetch_sector(token, sector):
    romes = ",".join(sector["romes"])
    url = f"{API_BASE}?romes={romes}"
    req = Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        log(f"  [erreur HTTP {e.code}] secteur {sector['id']} : {e.reason}")
        return []
    except URLError as e:
        log(f"  [erreur réseau] secteur {sector['id']} : {e.reason}")
        return []

    if DEBUG:
        log(f"  [debug] clés racine : {list(payload.keys())}")
        jobs_preview = payload.get("jobs", [])[:1]
        if jobs_preview:
            log(f"  [debug] exemple d'offre brute : {json.dumps(jobs_preview[0], ensure_ascii=False)[:800]}")

    jobs = payload.get("jobs", []) or []
    results = []
    for job in jobs:
        identifier = job.get("identifier", {}) or {}
        offer = job.get("offer", {}) or {}
        workplace = job.get("workplace", {}) or {}
        contract = job.get("contract", {}) or {}
        apply_block = job.get("apply", {}) or {}

        offer_id = identifier.get("id")
        if not offer_id:
            continue

        location = workplace.get("location", {}) or {}

        apply_url = (
            apply_block.get("url")
            or offer.get("url")
            or workplace.get("url")
            or None
        )

        results.append({
            "id": offer_id,
            "partner_label": identifier.get("partner_label"),
            "title": offer.get("title") or "Intitulé non précisé",
            "description": offer.get("description") or "",
            "target_diploma": offer.get("target_diploma"),
            "rome_codes": offer.get("rome_codes") or sector["romes"],
            "created_at": _as_date_string(offer.get("creation")),
            "company_name": workplace.get("name") or workplace.get("legal_name") or workplace.get("brand"),
            "address": location.get("address"),
            "contract_type": contract.get("type"),
            "contract_start": _as_date_string(contract.get("start")),
            "apply_url": apply_url,
            "sector_id": sector["id"],
            "sector_label": sector["label"],
        })

    return results


def merge_archive(archive, new_offers):
    existing_by_id = {o["id"]: o for o in archive["offres"]}
    for offer in new_offers:
        existing_by_id[offer["id"]] = offer

    merged = list(existing_by_id.values())

    def sort_key(o):
        d = o.get("created_at") or ""
        return d

    merged.sort(key=sort_key, reverse=True)
    archive["offres"] = merged
    archive["generated_at"] = datetime.now(timezone.utc).isoformat()
    return archive


def main():
    token = os.environ.get("LBA_API_TOKEN")
    if not token:
        log("Erreur : la variable d'environnement LBA_API_TOKEN n'est pas définie.")
        sys.exit(1)

    sectors = load_sectors()
    archive = load_archive()

    total_new = 0
    for i, sector in enumerate(sectors):
        log(f"Secteur {sector['id']} ({sector['label']}) - codes ROME : {', '.join(sector['romes'])}")
        offers = fetch_sector(token, sector)
        log(f"  -> {len(offers)} offre(s) récupérée(s)")
        total_new += len(offers)
        archive = merge_archive(archive, offers)

        if i < len(sectors) - 1:
            time.sleep(PAUSE_BETWEEN_CALLS)

    save_archive(archive)
    log(f"Terminé. {total_new} offre(s) traitée(s) sur {len(sectors)} secteur(s). "
        f"Archive : {len(archive['offres'])} offre(s) au total.")


if __name__ == "__main__":
    main()
