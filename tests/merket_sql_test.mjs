// Merkede brukere og den åpne ledertavla (15. november 2026) i en Postgres i minnet (PGlite): hele supabase/fuglekort.sql
// med stand-ins for auth, pg_cron og pg_net, og så supabase/merket_skjult.sql (fila som kjøres i Supabase) to ganger.
// Sjekker at merkede ikke vises for andre (tabellen for anon og innloggede, tavle og tavle_arter), at de ser seg selv,
// at grupper og favoritter (tavle_utvalg) fortsatt viser dem, at merk() bare kan kjøres i SQL Editor, at godkjenn()
// gir dem tilbake, og at mer enn 25 arter på én dag merker (25 gjør det ikke).
// Kjør (pakken må ligge ved siden av fila):  mkdir -p /tmp/pgl && cd /tmp/pgl && npm install @electric-sql/pglite
//        cp REPO/tests/merket_sql_test.mjs . && node merket_sql_test.mjs REPO
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const REPO = process.argv[2] || new URL('..', import.meta.url).pathname;
const db = new PGlite();
const q = (s, p) => db.query(s, p);
await db.exec(`
  create role anon; create role authenticated; create role service_role;
  create schema auth; create table auth.users (id uuid primary key);
  create table public.innlogget (id uuid);
  create function auth.uid() returns uuid language sql stable as $$ select id from public.innlogget limit 1 $$;
  grant usage on schema auth to anon, authenticated; grant select on public.innlogget to anon, authenticated;
  create schema net; create function net.http_post(url text, body jsonb default '{}', params jsonb default '{}', headers jsonb default '{}', timeout_milliseconds integer default 5000)
    returns bigint language sql as $$ select 1::bigint $$;
  create schema cron; create function cron.schedule(a text, b text, c text) returns bigint language sql as $$ select 1::bigint $$;
  set timezone = 'UTC';
`);
await db.exec(fs.readFileSync(`${REPO}/supabase/fuglekort.sql`, 'utf8').replace(/^create extension.*$/gm, ''));
for (let i = 0; i < 2; i++) await db.exec(fs.readFileSync(`${REPO}/supabase/merket_skjult.sql`, 'utf8'));
let feil = 0; const sjekk = (navn, ok, info) => { console.log((ok ? '  OK   ' : '  FEIL ') + navn + (ok ? '' : '  ' + JSON.stringify(info))); if (!ok) feil++; };
const U = ['1', '2', '3', '4', '5'].map(n => `${n.repeat(8)}-${n.repeat(4)}-${n.repeat(4)}-${n.repeat(4)}-${n.repeat(12)}`);
const NAVN = ['Vanlig En', 'Misforstått', 'Vanlig Tre'];
for (const u of U) await q(`insert into auth.users values ($1)`, [u]);
const som = async (uid, rolle) => { await q(`reset role`); await q(`delete from public.innlogget`); if (uid) await q(`insert into public.innlogget values ($1)`, [uid]); if (rolle) await q(`set role ${rolle}`); };
const idag = (await q(`select (now() at time zone 'Europe/Oslo')::date::text d`)).rows[0].d;
for (let i = 0; i < 3; i++) {
  await som(null);
  await q(`insert into public.ledertavle (user_id, navn, fro, arter, dager, tittel) values ($1, $2, $3, 3, 3, 1)`, [U[i], NAVN[i], 10000 * (3 - i)]);
  await q(`insert into public.fro_logg (user_id, tid, fro) values ($1, now() - interval '30 days', 100) on conflict do nothing`, [U[i]]);
  for (const art of ['parus-major', 'turdus-merula', 'pica-pica']) await q(`insert into public.sett (user_id, art, dager) values ($1, $2, array[$3::date])`, [U[i], art, idag]);
}
await som(null);
await q(`select public.merk($1)`, [U[1]]);
const m = (await q(`select l.merket, m.grunn from public.ledertavle l join public.merket m using (user_id) where l.user_id = $1`, [U[1]])).rows[0];
sjekk('merk(): merket, med grunnen «merket for hånd»', m && m.merket === true && m.grunn === 'merket for hånd', m);
const navn = rows => rows.map(r => r.navn).sort();
await som(null, 'anon');
sjekk('tabellen for anon (ikke innlogget): den merkede vises ikke', JSON.stringify(navn((await q(`select navn from public.ledertavle`)).rows)) === JSON.stringify(['Vanlig En', 'Vanlig Tre']));
await som(U[2], 'authenticated');
sjekk('tabellen for en annen innlogget: den merkede vises ikke', JSON.stringify(navn((await q(`select navn from public.ledertavle`)).rows)) === JSON.stringify(['Vanlig En', 'Vanlig Tre']));
const over = (await q(`select count(*)::int n from public.ledertavle where fro > 5000`)).rows[0].n;
sjekk('   «hvor mange er foran meg» teller ikke den merkede', over === 2, over);
await som(U[1], 'authenticated');
sjekk('den merkede ser seg selv', JSON.stringify(navn((await q(`select navn from public.ledertavle`)).rows)) === JSON.stringify(['Misforstått', 'Vanlig En', 'Vanlig Tre']));
let nektet = false; try { await q(`select public.merk($1)`, [U[0]]); } catch (e) { nektet = /permission denied/.test(e.message); }
sjekk('merk() kan ikke kjøres fra appen (innlogget)', nektet);
nektet = false; try { await q(`select public.godkjenn($1)`, [U[1]]); } catch (e) { nektet = /permission denied/.test(e.message); }
sjekk('godkjenn() heller ikke', nektet);
await som(U[2]);
const uke = (await q(`select public.tavle('uke') t`)).rows[0].t, art = (await q(`select public.tavle_arter('tot') t`)).rows[0].t;
sjekk('tavle(uke) for en annen: uten den merkede', JSON.stringify(navn(uke.rader)) === JSON.stringify(['Vanlig En', 'Vanlig Tre']) && uke.antall === 2, uke.rader);
sjekk('tavle_arter(tot) for en annen: uten den merkede', JSON.stringify(navn(art.rader)) === JSON.stringify(['Vanlig En', 'Vanlig Tre']) && art.antall === 2, art.rader);
await som(U[1]);
const uke2 = (await q(`select public.tavle('uke') t`)).rows[0].t, art2 = (await q(`select public.tavle_arter('uke') t`)).rows[0].t;
sjekk('tavle og tavle_arter for den merkede: med seg selv (merket)', uke2.rader.some(r => r.navn === 'Misforstått' && r.merket) && art2.rader.some(r => r.navn === 'Misforstått') && uke2.plass != null, [uke2.rader, uke2.plass]);
await som(U[2]);
const utv = (await q(`select public.tavle_utvalg($1::uuid[], 'tot', 'fro') t`, [`{${U.slice(0, 3).join(',')}}`])).rows[0].t;
sjekk('grupper og favoritter (tavle_utvalg): den merkede vises, med merket', utv.rader.length === 3 && utv.rader.find(r => r.navn === 'Misforstått').merket === true, utv.rader);
const pa = (await q(`select public.profil_arter($1) p`, [U[1]])).rows[0].p;
sjekk('profilen til den merkede kan fortsatt åpnes fra en gruppe', pa && pa.navn === 'Misforstått', pa);
await som(null);
await q(`select public.godkjenn($1)`, [U[1]]);
await som(U[2], 'authenticated');
sjekk('godkjenn(): tilbake på tavla', navn((await q(`select navn from public.ledertavle`)).rows).includes('Misforstått'));
// more than 25 species on one day
await som(null);
const arter = n => Array.from({ length: n }, (_, i) => `art-${String.fromCharCode(97 + Math.floor(i / 26))}${String.fromCharCode(97 + (i % 26))}`);
for (const [u, n, navnet] of [[U[3], 26, 'Tjueseks'], [U[4], 25, 'Tjuefem']]) {
  await q(`insert into public.ledertavle (user_id, navn, fro, arter, dager, tittel) values ($1, $2, 1000, $3, 1, 0)`, [u, navnet, n]);
  for (const a of arter(n)) await q(`insert into public.sett (user_id, art, dager) values ($1, $2, array[$3::date])`, [u, a, idag]);
}
const r26 = (await q(`select l.merket, m.grunn, m.arter_dogn from public.ledertavle l left join public.merket m using (user_id) where l.user_id = $1`, [U[3]])).rows[0];
const r25 = (await q(`select merket from public.ledertavle where user_id = $1`, [U[4]])).rows[0];
sjekk('26 arter på én dag: merket («mer enn 25 arter på én dag»)', r26.merket === true && r26.grunn === 'mer enn 25 arter på én dag' && r26.arter_dogn === 26, r26);
sjekk('25 arter på én dag: ikke merket', r25.merket === false, r25);
console.log(feil ? `FEIL: ${feil}` : 'FEIL: ingen');
process.exit(feil ? 1 : 0);
