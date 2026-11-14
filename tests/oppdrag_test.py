"""The task «Gjennomfør en hagefugltelling»: first in the list (and on «Kom i gang» in the introduction), done by a
finished count of at least an hour (not by one of 30 minutes), 3 000 seeds, the button «Tell» opens the count; the
strip «Neste oppdrag» and the introduction's text show it first from 1 January to 15 February only (the small tasks
first the rest of the year); BirdLife Norge named on the count pages; the help card «Om kortene» says «Hagefugler».

Run from the repo after python3 build.py:
    python3 tests/oppdrag_test.py [MAPPE_FOR_SKJERMBILDER]
The web version (docs/) is served; Supabase is not reached (nothing is shared). The date is set with Playwright's clock.
"""
import asyncio, json, subprocess, sys, time, pathlib
from datetime import datetime
from playwright.async_api import async_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent
BILDER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else None
URL = 'http://localhost:8796/'
FEIL = []
BIRDLIFE = 'Hagefugltellingen arrangeres av BirdLife Norge hvert år siste helga i januar.'


def sjekk(navn, ok, info=''):
    print(('  OK   ' if ok else '  FEIL ') + navn + (f'  ({info})' if not ok and info != '' else ''))
    if not ok: FEIL.append(navn)


def ms(d):
    return int(d.timestamp() * 1000)


def init(dato, tellinger=None, intro=True, sett=None):
    """localStorage for a user on this date: optionally finished counts [(start, minutes)] and seen birds"""
    x = {'hagefugler:testmerke': '2026-09-30-pluss'}
    if intro: x.update({'fuglekort:intro': 'ferdig', 'hagefugler-oslo:hint': 'ok', 'fuglekort:deling': 'nei', 'fuglekort:tittel:v2': '99'})   # else: as the very first time
    if tellinger:
        x['hagefugler:tellinger:v1'] = json.dumps({f't{ms(s)}': {'start': ms(s), 'slutt': ms(s) + m * 60000, 'omrade': '', 'arter': {'parus-major': 3}, 'ts': ms(s)} for s, m in tellinger})
    if sett: x['hagefugler-oslo:sett:v1'] = json.dumps(sett)
    return x


async def side(b, dato, lager, intro=True):
    ctx = await b.new_context(viewport={'width': 390, 'height': 800}, device_scale_factor=2, has_touch=True, is_mobile=True, service_workers='block')
    await ctx.route('https://qfustbltxgbpwsntcrpd.supabase.co/**', lambda r: r.abort())
    await ctx.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear();"
                              + ''.join(f'localStorage.setItem({json.dumps(k)}, {json.dumps(v)});' for k, v in lager.items()) + '}')
    pg = await ctx.new_page(); js = []; pg.on('pageerror', lambda e: js.append(str(e)))
    await pg.clock.set_fixed_time(dato)
    await pg.goto(URL, wait_until='networkidle'); await pg.wait_for_timeout(1200)
    lukk = "for (const id of ['#fest', '#bfest']) { const e = document.querySelector(id); if (e && e.classList.contains('on')) e.click(); } const v = document.querySelector('#festVent'); if (v && !v.hidden) v.click();"
    for _ in range(8):
        await pg.evaluate(lukk); await pg.wait_for_timeout(200)
    return ctx, pg, js


async def stripa(pg):
    return await pg.evaluate("(() => { const s = document.querySelector('#oppdragStripe'); return s.hidden ? null : s.querySelector('#osTekst b').textContent; })()")


async def lista(pg):
    await pg.evaluate("document.querySelector('#osApne') ? document.querySelector('#osApne').click() : null"); await pg.wait_for_timeout(700)
    if not await pg.evaluate("!!document.querySelector('#oppdragSek')"):
        await pg.evaluate("document.querySelector('#openStats').click()"); await pg.wait_for_timeout(500)
        await pg.evaluate("document.querySelector('#fane-merker').click()"); await pg.wait_for_timeout(700)
    return await pg.evaluate("""[...document.querySelectorAll('#oppdragSek ul.oppdrag li')].map(li => ({ t: li.querySelector('.o-t').firstChild.textContent,
        ok: li.classList.contains('ok'), under: (li.querySelector('.o-t small') || {}).textContent || '', knapp: (li.querySelector('.o-gaa') || {}).textContent || '',
        fro: li.querySelector('.o-fro').textContent.trim() }))""")


async def main():
    s = subprocess.Popen([sys.executable, '-m', 'http.server', '8796', '--bind', '127.0.0.1'], cwd=ROT / 'docs', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        async with async_playwright() as p:
            b = await p.chromium.launch()
            nov, jan, feb16 = datetime(2026, 11, 14, 12), datetime(2027, 1, 20, 12), datetime(2027, 2, 16, 12)

            print('=== ny bruker i november: lista, stripa, knappen «Tell»')
            ctx, pg, js = await side(b, nov, init(nov))
            sjekk('stripa i november: de små oppdragene først', await stripa(pg) == 'Registrer din første fugl', await stripa(pg))
            ls = await lista(pg)
            sjekk('tellingen står øverst i lista', ls and ls[0]['t'] == 'Gjennomfør en hagefugltelling' and not ls[0]['ok'], ls[:1])
            sjekk('med forklaring, knappen «Tell» og 3 000 frø', ls and ls[0]['under'] == 'Tell fuglene i hagen i minst én time, og send tallene til Hagefugltellingen på Fuglevennen.no.'
                  and ls[0]['knapp'] == 'Tell' and ls[0]['fro'].replace(' ', ' ') == '3 000', ls[:1])
            sjekk('de andre oppdragene som før', [o['t'] for o in ls[1:4]] == ['Registrer din første fugl', 'Finn en fugl med søket', 'Registrer tre ulike arter'], [o['t'] for o in ls])
            if BILDER: await pg.screenshot(path=str(BILDER / 'oppdrag_liste.png'))
            await pg.evaluate("document.querySelector('[data-oppdrag-gaa=telling]').click()"); await pg.wait_for_timeout(700)
            st = await pg.evaluate("(() => { const s = document.querySelector('#startSheet'); return [!!s && s.classList.contains('on') || getComputedStyle(s).visibility === 'visible', document.querySelector('#startTitle').textContent, (document.querySelector('.tl-birdlife') || {}).textContent || ''] })()")
            sjekk('«Tell» åpner startsiden for tellingen, med BirdLife Norge', st[0] and st[1] == 'Hagefugltelling' and st[2].startswith(BIRDLIFE), st)
            if BILDER: await pg.screenshot(path=str(BILDER / 'oppdrag_start.png'))
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== januar og 16. februar: stripa')
            ctx, pg, js = await side(b, jan, init(jan))
            sjekk('stripa 20. januar: tellingen først', await stripa(pg) == 'Gjennomfør en hagefugltelling', await stripa(pg))
            if BILDER: await pg.screenshot(path=str(BILDER / 'oppdrag_januar.png'))
            await ctx.close()
            ctx, pg, js = await side(b, feb16, init(feb16))
            sjekk('stripa 16. februar: de små oppdragene igjen', await stripa(pg) == 'Registrer din første fugl', await stripa(pg))
            await ctx.close()

            print('=== tellinger: 30 minutter og én time')
            ctx, pg, js = await side(b, nov, init(nov, tellinger=[(datetime(2026, 11, 1, 10), 30)]))
            ls = await lista(pg)
            sjekk('en telling på 30 minutter fullfører ikke oppdraget', ls and not ls[0]['ok'])
            await ctx.close()
            ctx, pg, js = await side(b, nov, init(nov, tellinger=[(datetime(2026, 11, 1, 10), 61)]))
            await pg.wait_for_timeout(1500)
            logg = await pg.evaluate("JSON.parse(localStorage.getItem('fuglekort:oppdrag') || '{}')")
            ls = await lista(pg)
            sjekk('en telling på én time fullfører oppdraget (og det lagres)', ls and ls[0]['ok'] and 'telling' in logg, (ls[:1], logg))
            sjekk('stripa går videre til neste oppdrag', await stripa(pg) in ('Registrer din første fugl', 'Registrer tre ulike arter', 'Finn en fugl med søket'), await stripa(pg))
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== første gang: introduksjonen')
            for dato, vent in ((nov, 'Det første er å registrere din første fugl'), (jan, 'Neste er: gjennomfør en hagefugltelling')):
                ctx, pg, js = await side(b, dato, init(dato, intro=False), intro=False)
                tekst, tre = '', []
                for _ in range(20):
                    t = await pg.evaluate("document.querySelector('.dlg.on') ? document.querySelector('#dlgT').textContent : ''")
                    if t == 'Ikke dele?':
                        await pg.evaluate("document.querySelector('#dlgKnapper .btn.pri').click()"); await pg.wait_for_timeout(600); continue
                    if t: break
                    x = await pg.evaluate("(() => { const s = document.querySelector('[data-s=oppdrag]'); return s ? [s.querySelector(':scope > p').textContent, [...s.querySelectorAll('.intro-oppdrag li')].map(li => li.textContent.trim())] : null; })()")
                    if x: tekst, tre = x
                    if x: break
                    ikke = await pg.evaluate("(() => { const b = document.querySelector('#inIkke'); return !!b && !b.hidden && b.getBoundingClientRect().width > 0; })()")
                    await pg.evaluate("document.querySelector(%s).click()" % json.dumps('#inIkke' if ikke else '#introNeste')); await pg.wait_for_timeout(600)
                sjekk(f'introduksjonen {dato:%d.%m}: «{vent}»', vent in tekst, tekst)
                sjekk(f'introduksjonen {dato:%d.%m}: tellingen først av de tre', tre and tre[0].startswith('Gjennomfør en hagefugltelling'), tre)
                sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== oppsummeringen og fanen Telling, og «Om kortene»')
            ctx, pg, js = await side(b, nov, init(nov, tellinger=[(datetime(2026, 11, 1, 10), 65)]))
            await pg.evaluate("document.querySelector('#openStats').click()"); await pg.wait_for_timeout(500)
            await pg.evaluate("document.querySelector('#fane-telling').click()"); await pg.wait_for_timeout(700)
            sjekk('fanen Telling nevner BirdLife Norge', BIRDLIFE in await pg.evaluate("document.querySelector('#statsSheet, .sheet.stats.on').textContent"))
            await pg.evaluate("document.querySelector('[data-tid]').click()"); await pg.wait_for_timeout(700)
            sjekk('oppsummeringen nevner BirdLife Norge', BIRDLIFE in await pg.evaluate("document.querySelector('#sumBody').textContent"))
            w = await pg.evaluate("fetch('cards/000a.webp').then(r => r.blob()).then(b => b.size)")
            sjekk('«Om kortene» er det nye kortet med «Hagefugler»', w == (ROT / 'docs/cards/000a.webp').stat().st_size == 108444, w)
            sjekk('ingen JS-feil', not js, js); await ctx.close()
            await b.close()
    finally:
        s.terminate()
    print('\nFEIL:', FEIL or 'ingen')
    sys.exit(1 if FEIL else 0)

asyncio.run(main())
