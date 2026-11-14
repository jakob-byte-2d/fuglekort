"""The task «Gjennomfør en hagefugltelling»: first in the list (and on «Kom i gang» in the introduction), done by a
finished count of at least an hour (not by one of 30 minutes), showing 75 000 seeds (they come from Tellekorps; the
task gives none of its own), the button «Tell» goes to the Telling tab, which says how to count and starts the count
at once (no window of its own); the strip «Neste oppdrag» shows it first from 1 January until Hagefugltellingen's
weekend is over (the small tasks first the rest of the year); BirdLife Norge named in the Telling tab and the summary,
with the next weekend, and a warning there and in the count bar when it is not Hagefugltellingen; the introduction: a card on Hagefugltellingen, «Frøbutikken», all the tasks without a sum; the help card «Om kortene» says «Hagefugler». The seeds of the counts: the
first good count (an hour or more, with species) in Hagefugltellingen's weekend (the last Saturday of January and the
Sunday) 75 000 via Tellekorps, once a year, and the task is done; counts started before 15 November 2026 keep the old
rule (the year's first good count, any day); every other good count 3 000 (at most one a day, not the day of
Tellekorps), none under an hour or without species; the summary and «Profil» say which, and Merker shows the next
Tellekorps.

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
    """localStorage for a user on this date: optionally finished counts [(start, minutes[, species])] and seen birds"""
    x = {'hagefugler:testmerke': '2026-09-30-pluss'}
    if intro: x.update({'fuglekort:intro': 'ferdig', 'hagefugler-oslo:hint': 'ok', 'fuglekort:deling': 'nei', 'fuglekort:tittel:v2': '99'})   # else: as the very first time
    if tellinger:
        x['hagefugler:tellinger:v1'] = json.dumps({f't{ms(t[0])}': {'start': ms(t[0]), 'slutt': ms(t[0]) + t[1] * 60000, 'omrade': '',
                                                    'arter': t[2] if len(t) > 2 else {'parus-major': 3}, 'ts': ms(t[0])} for t in tellinger})
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
        ok: li.classList.contains('ok'), under: ((li.querySelector('.o-t small') || {}).textContent || '').replace(/\u00a0/g, ' '), knapp: (li.querySelector('.o-gaa') || {}).textContent || '',
        fro: li.querySelector('.o-fro').textContent.trim() }))""")


async def main():
    s = subprocess.Popen([sys.executable, '-m', 'http.server', '8796', '--bind', '127.0.0.1'], cwd=ROT / 'docs', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        async with async_playwright() as p:
            b = await p.chromium.launch()
            nov, jan, feb16 = datetime(2026, 11, 14, 12), datetime(2027, 1, 20, 12), datetime(2027, 2, 16, 12)
            helg, feb1 = datetime(2027, 1, 30, 12), datetime(2027, 2, 1, 12)   # (in Hagefugltellingen's weekend, and after)

            print('=== ny bruker i november: lista, stripa, knappen «Tell»')
            ctx, pg, js = await side(b, nov, init(nov))
            sjekk('stripa i november: de små oppdragene først', await stripa(pg) == 'Registrer din første fugl', await stripa(pg))
            ls = await lista(pg)
            sjekk('tellingen står øverst i lista', ls and ls[0]['t'] == 'Gjennomfør en hagefugltelling' and not ls[0]['ok'], ls[:1])
            sjekk('med forklaring, knappen «Tell» og 75 000 frø', ls and ls[0]['under'] == 'Tell fuglene i hagen i minst én time under Hagefugltellingen 30.–31. januar 2027, og send tallene til Fuglevennen.no.'
                  and ls[0]['knapp'] == 'Tell' and ls[0]['fro'].replace('\u00a0', ' ') == '75 000', ls[:1])
            sjekk('de andre oppdragene som før', [o['t'] for o in ls[1:4]] == ['Registrer din første fugl', 'Finn en fugl med søket', 'Registrer tre ulike arter'], [o['t'] for o in ls])
            if BILDER: await pg.screenshot(path=str(BILDER / 'oppdrag_liste.png'))
            await pg.evaluate("document.querySelector('[data-oppdrag-gaa=telling]').click()"); await pg.wait_for_timeout(700)
            st = await pg.evaluate("""(() => { const f = document.querySelector('#faner [aria-selected=true]'), b = document.querySelector('#statsBody');
                return [f && f.textContent, !!b.querySelector('.tl-lead') && b.querySelector('.tl-lead').textContent, b.querySelectorAll('.fakta li').length, ((b.querySelector('.tl-birdlife') || {}).textContent || '').replace(/ /g, ' '),
                        !!b.querySelector('#tOmrade'), (b.querySelector('#tStart') || {}).textContent, !!document.querySelector('#startSheet')]; })()""")
            sjekk('«Tell» bytter til fanen Telling, med forklaringen og BirdLife Norge', st[0] == 'Telling' and st[1] == 'For hver art teller du det høyeste antallet du ser samtidig, ikke alle du ser i løpet av tellingen.' and st[2] == 4 and st[3].startswith(BIRDLIFE), st)
            sjekk('   og neste gang: lørdag 30. og søndag 31. januar 2027', 'Neste gang: lørdag 30. og søndag 31. januar 2027.' in st[3], st[3])
            sjekk('   med området og «Start telling», og uten eget startvindu', st[4] and st[5] == 'Start telling' and not st[6], st)
            if BILDER: await pg.screenshot(path=str(BILDER / 'oppdrag_start.png'))
            await pg.evaluate("document.querySelector('#tOmrade').value = 'Hagen hjemme'; document.querySelector('#tStart').click()"); await pg.wait_for_timeout(800)
            ig = await pg.evaluate("""(() => { const t = JSON.parse(localStorage.getItem('hagefugler:tellinger:v1') || '{}'), a = Object.values(t).find(v => !v.slutt);
                return [!!a, a && a.omrade, localStorage.getItem('hagefugler:omrade'), !!document.querySelector('.sheet.on'), !document.querySelector('#tTid').closest('[hidden]')]; })()""")
            sjekk('«Start telling» starter tellingen med en gang: området lagret, vinduet lukket, klokka går', ig == [True, 'Hagen hjemme', 'Hagen hjemme', False, True], ig)
            await pg.evaluate("document.querySelector('#openStats').click()"); await pg.wait_for_timeout(500)
            await pg.evaluate("document.querySelector('#fane-telling').click()"); await pg.wait_for_timeout(600)
            gt = await pg.evaluate("[(document.querySelector('#goTell') || {}).textContent, !!document.querySelector('#tStart'), !!document.querySelector('#tOmrade')]")
            sjekk('   mens den pågår: «Tilbake til tellingen» i fanen', gt == ['Tilbake til tellingen', False, False], gt)
            sjekk('ingen JS-feil', not js, js); await ctx.close()

            print('=== advarselen: ikke Hagefugltellingen nå')
            T = datetime
            V3000 = 'Det er ikke Hagefugltellingen nå. Du kan telle for moro skyld, men da får du bare 3 000 frø. Hagefugltellingen gir 75 000.'
            VDAG = 'Det er ikke Hagefugltellingen nå. Du kan telle for moro skyld, men du har alt fått frø for en telling i dag.'
            VENKEL = 'Det er ikke Hagefugltellingen nå, men du kan telle for moro skyld.'
            n20 = T(2026, 11, 20, 12)
            for navn, dato, tl, enk, vent, linje in (
                    ('14. nov. 2026, i dag gjelder den gamle regelen: ingen advarsel', nov, None, False, '', ''),
                    ('20. nov. 2026: 3 000 frø', n20, None, False, V3000, 'Ikke Hagefugltellingen nå · for moro skyld, 3 000 frø'),
                    ('20. nov. 2026, alt fått frø i dag', n20, [(T(2026, 11, 20, 8), 61)], False, VDAG, 'Ikke Hagefugltellingen nå · for moro skyld, ingen frø i dag'),
                    ('20. nov. 2026, den enkle versjonen', n20, None, True, VENKEL, 'Ikke Hagefugltellingen nå · for moro skyld'),
                    ('lørdag 30. januar 2027, i tellehelga: ingen advarsel', helg, None, False, '', '')):
                lager = init(dato, tellinger=tl); lager.update({'fuglekort:enkel': 'ja'} if enk else {})
                ctx, pg, js = await side(b, dato, lager)
                await pg.evaluate("document.querySelector('#openStats').click()"); await pg.wait_for_timeout(500)
                await pg.evaluate("document.querySelector('#fane-telling').click()"); await pg.wait_for_timeout(600)
                v = await pg.evaluate("((document.querySelector('#statsBody .tl-varsel') || {}).textContent || '').replace(/ /g, ' ')")
                sjekk(f'{navn}{": «" + vent + "»" if vent else ""}', v == vent, v)
                if BILDER and vent == V3000: await pg.screenshot(path=str(BILDER / 'telling_varsel.png'))
                await pg.evaluate("document.querySelector('#tStart').click()"); await pg.wait_for_timeout(800)
                l = await pg.evaluate("(() => { const e = document.querySelector('#tVarsel'); return e.hidden ? '' : e.textContent.replace(/ /g, ' '); })()")
                sjekk(f'   mens du teller: {"«" + linje + "»" if linje else "ingen linje"}', l == linje, l)
                if BILDER and linje.endswith('3 000 frø'): await pg.screenshot(path=str(BILDER / 'telling_varsel_teller.png'))
                if vent:
                    await pg.evaluate("document.querySelector('#openStats').click()"); await pg.wait_for_timeout(500)
                    await pg.evaluate("document.querySelector('#fane-telling').click()"); await pg.wait_for_timeout(600)
                    v2 = await pg.evaluate("((document.querySelector('#statsBody .tl-varsel') || {}).textContent || '').replace(/ /g, ' ')")
                    sjekk('   og i fanen mens du teller', v2 == vent, v2)
                sjekk('   ingen JS-feil', not js, js); await ctx.close()

            print('=== januar og 16. februar: stripa')
            ctx, pg, js = await side(b, jan, init(jan))
            sjekk('stripa 20. januar: tellingen først', await stripa(pg) == 'Gjennomfør en hagefugltelling', await stripa(pg))
            if BILDER: await pg.screenshot(path=str(BILDER / 'oppdrag_januar.png'))
            await ctx.close()
            ctx, pg, js = await side(b, helg, init(helg))
            sjekk('stripa lørdag 30. januar: tellingen først', await stripa(pg) == 'Gjennomfør en hagefugltelling', await stripa(pg))
            await pg.evaluate("document.querySelector('#openStats').click()"); await pg.wait_for_timeout(500)
            await pg.evaluate("document.querySelector('#fane-telling').click()"); await pg.wait_for_timeout(600)
            sjekk('fanen Telling i helga: «Årets telling er nå …»', 'Årets telling er nå: lørdag 30. og søndag 31. januar 2027.' in await pg.evaluate("document.querySelector('#statsBody').textContent.replace(/\u00a0/g, ' ')"))
            await ctx.close()
            for dato, navn in ((feb1, '1. februar'), (feb16, '16. februar')):
                ctx, pg, js = await side(b, dato, init(dato))
                sjekk(f'stripa {navn}, etter helga: de små oppdragene igjen', await stripa(pg) == 'Registrer din første fugl', await stripa(pg))
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
            TEKST = 'Fullfør oppdragene og få frø.'
            BUTIKK = 'Bruk frøene på nye dyrekort, baksider eller multiplikatorer.'
            TELLE = 'Tell fuglene i hagen for BirdLife Norge siste helga i januar. Bruk tellingen i appen: Min fugleliste → Telling.'
            INTRO = ['Velkommen til Hagefugler', 'Registrer fugler når du ser dem', 'Bli med på Hagefugltellingen', 'Frø og titler', 'Frøbutikken', 'Livslisten']
            for dato, vent in ((nov, TEKST), (jan, TEKST)):
                ctx, pg, js = await side(b, dato, init(dato, intro=False), intro=False)
                sider = await pg.evaluate("[...document.querySelectorAll('#introSpor > section')].map(s => [s.querySelector('h2').textContent, ((s.querySelector(':scope > p') || {}).textContent || '').replace(/\\u00a0/g, ' '), !!s.querySelector('.intro-q b'), !!s.querySelector('.intro-q .xdisk'), s.querySelectorAll('.intro-vifte > img').length, !!s.querySelector('.intro-tell .intro-ant'), !!s.querySelector('.intro-tell .intro-tid')])")
                titler = [x[0] for x in sider]
                sjekk(f'introduksjonen {dato:%d.%m}: tellingen etter «Registrer», «Frøbutikken» etter «Frø og titler»', titler[:6] == INTRO, titler)
                tk = next((x for x in sider if x[0] == 'Bli med på Hagefugltellingen'), None)
                sjekk('   tellingen: teksten om BirdLife og hvor tellingen er', tk and tk[1] == TELLE, tk)
                sjekk('   og bildet: et kort med antall og tid, som i tellingen', tk and tk[5] and tk[6], tk)
                sjekk('   livslisten: «Merk fugler du har sett før i livslisten.», og velkomsten og frøene kortere', [x[1] for x in sider[:6] if x[0] in ('Livslisten', 'Velkommen til Hagefugler', 'Frø og titler')]
                      == ['Bla gjennom fuglekort for de mest kjente fuglene i Norge.', 'Klarer du å oppnå tittelen Fuglekonge?', 'Merk fugler du har sett før i livslisten.'], [x[1] for x in sider])
                fb = next((x for x in sider if x[0] == 'Frøbutikken'), None)
                sjekk('   med teksten om dyrekort, baksider og merker', fb and fb[1] == BUTIKK, fb)
                sjekk('   og bildet: to baksider, et dyrekort med «?» og ×2', fb and fb[2] and fb[3] and fb[4] == 2, fb)
                tekst, tre = '', []
                for _ in range(20):
                    t = await pg.evaluate("document.querySelector('.dlg.on') ? document.querySelector('#dlgT').textContent : ''")
                    if t == 'Ikke dele?':
                        await pg.evaluate("document.querySelector('#dlgKnapper .btn.pri').click()"); await pg.wait_for_timeout(600); continue
                    if t: break
                    x = await pg.evaluate("(() => { const s = document.querySelector('[data-s=oppdrag]'); return s ? [s.querySelector(':scope > p').textContent.replace(/\\u00a0/g, ' '), [...s.querySelectorAll('.intro-oppdrag li')].map(li => [li.querySelector('.o-t').textContent, li.querySelector('.o-fro').textContent.replace(/\\u00a0/g, ' ')]), s.querySelector('.intro-oppdrag').textContent] : null; })()")
                    if x: tekst, tre, kort = x
                    if x: break
                    ikke = await pg.evaluate("(() => { const b = document.querySelector('#inIkke'); return !!b && !b.hidden && b.getBoundingClientRect().width > 0; })()")
                    await pg.evaluate("document.querySelector(%s).click()" % json.dumps('#inIkke' if ikke else '#introNeste')); await pg.wait_for_timeout(600)
                sjekk(f'«Kom i gang» {dato:%d.%m}: «{vent}»', tekst == vent, tekst)
                sjekk('   alle oppdragene (8 uten deling), tellingen først med 75 000', [o[0] for o in tre] == ['Gjennomfør en hagefugltelling', 'Registrer din første fugl', 'Finn en fugl med søket', 'Registrer tre ulike arter',
                      'Registrer fugler på to ulike dager', 'Kjøp noe i Frøbutikken', 'Registrer fem arter', 'Registrer fugler på tre ulike dager'] and tre[0][1] == '75 000', tre)
                sjekk('   ingen sum («frø i alt», «oppdrag til»)', 'i alt' not in kort and 'oppdrag til' not in kort, kort[-80:])
                hoyde = await pg.evaluate("(() => { const s = document.querySelector('[data-s=oppdrag]'); return [s.scrollHeight, s.clientHeight]; })()")
                sjekk(f'   får plass uten å rulle ({hoyde[0]} av {hoyde[1]} px)', hoyde[0] <= hoyde[1], hoyde)
                sjekk('ingen JS-feil', not js, js); await ctx.close()

            for enkel in (False, True):                              # from the menu; the simple version has no seeds, so no shop
                lager = init(nov); lager.update({'fuglekort:enkel': 'ja'} if enkel else {})
                ctx, pg, js = await side(b, nov, lager)
                await pg.evaluate("document.querySelector('#openIntro').click()"); await pg.wait_for_timeout(800)
                titler = await pg.evaluate("[...document.querySelectorAll('#introSpor > section h2')].map(h => h.textContent)")
                sjekk(f'fra menyen{" i den enkle versjonen" if enkel else ""}: {"uten" if enkel else "med"} «Frøbutikken», med tellingen', ('Frøbutikken' in titler) != enkel and 'Bli med på Hagefugltellingen' in titler, titler)
                sjekk('   ingen JS-feil', not js, js); await ctx.close()

            print('=== frøene for tellingene')
            T = datetime
            d1, d1b, d2 = T(2026, 11, 1, 10), T(2026, 11, 1, 13), T(2026, 11, 2, 10)
            j10, l30, l30b, s31 = T(2027, 1, 10, 10), T(2027, 1, 30, 10), T(2027, 1, 30, 14), T(2027, 1, 31, 10)
            KORPS_GML, KORPS27 = '+75 000 frø: Tellekorps 2026, årets første hagefugltelling.', '+75 000 frø: Tellekorps 2027, Hagefugltellingen 30.–31. januar.'
            NESTE, SAMME = '+3 000 frø for hagefugltellingen.', 'Du har alt fått frø for en telling denne dagen.'
            HINT = lambda h: f'Tellekorps-premien gis bare for tellinger under Hagefugltellingen {h}.'
            linje = lambda navn: "(() => { const li = [...document.querySelectorAll('.fro-kilder li')].find(l => l.querySelector('span').textContent === %s); return li ? +li.querySelector('b').textContent.replace(/\\D/g, '') : 0; })()" % json.dumps(navn)
            for navn, dato, tl, vent, opp, merke, sum_ in (
                    ('første telling, før regelen (1. nov. 2026): 75 000', nov, [(d1, 61)], 75000, True, 'Tellekorps 2026', {d1: [KORPS_GML]}),
                    ('to tellinger samme dag: fortsatt 75 000', nov, [(d1, 61), (d1b, 61)], 75000, True, 'Tellekorps 2026', {d1b: [SAMME]}),
                    ('en ny dag samme år: + 3 000', nov, [(d1, 61), (d1b, 61), (d2, 61)], 78000, True, 'Tellekorps 2026', {d2: [NESTE, HINT('30.–31. januar 2027')]}),
                    ('etter regelen, 20. nov. 2026: 3 000, ikke Tellekorps', T(2026, 11, 21, 12), [(T(2026, 11, 20, 10), 61)], 3000, False, 'Tellekorps 2027',
                     {T(2026, 11, 20, 10): [NESTE, HINT('30.–31. januar 2027')]}),
                    ('januar 2027: 3 000 før helga, 75 000 lørdag, 0 samme dag, 3 000 søndag', feb1, [(j10, 61), (l30, 61), (l30b, 61), (s31, 61)], 81000, True, 'Tellekorps 2027',
                     {j10: [NESTE], l30: [KORPS27], l30b: [SAMME], s31: [NESTE]}),
                    ('neste år: Tellekorps igjen i helga, + 75 000', feb1, [(d1, 61), (d1b, 61), (d2, 61), (l30, 61)], 153000, True, 'Tellekorps 2027', {l30: [KORPS27]}),
                    ('november 2027: 3 000, premien neste gang 29.–30. januar 2028', T(2027, 11, 20, 12), [(T(2027, 11, 10, 10), 61)], 3000, False, 'Tellekorps 2028',
                     {T(2027, 11, 10, 10): [NESTE, HINT('29.–30. januar 2028')]}),
                    ('under én time: 0', nov, [(d1, 30)], 0, False, 'Tellekorps 2027', {d1: ['Tellinger under én time gir ikke frø.']}),
                    ('uten arter: 0', nov, [(d1, 61, {})], 0, False, 'Tellekorps 2027', {d1: ['En telling uten arter gir ikke frø.']})):
                ctx, pg, js = await side(b, dato, init(dato, tellinger=tl))
                await pg.evaluate("document.querySelector('#openStats').click()"); await pg.wait_for_timeout(500)
                await pg.evaluate("document.querySelector('#fane-profil').click()"); await pg.wait_for_timeout(600)
                h, o = await pg.evaluate(linje('Hagefugltellinger')), await pg.evaluate(linje('Oppdrag'))
                sjekk(f'{navn} (Profil: «Hagefugltellinger» {h}, «Oppdrag» {o})', h == vent and o == 0, (h, o))
                if BILDER and len(tl) == 4 and tl[0][0] == j10: await pg.screenshot(path=str(BILDER / 'telling_fro_profil.png'))
                await pg.evaluate("document.querySelector('#fane-merker').click()"); await pg.wait_for_timeout(600)
                m = await pg.evaluate("""(() => { const li = [...document.querySelectorAll('#oppdragSek li')].find(l => l.querySelector('.o-t').firstChild.textContent === 'Gjennomfør en hagefugltelling');
                    const k = [...document.querySelectorAll('.merker .merke')].filter(x => x.querySelector('b').textContent.startsWith('Tellekorps')).map(x => [x.querySelector('b').textContent, x.className.includes('ok'), x.querySelector('small').textContent.replace(/\u00a0/g, ' ')]);
                    return [li ? li.classList.contains('ok') : 'ingen', k]; })()""")
                sjekk(f'   oppdraget {"fullført" if opp else "ikke fullført"}, Merker viser {merke}', (m[0] is True) == opp and len(m[1]) == 1 and m[1][0][0] == merke, m)
                if merke == 'Tellekorps 2027' and not opp:
                    sjekk('   med teksten «… under Hagefugltellingen 30.–31. januar 2027»', m[1][0][2] == 'En hagefugltelling på minst én time under Hagefugltellingen 30.–31. januar 2027', m[1][0][2])
                await pg.evaluate("document.querySelector('#fane-telling').click()"); await pg.wait_for_timeout(600)
                for start, vt in sum_.items():
                    await pg.evaluate("document.querySelector('[data-tid=\"t%d\"]').click()" % ms(start)); await pg.wait_for_timeout(700)
                    t = [x.replace(' ', ' ') for x in await pg.evaluate("[...document.querySelectorAll('#sumBody .sum-fro')].map(p => p.textContent)")]
                    sjekk(f'   oppsummeringen {start:%d.%m.%Y kl. %H}: {" / ".join("«" + x + "»" for x in vt)}', t == vt, t)
                    if BILDER and vt[0] in (KORPS27, NESTE) and (start == l30 or len(vt) == 2 and start.year == 2027): await pg.screenshot(path=str(BILDER / ('telling_fro_helg.png' if start == l30 else 'telling_fro_utenfor.png')))
                    await pg.evaluate("document.querySelector('#closeSum').click()"); await pg.wait_for_timeout(500)
                sjekk('   ingen JS-feil', not js, js); await ctx.close()

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
