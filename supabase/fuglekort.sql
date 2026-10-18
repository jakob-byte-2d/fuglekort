-- Fuglekort: felles ledertavle og observasjoner til statistikk
-- Lim inn alt i Supabase → SQL Editor og trykk Run. Kan kjøres flere ganger.
--
-- Hver telefon (hver bruker i appen) er en anonym Supabase-bruker. Telefonen er fasit; her ligger en kopi.
--   ledertavle   brukernavn og oppsummering på tavlen      alle kan lese, bare eieren kan skrive
--   profil       postnummer (valgfritt), appversjon …      bare eieren
--   sett         observasjonsdagene, én rad per art        bare eieren
--   tellinger    hagefugltellingene                        bare eieren
--   kjop         kjøp i Frøbutikken                        bare eieren
--   rapporter    navn andre har rapportert                 alle kan rapportere, bare du kan lese
--   stengte_ord  ord som ikke kan stå i et brukernavn      bare du (Table Editor)
--   stengte_navn navn som er sperret                       bare du (Table Editor)
--   fro_logg     frøene hver time (til ukes-, måneds- og årstavla)   bare du
--   premier      de tre beste i hver uke, måned og år       alle kan lese
--   merket       brukere med uvanlig mange frø på kort tid  bare du (godkjenn i SQL Editor)
--   dyrearter    dyrekortene, som ikke teller på artstavla  bare du (Table Editor)
-- Profilen på tavla (profil_arter): fugleartene en bruker har registrert, for andre på tavla (kan skjules med vis_arter).
-- Du som eier prosjektet, ser alt i SQL Editor (der gjelder ikke RLS), f.eks. via visningen observasjoner.
-- «Slett meg» sletter den anonyme brukeren, og alle radene forsvinner med den (on delete cascade).

-- ---------- felles: tidspunktet for siste endring settes av databasen ----------
create or replace function public.sett_oppdatert() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.oppdatert := now();
  return new;
end $$;

-- ---------- ledertavle (offentlig) ----------
-- Brukernavnet står i navn (fritekst med regler, se «Brukernavnet» under). ord, fugl og tall er den eldre formen
-- («rask» + «parus-major» + 42 → «Rask Kjøttmeis 42»), som eldre appversjoner fortsatt sender.
create table if not exists public.ledertavle (
  user_id   uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  ord       text     not null check (ord ~ '^[a-zæøå]{2,20}$'),
  fugl      text     not null check (fugl ~ '^[a-z]+(-[a-z]+){1,3}$' and length(fugl) <= 50),
  tall      smallint not null check (tall between 1 and 99),
  fro       bigint   not null default 0 check (fro between 0 and 100000000),     -- tjente frø (det titlene regnes av)
  arter     smallint not null default 0 check (arter between 0 and 100),        -- fuglearter sett
  dager     integer  not null default 0 check (dager between 0 and 40000),      -- observasjonsdager
  tittel    smallint not null default 0 check (tittel between 0 and 12),        -- 0 = Egg … 12 = Fuglekonge
  oppdatert timestamptz not null default now(),
  unique (ord, fugl, tall)
);
create index if not exists ledertavle_fro on public.ledertavle (fro desc);

-- ---------- profil (privat) ----------
create table if not exists public.profil (
  user_id    uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  postnr     text check (postnr ~ '^[0-9]{4}$'),            -- postnummer (valgfritt), bare til statistikk
  appversjon text check (length(appversjon) <= 40),
  bilder     text check (bilder in ('ki', 'foto', 'tegneserie')),
  bakside    text check (bakside ~ '^[a-z0-9-]{1,40}$'),
  opprettet  timestamptz not null default now(),
  oppdatert  timestamptz not null default now()
);

alter table public.profil add column if not exists postnr text check (postnr ~ '^[0-9]{4}$');

-- ---------- sett: observasjonsdagene (privat), samme form som på telefonen ----------
create table if not exists public.sett (
  user_id   uuid not null default auth.uid() references auth.users (id) on delete cascade,
  art       text not null check (art ~ '^[a-z]+(-[a-z]+){1,3}$' and length(art) <= 50),   -- f.eks. parus-major
  dager     date[] not null check (cardinality(dager) between 1 and 20000),
  oppdatert timestamptz not null default now(),
  primary key (user_id, art)
);
-- én rad per art og dag, til statistikk (bare i SQL Editor; ikke åpen for appen)
create or replace view public.observasjoner with (security_invoker = true) as
  select s.user_id, s.art, d.dato
  from public.sett s cross join lateral unnest(s.dager) as d(dato);
revoke all on public.observasjoner from anon, authenticated;

-- ---------- tellinger (privat) ----------
create table if not exists public.tellinger (
  user_id   uuid not null default auth.uid() references auth.users (id) on delete cascade,
  id        text not null check (id ~ '^t[0-9]{1,20}$'),
  start     timestamptz not null,
  slutt     timestamptz,
  omrade    text check (length(omrade) <= 80),
  arter     jsonb not null default '{}'::jsonb check (jsonb_typeof(arter) = 'object'),   -- art → høyeste antall
  oppdatert timestamptz not null default now(),
  primary key (user_id, id)
);

-- ---------- kjop (privat) ----------
create table if not exists public.kjop (
  user_id   uuid not null default auth.uid() references auth.users (id) on delete cascade,
  id        text not null check (id ~ '^(dyr|x|bakside)-[a-z0-9-]{1,60}$'),
  pris      integer not null check (pris between 0 and 10000000),
  dato      date not null,
  faktor    smallint,
  kort      jsonb,                                            -- hvor en multiplikator har sittet
  oppdatert timestamptz not null default now(),
  primary key (user_id, id)
);

-- ---------- tidspunkt, RLS og tilgang ----------
do $$
declare t text;
begin
  foreach t in array array['ledertavle', 'profil', 'sett', 'tellinger', 'kjop'] loop
    execute format('drop trigger if exists %1$s_oppdatert on public.%1$I', t);
    execute format('create trigger %1$s_oppdatert before insert or update on public.%1$I for each row execute function public.sett_oppdatert()', t);
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists "egne rader" on public.%I', t);
    execute format('create policy "egne rader" on public.%I for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id)', t);
    execute format('grant select, insert, update, delete on public.%I to authenticated', t);
  end loop;
end $$;

-- ledertavlen kan alle lese
drop policy if exists "alle kan lese tavlen" on public.ledertavle;
create policy "alle kan lese tavlen" on public.ledertavle for select to anon, authenticated using (true);
grant usage on schema public to anon, authenticated;
grant select on public.ledertavle to anon;

-- ---------- Brukernavnet: fritekst med regler, unikt, filter og rapporter ----------
-- 3–30 tegn: bokstaver (også æøå), tall, mellomrom, bindestrek og punktum, minst to bokstaver.
alter table public.ledertavle add column if not exists navn text;
alter table public.ledertavle alter column ord drop not null, alter column fugl drop not null, alter column tall drop not null;
alter table public.ledertavle drop constraint if exists ledertavle_navn_form;
alter table public.ledertavle add constraint ledertavle_navn_form check (navn is null or (
  char_length(navn) between 3 and 30
  and navn ~ '^[A-Za-z0-9ÆØÅæøåÄÖÜäöüÉÈÊéèêÁÀáàÓÒÔóòôÚúÍíÑñÇç]([A-Za-z0-9ÆØÅæøåÄÖÜäöüÉÈÊéèêÁÀáàÓÒÔóòôÚúÍíÑñÇç .-]*[A-Za-z0-9ÆØÅæøåÄÖÜäöüÉÈÊéèêÁÀáàÓÒÔóòôÚúÍíÑñÇç.])?$'
  and navn !~ '  '
  and navn ~ '[A-Za-zÆØÅæøåÄÖÜäöüÉÈÊéèêÁÀáàÓÒÔóòôÚúÍíÑñÇç].*[A-Za-zÆØÅæøåÄÖÜäöüÉÈÊéèêÁÀáàÓÒÔóòôÚúÍíÑñÇç]'));

-- ord som ikke kan stå i et navn. helt_ord = bare som eget ord (ellers også inni andre ord). Legg gjerne til flere
-- i Table Editor; det gjelder med en gang. Appen har den samme lista, så de fleste får beskjed før noe sendes.
create table if not exists public.stengte_ord (
  ord      text primary key check (char_length(ord) between 2 and 40),
  helt_ord boolean not null default false
);
-- navn som er sperret, enten av deg eller etter tre rapporter fra forskjellige brukere
create table if not exists public.stengte_navn (
  navn text primary key,
  tid  timestamptz not null default now()
);
alter table public.stengte_ord enable row level security;
alter table public.stengte_navn enable row level security;

-- navnet til sammenligning: små bokstaver også for ÆØÅ uansett databasens språkinnstilling
create or replace function public.navn_nokkel(t text) returns text
language sql immutable set search_path = '' as $$
  select lower(translate(t, 'ÆØÅÄÖÜÉÈÊÁÀÓÒÔÚÍÑÇ', 'æøåäöüéèêáàóòôúíñç'))
$$;
-- navnet til filteret: tall som bokstaver (f4en → faen), aksenter bort, bare bokstaver, doble bokstaver som én
create or replace function public.navn_ord(t text) returns text
language sql immutable set search_path = '' as $$
  select btrim(regexp_replace(regexp_replace(
    translate(public.navn_nokkel(t), '013457äöüéèêáàóòôúíñç', 'oieastæøueeeaaooouinc'),
    '[^a-zæøå]+', ' ', 'g'), '(.)\1+', '\1', 'g'))
$$;
alter table public.stengte_ord add column if not exists vasket text
  generated always as (replace(public.navn_ord(ord), ' ', '')) stored;
create or replace function public.navn_sperret(t text) returns boolean
language plpgsql stable security definer set search_path = '' as $$
declare o text := public.navn_ord(t);
begin
  return exists (select 1 from public.stengte_navn s where public.navn_nokkel(s.navn) = public.navn_nokkel(t))
      or exists (select 1 from public.stengte_ord s
                 where s.vasket <> '' and case when s.helt_ord
                   then s.vasket = any (string_to_array(o, ' '))
                   else position(s.vasket in replace(o, ' ', '')) > 0 end);
end $$;
create unique index if not exists ledertavle_navn_unik on public.ledertavle (public.navn_nokkel(navn));

-- et stengt navn blir aldri lagret (appen får «navn_stengt» tilbake og ber om et nytt)
create or replace function public.sjekk_navn() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if new.navn is not null and public.navn_sperret(new.navn) then
    raise exception 'navn_stengt' using hint = 'Navnet kan ikke brukes. Velg et annet.';
  end if;
  return new;
end $$;
drop trigger if exists ledertavle_sjekk_navn on public.ledertavle;
create trigger ledertavle_sjekk_navn before insert or update of navn on public.ledertavle
  for each row execute function public.sjekk_navn();

-- appen spør før den lagrer et navn: «ledig», «tatt» (av en annen) eller «stengt»
create or replace function public.navn_status(navn text) returns text
language sql stable security definer set search_path = '' as $$
  select case
    when public.navn_sperret(navn_status.navn) then 'stengt'
    when exists (select 1 from public.ledertavle l
                 where public.navn_nokkel(l.navn) = public.navn_nokkel(navn_status.navn)
                   and l.user_id is distinct from (select auth.uid())) then 'tatt'
    else 'ledig' end
$$;

-- rapporter: én per bruker og navn. Navnet settes av databasen (det som står på tavlen nå).
-- Tre rapporter fra forskjellige brukere: navnet sperres og fjernes fra tavlen til eieren velger et nytt.
create table if not exists public.rapporter (
  fra  uuid not null default auth.uid() references auth.users (id) on delete cascade,
  om   uuid not null references public.ledertavle (user_id) on delete cascade,
  navn text not null default '',
  tid  timestamptz not null default now(),
  primary key (fra, om, navn)
);
alter table public.rapporter enable row level security;
drop policy if exists "rapportere andre" on public.rapporter;
create policy "rapportere andre" on public.rapporter for insert to authenticated
  with check ((select auth.uid()) = fra and fra <> om);
create or replace function public.rapport_navn() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  select l.navn into new.navn from public.ledertavle l where l.user_id = new.om;
  if new.navn is null then raise exception 'ingen_navn'; end if;
  return new;
end $$;
create or replace function public.rapport_telling() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if (select count(distinct r.fra) from public.rapporter r where r.om = new.om and r.navn = new.navn) >= 3 then
    insert into public.stengte_navn (navn) values (public.navn_nokkel(new.navn)) on conflict do nothing;
    update public.ledertavle set navn = null where user_id = new.om and navn = new.navn;
  end if;
  return null;
end $$;
drop trigger if exists rapporter_navn on public.rapporter;
create trigger rapporter_navn before insert on public.rapporter for each row execute function public.rapport_navn();
drop trigger if exists rapporter_telling on public.rapporter;
create trigger rapporter_telling after insert on public.rapporter for each row execute function public.rapport_telling();

grant execute on function public.navn_nokkel(text), public.navn_ord(text) to anon, authenticated;
revoke execute on function public.navn_sperret(text), public.sjekk_navn(), public.rapport_navn(), public.rapport_telling() from public, anon, authenticated;
grant execute on function public.navn_status(text) to anon, authenticated;
grant insert on public.rapporter to authenticated;

-- ordene appen også har (stammer; «helt_ord» bare som eget ord, så f.eks. «Thoresen» og «Torpedo» går fint)
insert into public.stengte_ord (ord, helt_ord) values
  ('faen', false), ('fanden', false), ('satan', false), ('helvete', false), ('jævl', false), ('jævel', false),
  ('javl', false), ('jaevl', false), ('fitte', false), ('fitta', false), ('kuk', true), ('kuksug', false),
  ('pikk', true), ('pikkhode', false), ('pule', true), ('puling', false), ('knull', false), ('hore', true),
  ('hora', true), ('horunge', false), ('horebukk', false), ('ludder', false), ('tispe', false), ('drittsekk', false),
  ('rasshøl', false), ('rasshol', false), ('rævhøl', false), ('rævhol', false), ('homse', true), ('mongo', true),
  ('neger', false), ('negre', false), ('nigger', false), ('nigga', false), ('nazi', false), ('hitler', false), ('siegheil', false),
  ('pedo', true), ('pedofil', false), ('porno', false), ('porn', false), ('sex', true), ('fuck', false),
  ('fck', true), ('shit', false), ('cunt', false), ('bitch', false), ('whore', false), ('dick', false),
  ('penis', false), ('vagina', false), ('fag', true), ('retard', false), ('rapist', false), ('kys', true)
on conflict (ord) do nothing;

-- ---------- Ukes-, måneds- og årstavla, med premier til de tre beste ----------
-- Frøene i en periode = frøene nå minus frøene før perioden startet, fra et øyeblikksbilde hver time (fro_logg, satt
-- av databasen når appen sender). Premier og gjenopprettede frø (fro_utenfor) teller ikke. Ukene går fra mandag, og
-- grensene regnes i norsk tid. Den som begynner å dele midt i en periode, starter på 0.
alter table public.ledertavle add column if not exists fro_utenfor bigint not null default 0 check (fro_utenfor between 0 and 100000000);
alter table public.ledertavle add column if not exists arter_utenfor smallint not null default 0 check (arter_utenfor between 0 and 200);  -- arter fra en sikkerhetskopi
alter table public.ledertavle add column if not exists merket boolean not null default false;   -- settes bare av databasen
alter table public.ledertavle add column if not exists vis_arter boolean not null default true;   -- artslista på profilen (se profil_arter)
-- appen kan skrive sine egne kolonner, men aldri «merket»
revoke insert, update on public.ledertavle from authenticated;
grant insert (user_id, navn, ord, fugl, tall, fro, arter, dager, tittel, fro_utenfor, arter_utenfor, vis_arter),
      update (user_id, navn, ord, fugl, tall, fro, arter, dager, tittel, fro_utenfor, arter_utenfor, vis_arter) on public.ledertavle to authenticated;

create table if not exists public.fro_logg (
  user_id uuid not null references auth.users (id) on delete cascade,
  tid     timestamptz not null,                     -- timen (det siste som ble sendt den timen)
  fro     bigint not null,                          -- tjente frø uten premier og gjenopprettede frø
  arter   smallint not null default 0,              -- arter uten dem fra en sikkerhetskopi
  primary key (user_id, tid)
);
alter table public.fro_logg enable row level security;

create or replace function public.periode_start(hva text, t timestamptz default now()) returns timestamptz
language sql stable set search_path = '' as $$
  select date_trunc(case hva when 'uke' then 'week' when 'mnd' then 'month' else 'year' end, t at time zone 'Europe/Oslo') at time zone 'Europe/Oslo'
$$;
create or replace function public.periode_slutt(hva text, s timestamptz) returns timestamptz
language sql stable set search_path = '' as $$
  select ((s at time zone 'Europe/Oslo') + case hva when 'uke' then interval '1 week' when 'mnd' then interval '1 month' else interval '1 year' end) at time zone 'Europe/Oslo'
$$;
create or replace function public.periode_navn(hva text, s timestamptz) returns text      -- uke:2026-42, mnd:2026-10, aar:2026
language sql stable set search_path = '' as $$
  select hva || ':' || to_char(s at time zone 'Europe/Oslo', case hva when 'uke' then 'IYYY-IW' when 'mnd' then 'YYYY-MM' else 'YYYY' end)
$$;
create or replace function public.premie(hva text, plass integer) returns integer
language sql immutable set search_path = '' as $$
  select (case hva when 'uke' then array[2000, 1000, 500] when 'mnd' then array[5000, 3000, 1500] else array[25000, 15000, 7500] end)[plass]
$$;
-- frøene hver bruker fikk i [s, e): de som har sendt noe i perioden
create or replace function public.periode_poeng(s timestamptz, e timestamptz)
returns table (user_id uuid, poeng bigint, sist timestamptz)
language sql stable security definer set search_path = '' as $$
  with slutt as (
    select distinct on (l.user_id) l.user_id, l.fro, l.tid from public.fro_logg l
    where l.tid >= s and l.tid < e order by l.user_id, l.tid desc
  )
  select sl.user_id,
    greatest(0, sl.fro - coalesce(
      (select l.fro from public.fro_logg l where l.user_id = sl.user_id and l.tid < s order by l.tid desc limit 1),
      (select l.fro from public.fro_logg l where l.user_id = sl.user_id and l.tid >= s order by l.tid asc limit 1))) as poeng,
    sl.tid as sist
  from slutt sl
$$;

-- premiene: låst når perioden er over (de tre beste med frø, ikke merket; likt: den som kom dit først)
create table if not exists public.premier (
  periode text not null,                            -- uke:2026-42, mnd:2026-10, aar:2026
  plass   smallint not null check (plass between 1 and 3),
  user_id uuid references auth.users (id) on delete set null,
  navn    text,                                     -- navnet da perioden ble avsluttet
  poeng   bigint not null,                          -- frøene i perioden
  fro     integer not null,                         -- premien
  tid     timestamptz not null default now(),
  primary key (periode, plass)
);
alter table public.premier enable row level security;
drop policy if exists "alle kan lese premiene" on public.premier;
create policy "alle kan lese premiene" on public.premier for select to anon, authenticated using (true);
create table if not exists public.periode_sjekk (id smallint primary key default 1 check (id = 1), tid timestamptz not null);
alter table public.periode_sjekk enable row level security;

create or replace function public.avslutt_perioder() returns void
language plpgsql security definer set search_path = '' as $$
declare hva text; k integer; s timestamptz; e timestamptz; pid text;
begin
  perform pg_advisory_xact_lock(4242001);
  if exists (select 1 from public.periode_sjekk c where c.tid > now() - interval '10 minutes') then return; end if;
  insert into public.periode_sjekk (id, tid) values (1, now()) on conflict (id) do update set tid = excluded.tid;
  foreach hva in array array['uke', 'mnd', 'aar'] loop
    e := public.periode_start(hva);                                   -- the periods before this are over
    for k in 1 .. (case hva when 'uke' then 8 when 'mnd' then 3 else 1 end) loop
      s := public.periode_start(hva, e - interval '1 second');
      pid := public.periode_navn(hva, s);
      if not exists (select 1 from public.premier p where p.periode = pid) then
        insert into public.premier (periode, plass, user_id, navn, poeng, fro)
        select pid, r.nr, r.user_id, r.navn, r.poeng, public.premie(hva, r.nr::integer)
        from (select pp.user_id, pp.poeng, coalesce(l.navn, 'Fuglevenn') as navn,
                     row_number() over (order by pp.poeng desc, pp.sist asc, pp.user_id) as nr
              from public.periode_poeng(s, e) pp join public.ledertavle l on l.user_id = pp.user_id
              where pp.poeng > 0 and not l.merket) r
        where r.nr <= 3;
      end if;
      e := s;
    end loop;
  end loop;
end $$;

-- tavla for en periode (uke, mnd, aar): topp 50, antall, plassen og frøene dine, og forrige periodes premier
create or replace function public.tavle(hva text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare s timestamptz; e timestamptz; meg uuid := (select auth.uid()); ut jsonb;
begin
  if hva is null or hva not in ('uke', 'mnd', 'aar') then raise exception 'ukjent periode'; end if;
  perform public.avslutt_perioder();
  s := public.periode_start(hva); e := public.periode_slutt(hva, s);
  with r as (
    select pp.user_id, pp.poeng, l.navn, l.ord, l.fugl, l.tall, l.tittel, l.arter, l.dager, l.merket,
           row_number() over (order by pp.poeng desc, pp.sist asc, pp.user_id) as nr
    from public.periode_poeng(s, e) pp join public.ledertavle l on l.user_id = pp.user_id
    where pp.poeng > 0
  )
  select jsonb_build_object(
    'periode', public.periode_navn(hva, s), 'fra', s, 'til', e,
    'antall', (select count(*) from r),
    'plass', (select r.nr from r where r.user_id = meg),
    'meg', (select r.poeng from r where r.user_id = meg),
    'rader', coalesce((select jsonb_agg(jsonb_build_object('user_id', r.user_id, 'navn', r.navn, 'ord', r.ord, 'fugl', r.fugl, 'tall', r.tall,
                         'tittel', r.tittel, 'arter', r.arter, 'dager', r.dager, 'merket', r.merket, 'fro', r.poeng) order by r.nr) from r where r.nr <= 50), '[]'::jsonb),
    'forrige', coalesce((select jsonb_agg(jsonb_build_object('plass', p.plass, 'navn', p.navn, 'poeng', p.poeng, 'fro', p.fro, 'user_id', p.user_id) order by p.plass)
                         from public.premier p where p.periode = public.periode_navn(hva, public.periode_start(hva, s - interval '1 second'))), '[]'::jsonb),
    'premier', to_jsonb(array[public.premie(hva, 1), public.premie(hva, 2), public.premie(hva, 3)])
  ) into ut;
  return ut;
end $$;

-- ---------- Merking: uvanlig mange frø på kort tid ----------
-- Siste døgn mer enn 25 nye arter eller mer enn 300 000 frø (uten premier og gjenopprettede frø): brukeren merkes
-- på tavla og kan ikke vinne premier før du godkjenner: select public.godkjenn('<user_id>');
-- (Mer enn 40 arter registrert på én dag merkes også; se Artstavla under.)
create table if not exists public.merket (
  user_id   uuid primary key references auth.users (id) on delete cascade,
  tid       timestamptz not null default now(),     -- da brukeren ble merket
  grunn     text not null,
  fro_dogn  bigint,
  arter_dogn integer,
  godkjent  timestamptz                             -- satt av godkjenn(): det som kom før, teller ikke igjen
);
alter table public.merket enable row level security;
create or replace function public.sjekk_merking(uid uuid) returns void
language plpgsql security definer set search_path = '' as $$
declare na record; fra record; g timestamptz; grense timestamptz; df bigint; da integer;
begin
  if exists (select 1 from public.ledertavle l where l.user_id = uid and l.merket) then return; end if;
  select m.godkjent into g from public.merket m where m.user_id = uid;
  grense := greatest(date_trunc('hour', now()) - interval '24 hours', coalesce(g, '-infinity'::timestamptz));
  select l.fro, l.arter into na from public.fro_logg l where l.user_id = uid order by l.tid desc limit 1;
  if not found then return; end if;
  select l.fro, l.arter into fra from public.fro_logg l where l.user_id = uid and l.tid <= grense order by l.tid desc limit 1;
  if not found then
    select l.fro, l.arter into fra from public.fro_logg l where l.user_id = uid and l.tid > grense order by l.tid asc limit 1;
  end if;
  df := na.fro - fra.fro; da := na.arter - fra.arter;
  if df > 300000 or da > 25 then
    insert into public.merket (user_id, tid, grunn, fro_dogn, arter_dogn)
      values (uid, now(), case when da > 25 then 'mer enn 25 nye arter på et døgn' else 'mer enn 300 000 frø på et døgn' end, df, da)
      on conflict (user_id) do update set tid = excluded.tid, grunn = excluded.grunn, fro_dogn = excluded.fro_dogn, arter_dogn = excluded.arter_dogn;
    update public.ledertavle set merket = true where user_id = uid;
  end if;
end $$;
create or replace function public.godkjenn(uid uuid) returns void
language sql security definer set search_path = '' as $$
  update public.merket set godkjent = now() where user_id = uid;
  update public.ledertavle set merket = false where user_id = uid;
$$;

-- hver gang frøene sendes: øyeblikksbildet for timen, og sjekken
create or replace function public.logg_fro() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.fro_logg (user_id, tid, fro, arter)
    values (new.user_id, date_trunc('hour', now()), greatest(0, new.fro - new.fro_utenfor), greatest(0, new.arter - new.arter_utenfor))
    on conflict (user_id, tid) do update set fro = excluded.fro, arter = excluded.arter;
  perform public.sjekk_merking(new.user_id);
  return null;
end $$;
drop trigger if exists ledertavle_logg on public.ledertavle;
create trigger ledertavle_logg after insert or update of fro, fro_utenfor, arter, arter_utenfor on public.ledertavle
  for each row execute function public.logg_fro();

revoke execute on function public.periode_poeng(timestamptz, timestamptz), public.sjekk_merking(uuid), public.godkjenn(uuid), public.logg_fro()
  from public, anon, authenticated;
grant execute on function public.tavle(text) to anon, authenticated;
grant execute on function public.avslutt_perioder() to authenticated;
grant select on public.premier to anon, authenticated;

-- med Cron slått på (Integrations → Cron), avsluttes periodene hver time; ellers når noen åpner tavla eller sender
do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    execute $c$select cron.schedule('fuglekort-perioder', '7 * * * *', 'select public.avslutt_perioder()')$c$;
  end if;
end $$;

-- ---------- Artstavla: flest fuglearter i uka, måneden, året og totalt ----------
-- Uke, måned og år: fuglearter med minst én observasjonsdag i perioden (norsk tid), fra tabellen sett. Totalt:
-- fuglearter registrert i appen (arter på tavla). Dyrekortene teller ikke (tabellen dyrearter; legg nye dyrekort
-- inn der). Bare den som står på tavla, er med. Likt antall gir delt plass; flest frø står først. Ingen premier.
-- «Sett før appen» ligger bare på telefonen og teller ikke. Appen henter bare plass, antall og navn, aldri datoer.
create table if not exists public.dyrearter (art text primary key check (art ~ '^[a-z]+(-[a-z]+){1,3}$'));
alter table public.dyrearter enable row level security;
insert into public.dyrearter (art) values
  ('sciurus-vulgaris'), ('capreolus-capreolus'), ('lepus-timidus'), ('alces-alces'), ('vulpes-vulpes'),
  ('aglais-urticae'), ('coccinella-septempunctata'), ('bombus-terrestris'), ('cepaea-hortensis'), ('rana-temporaria'),
  ('apodemus-sylvaticus'), ('erinaceus-europaeus'), ('sorex-araneus'), ('bufo-bufo'), ('meles-meles'),
  ('anguis-fragilis'), ('vipera-berus')
on conflict (art) do nothing;

create or replace function public.tavle_arter(hva text) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare s timestamptz; e timestamptz; fra date; til date; meg uuid := (select auth.uid()); ut jsonb;
begin
  if hva is null or hva not in ('uke', 'mnd', 'aar', 'tot') then raise exception 'ukjent periode'; end if;
  if hva <> 'tot' then
    s := public.periode_start(hva); e := public.periode_slutt(hva, s);
    fra := (s at time zone 'Europe/Oslo')::date; til := (e at time zone 'Europe/Oslo')::date;
  end if;
  with tall as (
    select l.user_id,
      case when hva = 'tot' then l.arter::bigint else (
        select count(*) from public.sett st
        where st.user_id = l.user_id and not exists (select 1 from public.dyrearter da where da.art = st.art)
          and exists (select 1 from unnest(st.dager) d where d >= fra and d < til)) end as n
    from public.ledertavle l
  ), r as (
    select t.user_id, t.n, l.navn, l.ord, l.fugl, l.tall, l.tittel, l.arter, l.dager, l.fro, l.merket,
           rank() over (order by t.n desc) as plass,
           row_number() over (order by t.n desc, l.fro desc, l.user_id) as rekke
    from tall t join public.ledertavle l on l.user_id = t.user_id
    where t.n > 0
  )
  select jsonb_build_object(
    'periode', case when hva = 'tot' then null else public.periode_navn(hva, s) end, 'fra', s, 'til', e,
    'antall', (select count(*) from r),
    'plass', (select r.plass from r where r.user_id = meg),
    'meg', (select r.n from r where r.user_id = meg),
    'rader', coalesce((select jsonb_agg(jsonb_build_object('user_id', r.user_id, 'navn', r.navn, 'ord', r.ord, 'fugl', r.fugl, 'tall', r.tall,
                         'tittel', r.tittel, 'n', r.n, 'arter', r.arter, 'dager', r.dager, 'fro', r.fro, 'merket', r.merket, 'plass', r.plass) order by r.rekke)
                       from r where r.rekke <= 50), '[]'::jsonb)
  ) into ut;
  return ut;
end $$;
grant execute on function public.tavle_arter(text) to anon, authenticated;

-- Merking: mer enn 40 fuglearter registrert på samme dag (norsk tid). Som for frøene: merket på tavla, ingen premier
-- før du godkjenner (select public.godkjenn('<user_id>');), og ikke merket igjen samme dag etter en godkjenning.
create or replace function public.sjekk_arter_dag() returns trigger
language plpgsql security definer set search_path = '' as $$
declare idag date := (now() at time zone 'Europe/Oslo')::date; n integer; g timestamptz;
begin
  if not (idag = any(new.dager)) then return null; end if;
  if exists (select 1 from public.ledertavle l where l.user_id = new.user_id and l.merket) then return null; end if;
  select m.godkjent into g from public.merket m where m.user_id = new.user_id;
  if g is not null and (g at time zone 'Europe/Oslo')::date = idag then return null; end if;
  select count(*) into n from public.sett st
  where st.user_id = new.user_id and idag = any(st.dager) and not exists (select 1 from public.dyrearter da where da.art = st.art);
  if n > 40 then
    insert into public.merket (user_id, tid, grunn, fro_dogn, arter_dogn) values (new.user_id, now(), 'mer enn 40 arter på én dag', null, n)
      on conflict (user_id) do update set tid = excluded.tid, grunn = excluded.grunn, fro_dogn = excluded.fro_dogn, arter_dogn = excluded.arter_dogn;
    update public.ledertavle set merket = true where user_id = new.user_id;
  end if;
  return null;
end $$;
drop trigger if exists sett_arter_dag on public.sett;
create trigger sett_arter_dag after insert or update of dager on public.sett for each row execute function public.sjekk_arter_dag();
revoke execute on function public.sjekk_arter_dag() from public, anon, authenticated;

-- ---------- Profilen på tavla: fugleartene en bruker har registrert ----------
-- Trykker man på et navn på tavla, viser appen «42 fugler observert i hagen» og fuglene: artene fra tabellen sett, uten
-- datoer og antall dager, uten dyrekort (dyrearter) og uten «sett før appen» (som bare ligger på telefonen). Bare for
-- brukere på tavla. Den som har slått av «Vis artslista mi» i appen (vis_arter = false), viser bare antallet; en selv
-- ser alltid sin egen liste.
create or replace function public.profil_arter(uid uuid) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare l public.ledertavle; arter jsonb; vis boolean;
begin
  select * into l from public.ledertavle where user_id = uid;
  if not found then return null; end if;
  select coalesce(jsonb_agg(st.art order by st.art), '[]'::jsonb) into arter
  from public.sett st where st.user_id = uid and not exists (select 1 from public.dyrearter da where da.art = st.art);
  vis := l.vis_arter or uid = (select auth.uid());
  return jsonb_build_object('user_id', uid, 'navn', l.navn, 'antall', jsonb_array_length(arter), 'vis', vis,
                            'arter', case when vis then arter end);
end $$;
grant execute on function public.profil_arter(uuid) to anon, authenticated;

-- ---------- «Slett meg»: den anonyme brukeren og alt som hører til ----------
create or replace function public.slett_meg() returns void
language sql security definer set search_path = '' as $$
  delete from auth.users where id = (select auth.uid());
$$;
revoke execute on function public.slett_meg() from public, anon;
grant execute on function public.slett_meg() to authenticated;

-- ---------- Eksempler på statistikk (kjør i SQL Editor) ----------
-- Hvor mange dager og brukere hver art er sett:
--   select art, count(*) as dager, count(distinct user_id) as brukere
--   from public.observasjoner group by art order by dager desc;
-- Arter per måned:
--   select to_char(dato, 'YYYY-MM') as maned, art, count(*) as dager
--   from public.observasjoner group by 1, 2 order by 1, 3 desc;
-- Per postnummer:
--   select p.postnr, o.art, count(*) as dager
--   from public.observasjoner o join public.profil p using (user_id)
--   where p.postnr is not null group by 1, 2 order by 1, 3 desc;
-- Rapporterte navn (de nyeste først):
--   select r.navn, count(*) as rapporter, max(r.tid) as sist from public.rapporter r group by 1 order by 3 desc;
-- Sperre et navn selv og fjerne det fra tavlen (eieren får beskjed om å velge et nytt):
--   insert into public.stengte_navn (navn) values (lower('Navnet'));
--   update public.ledertavle set navn = null where public.navn_nokkel(navn) = lower('Navnet');
-- Åpne et sperret navn igjen:
--   delete from public.stengte_navn where navn = lower('Navnet');
-- Ukestavla akkurat nå (som i appen):
--   select public.tavle('uke');
-- Artstavla akkurat nå (uke, mnd, aar eller tot):
--   select public.tavle_arter('uke');
-- Profilen til en bruker, slik appen ser den:
--   select public.profil_arter('<user_id>');
-- Premiene som er delt ut:
--   select * from public.premier order by tid desc;
-- Merkede brukere, og godkjenne en (fjerner merket; det som kom før, teller ikke igjen):
--   select m.*, l.navn from public.merket m left join public.ledertavle l using (user_id) order by m.tid desc;
--   select public.godkjenn('<user_id>');
-- Tellinger: høyeste antall per art og telling:
--   select t.user_id, t.start, a.key as art, a.value::int as antall
--   from public.tellinger t cross join lateral jsonb_each_text(t.arter) a;
