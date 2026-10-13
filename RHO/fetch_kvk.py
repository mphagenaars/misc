import json, re, html, time, urllib.parse, urllib.request, os

orgs = json.load(open('/tmp/orgs.json'))
rho = [o for o in orgs if o['typ']=='Huisartsenorganisaties']

UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}

def ddg_search(q):
    url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers=UA)
    try:
        t = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
    except Exception as e:
        return []
    links = re.findall(r'href="[^"]*uddg=([^&"]+)[^"]*"', t)
    return [urllib.parse.unquote(u) for u in links]

def extract_kvk(text):
    # KVK-nummer: 8 cijfers, vaak met 'KVK' ernaast
    m = re.findall(r'KVK[^\d]{0,20}(\d{8})\b', text, re.I)
    if m: return m[0]
    m = re.findall(r'\b(\d{8})\b[^\d]{0,10}(?:KVK|Kamer)', text, re.I)
    if m: return m[0]
    return None

def extract_plaats(text):
    # companyinfo URL bevat plaats: /organisatieprofiel/<branche>/<naam>-<plaats>-<kvk>-<vestigingsnr>
    m = re.search(r'companyinfo\.nl/organisatieprofiel/[^/]+/[a-z0-9-]+-([a-z\-]+)-(\d{8})-\d+', text, re.I)
    if m: return m.group(1).replace('-', ' ').title()
    return None

results = {}
out_path = '/root/ZK/RHO/raw/kvk_progress.json'
if os.path.exists(out_path):
    results = json.load(open(out_path))

for o in rho:
    naam = o['naam']
    if naam in results and results[naam].get('kvk'):
        continue
    q = f'"{naam}" KVK nummer'
    urls = ddg_search(q)
    kvk = None; plaats = None; bron = None
    for u in urls[:8]:
        # Haal de snippet-titel niet op; probeer URL-patroon van companyinfo
        if 'companyinfo.nl' in u:
            p = extract_plaats(u)
            k = re.search(r'-(\d{8})-\d+', u)
            if k:
                kvk = k.group(1); bron = u
                if p: plaats = p
                break
        elif 'creditsafe.com' in u:
            k = re.search(r'nl(\d{8})', u)
            if k:
                kvk = k.group(1); bron = u; break
        elif 'drimble.nl' in u or 'oozo.nl' in u:
            # pagina ophalen en KVK extraheren
            try:
                req = urllib.request.Request(u, headers=UA)
                page = urllib.request.urlopen(req, timeout=25).read().decode('utf-8','ignore')
                k = extract_kvk(page)
                if k:
                    kvk = k; bron = u
                    pm = re.search(r'gevestigd op[^<]{0,80}|([A-Z][a-zA-Z]+(?: aan [A-Z][a-zA-Z]+| aan den [A-Z][a-zA-Z]+)?)', page)
                    break
            except Exception:
                pass
            time.sleep(1)
    results[naam] = dict(kvk=kvk, plaats=plaats, bron=bron)
    json.dump(results, open(out_path,'w'), ensure_ascii=False, indent=1)
    print(naam, '->', kvk, plaats)
    time.sleep(2.5)

print('KLAAR. Met KVK:', sum(1 for v in results.values() if v.get('kvk')), 'van', len(results))
