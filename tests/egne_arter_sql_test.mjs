// Egne arter i tellingen (tellinger.egne) i en Postgres i minnet (PGlite): hele supabase/fuglekort.sql med stand-ins,
// og så supabase/egne_arter.sql (fila som kjøres i Supabase) to ganger. Sjekker at kolonnen finnes med {} som standard,
// at eieren kan skrive og lese den, at andre ikke ser den, og at bare et objekt av rimelig størrelse godtas.
// Kjør (pakken må ligge ved siden av fila):  mkdir -p /tmp/pgl && cd /tmp/pgl && npm install @electric-sql/pglite
//        cp REPO/tests/egne_arter_sql_test.mjs . && node egne_arter_sql_test.mjs REPO
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
`);
await db.exec(fs.readFileSync(`${REPO}/supabase/fuglekort.sql`, 'utf8').replace(/^create extension.*$/gm, ''));
for (let i = 0; i < 2; i++) await db.exec(fs.readFileSync(`${REPO}/supabase/egne_arter.sql`, 'utf8'));
let feil = 0; const sjekk = (navn, ok, info) => { console.log((ok ? '  OK   ' : '  FEIL ') + navn + (ok ? '' : '  ' + JSON.stringify(info))); if (!ok) feil++; };
const A = '11111111-1111-1111-1111-111111111111', B = '22222222-2222-2222-2222-222222222222';
for (const u of [A, B]) await q(`insert into auth.users values ($1)`, [u]);
const som = async (uid) => { await q(`reset role`); await q(`delete from public.innlogget`); if (uid) { await q(`insert into public.innlogget values ($1)`, [uid]); await q(`set role authenticated`); } };
await som(A);
await q(`insert into public.tellinger (user_id, id, start, arter) values ($1, 't1', now(), '{"parus-major": 3}')`, [A]);
const r0 = (await q(`select egne from public.tellinger where id = 't1'`)).rows[0];
sjekk('en telling uten egne arter (eldre app): egne = {}', JSON.stringify(r0.egne) === '{}', r0);
await q(`insert into public.tellinger (user_id, id, start, arter, egne) values ($1, 't2', now(), '{}', '{"Sidensvans": 12, "Gråsisik": 2}')
         on conflict (user_id, id) do update set egne = excluded.egne`, [A]);
const r1 = (await q(`select egne from public.tellinger where id = 't2'`)).rows[0];
sjekk('eieren skriver og leser egne arter', r1 && r1.egne.Sidensvans === 12 && r1.egne['Gråsisik'] === 2, r1);
// an older app sends the row without egne: egne stays
await q(`insert into public.tellinger (user_id, id, start, arter) values ($1, 't2', now(), '{"pica-pica": 1}')
         on conflict (user_id, id) do update set arter = excluded.arter`, [A]);
sjekk('en eldre app som sender tellingen uten egne, sletter dem ikke', (await q(`select egne from public.tellinger where id = 't2'`)).rows[0].egne.Sidensvans === 12);
for (const [v, navn] of [['[]', 'en liste'], ['"tekst"', 'tekst'], [JSON.stringify(Object.fromEntries(Array.from({ length: 300 }, (_, i) => ['Art nummer ' + i, 1]))), 'for stor']]) {
  let avvist = false; try { await q(`update public.tellinger set egne = $1::jsonb where id = 't2'`, [v]); } catch (e) { avvist = /tellinger_egne_form/.test(e.message); }
  sjekk(`ugyldig egne avvises: ${navn}`, avvist);
}
await som(B);
sjekk('en annen bruker ser ikke tellingen (eller de egne artene)', (await q(`select count(*)::int n from public.tellinger`)).rows[0].n === 0);
console.log(feil ? `FEIL: ${feil}` : 'FEIL: ingen');
process.exit(feil ? 1 : 0);
