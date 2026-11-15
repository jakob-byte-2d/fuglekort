"""Profilbilde: a bird from the life list or the title icon (the default; in the simple version, nothing). Shown in the
ring at the top right and in the Profil tab; when sharing also at the name on the board and the profile (see
tavle_profilfugl_test.py). Per user on this device. A bird no longer on the life list falls back to the title. A
picture of your own (offered for a few hours on 15 Nov 2026) is deleted at the start.
Run from the repo after python3 build.py:   python3 tests/profilbilde_test.py [MAPPE_FOR_SKJERMBILDER]
"""
import asyncio, json, subprocess, sys, pathlib
from playwright.async_api import async_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent
BILDER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else None
URL = 'http://localhost:8792/'
FEIL = []


def sjekk(navn, ok, info=''):
    print(('  OK   ' if ok else '  FEIL ') + navn + (f'  ({info})' if not ok and info != '' else ''))
    if not ok: FEIL.append(navn)


def lager(**x):
    d = {'hagefugler:testmerke': '2026-09-30-pluss', 'fuglekort:intro': 'ferdig', 'hagefugler-oslo:hint': 'ok', 'fuglekort:deling': 'nei',
         'fuglekort:tittel:v2': '99', 'hagefugler:varsler-spurt': '1', 'fuglekort:fane': 'profil',
         'fuglekort:oppdrag': json.dumps({k: '2026-08-14' for k in ('forste', 'sok', 'arter3', 'tavle', 'dager2', 'kjop', 'arter5', 'dager3')}),
         'fuglekort:forsett:v1': json.dumps({'parus-major': {'svar': 'for', 'aar': 2015, 'ts': 1}}),
         'hagefugler-oslo:sett:v1': json.dumps({'turdus-merula': {'date': '2026-11-02', 'dager': ['2026-11-02', '2026-11-03'], 'ts': 1}}),
         'hagefugler:kjop:v1': json.dumps({'dyr-sciurus-vulgaris': {'pris': 12000, 'dato': '2026-10-01', 'ts': 1}}),
         'hagefugler:bonusvist:v1': json.dumps({'sciurus-vulgaris': {'ts': 1}}), 'hagefugler-oslo:kort': '0'}
    d.update(x); return d


async def side(b, ls, mork=False):
    ctx = await b.new_context(viewport={'width': 390, 'height': 800}, device_scale_factor=2, has_touch=True, is_mobile=True, service_workers='block',
                              color_scheme='dark' if mork else 'light')
    await ctx.route('https://qfustbltxgbpwsntcrpd.supabase.co/**', lambda r: r.abort())
    await ctx.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear();"
                              + ''.join(f'localStorage.setItem({json.dumps(k)}, {json.dumps(v)});' for k, v in ls.items()) + '}')
    pg = await ctx.new_page(); js = []; ut = []
    pg.on('pageerror', lambda e: js.append(str(e)))
    pg.on('request', lambda r: ut.append((r.url, r.post_data or '')) if not r.url.startswith(URL) else None)
    await pg.goto(URL, wait_until='networkidle'); await pg.wait_for_timeout(1500)
    return ctx, pg, js, ut


async def klikk(pg, sel, ms=500):
    await pg.evaluate(f"document.querySelector({json.dumps(sel)}).click()"); await pg.wait_for_timeout(ms)


async def dialog(pg):
    return await pg.evaluate("""(() => { const d = document.querySelector('#dlg'); return { apen: !d.hidden && d.classList.contains('on'), tittel: d.querySelector('#dlgT').textContent,
      fugler: [...d.querySelectorAll('[data-pb-fugl]')].map(b => b.querySelector('.pb-n').textContent), valgt: [...d.querySelectorAll('[data-pb-fugl][aria-pressed=true]')].map(b => b.dataset.pbFugl),
      knapper: [...d.querySelectorAll('#dlgKnapper .btn')].map(b => b.textContent), pri: (d.querySelector('#dlgKnapper .btn.pri') || {}).textContent || '',
      merk: (d.querySelector('.pb-merk') || {}).textContent || '' }; })()""")


async def tilstand(pg):
    return await pg.evaluate("""(() => { const r = document.querySelector('#ringBilde'), k = document.querySelector('#statsBody [data-profilbilde]');
      return { ring: !r.hidden && getComputedStyle(r).display !== 'none', ringFugl: !!r.querySelector('.ph'), harPb: document.querySelector('#openStats').classList.contains('har-pb'),
        tiSynlig: getComputedStyle(document.querySelector('#ringIkon')).visibility === 'visible' && getComputedStyle(document.querySelector('#ringIkon')).display !== 'none',
        enkelIkon: getComputedStyle(document.querySelector('#openStats .enkel-ikon')).display !== 'none',
        hode: k ? (k.querySelector('.pb-stor .ph') ? 'fugl' : k.querySelector('.ti') ? 'tittel' : k.querySelector('.pb-tom') ? 'tom' : '?') : null,
        fyll: [r, k && k.querySelector('.pb-stor')].filter(Boolean).every(e => { const p = e.firstElementChild; if (!p || e.hidden) return true; const a = p.getBoundingClientRect(), b = e.getBoundingClientRect(); return Math.abs(a.width - b.width) < 1 && Math.abs(a.height - b.height) < 1; }),
        label: k ? k.getAttribute('aria-label') : null, blyant: !!(k && k.querySelector('.pb-blyant')), fokus: document.activeElement && document.activeElement.matches('[data-profilbilde]'),
        lagret: localStorage.getItem('hagefugler:profilbilde') }; })()""")


async def main():
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8792', '-d', str(ROT / 'docs')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        async with async_playwright() as pw:
            b = await pw.chromium.launch()

            print('=== vanlig bruker: tittelikonet først, så en fugl fra livslisten')
            ctx, pg, js, ut = await side(b, lager())
            t = await tilstand(pg)
            sjekk('ringen viser tittelikonet, ikke noe profilbilde', not t['ring'] and t['tiSynlig'] and not t['harPb'], t)
            await klikk(pg, '#openStats', 700)
            t = await tilstand(pg)
            sjekk('Profil: tittelikonet med blyant, «Bytt profilbilde»', t['hode'] == 'tittel' and t['blyant'] and 'Bytt profilbilde' in t['label'], t)
            if BILDER: await pg.screenshot(path=str(BILDER / 'pb_profil_for.png'))
            await klikk(pg, '#statsBody [data-profilbilde]', 500)
            d = await dialog(pg)
            sjekk('«Profilbilde» viser fuglene på livslisten (registrert og sett før), ikke dyrekortet', d['apen'] and d['tittel'] == 'Profilbilde' and d['fugler'] == ['Kjøttmeis', 'Svarttrost'], d)
            sjekk('   knappene: Åpne livslisten, Avbryt (ikke «Velg eget bilde»)', d['knapper'] == ['Åpne livslisten', 'Avbryt'] and d['pri'] == '', d['knapper'])
            sjekk('   teksten: «Velg Foto eller Illustrasjon, og trykk på en fugl …»', await pg.evaluate("document.querySelector('#dlgTekst p').textContent") == 'Velg Foto eller Illustrasjon, og trykk på en fugl fra livslisten din.')
            r = await pg.evaluate("[[...document.querySelectorAll('#dlg [data-pb-sett]')].map(b => [b.textContent, b.getAttribute('aria-pressed')]), getComputedStyle(document.querySelector('[data-pb-fugl] .ph')).backgroundImage]")
            sjekk('   Foto · Illustrasjon, Foto valgt (bildevalget), fuglene som foto', r[0] == [['Foto', 'true'], ['Illustrasjon', 'false']] and 'photos-foto.webp' in r[1], r)
            sjekk('   «Flere fugler kommer …»', d['merk'].startswith('Flere fugler kommer'), d['merk'])
            if BILDER: await pg.screenshot(path=str(BILDER / 'pb_velg.png'))
            await klikk(pg, '[data-pb-fugl="parus-major"]', 600)
            t = await tilstand(pg)
            sjekk('kjøttmeis valgt: i ringen og i Profil, lagret som fugl, markøren tilbake på bildet',
                  not (await dialog(pg))['apen'] and t['ring'] and t['ringFugl'] and t['harPb'] and not t['tiSynlig'] and t['hode'] == 'fugl'
                  and json.loads(t['lagret'] or '{}') == {'fugl': 'parus-major', 'sett': 'foto'} and t['fokus'] and t['label'].startswith('Profilbilde: Kjøttmeis, foto'), t)
            sjekk('   fuglebildet fyller hele sirkelen i ringen og i Profil', t['fyll'], t)
            if BILDER: await pg.screenshot(path=str(BILDER / 'pb_profil_fugl.png'))
            await klikk(pg, '#statsBody [data-profilbilde]', 500)
            d = await dialog(pg)
            sjekk('   valgt fugl er merket, og «Bruk tittelikonet» er med', d['valgt'] == ['parus-major'] and 'Bruk tittelikonet' in d['knapper'], d)
            await klikk(pg, '[data-pb-sett="tegneserie"]', 300)
            r = await pg.evaluate("[[...document.querySelectorAll('#dlg [data-pb-sett]')].map(b => b.getAttribute('aria-pressed')), [...document.querySelectorAll('[data-pb-fugl] .ph')].every(p => getComputedStyle(p).backgroundImage.includes('photos-tegneserie.webp'))]")
            sjekk('   Illustrasjon: fuglene vises som illustrasjoner', r == [['false', 'true'], True], r)
            if BILDER: await pg.screenshot(path=str(BILDER / 'pb_velg_illustrasjon.png'))
            await klikk(pg, '[data-pb-fugl="parus-major"]', 600)
            t = await tilstand(pg)
            ill = await pg.evaluate("[getComputedStyle(document.querySelector('#ringBilde .ph')).backgroundImage, getComputedStyle(document.querySelector('#statsBody .pb-stor .ph')).backgroundImage]")
            sjekk('kjøttmeis som illustrasjon: lagret, i ringen og i Profil', json.loads(t['lagret'] or '{}') == {'fugl': 'parus-major', 'sett': 'tegneserie'}
                  and all('photos-tegneserie.webp' in v for v in ill) and t['label'].startswith('Profilbilde: Kjøttmeis, illustrasjon'), [t, ill])
            await klikk(pg, '#statsBody [data-profilbilde]', 500)
            r = await pg.evaluate("document.querySelector('#dlg [data-pb-sett][aria-pressed=true]').dataset.pbSett")
            sjekk('   «Profilbilde» åpnes på bildetypen til profilbildet (Illustrasjon)', r == 'tegneserie', r)
            await klikk(pg, '#dlgKnapper .btn:last-child', 400)
            await klikk(pg, '#statsBody [data-titler]', 400)
            r = await pg.evaluate("[document.querySelector('#statsBody [data-titler]').getAttribute('aria-expanded'), !!document.querySelector('#statsBody .titler')]")
            sjekk('tittelnavnet åpner lista over titlene', r == ['true', True], r)
            await pg.evaluate("document.querySelector('#statsBody .pb-knapp').scrollIntoView({block: 'center'})")
            if BILDER: await pg.screenshot(path=str(BILDER / 'pb_titler.png'))

            print('=== fuglen tas ut av livslisten: tilbake til tittelen')
            await pg.evaluate("localStorage.setItem('fuglekort:forsett:v1', '{}')")
            await pg.reload(wait_until='networkidle'); await pg.wait_for_timeout(1200)
            t = await tilstand(pg)
            sjekk('ringen viser tittelikonet igjen', not t['ring'] and t['tiSynlig'], t)
            await klikk(pg, '#openStats', 700)
            sjekk('   og Profil viser tittelikonet', (await tilstand(pg))['hode'] == 'tittel')
            await klikk(pg, '#statsBody [data-profilbilde]', 500)
            d = await dialog(pg)
            sjekk('   og bare svarttrost står i lista', d['fugler'] == ['Svarttrost'] and d['valgt'] == [], d)

            await klikk(pg, '[data-pb-fugl="turdus-merula"]', 600)
            sjekk('svarttrost valgt', (await tilstand(pg))['ringFugl'])
            await klikk(pg, '#statsBody [data-profilbilde]', 500)
            await pg.evaluate("[...document.querySelectorAll('#dlgKnapper .btn')].find(b => b.textContent === 'Bruk tittelikonet').click()"); await pg.wait_for_timeout(500)
            t = await tilstand(pg)
            sjekk('«Bruk tittelikonet»: tilbake til tittelen, ingenting lagret', t['lagret'] is None and not t['ring'] and t['hode'] == 'tittel', t)
            await klikk(pg, '#statsBody [data-profilbilde]', 500)
            await pg.evaluate("[...document.querySelectorAll('#dlgKnapper .btn')].find(b => b.textContent === 'Åpne livslisten').click()"); await pg.wait_for_timeout(600)
            d = await dialog(pg)
            sjekk('«Åpne livslisten» åpner livslisten', d['apen'] and d['tittel'].startswith('Livslisten'), d['tittel'])
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== den enkle versjonen, og en bruker til på telefonen uten livsliste')
            brukere = json.dumps([{'id': 'meg', 'navn': 'Jakob'}, {'id': 'b1', 'navn': 'Emma', 'type': 'barn'}])
            ctx, pg, js, ut = await side(b, lager(**{'fuglekort:enkel': 'ja', 'hagefugler:profilbilde': json.dumps({'fugl': 'turdus-merula'}), 'fuglekort:brukere': brukere}))
            t = await tilstand(pg)
            sjekk('enkel: ringen viser svarttrosten i stedet for bok-ikonet', t['ring'] and t['ringFugl'] and not t['enkelIkon'], t)
            if BILDER: await pg.screenshot(path=str(BILDER / 'pb_enkel.png'), clip={'x': 0, 'y': 0, 'width': 390, 'height': 120})
            await klikk(pg, '#openStats', 700)
            await klikk(pg, '#statsBody [data-profilbilde]', 500)
            d = await dialog(pg)
            sjekk('   «Fjern profilbildet» i den enkle versjonen', 'Fjern profilbildet' in d['knapper'], d['knapper'])
            await pg.evaluate("[...document.querySelectorAll('#dlgKnapper .btn')].find(b => b.textContent === 'Fjern profilbildet').click()"); await pg.wait_for_timeout(500)
            t = await tilstand(pg)
            sjekk('   fjernet: bok-ikonet i ringen, en tom figur i Profil', not t['ring'] and t['enkelIkon'] and t['hode'] == 'tom' and 'ikke valgt' in t['label'], t)
            if BILDER: await pg.screenshot(path=str(BILDER / 'pb_enkel_profil.png'))
            await pg.evaluate("localStorage.setItem('hagefugler:profilbilde', JSON.stringify({fugl: 'turdus-merula'})); localStorage.setItem('fuglekort:bruker', 'b1')")
            await pg.reload(wait_until='networkidle'); await pg.wait_for_timeout(1300)
            t = await tilstand(pg)
            sjekk('Emma (bruker nr. 2) ser ikke Jakobs profilbilde', not t['ring'], t)
            await klikk(pg, '#openStats', 700)
            await klikk(pg, '#statsBody [data-profilbilde]', 500)
            d = await dialog(pg)
            sjekk('   tom livsliste: ingen fugler, forklaring, «Åpne livslisten» er hovedknappen', d['fugler'] == [] and d['merk'].startswith('Fuglene på livslisten din kan bli profilbilde') and d['pri'] == 'Åpne livslisten' and d['knapper'] == ['Åpne livslisten', 'Avbryt'], d)
            if BILDER: await pg.screenshot(path=str(BILDER / 'pb_tom.png'))
            await klikk(pg, '#dlgKnapper .btn:last-child', 400)
            r = await pg.evaluate("[localStorage.getItem('hagefugler:profilbilde@b1'), JSON.parse(localStorage.getItem('hagefugler:profilbilde'))]")
            sjekk('   ingenting lagret for Emma, Jakobs står', r == [None, {'fugl': 'turdus-merula'}], r)
            await pg.evaluate("localStorage.setItem('fuglekort:bruker', 'meg')")
            await pg.reload(wait_until='networkidle'); await pg.wait_for_timeout(1300)
            sjekk('tilbake til Jakob: svarttrosten i ringen', (await tilstand(pg))['ringFugl'])
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== et eget bilde fra de timene det gikk an: slettes, tittelikonet igjen')
            eget = json.dumps({'eget': 'data:image/jpeg;base64,' + 'A' * 400})
            ctx, pg, js, ut = await side(b, lager(**{'hagefugler:profilbilde': eget, 'hagefugler:profilbilde@b1': eget, 'hagefugler:profilbilde@b2': json.dumps({'fugl': 'parus-major'}),
                                               'fuglekort:brukere': json.dumps([{'id': 'meg', 'navn': ''}, {'id': 'b1', 'navn': 'Emma'}, {'id': 'b2', 'navn': 'Ola'}])}))
            r = await pg.evaluate("[localStorage.getItem('hagefugler:profilbilde'), localStorage.getItem('hagefugler:profilbilde@b1'), localStorage.getItem('hagefugler:profilbilde@b2')]")
            sjekk('egne bilder slettet for alle brukerne, en valgt fugl står', r == [None, None, json.dumps({'fugl': 'parus-major'})], r)
            t = await tilstand(pg)
            sjekk('   ringen viser tittelikonet', not t['ring'] and t['tiSynlig'], t)
            await klikk(pg, '#openStats', 700)
            sjekk('   og Profil også', (await tilstand(pg))['hode'] == 'tittel')
            sjekk('ingen filvelger i appen', await pg.evaluate("!document.querySelector('input[type=file]')"))
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            if BILDER:
                ctx, pg, js, ut = await side(b, lager(**{'hagefugler:profilbilde': json.dumps({'fugl': 'parus-major'})}), mork=True)
                await klikk(pg, '#openStats', 700); await pg.screenshot(path=str(BILDER / 'pb_mork.png')); await ctx.close()
            await b.close()
    finally:
        srv.terminate()
    print('FEIL: ' + (', '.join(FEIL) if FEIL else 'ingen'))
    sys.exit(1 if FEIL else 0)

asyncio.run(main())
