{{
  config(
    materialized='view',
    description='Staging model for League of Legends ranked match data from ETL CSV output'
  )
}}

WITH source_data AS (
    SELECT * FROM {{ source('etl_raw', 'lol_ranked_matches') }}
),

cleaned_data AS (
    SELECT
        -- Match identification
        match_id,
        region,
        platform,
        
        -- Queue information
        queue_id,
        queue_name,
        
        -- Game metadata
        season,
        game_version,
        game_creation,
        game_duration,
        game_mode,
        game_type,
        map_id,
        
        -- Team 1 data
        team_1_id,
        team_1_win,
        team_1_first_blood,
        team_1_first_tower,
        team_1_first_inhibitor,
        team_1_first_baron,
        team_1_first_dragon,
        team_1_first_rift_herald,
        team_1_tower_kills,
        team_1_inhibitor_kills,
        team_1_baron_kills,
        team_1_dragon_kills,
        team_1_rift_herald_kills,
        
        -- Team 2 data
        team_2_id,
        team_2_win,
        team_2_first_blood,
        team_2_first_tower,
        team_2_first_inhibitor,
        team_2_first_baron,
        team_2_first_dragon,
        team_2_first_rift_herald,
        team_2_tower_kills,
        team_2_inhibitor_kills,
        team_2_baron_kills,
        team_2_dragon_kills,
        team_2_rift_herald_kills,
        
        -- Participant 1 data (representative participant)
        participant_1_summoner_id,
        participant_1_summoner_name,
        participant_1_champion_id,
        participant_1_champion_name,
        participant_1_team_id,
        participant_1_kills,
        participant_1_deaths,
        participant_1_assists,
        participant_1_gold_earned,
        participant_1_total_damage_dealt,
        participant_1_vision_score,
        participant_1_win,
        
        -- Data quality and processing metadata
        CURRENT_TIMESTAMP() as _loaded_at,
        'etl_csv' as _source
        
    FROM source_data
),

final_data AS (
    SELECT
        *,
        -- Derived fields
        CASE 
            WHEN team_1_win = true THEN 1
            WHEN team_2_win = true THEN 2
            ELSE NULL
        END as winning_team_id,
        
        -- Game duration in minutes
        ROUND(game_duration / 60.0, 2) as game_duration_minutes,
        
        -- Participant KDA
        CASE 
            WHEN participant_1_deaths = 0 THEN participant_1_kills + participant_1_assists
            ELSE ROUND((participant_1_kills + participant_1_assists) / participant_1_deaths::float, 2)
        END as participant_1_kda,
        
        -- Season and patch parsing
        SPLIT_PART(game_version, '.', 1) || '.' || SPLIT_PART(game_version, '.', 2) as major_patch,
        
        -- Region grouping
        CASE 
            WHEN region IN ('NA', 'LAN', 'LAS', 'BR') THEN 'Americas'
            WHEN region IN ('EUW', 'EUNE', 'TR', 'RU') THEN 'Europe'
            WHEN region IN ('KR', 'JP') THEN 'Asia'
            WHEN region = 'OCE' THEN 'Oceania'
            WHEN region = 'SEA' THEN 'Southeast Asia'
            ELSE 'Other'
        END as region_group
        
    FROM cleaned_data
)

SELECT * FROM final_data 