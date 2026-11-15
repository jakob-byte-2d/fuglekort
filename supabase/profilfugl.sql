-- Profilbildet på tavla (15. november 2026): fuglen du har valgt som profilbilde (en fugl fra livslisten) vises ved
-- navnet ditt på tavla, i gruppene, i favorittene og på profilen din. Kjør hele fila én gang i SQL Editor i Supabase.
-- Den kan kjøres flere ganger. Det samme står i fuglekort.sql.
--   ledertavle.profilfugl   artsnavnet, eller tom (tittelikonet)
--   tavle, tavle_arter, tavle_utvalg (grupper og favoritter) og profil_arter sender den med
-- Et eget bilde sendes aldri; appen har bare fugler som profilbilde.

-- profilbildet: en fugl fra livslisten (artsnavnet, f.eks. parus-major), eller tom for tittelikonet
alter table public.ledertavle add column if not exists profilfugl text
  constraint ledertavle_profilfugl_form check (profilfugl is null or (profilfugl ~ '^[a-z]+(-[a-z]+){1,3}$' and length(profilfugl) <= 50));

-- appen kan skrive sine egne kolonner, men aldri «merket»
revoke insert, update on public.ledertavle from authenticated;
grant insert (user_id, navn, ord, fugl, tall, fro, arter, dager, tittel, fro_utenfor, arter_utenfor, vis_arter, profilfugl),
      update (user_id, navn, ord, fugl, tall, fro, arter, dager, tittel, fro_utenfor, arter_utenfor, vis_arter, profilfugl) on public.ledertavle to authenticated;

create or replace function public.tavle(hva text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare s timestamptz; e timestamptz; meg uuid := (select auth.uid()); ut jsonb;
begin
  if hva is null or hva not in ('uke', 'mnd', 'aar') then raise exception 'ukjent periode'; end if;
  perform public.avslutt_perioder();
  s := public.periode_start(hva); e := public.periode_slutt(hva, s);
  with r as (
    select pp.user_id, pp.poeng, l.navn, l.ord, l.fugl, l.tall, l.tittel, l.arter, l.dager, l.merket, l.profilfugl,
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
                         'tittel', r.tittel, 'arter', r.arter, 'dager', r.dager, 'merket', r.merket, 'fro', r.poeng, 'profilfugl', r.profilfugl) order by r.nr) from r where r.nr <= 50), '[]'::jsonb),
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
    select t.user_id, t.n, l.navn, l.ord, l.fugl, l.tall, l.tittel, l.arter, l.dager, l.fro, l.merket, l.profilfugl,
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
                         'tittel', r.tittel, 'n', r.n, 'arter', r.arter, 'dager', r.dager, 'fro', r.fro, 'merket', r.merket, 'plass', r.plass,
                         'profilfugl', r.profilfugl) order by r.rekke)
                       from r where r.rekke <= 50), '[]'::jsonb)
  ) into ut;
  return ut;
end $$;

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
                            'arter', case when vis then arter end, 'profilfugl', l.profilfugl);
end $$;

create or replace function public.tavle_utvalg(ider uuid[], hva text, etter text) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare s timestamptz; e timestamptz; fra date; til date; meg uuid := (select auth.uid()); ut jsonb;
begin
  if hva is null or hva not in ('uke', 'mnd', 'aar', 'tot') then raise exception 'ukjent periode'; end if;
  if etter is null or etter not in ('fro', 'arter') then raise exception 'ukjent tavle'; end if;
  if hva <> 'tot' then
    s := public.periode_start(hva); e := public.periode_slutt(hva, s);
    fra := (s at time zone 'Europe/Oslo')::date; til := (e at time zone 'Europe/Oslo')::date;
  end if;
  with u as (
    select l.* from public.ledertavle l where l.user_id = any(ider)
  ), pp as (
    select p.user_id, p.poeng, p.sist from public.periode_poeng(s, e) p where hva <> 'tot' and etter = 'fro' and p.user_id = any(ider)
  ), tall as (
    select u.user_id, pp.sist,
      case when etter = 'fro' then (case when hva = 'tot' then u.fro else coalesce(pp.poeng, 0) end)
           when hva = 'tot' then u.arter::bigint
           else (select count(*) from public.sett st
                 where st.user_id = u.user_id and not exists (select 1 from public.dyrearter da where da.art = st.art)
                   and exists (select 1 from unnest(st.dager) d where d >= fra and d < til)) end as n
    from u left join pp on pp.user_id = u.user_id
  ), r as (
    select t.user_id, t.n, u.navn, u.ord, u.fugl, u.tall, u.tittel, u.arter, u.dager, u.fro, u.merket, u.profilfugl,
           rank() over (order by t.n desc) as plass,
           row_number() over (order by t.n desc, t.sist asc nulls last, u.fro desc, u.user_id) as rekke
    from tall t join u on u.user_id = t.user_id
  )
  select jsonb_build_object(
    'periode', case when hva = 'tot' then null else public.periode_navn(hva, s) end, 'fra', s, 'til', e,
    'antall', (select count(*) from r),
    'plass', (select r.plass from r where r.user_id = meg),
    'meg', (select r.n from r where r.user_id = meg),
    'rader', coalesce((select jsonb_agg(jsonb_build_object('user_id', r.user_id, 'navn', r.navn, 'ord', r.ord, 'fugl', r.fugl, 'tall', r.tall,
                         'tittel', r.tittel, 'n', r.n, 'fro', case when etter = 'fro' then r.n else r.fro end, 'arter', r.arter,
                         'dager', r.dager, 'merket', r.merket, 'plass', r.plass, 'profilfugl', r.profilfugl) order by r.rekke) from r), '[]'::jsonb)
  ) into ut;
  return ut;
end $$;

select 'profilfugl klar' as status;
