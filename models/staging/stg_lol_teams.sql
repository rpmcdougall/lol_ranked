{{
  config(
    materialized='view',
    description='Staging model for League of Legends team data from ETL CSV output'
  )
}}

WITH source_data AS (
    SELECT * FROM {{ source('etl_raw', 'lol_ranked_matches') }}
),

team_1_data AS (
    SELECT
        match_id,
        region,
        platform,
        season,
        game_version,
        game_creation,
        game_duration,
        queue_id,
        queue_name,
        
        -- Team 1 data
        1 as team_id,
        team_1_win as win,
        team_1_first_blood as first_blood,
        team_1_first_tower as first_tower,
        team_1_first_inhibitor as first_inhibitor,
        team_1_first_baron as first_baron,
        team_1_first_dragon as first_dragon,
        team_1_first_rift_herald as first_rift_herald,
        team_1_tower_kills as tower_kills,
        team_1_inhibitor_kills as inhibitor_kills,
        team_1_baron_kills as baron_kills,
        team_1_dragon_kills as dragon_kills,
        team_1_rift_herald_kills as rift_herald_kills,
        
        CURRENT_TIMESTAMP() as _loaded_at,
        'etl_csv' as _source
        
    FROM source_data
),

team_2_data AS (
    SELECT
        match_id,
        region,
        platform,
        season,
        game_version,
        game_creation,
        game_duration,
        queue_id,
        queue_name,
        
        -- Team 2 data
        2 as team_id,
        team_2_win as win,
        team_2_first_blood as first_blood,
        team_2_first_tower as first_tower,
        team_2_first_inhibitor as first_inhibitor,
        team_2_first_baron as first_baron,
        team_2_first_dragon as first_dragon,
        team_2_first_rift_herald as first_rift_herald,
        team_2_tower_kills as tower_kills,
        team_2_inhibitor_kills as inhibitor_kills,
        team_2_baron_kills as baron_kills,
        team_2_dragon_kills as dragon_kills,
        team_2_rift_herald_kills as rift_herald_kills,
        
        CURRENT_TIMESTAMP() as _loaded_at,
        'etl_csv' as _source
        
    FROM source_data
),

all_teams AS (
    SELECT * FROM team_1_data
    UNION ALL
    SELECT * FROM team_2_data
),

final_data AS (
    SELECT
        *,
        -- Derived fields
        tower_kills + inhibitor_kills + baron_kills + dragon_kills + rift_herald_kills as total_objectives,
        
        -- Objective efficiency (objectives per minute)
        CASE 
            WHEN game_duration > 0 THEN ROUND((tower_kills + inhibitor_kills + baron_kills + dragon_kills + rift_herald_kills) / (game_duration / 60.0), 3)
            ELSE NULL
        END as objectives_per_minute,
        
        -- First objective count
        CASE WHEN first_blood THEN 1 ELSE 0 END +
        CASE WHEN first_tower THEN 1 ELSE 0 END +
        CASE WHEN first_inhibitor THEN 1 ELSE 0 END +
        CASE WHEN first_baron THEN 1 ELSE 0 END +
        CASE WHEN first_dragon THEN 1 ELSE 0 END +
        CASE WHEN first_rift_herald THEN 1 ELSE 0 END as first_objectives_count,
        
        -- Team performance score (simple weighted calculation)
        (tower_kills * 1) + 
        (inhibitor_kills * 3) + 
        (baron_kills * 5) + 
        (dragon_kills * 2) + 
        (rift_herald_kills * 2) as objective_score
        
    FROM all_teams
)

SELECT * FROM final_data 