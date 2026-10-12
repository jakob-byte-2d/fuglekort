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
-- Tellinger: høyeste antall per art og telling:
--   select t.user_id, t.start, a.key as art, a.value::int as antall
--   from public.tellinger t cross join lateral jsonb_each_text(t.arter) a;
