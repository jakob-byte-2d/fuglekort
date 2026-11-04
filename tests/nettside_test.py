"""fuglekort.no: the front page (the 3D box and the five cards) and the privacy page, on a phone and a PC. No calls to
other sites, no missing files, no script errors, no sideways scrolling; the links to the app, the privacy page and
assetlinks.json. Screenshots in the scratch folder given as the second argument (optional).

    python3 tests/nettside_test.py ../fuglekort_nettside [MAPPE_FOR_SKJERMBILDER]
"""
import asyncio, json, subprocess, sys, time, pathlib
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent
NETTSIDE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROT.parent / 'fuglekort_nettside').resolve()
BILDER = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
EGEN = 'localhost:8767'
FEIL = []


def sjekk(navn, ok, info=''):
    print(('  OK   ' if ok else '  FEIL ') + navn + (f'  ({info})' if not ok and info != '' else ''))
    if not ok: FEIL.append(navn)


async def side(b, url, bredde, navn):
    ctx = await b.new_context(viewport={'width': bredde, 'height': 900}, device_scale_factor=1, is_mobile=bredde < 600, has_touch=bredde < 600)
    kall, mangler, js = [], [], []
    ctx.on('request', lambda r: kall.append(r.url))
    ctx.on('response', lambda r: mangler.append((r.status, r.url)) if r.status >= 400 else None)
    pg = await ctx.new_page(); pg.on('pageerror', lambda e: js.append(str(e)))
    await pg.goto(url, wait_until='networkidle'); await pg.wait_for_timeout(800)
    return ctx, pg, kall, mangler, js


async def main():
    s = subprocess.Popen([sys.executable, '-m', 'http.server', '8767', '--bind', '127.0.0.1'], cwd=NETTSIDE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        async with async_playwright() as p:
            b = await p.chromium.launch()
            for bredde in (390, 1280):
                print(f'=== forsiden, {bredde} px')
                ctx, pg, kall, mangler, js = await side(b, f'http://{EGEN}/', bredde, 'forside')
                sjekk('fem kort i galleriet', await pg.evaluate("document.querySelectorAll('#card-rail .card-tile img').length") == 5)
                await pg.click('[data-edition="illustrations"]'); await pg.wait_for_timeout(500)
                sjekk('illustrasjonene', 'illustrations' in await pg.evaluate("document.querySelector('#card-rail img').src"))
                await pg.click('#explore'); await pg.wait_for_timeout(2600)
                sjekk('esken åpnes', await pg.evaluate("document.querySelector('fuglekort-box').opened === true"))
                await pg.click('#card-rail .card-tile'); await pg.wait_for_timeout(500)
                sjekk('kortvisningen', await pg.evaluate("document.querySelector('#viewer').open && document.querySelector('#large-card').complete"))
                await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
                sjekk('ingen sidelengs rulling', await pg.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), await pg.evaluate("[document.documentElement.scrollWidth, innerWidth]"))
                lenker = await pg.evaluate("[...document.querySelectorAll('a')].map(a => a.getAttribute('href'))")
                sjekk('lenker til appen, personvern og kontakt', '/app/' in lenker and '/personvern/' in lenker and 'mailto:post.fuglekort@gmail.com' in lenker, lenker)
                sjekk('ingen lenke til Merlin', not any('merlin' in (l or '') for l in lenker))
                if BILDER:
                    await pg.evaluate("scrollTo(0, 0)"); await pg.screenshot(path=str(BILDER / f'forside_{bredde}.png'), full_page=True)
                verter = sorted({urlparse(k).netloc for k in kall}); print('    verter', verter)
                sjekk('ingen kall til andre nettsteder', verter == [EGEN], verter)
                sjekk('ingen manglende filer', not mangler, mangler[:5])
                sjekk('ingen skriptfeil', not js, js)
                await ctx.close()
                print(f'=== personvern, {bredde} px')
                ctx, pg, kall, mangler, js = await side(b, f'http://{EGEN}/personvern/', bredde, 'personvern')
                t = await pg.evaluate("document.body.innerText")
                sjekk('innholdet', all(x in t for x in ('Jakob Myking', 'post.fuglekort@gmail.com', 'Irland', '13 år', 'Datatilsynet', 'Slik sletter du')) and 'FYLL' not in t and '[' not in t)
                sjekk('ingen hjemmeadresse', 'Maurstien' not in t and 'Korsvoll' not in t)
                sjekk('#slett finnes', await pg.evaluate("!!document.getElementById('slett')"))
                sjekk('ingen sidelengs rulling', await pg.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"))
                if BILDER: await pg.screenshot(path=str(BILDER / f'personvern_{bredde}.png'), full_page=True)
                sjekk('ingen kall til andre nettsteder', sorted({urlparse(k).netloc for k in kall}) == [EGEN])
                sjekk('ingen manglende filer', not mangler, mangler[:5])
                await ctx.close()
            r = await (await b.new_context()).new_page()
            svar = await r.goto(f'http://{EGEN}/.well-known/assetlinks.json')
            a = json.loads(await svar.text())
            sjekk('assetlinks.json', svar.status == 200 and 'json' in svar.headers.get('content-type', '') and a[0]['target']['package_name'] == 'no.fuglekort.hagefugler')
            await b.close()
    finally:
        s.terminate()
    print('\nFEIL:', FEIL or 'ingen')
    sys.exit(1 if FEIL else 0)

asyncio.run(main())
