#!/usr/bin/env python3
"""Zoek jaarverantwoordingsstukken van een zorgaanbieder in het VWS Jaarverantwoording zorg archief.

Gebruik:
    python3 search_vws.py <organisatienaam> [jaar, standaard 2025] [plaats, optioneel]

Voorbeelden:
    python3 search_vws.py "Hadoks" 2025
    python3 search_vws.py "ROHA" 2025
    python3 search_vws.py "PrimaCura" 2025 Tilburg

Zie ../SKILL.md voor valkuilen (naamvarianten, vals-positieven) en de
herontdekmethode als het endpoint wijzigt.
"""
import json
import sys
import urllib.parse
import urllib.request

BASE = "https://digimv8.desan.nl/api/ArchiveSearch/GetArchiveSearchResult"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


def search(organization: str, year: str = "2025", town: str = "") -> list:
    """Geef de ruime zoekresultaten terug als lijst dicts."""
    url = (
        f"{BASE}?organization={urllib.parse.quote(organization)}"
        f"&town={urllib.parse.quote(town)}&year={urllib.parse.quote(year)}"
    )
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", "ignore")
        return json.loads(body) if body.strip() else []
    except Exception as exc:  # noqa: BLE001 - CLI-tool, alles tonen
        print(f"FOUT bij zoeken naar {organization!r}: {exc}", file=sys.stderr)
        return []


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    organization = sys.argv[1]
    year = sys.argv[2] if len(sys.argv) > 2 else "2025"
    town = sys.argv[3] if len(sys.argv) > 3 else ""

    hits = search(organization, year, town)
    if not hits:
        print(f"Geen zorgaanbieders gevonden voor {organization!r} ({year}).")
        print("Tip: probeer officiële naamvarianten (B.V., Coöperatie U.A., Stichting).")
        return 1

    print(f"{len(hits)} zorgaanbieder(s) gevonden voor {organization!r}, jaar {year}:\n")
    for hit in hits:
        docs = hit.get("documents", [])
        heeft_jr = any(d.get("type") == "Jaarrekening" for d in docs)
        print(f"== {hit.get('name')} | {hit.get('town')} | "
              f"extOrgId: {hit.get('externalOrganizationId')} | "
              f"documenten: {len(docs)} | jaarrekening: {'JA' if heeft_jr else 'NEE'}")
        for doc in docs:
            print(f"   - [{doc.get('type')}] {doc.get('fileName')} "
                  f"(id={doc.get('id')}, gepubliceerd: {doc.get('publishedDate')})")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())