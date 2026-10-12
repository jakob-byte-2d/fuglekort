-- Fuglekort: felles ledertavle og observasjoner til statistikk
-- Lim inn alt i Supabase → SQL Editor og trykk Run. Kan kjøres flere ganger.
--
-- Hver telefon (hver bruker i appen) er en anonym Supabase-bruker. Telefonen er fasit; her ligger en kopi.
--   ledertavle   oppsummeringen som vises på tavlen       alle kan lese, bare eieren kan skrive
--   profil       postnummer (valgfritt), appversjon …      bare eieren
--   sett         observasjonsdagene, én rad per art        bare eieren
--   tellinger    hagefugltellingene                        bare eieren
--   kjop         kjøp i Frøbutikken                        bare eieren
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
-- Kallenavnet lagres som ord-ID-er fra lister i appen («rask» + «parus-major» + 42 → «Rask Kjøttmeis 42»),
-- aldri som fritekst: appen viser bare ord den kjenner.
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
-- Tellinger: høyeste antall per art og telling:
--   select t.user_id, t.start, a.key as art, a.value::int as antall
--   from public.tellinger t cross join lateral jsonb_each_text(t.arter) a;
