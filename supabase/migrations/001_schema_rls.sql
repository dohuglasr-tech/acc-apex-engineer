-- ============================================================================
-- ACC Apex Engineer Pro - Migración 001: Esquema Multi-Usuario con RLS Estricto
-- Autenticación: Discord OAuth vía Supabase Auth
-- Aislamiento: 100% privado por usuario ((select auth.uid()) = id / user_id)
-- ============================================================================

create extension if not exists "pgcrypto";

-- 1. Perfil individual de cada piloto (vinculado a su Discord vía Supabase Auth)
create table if not exists public.profiles (
  id uuid references auth.users on delete cascade primary key,
  discord_username text,
  avatar_url text,
  input_mode text check (input_mode in ('keyboard', 'gamepad', 'wheel')), -- NULL al inicio para forzar la pregunta
  wheel_type text,
  agent_token uuid default gen_random_uuid() unique, -- Token único para conectar su ejecutable .exe
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 2. Setups individuales auto-generados e inyectados para ese usuario
create table if not exists public.user_setups (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  car_model text not null,
  track_name text not null,
  input_mode text not null check (input_mode in ('keyboard', 'gamepad', 'wheel')),
  version_num int not null default 1,
  file_name text not null, -- ej: APEX_AUTO_LIVE.json / APEX_V2.json
  setup_json jsonb not null, -- Estructura exacta de ACC (basicSetup + advancedSetup)
  changes_summary jsonb not null, -- Qué se ajustó automáticamente y por qué
  air_temp real,
  road_temp real,
  best_lap_ms int,
  created_at timestamptz default now()
);

-- 3. Vueltas, Telemetría, Errores Detectados y Soluciones por usuario
create table if not exists public.user_laps (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  setup_id uuid references public.user_setups(id) on delete set null,
  car_model text not null,
  track_name text not null,
  input_mode text not null check (input_mode in ('keyboard', 'gamepad', 'wheel')),
  lap_number int not null,
  lap_time_ms int not null,
  sector_1_ms int,
  sector_2_ms int,
  sector_3_ms int,
  is_valid boolean default true,
  tyre_pressures_hot real[4],
  tyre_temps_core real[4],
  brake_temps_avg real[4],
  bottoming_events int default 0,
  telemetry_trace jsonb not null, -- 100 muestras normalizadas (0..100% de pista: speed, gas, brake, steer, gear, slip)
  driving_errors jsonb not null,  -- Lista de errores por curva + solución concreta para su periférico
  created_at timestamptz default now()
);

-- Índices para consultas rápidas por usuario y evaluación RLS
create index if not exists idx_user_setups_user_id on public.user_setups(user_id, created_at desc);
create index if not exists idx_user_laps_user_id on public.user_laps(user_id, created_at desc);
create index if not exists idx_profiles_agent_token on public.profiles(agent_token);

-- Garantizar permisos sobre el esquema expuesto para el rol authenticated
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on public.profiles to authenticated;
grant select, insert, update, delete on public.user_setups to authenticated;
grant select, insert, update, delete on public.user_laps to authenticated;

-- ============================================================================
-- Row-Level Security (Aislamiento total entre cuentas con InitPlan caching)
-- ============================================================================
alter table public.profiles enable row level security;
alter table public.user_setups enable row level security;
alter table public.user_laps enable row level security;

-- Políticas de public.profiles
drop policy if exists "Usuarios ven solo su perfil" on public.profiles;
create policy "Usuarios ven solo su perfil" on public.profiles
  for select to authenticated
  using ( (select auth.uid()) = id );

drop policy if exists "Usuarios insertan solo su perfil" on public.profiles;
create policy "Usuarios insertan solo su perfil" on public.profiles
  for insert to authenticated
  with check ( (select auth.uid()) = id );

drop policy if exists "Usuarios actualizan solo su perfil" on public.profiles;
create policy "Usuarios actualizan solo su perfil" on public.profiles
  for update to authenticated
  using ( (select auth.uid()) = id )
  with check ( (select auth.uid()) = id );

-- Políticas de public.user_setups
drop policy if exists "Usuarios ven solo sus propios setups" on public.user_setups;
create policy "Usuarios ven solo sus propios setups" on public.user_setups
  for select to authenticated
  using ( (select auth.uid()) = user_id );

drop policy if exists "Usuarios crean solo sus propios setups" on public.user_setups;
create policy "Usuarios crean solo sus propios setups" on public.user_setups
  for insert to authenticated
  with check ( (select auth.uid()) = user_id );

drop policy if exists "Usuarios actualizan solo sus propios setups" on public.user_setups;
create policy "Usuarios actualizan solo sus propios setups" on public.user_setups
  for update to authenticated
  using ( (select auth.uid()) = user_id )
  with check ( (select auth.uid()) = user_id );

drop policy if exists "Usuarios eliminan solo sus propios setups" on public.user_setups;
create policy "Usuarios eliminan solo sus propios setups" on public.user_setups
  for delete to authenticated
  using ( (select auth.uid()) = user_id );

-- Políticas de public.user_laps
drop policy if exists "Usuarios ven solo sus propias vueltas" on public.user_laps;
create policy "Usuarios ven solo sus propias vueltas" on public.user_laps
  for select to authenticated
  using ( (select auth.uid()) = user_id );

drop policy if exists "Usuarios crean solo sus propias vueltas" on public.user_laps;
create policy "Usuarios crean solo sus propias vueltas" on public.user_laps
  for insert to authenticated
  with check ( (select auth.uid()) = user_id );

drop policy if exists "Usuarios actualizan solo sus propias vueltas" on public.user_laps;
create policy "Usuarios actualizan solo sus propias vueltas" on public.user_laps
  for update to authenticated
  using ( (select auth.uid()) = user_id )
  with check ( (select auth.uid()) = user_id );

drop policy if exists "Usuarios eliminan solo sus propias vueltas" on public.user_laps;
create policy "Usuarios eliminan solo sus propias vueltas" on public.user_laps
  for delete to authenticated
  using ( (select auth.uid()) = user_id );

-- ============================================================================
-- Trigger automático: Crea el perfil privado al iniciar sesión con Discord OAuth
-- ============================================================================
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, discord_username, avatar_url, input_mode)
  values (
    new.id,
    coalesce(
      new.raw_user_meta_data->>'custom_claims.global_name',
      new.raw_user_meta_data->>'full_name',
      new.raw_user_meta_data->>'name',
      new.email
    ),
    new.raw_user_meta_data->>'avatar_url',
    null -- Fuerza la pantalla de Onboarding (Teclado / Mando / Volante)
  )
  on conflict (id) do update set
    discord_username = coalesce(excluded.discord_username, public.profiles.discord_username),
    avatar_url = coalesce(excluded.avatar_url, public.profiles.avatar_url),
    updated_at = now();
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ============================================================================
-- RPCs seguras para el Agente Ejecutable Local (.exe) usando agent_token
-- ============================================================================
create or replace function public.verify_agent_token(p_agent_token uuid)
returns jsonb
language plpgsql
security definer set search_path = public
as $$
declare
  v_profile public.profiles%rowtype;
begin
  select * into v_profile
  from public.profiles
  where agent_token = p_agent_token;

  if not found then
    raise exception 'Token de agente inválido o revocado';
  end if;

  return jsonb_build_object(
    'id', v_profile.id,
    'discord_username', v_profile.discord_username,
    'avatar_url', v_profile.avatar_url,
    'input_mode', v_profile.input_mode,
    'wheel_type', v_profile.wheel_type
  );
end;
$$;

create or replace function public.update_agent_input_mode(
  p_agent_token uuid,
  p_input_mode text,
  p_wheel_type text default null
)
returns jsonb
language plpgsql
security definer set search_path = public
as $$
declare
  v_profile public.profiles%rowtype;
begin
  if p_input_mode not in ('keyboard', 'gamepad', 'wheel') then
    raise exception 'Modo de entrada inválido: %', p_input_mode;
  end if;

  update public.profiles
  set input_mode = p_input_mode,
      wheel_type = coalesce(p_wheel_type, wheel_type),
      updated_at = now()
  where agent_token = p_agent_token
  returning * into v_profile;

  if not found then
    raise exception 'Token de agente inválido';
  end if;

  return to_jsonb(v_profile);
end;
$$;

create or replace function public.agent_insert_setup(
  p_agent_token uuid,
  p_car_model text,
  p_track_name text,
  p_input_mode text,
  p_version_num int,
  p_file_name text,
  p_setup_json jsonb,
  p_changes_summary jsonb,
  p_air_temp real,
  p_road_temp real,
  p_best_lap_ms int default null
)
returns uuid
language plpgsql
security definer set search_path = public
as $$
declare
  v_user_id uuid;
  v_setup_id uuid;
begin
  select id into v_user_id from public.profiles where agent_token = p_agent_token;
  if v_user_id is null then
    raise exception 'Token de agente inválido';
  end if;

  insert into public.user_setups (
    user_id, car_model, track_name, input_mode, version_num,
    file_name, setup_json, changes_summary, air_temp, road_temp, best_lap_ms
  ) values (
    v_user_id, p_car_model, p_track_name, p_input_mode, p_version_num,
    p_file_name, p_setup_json, p_changes_summary, p_air_temp, p_road_temp, p_best_lap_ms
  )
  returning id into v_setup_id;

  return v_setup_id;
end;
$$;

create or replace function public.agent_insert_lap(
  p_agent_token uuid,
  p_setup_id uuid,
  p_car_model text,
  p_track_name text,
  p_input_mode text,
  p_lap_number int,
  p_lap_time_ms int,
  p_sector_1_ms int,
  p_sector_2_ms int,
  p_sector_3_ms int,
  p_is_valid boolean,
  p_tyre_pressures_hot real[4],
  p_tyre_temps_core real[4],
  p_brake_temps_avg real[4],
  p_bottoming_events int,
  p_telemetry_trace jsonb,
  p_driving_errors jsonb
)
returns uuid
language plpgsql
security definer set search_path = public
as $$
declare
  v_user_id uuid;
  v_lap_id uuid;
begin
  select id into v_user_id from public.profiles where agent_token = p_agent_token;
  if v_user_id is null then
    raise exception 'Token de agente inválido';
  end if;

  insert into public.user_laps (
    user_id, setup_id, car_model, track_name, input_mode, lap_number,
    lap_time_ms, sector_1_ms, sector_2_ms, sector_3_ms, is_valid,
    tyre_pressures_hot, tyre_temps_core, brake_temps_avg,
    bottoming_events, telemetry_trace, driving_errors
  ) values (
    v_user_id, p_setup_id, p_car_model, p_track_name, p_input_mode, p_lap_number,
    p_lap_time_ms, p_sector_1_ms, p_sector_2_ms, p_sector_3_ms, p_is_valid,
    p_tyre_pressures_hot, p_tyre_temps_core, p_brake_temps_avg,
    p_bottoming_events, p_telemetry_trace, p_driving_errors
  )
  returning id into v_lap_id;

  return v_lap_id;
end;
$$;
