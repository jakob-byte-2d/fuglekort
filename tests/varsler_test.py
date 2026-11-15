"""Varsler (push) in the app: on from the start, each can be turned off. The first time the phone is asked on «Kom i
gang»; users who already have the app get a window once («Slå på» / «Ikke nå»); with a yes already (Android before 13)
the address goes to Supabase at start without a question. Innstillinger → Varsler: two switches (Hagefugltellingen,
Premier du vinner; the second hidden in the simple version), a note when blocked or not supported, «Send et
testvarsel». What goes to Supabase (varsel_lagre, varsel_slett, send_testvarsel) and when; …/?vis=telling and a
message from the service worker open the right tab; the service worker shows a push (Chrome DevTools).

The browser's push service and the question are stand-ins (no network here); Supabase is stood in for.
Run from the repo after python3 build.py:
    python3 tests/varsler_test.py [MAPPE_FOR_SKJERMBILDER]
"""
import asyncio, json, subprocess, sys, pathlib
from playwright.async_api import async_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent
BILDER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else None
URL = 'http://localhost:8797/'
FEIL = []
NOKKEL = 'BOH6l3hpTVvx3D7c5GJvYqA8YWFIZm1t1wHdFGrJNA8l_5jYWFqtiP7zPzM5gDuKz-JZ8XYNgAJ3KF3lM8lWUo4'   # 65 bytes, any


def sjekk(navn, ok, info=''):
    print(('  OK   ' if ok else '  FEIL ') + navn + (f'  ({info})' if not ok and info != '' else ''))
    if not ok: FEIL.append(navn)


# the browser's push service and the question: stand-ins that remember across reloads (localStorage «__test:*»)
STANDIN = r"""
(() => {
  const L = (k, v) => (v === undefined ? localStorage.getItem('__test:' + k) : localStorage.setItem('__test:' + k, v));
  const perm = () => L('perm') || 'default';
  Object.defineProperty(Notification, 'permission', { get: perm, configurable: true });
  Notification.requestPermission = () => { L('spurt', String(+(L('spurt') || 0) + 1)); L('perm', L('svar') || 'granted'); return Promise.resolve(perm()); };
  const lag = key => ({ endpoint: 'https://fcm.googleapis.com/fcm/send/test-' + (L('nr') || '1'), options: { applicationServerKey: key },
    toJSON() { return { endpoint: this.endpoint, keys: { p256dh: 'BPp256dh-test', auth: 'auth-test' } }; },
    unsubscribe() { L('sub', ''); L('avmeldt', String(+(L('avmeldt') || 0) + 1)); return Promise.resolve(true); } });
  const pm = {
    getSubscription: () => Promise.resolve(L('sub') ? lag(Uint8Array.from(JSON.parse(L('sub'))).buffer) : null),
    subscribe: o => { const k = new Uint8Array(o.applicationServerKey); L('sub', JSON.stringify([...k])); L('abonnert', String(+(L('abonnert') || 0) + 1)); return Promise.resolve(lag(k.buffer)); },
  };
  Object.defineProperty(ServiceWorkerContainer.prototype, 'ready', { get: () => Promise.resolve({ pushManager: pm }), configurable: true });
})();
"""


async def side(b, lager, rpc, url=URL, enkel=False):
    ctx = await b.new_context(viewport={'width': 390, 'height': 800}, device_scale_factor=2, has_touch=True, is_mobile=True, service_workers='block')
    async def supa(route):
        r = route.request
        fn = r.url.split('/rest/v1/rpc/')[1].split('?')[0] if '/rest/v1/rpc/' in r.url else None
        if fn and fn.startswith('varsel') or fn == 'send_testvarsel':
            rpc.append((fn, json.loads(r.post_data or '{}')))
            svar = {'varsel_nokkel': json.dumps(NOKKEL), 'send_testvarsel': 'true'}.get(fn, '')
            await route.fulfill(status=200 if svar else 204, body=svar, headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'})
        else:
            await route.abort()
    await ctx.route('https://qfustbltxgbpwsntcrpd.supabase.co/**', supa)
    await ctx.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear();"
                              + ''.join(f'localStorage.setItem({json.dumps(k)}, {json.dumps(v)});' for k, v in lager.items()) + '}')
    await ctx.add_init_script(STANDIN)
    pg = await ctx.new_page(); js = []; pg.on('pageerror', lambda e: js.append(str(e)))
    await pg.goto(url, wait_until='networkidle'); await pg.wait_for_timeout(1200)
    return ctx, pg, js


def bruker(**x):
    d = {'hagefugler:testmerke': '2026-09-30-pluss', 'fuglekort:intro': 'ferdig', 'hagefugler-oslo:hint': 'ok', 'fuglekort:deling': 'nei', 'fuglekort:tittel:v2': '99'}
    d.update(x); return d


async def dlg(pg):
    return await pg.evaluate("document.querySelector('.dlg.on') ? [document.querySelector('#dlgT').textContent, document.querySelector('#dlgTekst').textContent] : null")


async def innst(pg):
    await pg.evaluate("document.querySelector('#menuBtn') && document.querySelector('#menuBtn').click()"); await pg.wait_for_timeout(300)
    await pg.evaluate("document.querySelector('#openSettings').click()"); await pg.wait_for_timeout(700)
    return await pg.evaluate("""[document.querySelector('#varselTelling').getAttribute('aria-checked'), document.querySelector('#varselPremie').getAttribute('aria-checked'),
        document.querySelector('#varselPremie').hidden, document.querySelector('#varselTelling').disabled, document.querySelector('#varselStatus').textContent, document.querySelector('#varselTest').hidden]""")


async def main():
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8797', '-d', str(ROT / 'docs')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        async with async_playwright() as pw:
            b = await pw.chromium.launch()

            print('=== første gang: telefonen spør på «Kom i gang»')
            rpc = []
            ctx, pg, js = await side(b, {'hagefugler:testmerke': '2026-09-30-pluss'}, rpc)
            for _ in range(20):
                d = await dlg(pg)
                if d and d[0] == 'Ikke dele?':
                    await pg.evaluate("document.querySelector('#dlgKnapper .btn.pri').click()"); await pg.wait_for_timeout(700); continue
                if d: break
                ikke = await pg.evaluate("(() => { const b = document.querySelector('#inIkke'); return !!b && !b.hidden && b.getBoundingClientRect().width > 0; })()")
                sjekk_for = await pg.evaluate("localStorage.getItem('__test:spurt')")
                if sjekk_for: break
                await pg.evaluate("document.querySelector(%s).click()" % json.dumps('#inIkke' if ikke else '#introNeste')); await pg.wait_for_timeout(700)
            await pg.wait_for_timeout(1200)
            sjekk('spurt én gang, på «Kom i gang»', await pg.evaluate("localStorage.getItem('__test:spurt')") == '1')
            sjekk('deretter valget om livslisten, som før', (await dlg(pg) or [''])[0] == 'Livslisten – valgfritt', await dlg(pg))
            lagre = [d for f, d in rpc if f == 'varsel_lagre']
            sjekk('adressen til Supabase: begge varslene på, ikke koblet (deler ikke), nettversjonen', len(lagre) == 1 and lagre[0] == {
                'p_endpoint': 'https://fcm.googleapis.com/fcm/send/test-1', 'p_p256dh': 'BPp256dh-test', 'p_auth': 'auth-test', 'p_telling': True, 'p_premier': True,
                'p_fro': True, 'p_app': 'web', 'p_koble': False}, lagre)
            sjekk('   med nøkkelen fra varsel_nokkel', await pg.evaluate("JSON.parse(localStorage.getItem('__test:sub')).length") == 65)
            await pg.evaluate("document.querySelector('#dlgKnapper [data-k=\"1\"]').click()"); await pg.wait_for_timeout(500)
            await pg.reload(wait_until='networkidle'); await pg.wait_for_timeout(5000)
            sjekk('neste start: ingen ny melding og ingen nytt spørsmål (samme dag)', await dlg(pg) is None and len([1 for f, d in rpc if f == 'varsel_lagre']) == 1 and await pg.evaluate("localStorage.getItem('__test:spurt')") == '1')
            sjekk('   ingen JS-feil', not js, js); await ctx.close()

            print('=== dere som alt bruker appen: ett vindu, én gang')
            for valg in ('Slå på', 'Ikke nå'):
                rpc = []
                ctx, pg, js = await side(b, bruker(), rpc)
                await pg.wait_for_timeout(3500)
                d = await dlg(pg)
                if valg == 'Slå på':
                    sjekk('vinduet «Varsler»', d == ['Varsler', 'Få beskjed når Hagefugltellingen starter. Du kan slå dem av i Innstillinger.'], d)
                    if BILDER: await pg.screenshot(path=str(BILDER / 'varsler_vindu.png'))
                await pg.evaluate("[...document.querySelectorAll('#dlgKnapper .btn')].find(b => b.textContent === %s).click()" % json.dumps(valg)); await pg.wait_for_timeout(1200)
                lagre = [d for f, d in rpc if f == 'varsel_lagre']
                if valg == 'Slå på':
                    sjekk('«Slå på»: telefonen spør, og adressen går til Supabase', await pg.evaluate("localStorage.getItem('__test:spurt')") == '1' and len(lagre) == 1 and lagre[0]['p_telling'] and lagre[0]['p_premier'], lagre)
                else:
                    sjekk('«Ikke nå»: ingen spørsmål, ingenting til Supabase', await pg.evaluate("localStorage.getItem('__test:spurt')") is None and not lagre, lagre)
                await pg.reload(wait_until='networkidle'); await pg.wait_for_timeout(5000)
                sjekk(f'   etter «{valg}»: vinduet kommer ikke igjen', await dlg(pg) is None, await dlg(pg))
                sjekk('   ingen JS-feil', not js, js); await ctx.close()
            rpc = []
            ctx, pg, js = await side(b, bruker(**{'fuglekort:deling': 'ja', 'fuglekort:kallenavn': json.dumps({'navn': 'Rask Kjøttmeis'}),
                                                  'fuglekort:okt': json.dumps({'access': 'x', 'refresh': 'y', 'uid': 'u1', 'utloper': 9999999999})}), rpc)
            await pg.wait_for_timeout(3500)
            sjekk('deler: vinduet nevner premiene', (await dlg(pg) or ['', ''])[1] == 'Få beskjed når Hagefugltellingen starter og når du vinner en premie. Du kan slå dem av i Innstillinger.', await dlg(pg))
            await pg.evaluate("document.querySelector('#dlgKnapper .btn.pri').click()"); await pg.wait_for_timeout(1500)
            lagre = [d for f, d in rpc if f == 'varsel_lagre']
            sjekk('   og telefonen kobles til brukeren (p_koble)', lagre and lagre[-1]['p_koble'] is True, lagre)
            await ctx.close()

            print('=== ja fra før (Android før 13): adressen går til Supabase uten spørsmål')
            rpc = []
            ctx, pg, js = await side(b, bruker(**{'__test:perm': 'granted'}), rpc)
            await pg.wait_for_timeout(4500)
            sjekk('ingen vindu, ikke spurt, adressen sendt', await dlg(pg) is None and await pg.evaluate("localStorage.getItem('__test:spurt')") is None
                  and len([1 for f, d in rpc if f == 'varsel_lagre']) == 1, rpc)
            print('=== Innstillinger → Varsler')
            v = await innst(pg)
            sjekk('begge bryterne på, testknappen synlig', v[:4] == ['true', 'true', False, False] and v[5] is False, v)
            if BILDER: await pg.evaluate("document.querySelector('#varselSek').scrollIntoView()"); await pg.screenshot(path=str(BILDER / 'varsler_innstillinger.png')) if BILDER else None
            rpc.clear()
            await pg.evaluate("document.querySelector('#varselTelling').click()"); await pg.wait_for_timeout(900)
            lagre = [d for f, d in rpc if f == 'varsel_lagre']
            sjekk('Hagefugltellingen av: lagret med p_telling false', (await innst(pg))[0] == 'false' and lagre and lagre[-1]['p_telling'] is False and lagre[-1]['p_premier'] is True, lagre)
            rpc.clear()
            await pg.evaluate("document.querySelector('#varselPremie').click()"); await pg.wait_for_timeout(900)
            sjekk('begge av: fjernet fra Supabase og nettleseren, testknappen skjult', [f for f, d in rpc] == ['varsel_slett'] and await pg.evaluate("localStorage.getItem('__test:avmeldt')") == '1'
                  and (await innst(pg))[5] is True, rpc)
            rpc.clear()
            await pg.evaluate("document.querySelector('#varselTelling').click()"); await pg.wait_for_timeout(900)
            lagre = [d for f, d in rpc if f == 'varsel_lagre']
            sjekk('Hagefugltellingen på igjen: ny adresse og lagret', await pg.evaluate("localStorage.getItem('__test:abonnert')") == '2' and lagre and lagre[-1]['p_telling'] is True and lagre[-1]['p_premier'] is False, lagre)
            rpc.clear()
            await pg.evaluate("document.querySelector('#varselTest').click()"); await pg.wait_for_timeout(900)
            sjekk('«Send et testvarsel»: send_testvarsel med adressen', [d for f, d in rpc if f == 'send_testvarsel'] == [{'p_endpoint': 'https://fcm.googleapis.com/fcm/send/test-1'}]
                  and await pg.evaluate("document.querySelector('#varselStatus').textContent") == 'Testvarselet er sendt. Det kommer om noen sekunder.', rpc)
            if BILDER: await pg.evaluate("document.querySelector('#varselSek').scrollIntoView()"); await pg.screenshot(path=str(BILDER / 'varsler_test.png')) if BILDER else None
            sjekk('   ingen JS-feil', not js, js); await ctx.close()

            rpc = []
            ctx, pg, js = await side(b, bruker(**{'__test:perm': 'granted', 'fuglekort:enkel': 'ja'}), rpc)
            await pg.wait_for_timeout(4500)
            lagre = [d for f, d in rpc if f == 'varsel_lagre']
            v = await innst(pg)
            sjekk('den enkle versjonen: uten premiebryteren, lagret uten premier og frø', v[2] is True and lagre and lagre[-1]['p_premier'] is False and lagre[-1]['p_fro'] is False, (v, lagre))
            await ctx.close()

            for perm, tekst in (('denied', 'Varsler er blokkert. Slå dem på i telefonens innstillinger.'), ('default', 'Trykk på en bryter for å slå på varsler.')):
                rpc = []
                ctx, pg, js = await side(b, bruker(**{'__test:perm': perm, 'hagefugler:varsler-spurt': '1'}), rpc)
                v = await innst(pg)
                sjekk(f'{"blokkert" if perm == "denied" else "ikke spurt"}: bryterne av, «{tekst}»', v[0] == v[1] == 'false' and v[3] is (perm == 'denied') and v[4] == tekst and v[5] is True, v)
                if perm == 'default':
                    await pg.evaluate("document.querySelector('#varselPremie').click()"); await pg.wait_for_timeout(1200)
                    v = await innst(pg)
                    sjekk('   en bryter: telefonen spør, og varslene er på', await pg.evaluate("localStorage.getItem('__test:spurt')") == '1' and v[:2] == ['true', 'true']
                          and [f for f, d in rpc].count('varsel_lagre') == 1, (v, rpc))
                await ctx.close()

            rpc = []
            ctx, pg, js = await side(b, bruker(**{'__test:perm': 'denied', 'hagefugler:varsler-sist': json.dumps({'sig': 'x', 't': 1, 'endpoint': 'https://fcm.googleapis.com/fcm/send/gammel'})}), rpc)
            await pg.wait_for_timeout(4500)
            sjekk('slått av i telefonens innstillinger: adressen slettes i Supabase ved start', rpc == [('varsel_slett', {'p_endpoint': 'https://fcm.googleapis.com/fcm/send/gammel'})]
                  and await pg.evaluate("localStorage.getItem('hagefugler:varsler-sist')") is None, rpc)
            await ctx.close()

            print('=== et trykk på varselet: riktig fane')
            rpc = []
            ctx, pg, js = await side(b, bruker(**{'__test:perm': 'granted'}), rpc, url=URL + '?vis=telling')
            await pg.wait_for_timeout(1000)
            sjekk('…/?vis=telling åpner Hagefugltelling, og adressen ryddes', await pg.evaluate("[document.querySelector('#tellSheet').classList.contains('on'), location.search]") == [True, ''])
            await pg.evaluate("document.querySelector('#closeTell').click()"); await pg.wait_for_timeout(500)
            await pg.evaluate("navigator.serviceWorker.dispatchEvent(new MessageEvent('message', { data: { type: 'vis', vis: 'telling' } }))"); await pg.wait_for_timeout(700)
            sjekk('en melding fra service workeren (appen var åpen) gjør det samme', await pg.evaluate("document.querySelector('#tellSheet').classList.contains('on')"))
            sjekk('   ingen JS-feil', not js, js); await ctx.close()

            print('=== service workeren viser varselet (push via Chrome DevTools)')
            b2 = await pw.chromium.launch(channel='chromium')        # the new headless shows notifications
            ctx = await b2.new_context(viewport={'width': 390, 'height': 800}, service_workers='allow')
            await ctx.grant_permissions(['notifications'], origin=URL.rstrip('/'))
            await ctx.route('https://qfustbltxgbpwsntcrpd.supabase.co/**', lambda r: r.abort())
            await ctx.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear();"
                                      + ''.join(f'localStorage.setItem({json.dumps(k)}, {json.dumps(v)});' for k, v in bruker(**{'hagefugler:varsler-spurt': '1'}).items()) + '}')
            pg = await ctx.new_page()
            await pg.goto(URL, wait_until='networkidle')
            await pg.evaluate("navigator.serviceWorker.ready"); await pg.wait_for_timeout(500)
            cdp = await ctx.new_cdp_session(pg)
            reg = {}
            cdp.on('ServiceWorker.workerRegistrationUpdated', lambda e: reg.update({r['registrationId']: r for r in e['registrations']}))
            await cdp.send('ServiceWorker.enable'); await pg.wait_for_timeout(800)
            rid = next(iter(reg), None)
            data = json.dumps({'tittel': 'Hagefugltellingen', 'tekst': 'Hagefugltellingen er i gang! Tell i én time og få 75 000 frø.', 'url': './?vis=telling', 'tag': 'telling'})
            await cdp.send('ServiceWorker.deliverPushMessage', {'origin': URL.rstrip('/'), 'registrationId': rid, 'data': data}); await pg.wait_for_timeout(1500)
            n = await pg.evaluate("navigator.serviceWorker.ready.then(r => r.getNotifications()).then(ns => ns.map(n => [n.title, n.body, n.tag, n.data && n.data.url]))")
            sjekk('varselet vises med tittel, tekst, tag og adresse', n == [['Hagefugltellingen', 'Hagefugltellingen er i gang! Tell i én time og få 75 000 frø.', 'telling', './?vis=telling']], (rid, n))
            await ctx.close(); await b2.close()
            await b.close()
    finally:
        srv.terminate()
    print('FEIL: ' + (', '.join(FEIL) if FEIL else 'ingen'))
    sys.exit(1 if FEIL else 0)

asyncio.run(main())
