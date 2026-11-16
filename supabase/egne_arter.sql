-- Egne arter i tellingen (16. november 2026): arter som ikke er i kortstokken, skrevet inn i Telleliste, lagres med
-- tellingen. Kjør hele fila én gang i SQL Editor i Supabase. Den kan kjøres flere ganger. Det samme står i fuglekort.sql.
--   tellinger.egne   navn → høyeste antall (privat, som resten av tellingen)

-- arter som ikke er i kortstokken, skrevet inn i Telleliste (16. november 2026): navn → høyeste antall
alter table public.tellinger add column if not exists egne jsonb not null default '{}'::jsonb
  constraint tellinger_egne_form check (jsonb_typeof(egne) = 'object' and pg_column_size(egne) <= 4000);

select 'egne arter klar' as status;
