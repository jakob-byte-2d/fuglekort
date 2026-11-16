"""Egne arter i tellingen: arter som ikke er i kortstokken, skrives inn i Telleliste («Legg til en art som ikke er i
kortstokken», eller «Legg til «X»» når søket ikke finner noe), telles med − tall + og kan fjernes med ×. Et navn som er i
kortstokken (eller Ekorn) telles der; samme navn to ganger er én rad; høyst 30. Oppsummeringen viser dem under «Ikke i
skjemaet», tallene og teksten tar dem med, de får ingen observasjonsdag, og de sendes med tellingen (tellinger.egne).
Kjør fra repoet etter python3 build.py:   python3 tests/egne_arter_test.py [MAPPE_FOR_SKJERMBILDER]
"""
import asyncio, json, subprocess, sys, time, uuid, pathlib
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent
BILDER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else None
URL = 'http://localhost:8786/'
SUPA = 'qfustbltxgbpwsntcrpd.supabase.co'
FEIL = []


def sjekk(navn, ok, info=''):
    print(('  OK   ' if ok else '  FEIL ') + navn + (f'  ({info})' if not ok and info != '' else ''))
    if not ok: FEIL.append(navn)


class Supa:
    """nok av Supabase til at tellingene speiles (POST /rest/v1/tellinger)"""
    def __init__(self): self.tellinger = []

    async def handle(self, route):
        req = route.request; u = urlparse(req.url); m = req.method
        h = {'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*', 'access-control-expose-headers': 'content-range', 'content-type': 'application/json'}
        if m == 'OPTIONS': return await route.fulfill(status=204, headers=h)
        svar = lambda st, b=None: route.fulfill(status=st, headers={**h, 'content-range': '*/0'}, body='' if b is None else json.dumps(b))
        if u.path in ('/auth/v1/signup', '/auth/v1/token'):
            uid = str(uuid.uuid4())
            return await svar(200, {'access_token': 'tok', 'refresh_token': 'ref', 'expires_in': 3600, 'expires_at': int(time.time()) + 3600, 'user': {'id': uid}})
        if u.path == '/rest/v1/tellinger' and m == 'POST':
            self.tellinger += json.loads(req.post_data or '[]'); return await svar(201)
        if u.path.startswith('/rest/v1/rpc/'): return await svar(200, {'navn_status': 'ledig'}.get(u.path.rsplit('/', 1)[-1]))
        return await svar(200, []) if m == 'GET' else await svar(201 if m == 'POST' else 204)


def lager(start_ms, **x):
    d = {'hagefugler:testmerke': '2026-09-30-pluss', 'fuglekort:intro': 'ferdig', 'hagefugler-oslo:hint': 'ok', 'fuglekort:deling': 'ja',
         'fuglekort:kallenavn': json.dumps({'navn': 'Test Meis 1', 'forslag': False}), 'fuglekort:tittel:v2': '99', 'hagefugler:varsler-spurt': '1',
         'fuglekort:oppdrag': json.dumps({k: '2026-08-14' for k in ('forste', 'sok', 'arter3', 'tavle', 'dager2', 'kjop', 'arter5', 'dager3', 'telling', 'livsliste')}),
         'hagefugler:tellinger:v1': json.dumps({f't{start_ms}': {'start': start_ms, 'slutt': 0, 'omrade': 'Hagen', 'arter': {}, 'egne': {}, 'ts': start_ms}})}
    d.update(x); return d


async def dlg(pg):
    return await pg.evaluate("""(() => { const d = document.querySelector('#dlg'); return { apen: !d.hidden && d.classList.contains('on'), tittel: d.querySelector('#dlgT').textContent,
      feil: (d.querySelector('#egFeil') || {}).textContent || '', navn: (d.querySelector('#egNavn') || {}).value }; })()""")


async def liste(pg):
    return await pg.evaluate("""(() => ({
      egne: [...document.querySelectorAll('#tliste li[data-egen]')].map(li => [li.dataset.egen, li.querySelector('input').value, li.classList.contains('har')]),
      ny: (document.querySelector('#tliste [data-ny-egen]') || {}).textContent || '', tom: (document.querySelector('#tliste .tl-tom') || {}).textContent || '',
      fokus: document.activeElement && document.activeElement.closest('li') ? (document.activeElement.closest('li').dataset.egen || document.activeElement.closest('li').dataset.k) : null }))()""")


async def sok(pg, t):
    await pg.evaluate(f"(() => {{ const q = document.querySelector('#lq'); q.value = {json.dumps(t)}; q.dispatchEvent(new Event('input', {{bubbles: true}})); }})()"); await pg.wait_for_timeout(250)


async def legg_til(pg, navn, antall, knapp='[data-ny-egen]'):
    await pg.evaluate(f"document.querySelector('#tliste {knapp}').click()"); await pg.wait_for_timeout(300)
    if navn is not None: await pg.fill('#egNavn', navn)
    await pg.fill('#egAntall', str(antall))
    await pg.evaluate("document.querySelector('#dlgKnapper .btn.pri').click()"); await pg.wait_for_timeout(500)


async def main():
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8786', '-d', str(ROT / 'docs')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        async with async_playwright() as pw:
            b = await pw.chromium.launch()
            sb = Supa()
            start = int(time.time() * 1000) - 70 * 60 * 1000
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True, is_mobile=True, service_workers='block', permissions=['clipboard-read', 'clipboard-write'])
            await ctx.route(f'https://{SUPA}/**', sb.handle)
            await ctx.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear();"
                                      + ''.join(f'localStorage.setItem({json.dumps(k)}, {json.dumps(v)});' for k, v in lager(start).items()) + '}')
            pg = await ctx.new_page(); js = []; pg.on('pageerror', lambda e: js.append(str(e)))
            await pg.goto(URL, wait_until='networkidle'); await pg.wait_for_timeout(1500)
            await pg.evaluate("document.querySelector('#tListe').click()"); await pg.wait_for_timeout(500)
            l = await liste(pg)
            sjekk('Telleliste: «Legg til en art som ikke er i kortstokken» nederst', l['ny'] == 'Legg til en art som ikke er i kortstokken' and not l['egne'], l)
            await sok(pg, 'snøspurv')
            l = await liste(pg)
            sjekk('søket finner ingen: «Ingen art i kortstokken passer …» og «Legg til «Snøspurv»»', l['tom'] == 'Ingen art i kortstokken passer til «snøspurv».' and l['ny'] == 'Legg til «Snøspurv»', l)
            if BILDER: await pg.screenshot(path=str(BILDER / 'egne_sok.png'))
            await pg.evaluate("document.querySelector('#tliste [data-ny-egen]').click()"); await pg.wait_for_timeout(300)
            d = await dlg(pg)
            sjekk('vinduet «Art som ikke er i kortstokken» med navnet fylt inn', d['apen'] and d['tittel'] == 'Art som ikke er i kortstokken' and d['navn'] == 'snøspurv', d)
            if BILDER: await pg.screenshot(path=str(BILDER / 'egne_vindu.png'))
            await pg.fill('#egAntall', '12'); await pg.evaluate("document.querySelector('#dlgKnapper .btn.pri').click()"); await pg.wait_for_timeout(500)
            l = await liste(pg)
            sjekk('lagt til: «Snøspurv» øverst med 12, søket tømt, markøren i tallet', l['egne'] == [['Snøspurv', '12', True]] and l['fokus'] == 'Snøspurv'
                  and await pg.evaluate("document.querySelector('#lq').value") == '', l)
            await pg.evaluate("document.querySelector('#tliste li[data-egen] [data-d=\"1\"]').click()"); await pg.wait_for_timeout(250)
            sjekk('+ gir 13', (await liste(pg))['egne'] == [['Snøspurv', '13', True]])
            await pg.evaluate("document.querySelector('#tliste li[data-egen] [data-d=\"-1\"]').click()"); await pg.wait_for_timeout(250)
            await legg_til(pg, 'SNØSPURV', 5)
            sjekk('samme navn igjen (store bokstaver, lavere tall): én rad, 12 står', (await liste(pg))['egne'] == [['Snøspurv', '12', True]], await liste(pg))
            await legg_til(pg, 'kjøttmeis', 4)
            r = await pg.evaluate("[document.querySelector('#lq').value, (document.querySelector('#tliste li[data-k=\"parus-major\"] input') || {}).value, Object.keys(Object.values(JSON.parse(localStorage.getItem('hagefugler:tellinger:v1')))[0].egne)]")
            sjekk('«kjøttmeis» er i kortstokken: telles der (4), ingen egen rad', r == ['Kjøttmeis', '4', ['Snøspurv']], r)
            await sok(pg, '')
            await pg.evaluate("document.querySelector('#tliste [data-ny-egen]').click()"); await pg.wait_for_timeout(300)
            await pg.fill('#egNavn', ' '); await pg.evaluate("document.querySelector('#dlgKnapper .btn.pri').click()"); await pg.wait_for_timeout(300)
            d = await dlg(pg)
            sjekk('tomt navn: «Skriv navnet på arten.», vinduet står', d['apen'] and d['feil'] == 'Skriv navnet på arten.', d)
            await pg.fill('#egNavn', 'fjelljo'); await pg.focus('#egNavn'); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(150)
            await pg.fill('#egAntall', '0'); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(500)
            sjekk('Enter i navnet går til tallet, Enter i tallet legger til: Fjelljo med 0', (await liste(pg))['egne'] == [['Fjelljo', '0', False], ['Snøspurv', '12', True]], await liste(pg))
            await pg.evaluate("[...document.querySelectorAll('#tliste li[data-egen]')].find(li => li.dataset.egen === 'Fjelljo').querySelector('[data-fjern-egen]').click()"); await pg.wait_for_timeout(300)
            sjekk('× fjerner Fjelljo', (await liste(pg))['egne'] == [['Snøspurv', '12', True]])
            await legg_til(pg, 'lappspurv', 2)
            if BILDER:
                await pg.evaluate("document.querySelector('#listeSheet').scrollTop = 0"); await pg.screenshot(path=str(BILDER / 'egne_liste.png'))
            await pg.reload(wait_until='networkidle'); await pg.wait_for_timeout(1200)
            await pg.evaluate("document.querySelector('#tListe').click()"); await pg.wait_for_timeout(500)
            sjekk('etter omstart: de egne artene står', (await liste(pg))['egne'] == [['Lappspurv', '2', True], ['Snøspurv', '12', True]], await liste(pg))
            await pg.evaluate("document.querySelector('#closeListe').click()"); await pg.wait_for_timeout(400)
            # the summary, and ending the count
            await pg.evaluate("document.querySelector('#tSlutt').click()"); await pg.wait_for_timeout(500)
            r = await pg.evaluate("""[[...document.querySelectorAll('#sumBody .skjema:not(.egne) li')].map(li => li.textContent), [...document.querySelectorAll('#sumBody .skjema.egne li')].map(li => li.textContent),
              (document.querySelector('#sumBody .sum-h') || {}).textContent, [...document.querySelectorAll('#sumBody .sum-tall b')].map(x => x.textContent)]""")
            sjekk('oppsummeringen: Kjøttmeis i skjemalista, de egne under «Ikke i skjemaet», 3 arter og 18 individer',
                  r == [['Kjøttmeis4'], ['Lappspurv2', 'Snøspurv12'], 'Ikke i skjemaet', ['3', '18']], r)
            if BILDER: await pg.screenshot(path=str(BILDER / 'egne_sum.png'))
            await pg.evaluate("document.querySelector('#sumAvslutt').click()"); await pg.wait_for_timeout(1200)
            for _ in range(8):
                await pg.evaluate("for (const id of ['#fest', '#bfest']) { const e = document.querySelector(id); if (e && e.classList.contains('on')) e.click(); } const v = document.querySelector('#festVent'); if (v && !v.hidden) v.click();"); await pg.wait_for_timeout(200)
            tl = await pg.evaluate("Object.values(JSON.parse(localStorage.getItem('hagefugler:tellinger:v1')))[0]")
            sett = await pg.evaluate("JSON.parse(localStorage.getItem('hagefugler-oslo:sett:v1') || '{}')")
            sjekk('lagret: egne = Snøspurv 12, Lappspurv 2; kjøttmeis fikk en observasjonsdag, de egne ikke', tl['slutt'] > 0 and tl['egne'] == {'Snøspurv': 12, 'Lappspurv': 2} and 'parus-major' in sett and len(sett) == 1, [tl, list(sett)])
            if not await pg.evaluate("document.querySelector('#sumSheet').classList.contains('on')"):
                await pg.evaluate("document.querySelector('#openMeny').click()"); await pg.wait_for_timeout(300)
                await pg.evaluate("document.querySelector('#openTelling').click()"); await pg.wait_for_timeout(500)
                await pg.evaluate("document.querySelector('#tellBody [data-tid]').click()"); await pg.wait_for_timeout(500)
            await pg.evaluate("document.querySelector('#sumKopier').click()"); await pg.wait_for_timeout(500)
            txt = await pg.evaluate("navigator.clipboard.readText().catch(() => document.querySelector('#sumTekst').value)")
            sjekk('«Kopier som tekst»: «Ikke i skjemaet:» med de egne, og 3 arter, 18 individer', 'Kjøttmeis: 4' in txt and 'Ikke i skjemaet:\nLappspurv: 2\nSnøspurv: 12' in txt and '3 arter, 18 individer' in txt, txt)
            await pg.evaluate("document.querySelector('#closeSum').click()"); await pg.wait_for_timeout(300)
            await pg.evaluate("document.querySelector('#openMeny').click()"); await pg.wait_for_timeout(300)
            await pg.evaluate("document.querySelector('#openTelling').click()"); await pg.wait_for_timeout(500)
            h = await pg.evaluate("(document.querySelector('#tellBody .tl-hist li') || {}).textContent || ''")
            sjekk('Tidligere tellinger: 3 arter', '3 arter' in h, h)
            for _ in range(20):
                if any(r.get('egne') == {'Snøspurv': 12, 'Lappspurv': 2} and r.get('slutt') for r in sb.tellinger): break
                await pg.wait_for_timeout(250)
            sjekk('sendt til Supabase med egne', any(r.get('egne') == {'Snøspurv': 12, 'Lappspurv': 2} and r.get('slutt') for r in sb.tellinger), sb.tellinger[-1:])
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== høyst 30 egne arter')
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block')
            await ctx.route(f'https://{SUPA}/**', lambda r: r.abort())
            tretti = {f'Art {i:02d}': 1 for i in range(30)}
            ls = lager(start, **{'fuglekort:deling': 'nei'}); t = json.loads(ls['hagefugler:tellinger:v1']); list(t.values())[0]['egne'] = tretti; ls['hagefugler:tellinger:v1'] = json.dumps(t)
            await ctx.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear();" + ''.join(f'localStorage.setItem({json.dumps(k)}, {json.dumps(v)});' for k, v in ls.items()) + '}')
            pg = await ctx.new_page(); js = []; pg.on('pageerror', lambda e: js.append(str(e)))
            await pg.goto(URL, wait_until='networkidle'); await pg.wait_for_timeout(1200)
            await pg.evaluate("document.querySelector('#tListe').click()"); await pg.wait_for_timeout(500)
            await legg_til(pg, 'Snøspurv', 3)
            d = await dlg(pg)
            sjekk('den 31.: «Du kan ha høyst 30 egne arter i en telling.»', d['apen'] and d['feil'] == 'Du kan ha høyst 30 egne arter i en telling.', d)
            await pg.evaluate("document.querySelector('#dlgKnapper .btn:last-child').click()"); await pg.wait_for_timeout(300)
            await legg_til(pg, 'art 05', 7)
            sjekk('   et navn som finnes, går fortsatt (Art 05 får 7)', ['Art 05', '7', True] in (await liste(pg))['egne'])
            sjekk('ingen JS-feil', not js, js); await ctx.close()
            await b.close()
    finally:
        srv.terminate()
    print('FEIL: ' + (', '.join(FEIL) if FEIL else 'ingen'))
    sys.exit(1 if FEIL else 0)

asyncio.run(main())
