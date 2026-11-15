// Varsler i Supabase (seksjonen «Varsler (push)» i supabase/fuglekort.sql) i en Postgres i minnet (PGlite), med
// stand-ins for auth, pg_net og premiene: helga for Hagefugltellingen, når varslene legges i køen (fredag kl. 18 og
// lørdag kl. 9, premiene kl. 9 dagen etter), tekstene, testvarselet, køen for send-varsler, nøklene og opprydding.
// Kjør (pakken må ligge ved siden av fila):  mkdir -p /tmp/pgl && cd /tmp/pgl && npm install @electric-sql/pglite
//        cp REPO/tests/varsler_sql_test.mjs . && node varsler_sql_test.mjs REPO
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite();
const q = (s, p) => db.query(s, p);
const hele = fs.readFileSync(process.argv[2] ? `${process.argv[2]}/supabase/fuglekort.sql` : new URL('../supabase/fuglekort.sql', import.meta.url), 'utf8'), fra = hele.indexOf('-- ---------- Varsler (push) ----------');
let sql = hele.slice(fra, hele.indexOf('-- ---------- Eksempler på statistikk', fra)).replace(/^create extension.*$/gm, '');
await db.exec(`
  create role anon; create role authenticated; create role service_role;
  create schema auth; create table auth.users (id uuid primary key);
  create table public.innlogget (id uuid);
  create function auth.uid() returns uuid language sql stable as $$ select id from public.innlogget limit 1 $$;
  create schema net; create table net.kall (url text, tid timestamptz default now());
  create function net.http_post(url text, body jsonb default '{}', params jsonb default '{}', headers jsonb default '{}', timeout_milliseconds integer default 5000)
    returns bigint language sql as $$ insert into net.kall (url) values (url) returning 1::bigint $$;
  create table public.premier (periode text not null, plass smallint not null, user_id uuid references auth.users (id) on delete set null,
    navn text, poeng bigint not null, fro integer not null, tid timestamptz not null default now(), primary key (periode, plass));
  create function public.avslutt_perioder() returns void language sql as $$ select $$;
  set timezone = 'UTC';
`);
await db.exec(sql);
let feil = 0; const sjekk = (navn, ok, info) => { console.log((ok ? '  OK   ' : '  FEIL ') + navn + (ok ? '' : '  ' + JSON.stringify(info))); if (!ok) feil++; };
// the weekend
const lor = async y => (await q(`select public.tellehelg_lordag($1)::text d`, [y])).rows[0].d;
sjekk('tellehelga 2026: 31. januar', await lor(2026) === '2026-01-31');
sjekk('tellehelga 2027: 30. januar', await lor(2027) === '2027-01-30');
sjekk('tellehelga 2028: 29. januar', await lor(2028) === '2028-01-29');
await q(`insert into public.tellehelg values (2031, '2031-01-25')`);
sjekk('egen dato for 2031', await lor(2031) === '2031-01-25');
// subscriptions
const U1 = '11111111-1111-1111-1111-111111111111', U2 = '22222222-2222-2222-2222-222222222222';
await q(`insert into auth.users values ($1), ($2)`, [U1, U2]);
const ep = n => `https://fcm.googleapis.com/fcm/send/abc${n}xyz-${'x'.repeat(30)}`;
const lagre = async (n, telling, premier, fro, koble, uid) => {
  await q(`delete from public.innlogget`); if (uid) await q(`insert into public.innlogget values ($1)`, [uid]);
  await q(`select public.varsel_lagre($1, $2, $3, $4, $5, $6, 'play', $7)`, [ep(n), 'B' + 'p'.repeat(80), 'a'.repeat(22), telling, premier, fro, koble]);
};
await lagre(1, true, true, true, true, U1);       // shares, wins
await lagre(2, true, true, false, false, U2);      // simple version, does not share
await lagre(3, false, true, true, true, U2);       // no count reminder
const ab = (await q(`select endpoint, user_id, telling, premier, fro from public.varsel_abonnement order by endpoint`)).rows;
sjekk('tre telefoner lagret, bruker bare når de deler', ab.length === 3 && ab[0].user_id === U1 && ab[1].user_id === null && ab[2].user_id === U2, ab);
let feilet = false; try { await q(`select public.varsel_lagre('https://evil.example.com/x/${'y'.repeat(30)}', '${'p'.repeat(80)}', '${'a'.repeat(22)}', true, true, true, 'web', false)`); } catch (e) { feilet = /ukjent_adresse/.test(e.message); }
sjekk('ukjent push-tjeneste avvises', feilet);
// count reminders
const ko = async () => (await q(`select endpoint, tittel, tekst, url from public.varsel_ko order by id`)).rows;
const plan = async t => (await q(`select public.planlegg_varsler($1::timestamptz) n`, [t])).rows[0].n;
sjekk('torsdag 28. jan. 2027 kl. 20: ingenting', await plan('2027-01-28T19:00:00Z') === 0);
sjekk('fredag 29. jan. kl. 17 norsk tid: ingenting ennå', await plan('2027-01-29T16:00:00Z') === 0);
sjekk('fredag kl. 18: to telefoner (den uten tellingsvarsler hoppes over)', await plan('2027-01-29T17:00:00Z') === 2);
sjekk('fredag kl. 19: ikke en gang til', await plan('2027-01-29T18:00:00Z') === 0);
sjekk('lørdag kl. 8: ingenting', await plan('2027-01-30T07:30:00Z') === 0);
sjekk('lørdag kl. 9: to igjen', await plan('2027-01-30T08:05:00Z') === 2);
sjekk('lørdag kl. 19: ikke mer', await plan('2027-01-30T18:00:00Z') === 0);
let k = await ko();
sjekk('teksten fredag', k[0].tekst === 'Hagefugltellingen er i morgen og søndag. Tell fuglene i hagen i én time.' && k[0].url === './?vis=telling', k[0]);
sjekk('teksten lørdag, med frø og uten (den enkle versjonen)', k.filter(x => x.tekst === 'Hagefugltellingen er i gang! Tell i én time og få 75 000 frø.').length === 1
      && k.filter(x => x.tekst === 'Hagefugltellingen er i gang! Tell fuglene i hagen i én time.').length === 1, k.slice(2));
// prizes
await q(`delete from public.varsel_ko`);
await q(`insert into public.premier values ('uke:2027-05', 2, $1, 'Rask Kjøttmeis', 50000, 20000, '2027-02-07T23:07:00Z'), ('mnd:2027-01', 1, $2, 'Blid Blåmeis', 90000, 100000, '2027-01-31T23:07:00Z'), ('aar:2026', 3, $1, 'Rask Kjøttmeis', 1, 250000, '2026-12-31T23:07:00Z')`, [U1, U2]);
sjekk('mandag kl. 01: ingen premievarsler før kl. 9', await plan('2027-02-08T00:00:00Z') === 0);
const n9 = await plan('2027-02-08T08:10:00Z');
k = await ko();
sjekk('mandag kl. 9: uka til U1 (månedens til U2 er over tre dager gammel)', n9 === 1 && k.length === 1 && k[0].tittel === 'Ukas ledertavle', k);
sjekk('teksten: «Du kom på 2. plass i uke 5 og vant 20 000 frø!»', k[0] && k[0].tekst === 'Du kom på 2. plass i uke 5 og vant 20 000 frø!' && k[0].url === './?vis=tavle', k[0]);
sjekk('ikke en gang til', await plan('2027-02-08T09:10:00Z') === 0);
await q(`delete from public.varsel_ko`);
const n2 = await plan('2027-02-01T08:30:00Z');
k = await ko();
sjekk('1. februar kl. 9: månedens til U2, men bare telefonen med premievarsler og frø (ikke den enkle)', n2 === 1 && k.length === 1 && k[0].endpoint === ep(3) && k[0].tekst === 'Du kom på 1. plass i januar 2027 og vant 100 000 frø!', k);
await q(`delete from public.varsel_ko`);
const n3 = await plan('2027-01-01T09:30:00Z');
k = await ko();
sjekk('1. januar: årets', n3 === 1 && k[0].tittel === 'Årets ledertavle' && k[0].tekst === 'Du kom på 3. plass i 2026 og vant 250 000 frø!', k);
// test notification, rate limit, the queue for the function
await db.exec(`delete from public.varsel_ko; delete from net.kall`);
sjekk('testvarsel', (await q(`select public.send_testvarsel($1) ok`, [ep(1)])).rows[0].ok === true);
sjekk('   ikke to i samme minutt', (await q(`select public.send_testvarsel($1) ok`, [ep(1)])).rows[0].ok === false);
sjekk('   send-varsler ble bedt om å sende', (await q(`select count(*)::int n from net.kall where url like '%/functions/v1/hyper-api'`)).rows[0].n === 1);
sjekk('   teksten', (await ko())[0].tekst === 'Varslene virker. Du får beskjed når Hagefugltellingen starter og når du vinner en premie.');
await q(`select public.send_testvarsel($1)`, [ep(2)]);
sjekk('   den enkle versjonen: bare tellingen', (await ko())[1].tekst === 'Varslene virker. Du får beskjed når Hagefugltellingen starter.');
const hent = (await q(`select * from public.varsler_hent(10)`)).rows;
sjekk('varsler_hent: køen med nøklene', hent.length === 2 && hent[0].p256dh && hent[0].auth && hent[0].ttl === 600, hent);
await q(`select public.varsler_ferdig($1::jsonb)`, [JSON.stringify([{ id: hent[0].id, status: 201 }, { id: hent[1].id, status: 410 }])]);
const igjen = (await q(`select endpoint from public.varsel_abonnement order by endpoint`)).rows.map(r => r.endpoint);
sjekk('varsler_ferdig: 410 fjerner telefonen, 201 står', igjen.length === 2 && !igjen.includes(ep(2)), igjen);
sjekk('   køen er tom', (await q(`select count(*)::int n from public.varsel_ko where sendt is null`)).rows[0].n === 0);
// keys
sjekk('ingen nøkkel ennå: null, og send-varsler bes lage den', (await q(`select public.varsel_nokkel() k`)).rows[0].k === null && (await q(`select count(*)::int n from net.kall`)).rows[0].n === 3);
await q(`select public.varsler_nokler('BOFFENTLIG', '{"d":"x"}'::jsonb)`);
await q(`select public.varsler_nokler('ANNEN', '{"d":"y"}'::jsonb)`);
sjekk('nøklene lagres én gang og blir stående', (await q(`select public.varsel_nokkel() k`)).rows[0].k === 'BOFFENTLIG');
// slett_meg-like: the user goes, the phone stays without user
await q(`delete from auth.users where id = $1`, [U1]);
sjekk('brukeren slettet: telefonen står, uten bruker', (await q(`select user_id from public.varsel_abonnement where endpoint = $1`, [ep(1)])).rows[0].user_id === null);
await q(`select public.varsel_slett($1)`, [ep(1)]);
sjekk('varsel_slett', (await q(`select count(*)::int n from public.varsel_abonnement where endpoint = $1`, [ep(1)])).rows[0].n === 0);
// five errors in a row
await q(`select public.send_testvarsel($1)`, [ep(3)]);
for (let i = 0; i < 5; i++) {
  await q(`insert into public.varsel_ko (endpoint, tittel, tekst) values ($1, 't', 't')`, [ep(3)]);
  const h = (await q(`select id from public.varsler_hent(10)`)).rows;
  await q(`select public.varsler_ferdig($1::jsonb)`, [JSON.stringify(h.map(r => ({ id: r.id, status: 500 })))]);
}
sjekk('fem feil på rad: telefonen fjernes', (await q(`select count(*)::int n from public.varsel_abonnement`)).rows[0].n === 0);
console.log(feil ? `FEIL: ${feil}` : 'FEIL: ingen');
