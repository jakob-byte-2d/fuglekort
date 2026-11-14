"""The walk-through of the life list (registreringsmodusen): the choice before it starts («Livslisten – valgfritt»,
Start / Ikke nå; the first time too; «Endre i livslisten» on the back of a card starts it straight away); the mode
plain to see («Livslisten» in the strip, an orange frame round the screen); «SETT (FØR)» on the bird cards, in orange,
on the line of the printed SETT; the SETT box shows and ticks «seen before» only; the year on the date line; a tap on
a marked bird takes it off; a bird registered in the app; no «(FØR)» on the dyrekort; everything as before after Ferdig.

Run from the repo after python3 build.py (and python3 build.py --play ../fuglekort_nettside/app for the second part):
    python3 tests/forsett_test.py [../fuglekort_nettside] [MAPPE_FOR_SKJERMBILDER]
Without the website folder only the web version (docs/) is tested. Supabase is not reached (nothing is shared).
"""
import asyncio, io, json, subprocess, sys, time, pathlib
from urllib.parse import urlparse
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent
NETTSIDE = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 and sys.argv[1] else None
BILDER = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
FEIL = []
ORANSJE = (184, 74, 37)


def sjekk(navn, ok, info=''):
    print(('  OK   ' if ok else '  FEIL ') + navn + (f'  ({info})' if not ok and info != '' else ''))
    if not ok: FEIL.append(navn)


INIT = {'hagefugler:testmerke': '2026-09-30-pluss', 'fuglekort:intro': 'ferdig', 'hagefugler-oslo:hint': 'ok', 'fuglekort:deling': 'nei',
        'fuglekort:tittel:v2': '99', 'fuglekort:oppdrag': json.dumps({k: '2026-08-14' for k in ('forste', 'sok', 'arter3', 'tavle', 'dager2', 'kjop', 'arter5', 'dager3')}),
        'fuglekort:forsett:v1': json.dumps({'parus-major': {'svar': 'for', 'aar': 2015, 'ts': 1}}),
        'hagefugler-oslo:sett:v1': json.dumps({'turdus-merula': {'date': '2026-11-02', 'dager': ['2026-11-02', '2026-11-03'], 'ts': 1}}),
        'hagefugler:kjop:v1': json.dumps({'dyr-sciurus-vulgaris': {'pris': 12000, 'dato': '2026-10-01', 'ts': 1}}),
        'hagefugler:bonusvist:v1': json.dumps({'sciurus-vulgaris': {'ts': 1}}), 'hagefugler-oslo:kort': '0'}


def masker(bilde):
    """the printed black text (its core and its soft edge, the card image is scaled up), the orange and the red"""
    a = np.asarray(Image.open(io.BytesIO(bilde)).convert('RGB')).astype(int)
    lys = a @ [.299, .587, .114]
    gra = (a.max(axis=-1) - a.min(axis=-1)) < 70                  # the printed text is black; the orange and the red are not
    oransje = (abs(a[..., 0] - ORANSJE[0]) < 40) & (abs(a[..., 1] - ORANSJE[1]) < 40) & (abs(a[..., 2] - ORANSJE[2]) < 40)
    rod = (a[..., 0] > 200) & (a[..., 1] < 90) & (a[..., 2] < 90)
    return {'kjerne': (lys < 80) & gra, 'mork': (lys < 110) & gra, 'kant': (lys < 170) & gra, 'oransje': oransje, 'rod': rod}


def boks(m):
    ys, xs = np.nonzero(m)
    return (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None


async def kjor(b, navn, rot, url, egen, bredde, hoyde, alt=True):
    print(f'=== {navn}, {bredde} px: {url}')
    s = subprocess.Popen([sys.executable, '-m', 'http.server', str(urlparse(url).port), '--bind', '127.0.0.1'], cwd=rot, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        ctx = await b.new_context(viewport={'width': bredde, 'height': hoyde}, device_scale_factor=3, has_touch=True, is_mobile=True, service_workers='block')
        await ctx.route('https://qfustbltxgbpwsntcrpd.supabase.co/**', lambda r: r.abort())
        await ctx.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear();"
                                  + ''.join(f'localStorage.setItem({json.dumps(k)}, {json.dumps(v)});' for k, v in INIT.items()) + '}')
        kall, js = [], []
        ctx.on('request', lambda r: kall.append(r.url))
        pg = await ctx.new_page(); pg.on('pageerror', lambda e: js.append(str(e)))
        await pg.goto(url, wait_until='networkidle'); await pg.wait_for_timeout(1200)
        trykk = lambda sel, ms=600: _trykk(pg, sel, ms)
        topp = lambda js_: pg.evaluate(f"(() => {{ const el = document.querySelector('.card.is-top'); return {js_}; }})()")
        forsett = lambda: pg.evaluate("JSON.parse(localStorage.getItem('fuglekort:forsett:v1') || '{}')")
        fp = lambda: pg.evaluate("document.querySelector('#fpNavn').textContent")

        sjekk('«(FØR)» er skjult utenfor modusen', await topp("getComputedStyle(el.querySelector('.forord')).opacity") == '0')
        # the choice before the walk-through: optional, Start / Ikke nå
        await trykk('#openMeny', 300); await trykk('#openFor', 600)
        sjekk('valget før start: «Livslisten – valgfritt», Start og Ikke nå', await pg.evaluate("[document.querySelector('#dlgT').textContent, document.body.classList.contains('formodus'), [...document.querySelectorAll('#dlgKnapper .btn')].map(b => b.textContent), document.querySelector('#dlgTekst p').textContent === 'Merk fuglene du har sett før du begynte med appen, gjerne med år.', document.querySelector('#dlgTekst').textContent.includes('allerede 1 art')]")
              == ['Livslisten – valgfritt', False, ['Start', 'Ikke nå'], True, True])
        if alt:
            await trykk('#dlgKnapper [data-k="1"]', 500)
            sjekk('«Ikke nå» starter ikke modusen', await pg.evaluate("[document.body.classList.contains('formodus'), !!document.querySelector('.dlg.on')]") == [False, False])
            await trykk('#openMeny', 300); await trykk('#openFor', 600)
        await trykk('#dlgKnapper .btn.pri', 1000)
        sjekk('«Livslisten» i stripa og oransje ramme rundt skjermen', await pg.evaluate("[document.querySelector('#forbar .fb-navn').textContent, getComputedStyle(document.querySelector('#forbar .fb-navn')).color, getComputedStyle(document.body, '::after').borderTopColor, getComputedStyle(document.body, '::after').opacity, document.querySelector('#forbar .fb-sub').textContent]")
              == ['Livslisten', 'rgb(184, 74, 37)', 'rgb(184, 74, 37)', '1', '1 art sett før · Ferdig avslutter'])
        sjekk('fonten Barlow SC Sett er lastet fra egen mappe', await pg.evaluate("document.fonts.check(\"700 20px 'Barlow SC Sett'\")")
              and any(urlparse(k).netloc == egen and k.endswith('/fonts/barlow-semi-condensed-700-sett.woff') for k in kall))
        sjekk('modusfargen på stripa og panelet', await pg.evaluate("[getComputedStyle(document.querySelector('#forbar')).borderTopColor, getComputedStyle(document.querySelector('#forpanel')).borderTopColor]")
              == ['rgb(184, 74, 37)'] * 2)
        sjekk('hjelpeteksten', await pg.evaluate("document.querySelector('#fpHjelp').textContent") == 'Kryss av i ruta eller trykk «Sett før» · sveip for å hoppe over')

        # Kjøttmeis, seen before 2015: «SETT (FØR)», the pencil tick, the year on the line, no «× n»
        sjekk('Kjøttmeis øverst', await fp() == 'Kjøttmeis', await fp())
        sjekk('«(FØR)» vises i modusen', await topp("getComputedStyle(el.querySelector('.forord')).opacity") == '1')
        sjekk('ruta har blyanthaken og året står på linja', await topp("[el.classList.contains('for'), el.classList.contains('seen'), el.querySelector('.hand').textContent, getComputedStyle(el.querySelector('.antall')).display]")
              == [True, False, '2015', 'none'])

        # the line: the transparent SETT, drawn in red, lies on the printed one; «(FØR)» between SETT and «Dato:»
        await pg.add_style_tag(content='.float.stopp{animation:none}')             # the deck bobs; still while measuring
        await pg.evaluate("document.querySelector('.float').classList.add('stopp')"); await pg.wait_for_timeout(400)
        r = await topp("(() => { const r = el.querySelector('.front').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
        klipp = {'x': r[0] + r[2] * .150, 'y': r[1] + r[3] * .872, 'width': r[2] * .33, 'height': r[3] * .055}
        m = masker(await pg.screenshot(clip=klipp))
        await topp("el.querySelector('.fo-sett').style.fill = '#ff0000'")
        rod = masker(await pg.screenshot(clip=klipp))['rod']
        await topp("el.querySelector('.fo-sett').style.fill = ''")
        w = rod.shape[1]; kol = lambda x: int(w * (x - 0.150) / 0.33)        # a column at x (share of the card width)
        sett = {k: v.copy() for k, v in m.items()}
        for v in sett.values(): v[:, kol(0.29):] = False                     # the printed SETT ends at about 0.27 of the card
        pa = (rod & sett['kant']).sum() / max(1, rod.sum())                   # the red lies on the printed SETT
        dekker = (sett['kjerne'] & rod).sum() / max(1, sett['kjerne'].sum())  # and covers it
        br, bt = boks(rod), boks(sett['mork'])
        avvik = max(abs(int(x) - int(y)) for x, y in zip(br, bt)) if br and bt else 99
        tol = max(2, round(r[2] * 3 * 0.003))                                   # 0.3 % of the card width, in screen pixels
        print(f'    SETT oppå SETT: {pa:.3f} av det røde på det trykte, {dekker:.3f} av det trykte dekket, kantene {avvik} px fra hverandre (grense {tol})')
        sjekk('den usynlige SETT ligger oppå den trykte', pa >= 0.95 and dekker >= 0.9 and avvik <= tol, (round(pa, 3), round(dekker, 3), avvik))
        ys, xs = np.nonzero(m['oransje']); ds = np.nonzero(m['mork'][:, kol(0.42):])[1]
        sjekk('«(FØR)» står mellom SETT og «Dato:»', len(xs) > 50 and xs.min() > bt[2] + 2 and len(ds) and xs.max() < kol(0.42) + ds.min() - 4,
              (len(xs), xs.min() if len(xs) else None, xs.max() if len(xs) else None))
        hoyde_for = ys.max() - ys.min() + 1 if len(ys) else 0
        sjekk('«(FØR)» har samme høyde som SETT (parentesene går litt over og under)', len(ys) and 1.0 <= hoyde_for / (bt[3] - bt[1] + 1) <= 1.45, hoyde_for)
        midt_for = (ys.min() + ys.max()) / 2 if len(ys) else 0
        sjekk('«(FØR)» står på linja til SETT (samme midt)', len(ys) and abs(midt_for - (bt[1] + bt[3]) / 2) <= tol, (midt_for, (bt[1] + bt[3]) / 2))
        await pg.evaluate("document.querySelector('.float').classList.remove('stopp')")
        if BILDER:
            await pg.screenshot(path=str(BILDER / f'forsett_{navn}_{bredde}.png'))

        if alt:
            # a tap in the box on a marked bird takes it off, and it stays
            await trykk('.card.is-top [data-act="toggle"]', 900)
            sjekk('trykk i ruta på en avkrysset fugl tar den ut', 'parus-major' not in await forsett() and await fp() == 'Kjøttmeis'
                  and await topp("el.classList.contains('for')") is False and await topp("el.querySelector('.hand').textContent") == '')
            # a year, then a tap in the box: marked with the year, the tick drawn, the next bird after a moment
            await pg.select_option('#fpAar', '2010')
            await trykk('.card.is-top [data-act="toggle"]', 120)
            sjekk('trykk i ruta krysser av for sett før, med året', (await forsett()).get('parus-major', {}).get('aar') == 2010
                  and await topp("[el.classList.contains('for'), el.classList.contains('ny-for'), el.querySelector('.hand').textContent]") == [True, True, '2010'])
            await pg.wait_for_timeout(300)
            sjekk('blir på kortet en stund (haken tegnes)', await fp() == 'Kjøttmeis')
            await pg.wait_for_timeout(800)
            sjekk('så kommer neste fugl', await fp() == 'Blåmeis', await fp())
            # Blåmeis without a year: the line is empty in the mode
            await trykk('.card.is-top [data-act="toggle"]', 1300)
            sjekk('uten år: avkrysset og tom linje', 'cyanistes-caeruleus' in await forsett() and (await forsett())['cyanistes-caeruleus']['aar'] is None and await fp() == 'Svarttrost')
            await pg.keyboard.press('ArrowLeft'); await pg.wait_for_timeout(800)
            sjekk('Blåmeis: haken, tom linje i modusen', await topp("[el.classList.contains('for'), el.querySelector('.hand').textContent]") == [True, ''])
            await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(800)
            # Svarttrost, registered in the app: in the mode only «seen before» (empty now), the days are back after Ferdig
            sjekk('fugl i appen: ruta viser bare sett før', await topp("[el.classList.contains('seen'), el.classList.contains('for'), el.querySelector('.hand').textContent, el.querySelector('[data-act=toggle]').getAttribute('aria-pressed')]")
                  == [False, False, '', 'false'] and '2 dager i appen' in await pg.evaluate("document.querySelector('#fpInfo').textContent"))
            await trykk('#fpSett', 120)
            sjekk('«Sett før» på en fugl i appen gir blyanthaken', await topp("[el.classList.contains('for'), el.classList.contains('seen')]") == [True, False] and 'turdus-merula' in await forsett())
            await pg.wait_for_timeout(1000)
            # the dyrekort: no «(FØR)»
            kort = {}
            for _ in range(32):
                for lbl, har in await pg.evaluate("[...document.querySelectorAll('.card')].map(el => [el.getAttribute('aria-label'), !!el.querySelector('.forord')])"):
                    kort[lbl] = har
                await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(120)
            dyr = {k: v for k, v in kort.items() if k.startswith('Dyrekort')}
            sjekk('ingen «(FØR)» på dyrekortene, men på alle fuglekortene', dyr and not any(dyr.values()) and all(v for k, v in kort.items() if not k.startswith('Dyrekort')), (len(kort), dyr))
            # Ferdig: everything as before
            await trykk('#fbFerdig', 700); await trykk('#dlgKnapper .btn.pri', 900)
            await pg.keyboard.press('Home'); await pg.wait_for_timeout(300)
            for _ in range(40):
                if await pg.evaluate("document.querySelector('.card.is-top').getAttribute('aria-label')") == 'Kort 001: Kjøttmeis': break
                await pg.keyboard.press('ArrowLeft'); await pg.wait_for_timeout(150)
            await pg.wait_for_timeout(500)
            sjekk('etter Ferdig: «(FØR)» borte, Kjøttmeis med 2010', await topp("[getComputedStyle(el.querySelector('.forord')).opacity, el.querySelector('.hand').textContent, el.classList.contains('for')]") == ['0', '2010', True])
            sjekk('etter Ferdig: rammen er borte', await pg.evaluate("getComputedStyle(document.body, '::after').opacity") == '0')
            # «Endre i livslisten» on the back of the card: straight into the mode, no question
            await trykk('.card.is-top [data-act="forsett"]', 900)
            sjekk('«Endre i livslisten» starter modusen direkte', await pg.evaluate("[document.body.classList.contains('formodus'), !!document.querySelector('.dlg.on')]") == [True, False])
            await trykk('#fbFerdig', 700); await trykk('#dlgKnapper .btn.pri', 700)
            await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(700)
            sjekk('etter Ferdig: Blåmeis uten år viser «før appen»', await topp("el.querySelector('.hand').textContent") == 'før appen')
            await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(700)
            sjekk('etter Ferdig: Svarttrost med den blå haken, datoen og × 2', await topp("[el.classList.contains('seen'), el.classList.contains('for'), el.querySelector('.antall').textContent, getComputedStyle(el.querySelector('.antall')).display !== 'none', el.querySelector('.hand').textContent.length > 0]")
                  == [True, False, '× 2', True, True])
            # outside the mode, a tap on SETT registers for today again
            await trykk('.card.is-top [data-act="toggle"]', 900)
            sjekk('utenfor modusen registrerer SETT som før', await pg.evaluate("JSON.parse(localStorage.getItem('hagefugler-oslo:sett:v1'))['turdus-merula'].dager.length") == 3)
        if alt:
            # the first time: the introduction, then the choice; Ikke nå goes to the cards
            ctx2 = await b.new_context(viewport={'width': bredde, 'height': hoyde}, device_scale_factor=1, has_touch=True, is_mobile=True, service_workers='block')
            await ctx2.route('https://qfustbltxgbpwsntcrpd.supabase.co/**', lambda r: r.abort())
            await ctx2.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear(); localStorage.setItem('hagefugler:testmerke', '2026-09-30-pluss'); }")
            p2 = await ctx2.new_page(); p2.on('pageerror', lambda e: js.append(str(e)))
            await p2.goto(url, wait_until='networkidle'); await p2.wait_for_timeout(1200)
            sistetekst = ''
            for _ in range(20):
                t = await p2.evaluate("document.querySelector('.dlg.on') ? document.querySelector('#dlgT').textContent : ''")
                if t == 'Ikke dele?':                                # the name step: not sharing
                    await p2.evaluate("document.querySelector('#dlgKnapper .btn.pri').click()"); await p2.wait_for_timeout(700); continue
                if t: break
                sistetekst = await p2.evaluate("(document.querySelector('[data-s=oppdrag] > p') || {}).textContent || ''") or sistetekst
                ikke = await p2.evaluate("(() => { const b = document.querySelector('#inIkke'); return !!b && !b.hidden && b.getBoundingClientRect().width > 0; })()")
                await p2.evaluate("document.querySelector(%s).click()" % json.dumps('#inIkke' if ikke else '#introNeste')); await p2.wait_for_timeout(700)
            sjekk('første gang: «Kom i gang» sier bare «Fullfør oppdragene og få frø.»', sistetekst == 'Fullfør oppdragene og få frø.', sistetekst)
            sjekk('første gang: valget kommer etter introduksjonen', await p2.evaluate("[document.querySelector('.dlg.on #dlgT') && document.querySelector('#dlgT').textContent, document.body.classList.contains('formodus')]") == ['Livslisten – valgfritt', False])
            await p2.evaluate("document.querySelector('#dlgKnapper [data-k=\"1\"]').click()"); await p2.wait_for_timeout(600)
            sjekk('første gang: «Ikke nå» går til kortene', await p2.evaluate("[document.body.classList.contains('formodus'), !!document.querySelector('.dlg.on'), !!document.querySelector('.card.is-top')]") == [False, False, True])
            await ctx2.close()
        sjekk('ingen kall utenom eget nettsted (og Supabase, som er stengt)', {urlparse(k).netloc for k in kall if urlparse(k).scheme in ('http', 'https')} <= {egen, 'qfustbltxgbpwsntcrpd.supabase.co'})
        sjekk('ingen JS-feil', not js, js)
        await ctx.close()
    finally:
        s.terminate()


async def _trykk(pg, sel, ms):
    await pg.evaluate(f"document.querySelector({json.dumps(sel)}).click()"); await pg.wait_for_timeout(ms)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        await kjor(b, 'nettversjonen', ROT / 'docs', 'http://localhost:8781/', 'localhost:8781', 390, 760)
        await kjor(b, 'nettversjonen', ROT / 'docs', 'http://localhost:8782/', 'localhost:8782', 810, 1080, alt=False)    # a tablet: the line only
        if NETTSIDE:
            await kjor(b, 'play', NETTSIDE, 'http://localhost:8783/app/', 'localhost:8783', 390, 760)
        await b.close()
    print('\nFEIL:', FEIL or 'ingen')
    sys.exit(1 if FEIL else 0)

asyncio.run(main())
