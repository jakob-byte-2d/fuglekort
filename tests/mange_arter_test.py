"""«Mange nye arter i dag»: 10 nye arter med SETT samme dag (ikke fra en telling) gir én gang om dagen en beskjed om at
fugler sett før appen hører hjemme i livslisten, med «Flytt dem til livslisten» (dagens nye blir «sett før», og dagens
registrering og frøene for dem tas bort) og «Jeg har sett dem i dag». En art som var registrert før, teller ikke.
Kjør fra repoet etter python3 build.py:   python3 tests/mange_arter_test.py [MAPPE_FOR_SKJERMBILDER]
"""
import asyncio, json, subprocess, sys, pathlib
from datetime import date, timedelta
from playwright.async_api import async_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent
BILDER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else None
URL = 'http://localhost:8787/'
FEIL = []
IGAR = (date.today() - timedelta(days=1)).isoformat()


def sjekk(navn, ok, info=''):
    print(('  OK   ' if ok else '  FEIL ') + navn + (f'  ({info})' if not ok and info != '' else ''))
    if not ok: FEIL.append(navn)


def lager(**x):
    d = {'hagefugler:testmerke': '2026-09-30-pluss', 'fuglekort:intro': 'ferdig', 'hagefugler-oslo:hint': 'ok', 'fuglekort:deling': 'nei',
         'fuglekort:tittel:v2': '99', 'hagefugler:varsler-spurt': '1', 'hagefugler-oslo:kort': '0',
         'fuglekort:oppdrag': json.dumps({k: '2026-08-14' for k in ('forste', 'sok', 'arter3', 'tavle', 'dager2', 'kjop', 'arter5', 'dager3', 'telling', 'livsliste')}),
         'hagefugler-oslo:sett:v1': json.dumps({'parus-major': {'date': IGAR, 'dager': [IGAR], 'ts': 1}})}
    d.update(x); return d


LUKK = "for (const id of ['#fest', '#bfest']) { const e = document.querySelector(id); if (e && e.classList.contains('on')) e.click(); } const v = document.querySelector('#festVent'); if (v && !v.hidden) v.click();"


async def side(b, ls):
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True, is_mobile=True, service_workers='block')
    await ctx.route('https://qfustbltxgbpwsntcrpd.supabase.co/**', lambda r: r.abort())
    await ctx.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear();"
                              + ''.join(f'localStorage.setItem({json.dumps(k)}, {json.dumps(v)});' for k, v in ls.items()) + '}')
    pg = await ctx.new_page(); js = []; pg.on('pageerror', lambda e: js.append(str(e)))
    await pg.goto(URL, wait_until='networkidle'); await pg.wait_for_timeout(1200)
    return ctx, pg, js


async def dlg(pg):
    return await pg.evaluate("""(() => { const d = document.querySelector('#dlg'); return { apen: !d.hidden && d.classList.contains('on'), tittel: d.querySelector('#dlgT').textContent,
      tekst: d.querySelector('#dlgTekst').textContent.replace(/\\s+/g, ' ').trim(), knapper: [...d.querySelectorAll('#dlgKnapper .btn')].map(b => b.textContent) }; })()""")


async def registrer(pg, n):
    """SETT on the card on top, then the next card; n times. The dialog, if it comes, is left open"""
    for _ in range(n):
        await pg.evaluate(LUKK)
        await pg.evaluate("document.querySelector('.card.is-top [data-act=\"toggle\"]').click()"); await pg.wait_for_timeout(350)
        for _ in range(6):
            await pg.evaluate(LUKK); await pg.wait_for_timeout(120)
        if (await dlg(pg))['apen']: return
        await pg.evaluate("document.body.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }))"); await pg.wait_for_timeout(450)


async def data(pg):
    return await pg.evaluate("[JSON.parse(localStorage.getItem('hagefugler-oslo:sett:v1') || '{}'), JSON.parse(localStorage.getItem('fuglekort:forsett:v1') || '{}')]")


async def vent_dlg(pg, ms=4000):
    for _ in range(ms // 250):
        await pg.evaluate(LUKK)
        d = await dlg(pg)
        if d['apen']: return d
        await pg.wait_for_timeout(250)
    return await dlg(pg)


async def main():
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8787', '-d', str(ROT / 'docs')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        async with async_playwright() as pw:
            b = await pw.chromium.launch()

            print('=== 10 nye arter i dag (kjøttmeis var registrert i går): flytt dem til livslisten')
            ctx, pg, js = await side(b, lager(**{'fuglekort:deling': 'ja'}))
            await registrer(pg, 10)                          # kjøttmeis (not new) + 9 new
            await pg.wait_for_timeout(1500)
            d = await dlg(pg)
            sjekk('9 nye (kjøttmeis var registrert før): ingen beskjed', not d['apen'], d)
            await registrer(pg, 1)
            d = await vent_dlg(pg)
            sett, fs = await data(pg)
            nye = [k for k, v in sett.items() if v.get('dager') == [date.today().isoformat()]]
            sjekk('den 10. nye arten: «Mange nye arter i dag»', d['apen'] and d['tittel'] == 'Mange nye arter i dag' and 'Du har registrert 10 nye arter i dag.' in d['tekst'], d)
            sjekk('   forklarer livslisten, og knappene Flytt dem til livslisten / Jeg har sett dem i dag',
                  'hører hjemme i livslisten' in d['tekst'] and 'De gir ingen frø der' in d['tekst'] and d['knapper'] == ['Flytt dem til livslisten', 'Jeg har sett dem i dag'], d)
            sjekk('   deler: sier at uvanlig mange arter gir merking og bort fra den åpne ledertavla', 'tatt bort fra den åpne ledertavla' in d['tekst'], d['tekst'])
            sjekk('   navnene på de 10 står i beskjeden', len(nye) == 10 and 'Kjøttmeis' not in d['tekst'], [len(nye), d['tekst'][-200:]])
            if BILDER: await pg.screenshot(path=str(BILDER / 'mange_arter.png'))
            await pg.evaluate("[...document.querySelectorAll('#dlgKnapper .btn')].find(b => b.textContent === 'Flytt dem til livslisten').click()"); await pg.wait_for_timeout(700)
            d = await dlg(pg)
            sett2, fs2 = await data(pg)
            sjekk('flyttet: «Flyttet til livslisten», 10 arter', d['apen'] and d['tittel'] == 'Flyttet til livslisten' and d['tekst'].startswith('10 arter står nå som sett før'), d)
            sjekk('   de 10 er ikke lenger registrert, kjøttmeis står', all(k not in sett2 for k in nye) and 'parus-major' in sett2, list(sett2))
            sjekk('   de 10 står som «sett før» uten år', all(fs2.get(k, {}).get('svar') == 'for' and fs2[k].get('aar') is None for k in nye), fs2)
            if BILDER: await pg.screenshot(path=str(BILDER / 'mange_arter_flyttet.png'))
            await pg.evaluate("document.querySelector('#dlgKnapper .btn').click()"); await pg.wait_for_timeout(400)
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== «Jeg har sett dem i dag», og bare én gang om dagen')
            ctx, pg, js = await side(b, lager())
            await registrer(pg, 11)
            d = await vent_dlg(pg)
            sjekk('beskjeden kommer, uten setningen om ledertavla (deler ikke)', d['apen'] and 'ledertavla' not in d['tekst'], d)
            await pg.evaluate("[...document.querySelectorAll('#dlgKnapper .btn')].find(b => b.textContent === 'Jeg har sett dem i dag').click()"); await pg.wait_for_timeout(500)
            sett, fs = await data(pg)
            sjekk('«Jeg har sett dem i dag»: registreringene står', len([k for k, v in sett.items() if v.get('dager') == [date.today().isoformat()]]) == 10 and not fs, [len(sett), fs])
            await pg.evaluate("document.body.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }))"); await pg.wait_for_timeout(400)
            await registrer(pg, 3); await pg.wait_for_timeout(1500)
            sjekk('tre til samme dag: ingen ny beskjed', not (await dlg(pg))['apen'])
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== den enkle versjonen')
            ctx, pg, js = await side(b, lager(**{'fuglekort:enkel': 'ja'}))
            await registrer(pg, 11)
            d = await vent_dlg(pg)
            sjekk('beskjeden uten frø: «Der kommer de med på listen din.»', d['apen'] and 'Der kommer de med på listen din.' in d['tekst'] and 'frø' not in d['tekst'], d)
            sjekk('ingen JS-feil', not js, js); await ctx.close()
            await b.close()
    finally:
        srv.terminate()
    print('FEIL: ' + (', '.join(FEIL) if FEIL else 'ingen'))
    sys.exit(1 if FEIL else 0)

asyncio.run(main())
