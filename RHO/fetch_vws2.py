import json, re, time, urllib.parse, urllib.request, os

orgs = json.load(open('/tmp/orgs.json'))
rho = [o for o in orgs if o['typ']=='Huisartsenorganisaties']

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Accept': 'application/json'}
BASE = 'https://digimv8.desan.nl/api/ArchiveSearch/GetArchiveSearchResult'

def search(org, town='', year='2025'):
    url = BASE + '?organization=' + urllib.parse.quote(org) + '&town=' + urllib.parse.quote(town) + '&year=' + urllib.parse.quote(str(year))
    req = urllib.request.Request(url, headers=UA)
    try:
        t = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
        return json.loads(t) if t.strip() else []
    except Exception:
        return []

def name_variants(naam):
    v = set()
    v.add(naam)
    # Strip haakjes-afkortingen
    base = re.sub(r'\s*\([^)]*\)', '', naam).strip()
    v.add(base)
    # Voeg suffixen toe
    for suf in [' B.V.', ' B.V', ' Coöperatie U.A.', ' U.A.', ' Coöperatie', ' Stichting', ' Vereniging']:
        v.add(base + suf)
    # Zonder 'Huisartsenorganisatie'-prefix
    short = re.sub(r'^(Huisartsenorganisatie|Regionale Huisartsen Organisatie|Regionale Ondersteuning Huisartsen)\s+', '', base)
    v.add(short)
    return [x for x in v if x]

out_path = '/root/ZK/RHO/raw/vws_progress.json'
results = json.load(open(out_path))

for o in rho:
    naam = o['naam']
    if results.get(naam, {}).get('aantal_hits', 0) > 0:
        continue
    found_any = False
    for variant in name_variants(naam):
        hits = search(variant)
        if hits:
            entry = {'gevonden': [], 'aantal_hits': len(hits), 'zoekterm': variant}
            for h in hits:
                docs = h.get('documents', [])
                entry['gevonden'].append({
                    'naam_officieel': h.get('name'),
                    'plaats': h.get('town'),
                    'externalOrganizationId': h.get('externalOrganizationId'),
                    'concernId': h.get('concernId'),
                    'documenten': [
                        {'type': d.get('type'), 'bestand': d.get('fileName'), 'id': d.get('id'),
                         'grootte': d.get('fileSize'), 'gepubliceerd': d.get('publishedDate')}
                        for d in docs
                    ],
                    'heeft_jaarrekening': any(d.get('type') == 'Jaarrekening' for d in docs),
                })
            results[naam] = entry
            found_any = True
            n_docs = sum(len(g['documenten']) for g in entry['gevonden'])
            jr = any(g['heeft_jaarrekening'] for g in entry['gevonden'])
            print(f"{naam} [via '{variant}'] -> hits={len(hits)} docs={n_docs} jaarrekening={jr}", flush=True)
            break
        time.sleep(1)
    if not found_any:
        results[naam]['zoekterm'] = None
    json.dump(results, open(out_path, 'w'), ensure_ascii=False, indent=1)
    time.sleep(1.5)

print('KLAAR ronde 2')
