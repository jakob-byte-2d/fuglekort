-- Merkede brukere vises ikke på den åpne ledertavla (15. november 2026), og grensen for arter på én dag er 25 (var 40).
-- Kjør hele fila én gang i SQL Editor i Supabase. Den kan kjøres flere ganger. Det samme står i fuglekort.sql.
--   ledertavlen (policyen, tavle og tavle_arter): merkede ser bare seg selv; grupper og favoritter viser dem med «!»
--   sjekk_arter_dag: merket ved mer enn 25 arter registrert på samme dag
--   merk(uid): merk en bruker for hånd, f.eks. en som har misforstått registreringen
--     select public.merk(user_id) from public.ledertavle where navn = 'Navnet';
--   godkjenn(uid) som før: tilbake på tavla

-- merkede brukere (uvanlig mange frø eller arter på kort tid) ser bare de selv på tavla, til de er godkjent
-- (15. november 2026; før stod de der med «!»). Grupper og favoritter (tavle_utvalg) viser dem
drop policy if exists "alle kan lese tavlen" on public.ledertavle;
create policy "alle kan lese tavlen" on public.ledertavle for select to anon, authenticated using (not merket or user_id = (select auth.uid()));

create or replace function public.merk(uid uuid, grunn text default 'merket for hånd') returns void
language sql security definer set search_path = '' as $$
  insert into public.merket (user_id, tid, grunn) values (uid, now(), grunn)
    on conflict (user_id) do update set tid = excluded.tid, grunn = excluded.grunn, fro_dogn = null, arter_dogn = null, godkjent = null;
  update public.ledertavle set merket = true where user_id = uid;
$$;
revoke execute on function public.merk(uuid, text) from public, anon, authenticated;

-- tavla for en periode (uke, mnd, aar): topp 50, antall, plassen og frøene dine, og forrige periodes premier
create or replace function public.tavle(hva text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare s timestamptz; e timestamptz; meg uuid := (select auth.uid()); ut jsonb;
begin
  if hva is null or hva not in ('uke', 'mnd', 'aar') then raise exception 'ukjent periode'; end if;
  perform public.avslutt_perioder();
  s := public.periode_start(hva); e := public.periode_slutt(hva, s);
  with r as (
    select pp.user_id, pp.poeng, l.navn, l.ord, l.fugl, l.tall, l.tittel, l.arter, l.dager, l.merket, l.profilfugl, l.profilsett,
           row_number() over (order by pp.poeng desc, pp.sist asc, pp.user_id) as nr
    from public.periode_poeng(s, e) pp join public.ledertavle l on l.user_id = pp.user_id
    where pp.poeng > 0 and (not l.merket or l.user_id = meg)          -- merkede: bare for seg selv
  )
  select jsonb_build_object(
    'periode', public.periode_navn(hva, s), 'fra', s, 'til', e,
    'antall', (select count(*) from r),
    'plass', (select r.nr from r where r.user_id = meg),
    'meg', (select r.poeng from r where r.user_id = meg),
    'rader', coalesce((select jsonb_agg(jsonb_build_object('user_id', r.user_id, 'navn', r.navn, 'ord', r.ord, 'fugl', r.fugl, 'tall', r.tall,
                         'tittel', r.tittel, 'arter', r.arter, 'dager', r.dager, 'merket', r.merket, 'fro', r.poeng, 'profilfugl', r.profilfugl, 'profilsett', r.profilsett) order by r.nr) from r where r.nr <= 50), '[]'::jsonb),
    'forrige', coalesce((select jsonb_agg(jsonb_build_object('plass', p.plass, 'navn', p.navn, 'poeng', p.poeng, 'fro', p.fro, 'user_id', p.user_id) order by p.plass)
                         from public.premier p where p.periode = public.periode_navn(hva, public.periode_start(hva, s - interval '1 second'))), '[]'::jsonb),
    'premier', to_jsonb(array[public.premie(hva, 1), public.premie(hva, 2), public.premie(hva, 3)])
  ) into ut;
  return ut;
end $$;

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
    select t.user_id, t.n, l.navn, l.ord, l.fugl, l.tall, l.tittel, l.arter, l.dager, l.fro, l.merket, l.profilfugl, l.profilsett,
           rank() over (order by t.n desc) as plass,
           row_number() over (order by t.n desc, l.fro desc, l.user_id) as rekke
    from tall t join public.ledertavle l on l.user_id = t.user_id
    where t.n > 0 and (not l.merket or l.user_id = meg)               -- merkede: bare for seg selv
  )
  select jsonb_build_object(
    'periode', case when hva = 'tot' then null else public.periode_navn(hva, s) end, 'fra', s, 'til', e,
    'antall', (select count(*) from r),
    'plass', (select r.plass from r where r.user_id = meg),
    'meg', (select r.n from r where r.user_id = meg),
    'rader', coalesce((select jsonb_agg(jsonb_build_object('user_id', r.user_id, 'navn', r.navn, 'ord', r.ord, 'fugl', r.fugl, 'tall', r.tall,
                         'tittel', r.tittel, 'n', r.n, 'arter', r.arter, 'dager', r.dager, 'fro', r.fro, 'merket', r.merket, 'plass', r.plass,
                         'profilfugl', r.profilfugl, 'profilsett', r.profilsett) order by r.rekke)
                       from r where r.rekke <= 50), '[]'::jsonb)
  ) into ut;
  return ut;
end $$;

-- Merking: mer enn 25 fuglearter registrert på samme dag (norsk tid; 40 til 15. november 2026). Som for frøene: borte
-- fra den åpne tavla, ingen premier før du godkjenner (select public.godkjenn('<user_id>');), og ikke merket igjen samme
-- dag etter en godkjenning.
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
  if n > 25 then
    insert into public.merket (user_id, tid, grunn, fro_dogn, arter_dogn) values (new.user_id, now(), 'mer enn 25 arter på én dag', null, n)
      on conflict (user_id) do update set tid = excluded.tid, grunn = excluded.grunn, fro_dogn = excluded.fro_dogn, arter_dogn = excluded.arter_dogn;
    update public.ledertavle set merket = true where user_id = new.user_id;
  end if;
  return null;
end $$;

select 'merket skjult klar' as status;
