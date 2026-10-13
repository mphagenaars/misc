import json, re, time, urllib.parse, urllib.request, os

orgs = json.load(open('/tmp/orgs.json'))
rho = [o for o in orgs if o['typ']=='Huisartsenorganisaties']
regions = json.load(open('/tmp/regions.json'))

UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}

def ddg_search(q):
    url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers=UA)
    try:
        t = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
    except Exception:
        return []
    links = re.findall(r'href="[^"]*uddg=([^&"]+)[^"]*"', t)
    return [urllib.parse.unquote(u) for u in links]

def kvk_from_url(u):
    # companyinfo: ...-<kvk>-<vestiging>
    m = re.search(r'-(\d{8})-\d{6,}', u)
    if m: return m.group(1)
    # creditsafe: nl<kvk>
    m = re.search(r'nl(\d{8})', u)
    if m: return m.group(1)
    return None

def plaats_from_url(u):
    m = re.search(r'companyinfo\.nl/organisatieprofiel/[^/]+/[a-z0-9\-]+-([a-z\-]+)-(\d{8})-\d+', u, re.I)
    if m: return m.group(1).replace('-', ' ').title()
    m = re.search(r'drimble\.nl/bedrijf/([a-z\-]+)/', u)
    if m: return m.group(1).replace('-', ' ').title()
    m = re.search(r'oozo\.nl/bedrijven/([a-z\-]+)/', u)
    if m: return m.group(1).replace('-', ' ').title()
    return None

results = json.load(open('/root/ZK/RHO/raw/kvk_progress.json'))

for o in rho:
    naam = o['naam']
    if results.get(naam, {}).get('kvk'):
        continue
    # Bepaal regio-naam voor context
    regio = ''
    if o['regios'] and o['regios'][0] in regions:
        regio = regions[o['regios'][0]]['naam'].replace('Regio ', '')
    queries = [
        f'"{naam}" site:companyinfo.nl',
        f'"{naam}" huisartsen coöperatie KVK',
        f'"{naam}" {regio} KVK nummer',
    ]
    found = False
    for q in queries:
        urls = ddg_search(q)
        for u in urls[:6]:
            k = kvk_from_url(u)
            if k:
                results[naam] = dict(kvk=k, plaats=plaats_from_url(u), bron=u)
                found = True
                break
        if found: break
        time.sleep(2)
    if not found:
        results[naam] = dict(kvk=None, plaats=None, bron=None)
    json.dump(results, open('/root/ZK/RHO/raw/kvk_progress.json','w'), ensure_ascii=False, indent=1)
    print(naam, '->', results[naam].get('kvk'), results[naam].get('plaats'))
    time.sleep(2.5)

print('KLAAR. Met KVK:', sum(1 for v in results.values() if v.get('kvk')), 'van', len(results))
