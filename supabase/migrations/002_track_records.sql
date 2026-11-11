-- Migration 002: Agregar soporte para récord histórico de vuelta por pista en get_active_telemetry_state

create or replace function public.get_active_telemetry_state(p_user_id uuid default null)
returns jsonb
language plpgsql
security definer set search_path = public
as $$
declare
  v_target_user_id uuid;
  v_prof public.profiles%rowtype;
  v_setups jsonb;
  v_last_lap jsonb;
  v_track_records jsonb;
begin
  v_target_user_id := coalesce(p_user_id, auth.uid());

  if v_target_user_id is null then
    return jsonb_build_object(
      'found', false,
      'error', 'No se ha especificado ningún usuario ni existe sesión activa.'
    );
  end if;

  select * into v_prof from public.profiles where id = v_target_user_id limit 1;

  if not found then
    return jsonb_build_object('found', false, 'error', 'Perfil no encontrado');
  end if;

  select coalesce(jsonb_agg(t), '[]'::jsonb) into v_setups
  from (
    select id, version_num, file_name, car_model, track_name, input_mode,
           created_at, air_temp, road_temp, best_lap_ms, changes_summary, setup_json
    from public.user_setups
    where user_id = v_prof.id
    order by created_at desc
    limit 15
  ) t;

  select to_jsonb(l) into v_last_lap
  from (
    select lap_number, lap_time_ms, telemetry_trace, driving_errors, created_at
    from public.user_laps
    where user_id = v_prof.id
    order by created_at desc
    limit 1
  ) l;

  select coalesce(jsonb_object_agg(track_name, best_ms), '{}'::jsonb) into v_track_records
  from (
    select track_name, min(lap_time_ms) as best_ms
    from public.user_laps
    where user_id = v_prof.id and is_valid = true and lap_time_ms > 45000 and lap_time_ms < 600000
    group by track_name
  ) b;

  return jsonb_build_object(
    'found', true,
    'profile', jsonb_build_object(
      'id', v_prof.id,
      'discord_username', v_prof.discord_username,
      'avatar_url', v_prof.avatar_url,
      'input_mode', v_prof.input_mode,
      'wheel_type', v_prof.wheel_type,
      'agent_token', v_prof.agent_token,
      'is_live_acc', v_prof.is_live_acc,
      'live_telemetry', v_prof.live_telemetry,
      'updated_at', v_prof.updated_at,
      'seconds_since_seen', extract(epoch from (now() - v_prof.updated_at))
    ),
    'setups', v_setups,
    'last_lap', v_last_lap,
    'track_records', v_track_records
  );
end;
$$;

