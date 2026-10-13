import json, re, time, urllib.parse, urllib.request, os

orgs = json.load(open('/tmp/orgs.json'))
rho = [o for o in orgs if o['typ']=='Huisartsenorganisaties']

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}

def brave_search(q):
    url = 'https://search.brave.com/search?q=' + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers=UA)
    try:
        t = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
    except Exception:
        return []
    links = re.findall(r'href="(https?://[^"]+)"', t)
    skip = ('brave.com','bravesoftware','search.brave','linkedin.com','spotify.com','facebook.com','instagram.com','twitter.com','x.com','youtube.com','reddit.com','wikipedia.org','duckduckgo.com','google.com','bing.com','hechtehuisartsenzorg.nl','werkenbij')
    out = []
    for u in links:
        if any(s in u for s in skip): continue
        if u not in out: out.append(u)
    return out

out_path = '/root/ZK/RHO/raw/sites_progress.json'
results = json.load(open(out_path))

for o in rho:
    naam = o['naam']
    if results.get(naam, {}).get('website'):
        continue
    urls = brave_search(f'{naam} huisartsen')
    site = None
    for u in urls[:3]:
        site = u.rstrip('/')
        break
    results[naam] = dict(website=site)
    json.dump(results, open(out_path,'w'), ensure_ascii=False, indent=1)
    print(naam, '->', site, flush=True)
    time.sleep(8)

print('KLAAR:', sum(1 for v in results.values() if v.get('website')), 'van', len(results))
