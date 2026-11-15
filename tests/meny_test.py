"""The menu at the top right: Profil first (Min fugleliste on the Profil tab, also in the simple version and for
children), then Søk etter fugl, Livslisten, Om kortene, Slik virker appen, «Få kortene i postkassen» (opens
https://hagefugler.no/#bestill; not for the user type «Barn») and Innstillinger.
Run from the repo after python3 build.py:   python3 tests/meny_test.py [MAPPE_FOR_SKJERMBILDER]
"""
import asyncio, json, subprocess, sys, pathlib
from playwright.async_api import async_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent
BILDER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else None
URL = 'http://localhost:8794/'
FEIL = []
ALLE = ['Profil', 'Søk etter fugl', 'Livslisten', 'Om kortene', 'Slik virker appen', 'Få kortene i postkassen', 'Innstillinger']


def sjekk(navn, ok, info=''):
    print(('  OK   ' if ok else '  FEIL ') + navn + (f'  ({info})' if not ok and info != '' else ''))
    if not ok: FEIL.append(navn)


def bruker(**x):
    d = {'hagefugler:testmerke': '2026-09-30-pluss', 'fuglekort:intro': 'ferdig', 'hagefugler-oslo:hint': 'ok', 'fuglekort:deling': 'nei',
         'fuglekort:tittel:v2': '99', 'hagefugler:varsler-spurt': '1', 'fuglekort:fane': 'telling'}
    d.update(x); return d


async def side(b, lager):
    ctx = await b.new_context(viewport={'width': 390, 'height': 800}, device_scale_factor=2, has_touch=True, is_mobile=True, service_workers='block')
    await ctx.route('https://qfustbltxgbpwsntcrpd.supabase.co/**', lambda r: r.abort())
    await ctx.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.clear();"
                              + ''.join(f'localStorage.setItem({json.dumps(k)}, {json.dumps(v)});' for k, v in lager.items()) + '}'
                              + "window.__apnet = []; window.open = (u, t, f) => { window.__apnet.push([u, t, f]); return null; };")
    pg = await ctx.new_page(); js = []; pg.on('pageerror', lambda e: js.append(str(e)))
    await pg.goto(URL, wait_until='networkidle'); await pg.wait_for_timeout(1500)
    return ctx, pg, js


async def meny(pg):
    await pg.evaluate("document.querySelector('#openMeny').click()"); await pg.wait_for_timeout(400)
    return await pg.evaluate("[[...document.querySelectorAll('#meny [role=menuitem]')].filter(b => !b.hidden).map(b => b.querySelector('.mt').textContent), document.activeElement && document.activeElement.id]")


async def main():
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8794', '-d', str(ROT / 'docs')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        async with async_playwright() as pw:
            b = await pw.chromium.launch()
            for navn, lager, vent in (
                    ('vanlig bruker', bruker(), ALLE),
                    ('den enkle versjonen', bruker(**{'fuglekort:enkel': 'ja'}), ALLE),
                    ('barn', bruker(**{'fuglekort:brukere': json.dumps([{'id': 'meg', 'navn': ''}, {'id': 'b1', 'navn': 'Emma', 'type': 'barn'}]), 'fuglekort:bruker': 'b1'}),
                     [x for x in ALLE if x != 'Få kortene i postkassen'])):
                print(f'=== {navn}')
                ctx, pg, js = await side(b, lager)
                m, fokus = await meny(pg)
                sjekk('menyen: ' + ', '.join(m), m == vent, m)
                sjekk('   markøren står på Profil', fokus == 'openProfil', fokus)
                if BILDER and navn == 'vanlig bruker': await pg.screenshot(path=str(BILDER / 'meny.png'))
                await pg.evaluate("document.querySelector('#openProfil').click()"); await pg.wait_for_timeout(700)
                r = await pg.evaluate("[document.querySelector('#statsSheet').classList.contains('on'), document.querySelector('#faner [aria-selected=true]').textContent, document.querySelector('#meny').hidden]")
                sjekk('   Profil åpner Min fugleliste på fanen Profil (fra fanen Telling sist)', r == [True, 'Profil', True], r)
                await pg.evaluate("document.querySelector('#closeStats').click()"); await pg.wait_for_timeout(500)
                if 'Få kortene i postkassen' in vent:
                    await meny(pg)
                    await pg.evaluate("document.querySelector('#openPost').click()"); await pg.wait_for_timeout(400)
                    r = await pg.evaluate("[window.__apnet, document.querySelector('#meny').hidden]")
                    sjekk('   «Få kortene i postkassen» åpner hagefugler.no/#bestill i en ny fane', r == [[['https://hagefugler.no/#bestill', '_blank', 'noopener']], True], r)
                sjekk('   ingen JS-feil', not js, js); await ctx.close()
            await b.close()
    finally:
        srv.terminate()
    print('FEIL: ' + (', '.join(FEIL) if FEIL else 'ingen'))
    sys.exit(1 if FEIL else 0)

asyncio.run(main())
