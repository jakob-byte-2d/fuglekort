"""Profilbildet på tavla: fuglen du har valgt som profilbilde og bildetypen (Foto eller Illustrasjon) sendes med raden
(ledertavle.profilfugl og .profilsett) og vises ved navnet i den bildetypen (en rund fugl med tittelikonet i hjørnet; i
den enkle versjonen uten tittelikon), i boksen «deg» øverst og på profilen. Uten bildetype (en eldre app): bildevalget
til den som ser på. Et skjult navn, en ukjent art eller et dyrekort gir tittelikonet. Ledertavle åpnes fra menyen, på
Totalt. Før profilfugl.sql / profilsett.sql er kjørt (kolonnen mangler) sendes og hentes tavla uten dem.
Kjør fra repoet etter python3 build.py:   python3 tests/tavle_profilfugl_test.py [MAPPE_FOR_SKJERMBILDER]
"""
import asyncio, json, subprocess, sys, time, uuid, pathlib
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent
BILDER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else None
URL = 'http://localhost:8789/'
SUPA = 'qfustbltxgbpwsntcrpd.supabase.co'
FEIL = []
MANGLER = {'code': 'PGRST204', 'details': None, 'hint': None, 'message': "Could not find the 'profilfugl' column of 'ledertavle' in the schema cache"}
ANDRE = [
    {'user_id': 'u1', 'navn': 'Kjøttmeisen', 'tittel': 6, 'fro': 90000, 'arter': 30, 'dager': 80, 'merket': False, 'profilfugl': 'parus-major', 'profilsett': 'tegneserie'},
    {'user_id': 'u6', 'navn': 'Eldre app', 'tittel': 5, 'fro': 70000, 'arter': 25, 'dager': 60, 'merket': False, 'profilfugl': 'turdus-merula', 'profilsett': None},
    {'user_id': 'u2', 'navn': 'Uten fugl', 'tittel': 3, 'fro': 50000, 'arter': 20, 'dager': 40, 'merket': False, 'profilfugl': None},
    {'user_id': 'u3', 'navn': 'Dyrekortet', 'tittel': 2, 'fro': 30000, 'arter': 12, 'dager': 20, 'merket': False, 'profilfugl': 'sciurus-vulgaris'},
    {'user_id': 'u4', 'navn': 'Ukjent art', 'tittel': 1, 'fro': 20000, 'arter': 8, 'dager': 10, 'merket': False, 'profilfugl': 'finnes-ikke'},
    {'user_id': 'u5', 'navn': 'Skjult person', 'tittel': 4, 'fro': 10000, 'arter': 5, 'dager': 5, 'merket': False, 'profilfugl': 'pica-pica'},
]


def sjekk(navn, ok, info=''):
    print(('  OK   ' if ok else '  FEIL ') + navn + (f'  ({info})' if not ok and info != '' else ''))
    if not ok: FEIL.append(navn)


class Supa:
    """nok av Supabase til raden på tavla, hovedtavla (tabellen), artstavla og profilen; uten kolonnen før SQL-en"""
    def __init__(self, kolonne=True, sett=True):
        self.kolonne, self.sett, self.sendt, self.avvist, self.lest = kolonne, kolonne and sett, [], 0, []

    def mangler(self, navn):
        return navn == 'profilfugl' and not self.kolonne or navn == 'profilsett' and not self.sett

    def rader(self):
        return [{k: v for k, v in r.items() if not self.mangler(k)} for r in ANDRE]

    async def handle(self, route):
        req = route.request; u = urlparse(req.url); m = req.method
        h = {'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*',
             'access-control-expose-headers': 'content-range', 'content-type': 'application/json'}
        if m == 'OPTIONS': return await route.fulfill(status=204, headers=h)
        svar = lambda st, b=None, ekstra=None: route.fulfill(status=st, headers={**h, **(ekstra or {})}, body='' if b is None else json.dumps(b))
        body = json.loads(req.post_data) if req.post_data else None
        if u.path in ('/auth/v1/signup', '/auth/v1/token'):
            uid = str(uuid.uuid4())
            return await svar(200, {'access_token': 'tok-' + uid[:8], 'refresh_token': 'ref-' + uid[:8], 'expires_in': 3600, 'expires_at': int(time.time()) + 3600, 'user': {'id': uid}})
        fn = u.path.rsplit('/', 1)[-1]
        if u.path == '/rest/v1/ledertavle' and m == 'POST':
            for k in ('profilfugl', 'profilsett'):
                if self.mangler(k) and k in body[0]: self.avvist += 1; return await svar(400, {**MANGLER, 'message': MANGLER['message'].replace('profilfugl', k)})
            self.sendt.append(body[0]); return await svar(201)
        if u.path == '/rest/v1/ledertavle' and m == 'GET':
            sel = parse_qs(u.query).get('select', [''])[0]
            if sel == 'user_id': return await svar(200, [], {'content-range': '*/0'})
            self.lest.append(sel)
            if any(self.mangler(k) and k in sel for k in ('profilfugl', 'profilsett')): return await svar(400, MANGLER)
            return await svar(200, self.rader(), {'content-range': f'0-{len(ANDRE) - 1}/{len(ANDRE)}'})
        if fn == 'profil_arter':
            r = next(x for x in ANDRE if x['user_id'] == body['uid'])
            return await svar(200, {'user_id': r['user_id'], 'navn': r['navn'], 'antall': 2, 'vis': True, 'arter': ['parus-major', 'turdus-merula'],
                                    **{k: r.get(k) for k in ('profilfugl', 'profilsett') if not self.mangler(k)}})
        if fn in ('tavle_arter', 'tavle'):
            return await svar(200, {'periode': None, 'fra': None, 'til': None, 'antall': len(ANDRE), 'plass': None, 'meg': None, 'premier': [2000, 1000, 500], 'forrige': [],
                                    'rader': [{**r, 'n': r['arter'], 'plass': i + 1} for i, r in enumerate(self.rader())]})
        if u.path.startswith('/rest/v1/rpc/'):
            return await svar(200, {'navn_status': 'ledig', 'mine_grupper': [], 'gruppe_fra_kode': None}.get(fn, None))
        if m == 'GET': return await svar(200, [], {'content-range': '*/0'})
        return await svar(201 if m == 'POST' else 204)


def lager(**x):
    d = {'hagefugler:testmerke': '2026-09-30-pluss', 'fuglekort:intro': 'ferdig', 'hagefugler-oslo:hint': 'ok', 'fuglekort:tittel:v2': '99', 'hagefugler:varsler-spurt': '1',
         'fuglekort:oppdrag': json.dumps({k: '2026-08-14' for k in ('forste', 'sok', 'arter3', 'tavle', 'dager2', 'kjop', 'arter5', 'dager3')}),
         'fuglekort:deling': 'ja', 'fuglekort:kallenavn': json.dumps({'navn': 'Test Meis 1', 'forslag': False}),
         'fuglekort:tavlevis': 'uke', 'fuglekort:skjulte': json.dumps({'u5': 'Skjult person'}),
         'fuglekort:forsett:v1': json.dumps({'parus-major': {'svar': 'for', 'aar': 2015, 'ts': 1}}),
         'hagefugler-oslo:sett:v1': json.dumps({'turdus-merula': {'date': '2026-11-02', 'dager': ['2026-11-02', '2026-11-03'], 'ts': 1}}),
         'hagefugler:profilbilde': json.dumps({'fugl': 'turdus-merula', 'sett': 'foto'})}
    d.update(x); return d


async def side(b, sb, ls):
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True, is_mobile=True, service_workers='block')
    await ctx.route(f'https://{SUPA}/**', sb.handle)
    await ctx.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear();"
                              + ''.join(f'localStorage.setItem({json.dumps(k)}, {json.dumps(v)});' for k, v in ls.items()) + '}')
    pg = await ctx.new_page(); js = []; pg.on('pageerror', lambda e: js.append(str(e)))
    await pg.goto(URL, wait_until='networkidle')
    for _ in range(40):
        await pg.wait_for_timeout(250)
        if sb.sendt or sb.avvist >= 1 and sb.sendt: break
    await pg.wait_for_timeout(500)
    return ctx, pg, js


async def klikk(pg, sel, ms=500):
    await pg.evaluate(f"document.querySelector({json.dumps(sel)}).click()"); await pg.wait_for_timeout(ms)


async def tavla(pg):
    """Ledertavle from the menu: each row's picture (the bird with its sprite, or the title), and your box"""
    if not await pg.evaluate("document.querySelector('#tavleSheet').classList.contains('on')"):
        if await pg.evaluate("!!document.querySelector('.sheet.on')"): await pg.keyboard.press('Escape'); await pg.wait_for_timeout(400)
        await klikk(pg, '#openMeny', 300); await klikk(pg, '#openTavle', 600)
    for _ in range(20):
        if await pg.evaluate("document.querySelectorAll('#tavleBody [data-tavle-rad]').length > 1"): break
        await pg.wait_for_timeout(250)
    return await pg.evaluate("""(() => {
      const ut = {}, sprite = p => (/photos(-[a-z]+)?\\.webp/.exec(getComputedStyle(p).backgroundImage) || [''])[0];
      for (const b of document.querySelectorAll('#tavleBody [data-tavle-rad]')) {
        const pb = b.querySelector(':scope > .tv-pb');
        const ph = pb && pb.querySelector('.ph'), st = ph && ph.getBoundingClientRect();
        ut[b.querySelector('.tv-t b').firstChild.textContent] = pb ? (pb.classList.contains('tom') ? 'tom' : { fugl: ph.style.backgroundPosition, sprite: sprite(ph), tittel: !!pb.querySelector('.ti'), str: Math.round(st.width) + 'x' + Math.round(st.height) }) : (b.querySelector(':scope > .ti') ? 'tittel' : '-');
      }
      const m = document.querySelector('#tavleBody .tv-meg'), mp = m && m.querySelector('.tv-pb');
      const mph = mp && mp.querySelector('.ph'), ms = mph && mph.getBoundingClientRect();
      ut['(boksen deg)'] = mp ? { fugl: mph.style.backgroundPosition, sprite: sprite(mph), tittel: !!mp.querySelector('.ti'), str: Math.round(ms.width) + 'x' + Math.round(ms.height) } : m && m.querySelector('.ti') ? 'tittel' : '-';
      ut['(periode)'] = (document.querySelector('#tavleBody [data-tavlevis][aria-pressed=true]') || {}).textContent;
      return ut; })()""")


async def fuglPos(pg, nokkel):
    """the sprite position of a bird, as the chooser «Profilbilde» shows it (the bird must be on the life list)"""
    return await pg.evaluate(f"(() => {{ const b = document.querySelector('[data-pb-fugl=\"{nokkel}\"] .ph'); return b && b.style.backgroundPosition; }})()")


async def main():
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8789', '-d', str(ROT / 'docs')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        async with async_playwright() as pw:
            b = await pw.chromium.launch()

            print('=== med kolonnen (profilfugl.sql kjørt)')
            sb = Supa(True)
            ctx, pg, js = await side(b, sb, lager())
            sjekk('raden sendes med profilfugl = turdus-merula og profilsett = foto', sb.sendt and sb.sendt[-1].get('profilfugl') == 'turdus-merula' and sb.sendt[-1].get('profilsett') == 'foto', sb.sendt[-1:])
            # the sprite positions to compare with: from the chooser
            await klikk(pg, '#openStats', 600); await klikk(pg, '#fane-profil', 500); await klikk(pg, '#statsBody [data-profilbilde]', 500)
            POS = {k: await fuglPos(pg, k) for k in ('parus-major', 'turdus-merula')}
            await klikk(pg, '#dlgKnapper .btn:last-child', 400); await klikk(pg, '#closeStats', 400)
            t = await tavla(pg)
            sjekk('Ledertavle åpnes på Totalt (selv om Uke var lagret fra før)', t.get('(periode)') == 'Totalt', t.get('(periode)'))
            sjekk('Kjøttmeisen: kjøttmeis som illustrasjon i rund ramme med tittelikonet i hjørnet', t.get('Kjøttmeisen') == {'fugl': POS['parus-major'], 'sprite': 'photos-tegneserie.webp', 'tittel': True, 'str': '30x30'}, t)
            sjekk('Eldre app (uten bildetype): fuglen i bildevalget til den som ser på', isinstance(t.get('Eldre app'), dict) and t['Eldre app']['sprite'] == 'photos-foto.webp', t.get('Eldre app'))
            sjekk('Uten fugl: tittelikonet som før', t.get('Uten fugl') == 'tittel', t)
            sjekk('Dyrekortet (ikke en fugl) og en ukjent art: tittelikonet', t.get('Dyrekortet') == 'tittel' and t.get('Ukjent art') == 'tittel', t)
            sjekk('et navn du har skjult: tittelikonet, ikke fuglen', t.get('Skjult navn') == 'tittel', t)
            sjekk('boksen øverst (deg): svarttrosten som foto med tittelikonet', t.get('(boksen deg)') == {'fugl': POS['turdus-merula'], 'sprite': 'photos-foto.webp', 'tittel': True, 'str': '44x44'}, t)
            if BILDER: await pg.screenshot(path=str(BILDER / 'tavle_pf.png'))
            await klikk(pg, '#tavleBody [data-tavle-rad="u1"]', 700)
            r = await pg.evaluate("(() => { const p = document.querySelector('#tavleBody .profil-pb'), f = p && p.querySelector('.ph').getBoundingClientRect(); return p && [p.getAttribute('aria-label'), p.querySelector('.ph').style.backgroundPosition, Math.round(f.width), getComputedStyle(p.querySelector('.ph')).backgroundImage.includes('photos-tegneserie.webp')]; })()")
            sjekk('profilen til Kjøttmeisen: fuglen som illustrasjon ved navnet (56 px)', r == ['Profilbilde: Kjøttmeis', POS['parus-major'], 56, True], r)
            await pg.keyboard.press('Escape'); await pg.wait_for_timeout(400)
            sjekk('Esc på en profil går tilbake til tavla', await pg.evaluate("document.querySelector('#tavleSheet').classList.contains('on') && !!document.querySelector('#tavleBody [data-tavle-rad]')"))
            await klikk(pg, '#tavleBody [data-tavle-rad="u1"]', 700)
            if BILDER: await pg.screenshot(path=str(BILDER / 'tavle_pf_profil.png'))
            await klikk(pg, '#tavleBody [data-profillukk]', 500)
            await klikk(pg, '#tavleBody [data-tavle-rad="u2"]', 700)
            sjekk('profilen til en uten fugl: ingen fugl', await pg.evaluate("!document.querySelector('#tavleBody .profil-pb')"))
            await klikk(pg, '#tavleBody [data-profillukk]', 500)
            # changing the profile bird sends the row again
            n = len(sb.sendt)
            await klikk(pg, '#closeTavle', 400); await klikk(pg, '#openStats', 600); await klikk(pg, '#statsBody [data-profilbilde]', 500)
            await klikk(pg, '[data-pb-sett="tegneserie"]', 200); await klikk(pg, '[data-pb-fugl="parus-major"]', 0)
            for _ in range(20):
                await pg.wait_for_timeout(250)
                if len(sb.sendt) > n: break
            sjekk('bytter du til kjøttmeis som illustrasjon, sendes raden med parus-major og tegneserie', len(sb.sendt) > n and sb.sendt[-1].get('profilfugl') == 'parus-major' and sb.sendt[-1].get('profilsett') == 'tegneserie', sb.sendt[n:])
            n = len(sb.sendt)
            await klikk(pg, '#statsBody [data-profilbilde]', 500)
            txt = await pg.evaluate("document.querySelector('#dlgTekst p').textContent")
            sjekk('«Profilbilde» sier at fuglen også vises på ledertavla når du deler', txt == 'Velg Foto eller Illustrasjon, og trykk på en fugl fra livslisten din. Den vises også ved navnet ditt på ledertavla.', txt)
            await pg.evaluate("[...document.querySelectorAll('#dlgKnapper .btn')].find(b => b.textContent === 'Bruk tittelikonet').click()")
            for _ in range(20):
                await pg.wait_for_timeout(250)
                if len(sb.sendt) > n: break
            sjekk('«Bruk tittelikonet» sender profilfugl og profilsett = null', len(sb.sendt) > n and sb.sendt[-1].get('profilfugl', 1) is None and sb.sendt[-1].get('profilsett', 1) is None, sb.sendt[n:])
            sjekk('hovedtavla leses med profilfugl og profilsett', any('profilfugl,profilsett' in s for s in sb.lest), sb.lest)
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== den enkle versjonen')
            sb = Supa(True)
            ctx, pg, js = await side(b, sb, lager(**{'fuglekort:enkel': 'ja'}))
            await klikk(pg, '#openStats', 600); await klikk(pg, '#statsBody [data-profilbilde]', 500)
            POS = {k: await fuglPos(pg, k) for k in ('parus-major', 'turdus-merula')}
            await klikk(pg, '#dlgKnapper .btn:last-child', 400); await klikk(pg, '#closeStats', 400)
            t = await tavla(pg)
            sjekk('Kjøttmeisen: fuglen (illustrasjon) uten tittelikon', t.get('Kjøttmeisen') == {'fugl': POS['parus-major'], 'sprite': 'photos-tegneserie.webp', 'tittel': False, 'str': '30x30'}, t)
            sjekk('rader uten fugl holder av plassen (tom)', t.get('Uten fugl') == 'tom' and t.get('Skjult navn') == 'tom', t)
            sjekk('boksen øverst: svarttrosten uten tittelikon', t.get('(boksen deg)') == {'fugl': POS['turdus-merula'], 'sprite': 'photos-foto.webp', 'tittel': False, 'str': '44x44'}, t)
            if BILDER: await pg.screenshot(path=str(BILDER / 'tavle_pf_enkel.png'))
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== uten kolonnen (profilfugl.sql ikke kjørt ennå)')
            sb = Supa(False)
            ctx, pg, js = await side(b, sb, lager())
            sjekk('raden avvises med fuglen, og sendes så uten', sb.avvist == 1 and sb.sendt and 'profilfugl' not in sb.sendt[-1], [sb.avvist, sb.sendt[-1:]])
            sjekk('   og appen husker det (prøver igjen om 6 timer)', bool(await pg.evaluate("localStorage.getItem('fuglekort:uten-profilfugl')")))
            t = await tavla(pg)
            sjekk('hovedtavla hentes likevel (uten profilfugl), med tittelikonene', t.get('Kjøttmeisen') == 'tittel' and t.get('Uten fugl') == 'tittel' and len(sb.lest) >= 2 and 'profilfugl' not in sb.lest[-1], [t, sb.lest])
            n = len(sb.sendt)
            await klikk(pg, '#closeTavle', 400); await klikk(pg, '#openStats', 600); await klikk(pg, '#statsBody [data-profilbilde]', 500); await klikk(pg, '[data-pb-fugl="parus-major"]', 0)
            await pg.wait_for_timeout(3000)
            sjekk('et nytt valg sendes uten fuglen i mellomtiden, uten nye avvisninger', sb.avvist == 1 and all('profilfugl' not in s and 'profilsett' not in s for s in sb.sendt[n:]), [sb.avvist, sb.sendt[n:]])
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== med profilfugl, men uten profilsett (profilsett.sql ikke kjørt)')
            sb = Supa(True, sett=False)
            ctx, pg, js = await side(b, sb, lager())
            sjekk('raden avvises med bildetypen, og sendes så med fuglen, men uten bildetypen', sb.avvist == 1 and sb.sendt and sb.sendt[-1].get('profilfugl') == 'turdus-merula' and 'profilsett' not in sb.sendt[-1], [sb.avvist, sb.sendt[-1:]])
            t = await tavla(pg)
            sjekk('hovedtavla hentes likevel, fuglene i bildevalget til den som ser på', t.get('Kjøttmeisen', {}).get('sprite') == 'photos-foto.webp', t)
            sjekk('ingen JS-feil', not js, js); await ctx.close()
            await b.close()
    finally:
        srv.terminate()
    print('FEIL: ' + (', '.join(FEIL) if FEIL else 'ingen'))
    sys.exit(1 if FEIL else 0)

asyncio.run(main())
