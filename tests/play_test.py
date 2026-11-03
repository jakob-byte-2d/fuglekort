"""The Play version (fuglekort.no/app/) and the web version (github.io/fuglekort/): no calls to anything but the app's own
server and Supabase, the fonts from the app's own folder, the manifest and the scope of the service worker, and
profil.appversjon. Supabase is a small stand-in, so nothing leaves the machine.

Run from the repo (after python3 build.py and python3 build.py --play ../fuglekort_nettside/app):
    python3 tests/play_test.py ../fuglekort_nettside
The website folder is served at the root, as fuglekort.no is (the app under /app/); docs/ is served as the web version.
"""
import asyncio, json, subprocess, sys, time, uuid, pathlib
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent
NETTSIDE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROT.parent / 'fuglekort_nettside').resolve()
SUPA = 'qfustbltxgbpwsntcrpd.supabase.co'
FEIL = []


def sjekk(navn, ok, info=''):
    print(('  OK   ' if ok else '  FEIL ') + navn + (f'  ({info})' if not ok and info != '' else ''))
    if not ok: FEIL.append(navn)


class Supa:
    """just enough of Supabase for the app to sign up, send its row and profile, and fetch the boards"""
    def __init__(self):
        self.profil, self.tok = [], {}

    async def handle(self, route):
        req = route.request; u = urlparse(req.url); m = req.method
        h = {'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*',
             'access-control-expose-headers': 'content-range', 'content-type': 'application/json'}
        if m == 'OPTIONS': return await route.fulfill(status=204, headers=h)
        svar = lambda st, b=None, ekstra=None: route.fulfill(status=st, headers={**h, **(ekstra or {})}, body='' if b is None else json.dumps(b))
        body = json.loads(req.post_data) if req.post_data else None
        if u.path in ('/auth/v1/signup', '/auth/v1/token'):
            uid = str(uuid.uuid4()); a = 'tok-' + uid[:8]; self.tok[a] = uid
            return await svar(200, {'access_token': a, 'refresh_token': 'ref-' + uid[:8], 'expires_in': 3600, 'expires_at': int(time.time()) + 3600, 'user': {'id': uid}})
        fn = u.path.rsplit('/', 1)[-1]
        if u.path.startswith('/rest/v1/rpc/'):
            return await svar(200, {'navn_status': 'ledig', 'mine_grupper': [], 'gruppe_fra_kode': None, 'profil_arter': None}.get(fn,
                              {'periode': None, 'fra': None, 'til': None, 'antall': 0, 'plass': None, 'meg': None, 'rader': [], 'premier': [2000, 1000, 500], 'forrige': []}))
        if m == 'GET': return await svar(200, [], {'content-range': '*/0'})
        if fn == 'profil' and body: self.profil += body
        return await svar(201 if m == 'POST' else 204)


def server(mappe, port):
    return subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=mappe, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def kjor(b, navn, url, egen, play):
    print(f'=== {navn}: {url}')
    sb = Supa(); kall, feilsvar = [], []
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True, is_mobile=True, service_workers='allow')
    await ctx.route(f'https://{SUPA}/**', sb.handle)
    ctx.on('request', lambda r: kall.append(r.url))
    ctx.on('response', lambda r: feilsvar.append((r.status, r.url)) if r.status >= 400 and urlparse(r.url).netloc == egen else None)
    await ctx.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear();"
                              "localStorage.setItem('fuglekort:intro', 'ferdig'); localStorage.setItem('hagefugler-oslo:hint', 'ok');"
                              "localStorage.setItem('fuglekort:deling', 'ja'); localStorage.setItem('fuglekort:kallenavn', JSON.stringify({navn: 'Test Meis 1', forslag: false})); }")
    pg = await ctx.new_page(); js = []; pg.on('pageerror', lambda e: js.append(str(e)))
    await pg.goto(url, wait_until='networkidle'); await pg.wait_for_timeout(1500)
    lukk = "for (const id of ['#fest', '#bfest']) { const e = document.querySelector(id); if (e && e.classList.contains('on')) e.click(); } const v = document.querySelector('#festVent'); if (v && !v.hidden) v.click();"
    async def trykk(sel, ms=400):                       # a click in the page itself: a celebration in front does not stop it
        await pg.evaluate(lukk)
        await pg.evaluate(f"(() => {{ const e = document.querySelector({json.dumps(sel)}); if (e) e.click(); }})()"); await pg.wait_for_timeout(ms)

    # register a bird: the row on the board and the profile are sent
    box = await pg.locator('.card.is-top [data-act="toggle"]').bounding_box()
    await pg.touchscreen.tap(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    for _ in range(40):
        await pg.evaluate(lukk); await pg.wait_for_timeout(250)
        if sb.profil: break
    versjon = sb.profil[-1].get('appversjon') if sb.profil else None; print('    appversjon', versjon)
    sjekk('profil.appversjon', bool(versjon) and (versjon.startswith('play-1.0.0-') if play else not versjon.startswith('play-')) and len(versjon) <= 40, versjon)

    # the board, the favourites and a group, the picture sets and the big picture, Innstillinger
    await pg.evaluate(lukk); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
    await trykk('#openStats')
    for fane in ('#fane-statistikk', '#fane-kort', '#fane-merker', '#fane-tavle'): await trykk(fane, 500)
    await trykk('[data-tavlehvem="fav"]'); await trykk('[data-tavlehvem="alle"]')
    await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
    await trykk('#openMeny', 200); await trykk('#openSettings')
    for sett in ('tegneserie', 'ki', 'foto'): await trykk(f'[data-bilder="{sett}"]', 500)
    sjekk('lenken til personvernerklæringen', await pg.get_attribute('#delingSek a[href*="personvern"]', 'href') == 'https://fuglekort.no/personvern/')
    await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300); await pg.evaluate(lukk)
    r = await pg.evaluate("(() => { const r = document.querySelector('.card.is-top .front').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
    await pg.touchscreen.tap(r[0] + r[2] * .5, r[1] + r[3] * .35); await pg.wait_for_timeout(700)
    await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)

    # the fonts, the manifest and the service worker
    lastet = await pg.evaluate("Promise.all(['400 16px \"Familjen Grotesk\"', '700 16px \"Familjen Grotesk\"', '500 16px Caveat', '600 16px Caveat'].map(f => document.fonts.load(f).then(a => a.length))).then(a => a.every(n => n > 0))")
    sjekk('fontene fra appens egen mappe', lastet
          and any(urlparse(k).netloc == egen and '/fonts/familjen-grotesk-latin-' in k for k in kall) and any(urlparse(k).netloc == egen and '/fonts/caveat-latin-500' in k for k in kall))
    man = await pg.evaluate("fetch('manifest.webmanifest').then(r => r.json())")
    if play:
        sjekk('manifest: id, start_url og scope = /app/', man.get('id') == man.get('start_url') == man.get('scope') == '/app/', man)
    else:
        sjekk('manifest som før', man.get('id') == man.get('start_url') == man.get('scope') == './', man)
    scope = await pg.evaluate("navigator.serviceWorker.ready.then(r => r.scope)"); print('    scope', scope)
    sjekk('service worker: scope', scope == (f'http://{egen}/app/' if play else f'http://{egen}/'), scope)
    cache = await pg.evaluate("caches.keys()"); print('    hurtigbuffer', cache)
    sjekk('egen hurtigbuffer', len(cache) == 1 and cache[0].startswith('hagefugler-play-' if play else 'hagefugler-') and (play or not cache[0].startswith('hagefugler-play-')), cache)
    await pg.reload(wait_until='networkidle'); await pg.wait_for_timeout(1500)
    sjekk('virker fra service workeren etter omstart', await pg.evaluate("!!navigator.serviceWorker.controller && !!document.querySelector('.card.is-top')"))

    verter = sorted({urlparse(k).netloc for k in kall if urlparse(k).scheme in ('http', 'https')}); print('    verter', verter)
    sjekk('ingen kall utenom eget nettsted og Supabase', set(verter) <= {egen, SUPA}, verter)
    sjekk('ingen manglende filer', not feilsvar, feilsvar[:5])
    sjekk('ingen JS-feil', not js, js)
    await ctx.close()


async def main():
    s1, s2 = server(ROT / 'docs', 8765), server(NETTSIDE, 8766)
    try:
        time.sleep(1)
        async with async_playwright() as p:
            b = await p.chromium.launch()
            await kjor(b, 'Play-versjonen', 'http://localhost:8766/app/', 'localhost:8766', True)
            await kjor(b, 'Nettversjonen', 'http://localhost:8765/', 'localhost:8765', False)
            await b.close()
    finally:
        s1.terminate(); s2.terminate()
    print('\nFEIL:', FEIL or 'ingen')
    sys.exit(1 if FEIL else 0)

asyncio.run(main())
