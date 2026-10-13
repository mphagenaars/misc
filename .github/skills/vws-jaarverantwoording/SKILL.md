---
name: vws-jaarverantwoording
description: 'Zoek jaarverslagen en jaarrekeningen van Nederlandse zorgaanbieders (RHO"s, huisartsenposten, GGZ, etc.) in het VWS Jaarverantwoording zorg archief. Use when: jaarrekening, jaarverslag, jaarverantwoording, accountantsverklaring of bestuursverslag van een zorgaanbieder zoeken; Wzk-verantwoording controleren; digimv.desan.nl of jaarverantwoordingzorg.nl raadplegen.'
argument-hint: '[organisatienaam] [jaar, standaard 2025]'
---

# VWS Jaarverantwoording zorg archief doorzoeken

## Wat en wanneer

Zoek gepubliceerde jaarverantwoordingsstukken (jaarrekening, bestuursverslag,
accountantsverklaring, etc.) van Nederlandse zorgaanbieders in het publieke
archief van VWS Jaarverantwoording zorg. Gebruik dit bij vragen over
jaarverslagen/jaarrekeningen van zorgaanbieders, of bij het controleren of
een aanbieder Wzk-verantwoording heeft gepubliceerd.

## Endpoint (snelstart)

De publieke zoekpagina is een Angular-SPA, maar er is een **open JSON-API,
geen authenticatie nodig**:

```
GET https://digimv8.desan.nl/api/ArchiveSearch/GetArchiveSearchResult
    ?organization=<naam>&town=<plaats>&year=<verslagjaar>
```

- Alle drie de parameters zijn verplicht in de query-string (`town` mag leeg zijn).
- `Accept: application/json` meesturen; een gewone browser-UA werkt.
- Response: JSON-array van zorgaanbieders, elk met `name` (officiële naam),
  `town`, `externalOrganizationId`, `concernId` en `documents[]`.
- Elk document heeft: `type`, `fileName`, `id`, `fileSize`, `publishedDate`.
- Documenten downloaden kan via `GET /api/ArchiveSearch/GetDocument?documentId=<id>&year=<jaar>&...`.

Gebruik het meegeleverde script: [search_vws.py](./scripts/search_vws.py)

```bash
python3 .github/skills/vws-jaarverantwoording/scripts/search_vws.py "Hadoks" 2025
```

## Documenttypes (vaste waarden)

`Jaarrekening`, `Bestuursverslag`, `Accountantsverklaring (controle-,
beoordelings- of samenstellingsverklaring)`, `Verslag interne toezichthouder`,
`Verzameldocument`, `Overig`.

Tip: veel organisaties publiceren één PDF als `Verzameldocument` en
registreren die óók per onderdeel (jaarrekening, bestuursverslag, etc.) —
dezelfde `fileName` met verschillende `type`s en `id`s is normaal.

## Valkuilen ( geleerd uit praktijk )

1. **Zoek op officiële naam, niet op handelsnaam.** Het archief gebruikt
   Handelsregister-namen met rechtsvorm-suffixen (`B.V.`, `Coöperatie U.A.`,
   `Stichting`). Zoek met varianten: exacte naam, naam zonder
   haakjes-afkortingen, met elke rechtsvorm-suffix. Voorbeeld: RHO "ROHA"
   staat er als `ROHA B.V.`.
2. **Generieke zoektermen geven vals-positieven.** Zoekt op "Amsterdam" of
   "West-Friesland" dan krijg je honderden willekeurige zorgaanbieders.
   Filter hits: alleen vertrouwen als de officiële naam duidelijk bij de
   gezochte organisatie hoort.
3. **Hits met 0 documenten bestaan.** Organisatie geregistreerd maar niets
   gepubliceerd voor dat jaar — geen jaarverantwoording dus.
4. **Geen hit betekent niet: geen verplichting.** Veel organisaties publiceren
   onder een holding/andere entiteit, of vallen buiten de publicatieplicht
   (afhankelijk van zorgtype en Wzk-omvang).
5. **Host is versienummer-gedragen** (`digimv8`, `digimv13`, ...) en de
   JS-bundel-hashes wijzigen per deploy. Zie hieronder de herontdekmethode.

## Herontdekmethode (als het endpoint wijzigt)

De site linkt soms naar een nieuwere host (bijv. `digimv13.desan.nl`) die
dezelfde app serveert. Werkt het endpoint niet meer:

1. Haal `https://www.jaarverantwoordingzorg.nl` op en zoek de actuele
   `digimvN.desan.nl`-link.
2. Haal de main-bundle op (naam staat in de HTML als `src="main-*.js"`).
3. Zoek in de main-bundle op `loadChildren` → vind de chunk voor het
   `archive`-pad (bijv. `chunk-KXWP6UVN.js`).
4. Download die chunk en grep op `/api/` → daar staan de endpoint-strings
   (`GetArchiveSearchResult`, `GetDocument`).

## Bewaarde data in deze workspace

- `RHO/jaarverantwoording_2025.json` — definitieve resultaten voor 74 RHO's
  (19 gevonden, 17 met jaarrekening 2025).
- `RHO/raw/vws_progress.json` — ruwe zoekresultaten per RHO.