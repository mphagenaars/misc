#!/usr/bin/env python3
"""Converteer de Maasstad Ziekenhuis jaarrekening-PDF naar markdown."""
import re
from pypdf import PdfReader

SRC = "pdf/maasstad_jaarrekening_2025.pdf"
DST = "maasstad_jaarrekening_2025.md"

# Grote sectiegrenzen in het document (pagina-index 0-based) met titel
SECTIES = [
    (0, "Voorpagina"),
    (2, "Bestuursverslag"),
    (30, "Verslag interne toezichthouder"),
    (35, "Jaarrekening"),
    (84, "Controleverklaring van de onafhankelijke accountant"),
]

def clean_line(l: str) -> str:
    l = l.replace("\uf0b7", "-").replace("\uf0a7", "-").replace("\uf0fc", "v")
    l = l.replace("\uf0d8", ">").replace("\uf0e0", ">").replace("\uf0a8", "*")
    return l

def main() -> None:
    r = PdfReader(SRC)
    out = []
    out.append("# Jaarstukken 2025 — Stichting Maasstad Ziekenhuis\n")
    out.append("> Bron: VWS Jaarverantwoording zorg archief (digimv8.desan.nl),")
    out.append("> document-id 97458, verslagjaar 2025, gepubliceerd 2026-05-28.")
    out.append("> Bevat: bestuursverslag, verslag interne toezichthouder,")
    out.append("> jaarrekening en controleverklaring (Deloitte, 27 mei 2026).\n")

    sectie_grenzen = {p: t for p, t in SECTIES}
    for i, page in enumerate(r.pages):
        if i in sectie_grenzen and i > 0:
            out.append(f"\n---\n\n# {sectie_grenzen[i]}\n")
        text = page.extract_text() or ""
        lines = [clean_line(l).rstrip() for l in text.split("\n")]
        # Paginanummer-regel (eerste regel die alleen een getal is) wegfilteren
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        # Lege regels comprimeren
        body = "\n".join(lines).strip()
        if not body:
            continue
        out.append(body)
        out.append("")  # lege regel na elke pagina

    md = "\n".join(out)
    # Comprimeer 3+ lege regels naar 1
    md = re.sub(r"\n{3,}", "\n\n", md)
    with open(DST, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"OK: {DST} ({len(md):,} tekens, {len(r.pages)} pagina's verwerkt)")

if __name__ == "__main__":
    main()