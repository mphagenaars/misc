import json, re, urllib.parse, urllib.request

# Laad alle data
orgs = json.load(open('/tmp/orgs.json'))
regions = json.load(open('/tmp/regions.json'))
vws = json.load(open('/root/ZK/RHO/raw/vws_progress.json'))
kvk = json.load(open('/root/ZK/RHO/raw/kvk_progress.json'))
rho = [o for o in orgs if o['typ']=='Huisartsenorganisaties']

# Fix ROHA met de correcte hit
UA = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
BASE = 'https://digimv8.desan.nl/api/ArchiveSearch/GetArchiveSearchResult'
def search(org, year='2025'):
    url = BASE + '?organization=' + urllib.parse.quote(org) + '&town=&year=' + year
    req = urllib.request.Request(url, headers=UA)
    try:
        t = urllib.request.urlopen(req, timeout=15).read().decode('utf-8','ignore')
        return json.loads(t) if t.strip() else []
    except Exception:
        return []

hits = search('ROHA')
roha_entry = {'gevonden': [], 'aantal_hits': len(hits), 'zoekterm': 'ROHA'}
for h in hits:
    if h.get('name') == 'ROHA B.V.':
        docs = h.get('documents', [])
        roha_entry['gevonden'].append({
            'naam_officieel': h.get('name'), 'plaats': h.get('town'),
            'externalOrganizationId': h.get('externalOrganizationId'), 'concernId': h.get('concernId'),
            'documenten': [{'type': d.get('type'), 'bestand': d.get('fileName'), 'id': d.get('id'),
                            'grootte': d.get('fileSize'), 'gepubliceerd': d.get('publishedDate')} for d in docs],
            'heeft_jaarrekening': any(d.get('type') == 'Jaarrekening' for d in docs)})
vws['Regionale Ondersteuning Huisartsen Amsterdam (ROHA)'] = roha_entry
json.dump(vws, open('/root/ZK/RHO/raw/vws_progress.json','w'), ensure_ascii=False, indent=1)

# Vals-positief-zoektermen: generieke termen die willekeurige zorgaanbieders opleveren
GENERIC = {'Amsterdam', 'Regio Zutphen', 'West-Friesland'}

def clean_hits(entry):
    """Filter hits: alleen behouden als de officiële naam duidelijk bij de RHO hoort."""
    zt = entry.get('zoekterm')
    out = []
    for g in entry['gevonden']:
        naam = g['naam_officieel'] or ''
        # Als de zoekterm generiek was, vertrouw de hit niet tenzij de naam de RHO-naam bevat
        if zt in GENERIC:
            # ROHA-uitzondering is al gefixt; deze entries zijn vals-positief
            continue
        out.append(g)
    return out

resultaat = {'metadata': {
    'bron': 'VWS Jaarverantwoording zorg archief (digimv8.desan.nl), API /api/ArchiveSearch/GetArchiveSearchResult',
    'zoekjaar': '2025',
    'datum_verzameling': '2026-10-12',
    'rho_lijst_bron': 'hechtehuisartsenzorg.nl (initiatief LHV, NHG en InEen), categorie Huisartsenorganisaties',
    'toelichting': 'Voor elke RHO zijn de in het VWS-archief gevonden zorgaanbieders met publicaties over verslagjaar 2025 opgenomen. heeft_jaarrekening geeft aan of bij die zorgaanbieder een document van het type Jaarrekening is gepubliceerd.',
}, 'rho_overzicht': []}

for o in rho:
    naam = o['naam']
    regios = []
    for r in o['regios']:
        if r in regions:
            reg = regions[r]
            zz = reg['zz1'] + ((' + ' + reg['zz2']) if reg.get('zz2') else '')
            regios.append({'code': r, 'naam': reg['naam'], 'preferente_zorgverzekeraar': zz or None})
    entry_vws = vws.get(naam, {'gevonden': [], 'aantal_hits': 0})
    gevonden = clean_hits(entry_vws)
    # Verwijder hits zonder documenten (geen jaarverantwoording)
    gevonden = [g for g in gevonden if g['documenten']]
    heeft_jr = any(g['heeft_jaarrekening'] for g in gevonden)
    resultaat['rho_overzicht'].append({
        'rho_naam': naam,
        'regios': regios,
        'kvk_nummer': kvk.get(naam, {}).get('kvk'),
        'kvk_bron': kvk.get(naam, {}).get('bron'),
        'vws_gevonden': bool(gevonden),
        'vws_zoekterm': entry_vws.get('zoekterm') if entry_vws.get('zoekterm') not in GENERIC else None,
        'vws_zorgaanbieders': gevonden,
        'jaarrekening_2025_aanwezig': heeft_jr,
    })

json.dump(resultaat, open('/root/ZK/RHO/jaarverantwoording_2025.json','w'), ensure_ascii=False, indent=2)
n_gevonden = sum(1 for r in resultaat['rho_overzicht'] if r['vws_gevonden'])
n_jr = sum(1 for r in resultaat['rho_overzicht'] if r['jaarrekening_2025_aanwezig'])
print('RHO total:', len(resultaat['rho_overzicht']))
print('Gevonden in VWS-archief:', n_gevonden)
print('Met jaarrekening 2025:', n_jr)
for r in resultaat['rho_overzicht']:
    if r['vws_gevonden']:
        namen = [g['naam_officieel'] for g in r['vws_zorgaanbieders']]
        print(' -', r['rho_naam'], '->', namen, '| jaarrekening:', r['jaarrekening_2025_aanwezig'])
