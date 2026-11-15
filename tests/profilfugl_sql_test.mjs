// Profilbildet på tavla (ledertavle.profilfugl og .profilsett) i en Postgres i minnet (PGlite): hele
// supabase/fuglekort.sql med stand-ins for auth, pg_cron og pg_net, og så supabase/profilfugl.sql og profilsett.sql
// (filene som kjøres i Supabase) en gang til. Sjekker formen på artsnavnet og bildetypen, at appen får skrive
// kolonnene, og at tavle, tavle_arter, tavle_utvalg (grupper og favoritter) og profil_arter sender dem med, også for
// rader uten fugl.
// Kjør (pakken må ligge ved siden av fila):  mkdir -p /tmp/pgl && cd /tmp/pgl && npm install @electric-sql/pglite
//        cp REPO/tests/profilfugl_sql_test.mjs . && node profilfugl_sql_test.mjs REPO
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const REPO = process.argv[2] || new URL('..', import.meta.url).pathname;
const db = new PGlite();
const q = (s, p) => db.query(s, p);
const fjern = t => t.replace(/^create extension.*$/gm, '');
await db.exec(`
  create role anon; create role authenticated; create role service_role;
  create schema auth; create table auth.users (id uuid primary key);
  create table public.innlogget (id uuid);
  create function auth.uid() returns uuid language sql stable as $$ select id from public.innlogget limit 1 $$;
  create schema net; create function net.http_post(url text, body jsonb default '{}', params jsonb default '{}', headers jsonb default '{}', timeout_milliseconds integer default 5000)
    returns bigint language sql as $$ select 1::bigint $$;
  create schema cron; create function cron.schedule(a text, b text, c text) returns bigint language sql as $$ select 1::bigint $$;
  set timezone = 'UTC';
`);
await db.exec(fjern(fs.readFileSync(`${REPO}/supabase/fuglekort.sql`, 'utf8')));
await db.exec(fs.readFileSync(`${REPO}/supabase/profilfugl.sql`, 'utf8'));           // the file run in Supabase: again, on top
await db.exec(fs.readFileSync(`${REPO}/supabase/profilfugl.sql`, 'utf8'));           // and once more: it can be run twice
for (let i = 0; i < 2; i++) await db.exec(fs.readFileSync(`${REPO}/supabase/profilsett.sql`, 'utf8'));   // the style, twice too
let feil = 0; const sjekk = (navn, ok, info) => { console.log((ok ? '  OK   ' : '  FEIL ') + navn + (ok ? '' : '  ' + JSON.stringify(info))); if (!ok) feil++; };
const som = async uid => { await q(`delete from public.innlogget`); if (uid) await q(`insert into public.innlogget values ($1)`, [uid]); };
const U = ['11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333'];
for (const u of U) await q(`insert into auth.users values ($1)`, [u]);
// the column, the form of the name and the right to write it
const kol = (await q(`select data_type from information_schema.columns where table_name = 'ledertavle' and column_name = 'profilfugl'`)).rows;
sjekk('kolonnen ledertavle.profilfugl finnes (tekst)', kol.length === 1 && kol[0].data_type === 'text', kol);
const rett = (await q(`select privilege_type from information_schema.column_privileges where table_name = 'ledertavle' and column_name = 'profilfugl' and grantee = 'authenticated' order by 1`)).rows.map(r => r.privilege_type);
sjekk('appen (authenticated) får skrive den: INSERT og UPDATE', rett.includes('INSERT') && rett.includes('UPDATE'), rett);
const merket = (await q(`select privilege_type from information_schema.column_privileges where table_name = 'ledertavle' and column_name = 'merket' and grantee = 'authenticated' and privilege_type in ('INSERT', 'UPDATE')`)).rows;
sjekk('   men fortsatt ikke «merket»', merket.length === 0, merket);
const rett2 = (await q(`select privilege_type from information_schema.column_privileges where table_name = 'ledertavle' and column_name = 'profilsett' and grantee = 'authenticated' order by 1`)).rows.map(r => r.privilege_type);
sjekk('appen får skrive profilsett også', rett2.includes('INSERT') && rett2.includes('UPDATE'), rett2);
const rad = async (u, navn, fro, fugl, sett = null) => { await som(u);
  await q(`insert into public.ledertavle (user_id, navn, fro, arter, dager, tittel, profilfugl, profilsett) values ($1, $2, $3, 3, 4, 2, $4, $5)
           on conflict (user_id) do update set navn = excluded.navn, fro = excluded.fro, profilfugl = excluded.profilfugl, profilsett = excluded.profilsett`, [u, navn, fro, fugl, sett]); };
await rad(U[0], 'Kjøttmeisen', 5000, 'parus-major', 'tegneserie');
await rad(U[1], 'Uten fugl', 3000, null);
await rad(U[2], 'Svarttrosten', 1000, 'turdus-merula', 'foto');
for (const v of ['ki', 'Foto', 'illustrasjon', '']) {
  let avvist = false; try { await rad(U[2], 'Svarttrosten', 1000, 'turdus-merula', v); } catch (e) { avvist = /profilsett_gyldig/.test(e.message); }
  sjekk(`ugyldig bildetype avvises: «${v}»`, avvist);
}
for (const [v, navn] of [['Parus-major', 'store bokstaver'], ['parus major', 'mellomrom'], ['parus', 'bare ett ord'], ['<script>', 'tegn'], ['a-' + 'b'.repeat(60), 'for langt']]) {
  let avvist = false; try { await rad(U[2], 'Svarttrosten', 1000, v); } catch (e) { avvist = /profilfugl_form/.test(e.message); }
  sjekk(`ugyldig artsnavn avvises: ${navn}`, avvist);
}
await rad(U[2], 'Svarttrosten', 1000, 'turdus-merula', 'foto');
const pf = r => Object.fromEntries(r.map(x => [x.navn, [x.profilfugl, x.profilsett]]));
const VENT = { 'Kjøttmeisen': ['parus-major', 'tegneserie'], 'Uten fugl': [null, null], 'Svarttrosten': ['turdus-merula', 'foto'] };
const lik = (a, b) => JSON.stringify(a) === JSON.stringify(b);
// the board, all time: read straight from the table
const tot = (await q(`select navn, profilfugl, profilsett from public.ledertavle order by fro desc`)).rows;
sjekk('hovedtavla (tabellen): fuglene og tom for den uten', lik(pf(tot), VENT), tot);
// the period boards: points come from fro_logg (the seeds now minus the seeds before the period); 100 seeds a month ago
await q(`insert into public.fro_logg (user_id, tid, fro) select u, now() - interval '30 days', 100 from unnest($1::uuid[]) u on conflict do nothing`, [`{${U.join(',')}}`]);
await som(U[0]);
const uke = (await q(`select public.tavle('uke') t`)).rows[0].t;
sjekk('tavle(uke) sender profilfugl og profilsett for hver rad', uke.rader.every(r => 'profilfugl' in r && 'profilsett' in r) && lik(pf(uke.rader), Object.fromEntries(Object.entries(VENT).filter(([n]) => uke.rader.some(r => r.navn === n)))), uke.rader);
sjekk('   (med rader å sjekke)', uke.rader.length >= 1, uke);
const art = (await q(`select public.tavle_arter('tot') t`)).rows[0].t;
sjekk('tavle_arter(tot) sender profilfugl og profilsett', art.rader.length === 3 && lik(pf(art.rader), VENT), art.rader);
const utv = (await q(`select public.tavle_utvalg($1::uuid[], 'tot', 'fro') t`, [`{${U.join(',')}}`])).rows[0].t;
sjekk('tavle_utvalg (grupper og favoritter) sender profilfugl og profilsett', utv.rader.length === 3 && lik(pf(utv.rader), VENT), utv.rader);
const fav = (await q(`select public.favoritt_tavle($1::uuid[], 'tot', 'arter') t`, [`{${U[1]},${U[2]}}`])).rows[0].t;
sjekk('favoritt_tavle (via tavle_utvalg) også', fav.rader.length === 3 && fav.rader.find(r => r.navn === 'Svarttrosten').profilsett === 'foto', fav.rader);
await som(U[1]);
const p0 = (await q(`select public.profil_arter($1) p`, [U[0]])).rows[0].p, p1 = (await q(`select public.profil_arter($1) p`, [U[1]])).rows[0].p;
sjekk('profil_arter: fuglen og bildetypen til den andre, null uten fugl', p0.profilfugl === 'parus-major' && p0.profilsett === 'tegneserie' && p0.navn === 'Kjøttmeisen' && p1.profilfugl === null && 'profilsett' in p1, [p0, p1]);
// back to the title: null
await rad(U[0], 'Kjøttmeisen', 5000, null);
sjekk('tilbake til tittelikonet: null på tavla', (await q(`select public.tavle_arter('tot') t`)).rows[0].t.rader.find(r => r.navn === 'Kjøttmeisen').profilfugl === null);
console.log(feil ? `FEIL: ${feil}` : 'FEIL: ingen');
process.exit(feil ? 1 : 0);
