{{
  config(
    materialized='view',
    description='Staging model for League of Legends participant data from ETL CSV output'
  )
}}

WITH source_data AS (
    SELECT * FROM {{ source('etl_raw', 'lol_ranked_matches') }}
),

participant_data AS (
    SELECT
        -- Match identification
        match_id,
        region,
        platform,
        
        -- Game metadata
        season,
        game_version,
        game_creation,
        game_duration,
        queue_id,
        queue_name,
        
        -- Participant information
        participant_1_summoner_id as summoner_id,
        participant_1_summoner_name as summoner_name,
        participant_1_champion_id as champion_id,
        participant_1_champion_name as champion_name,
        participant_1_team_id as team_id,
        
        -- Participant statistics
        participant_1_kills as kills,
        participant_1_deaths as deaths,
        participant_1_assists as assists,
        participant_1_gold_earned as gold_earned,
        participant_1_total_damage_dealt as total_damage_dealt,
        participant_1_vision_score as vision_score,
        participant_1_win as win,
        
        -- Data quality and processing metadata
        CURRENT_TIMESTAMP() as _loaded_at,
        'etl_csv' as _source,
        1 as participant_number  -- Currently only one participant per match in CSV
        
    FROM source_data
    WHERE participant_1_summoner_id IS NOT NULL  -- Only include records with participant data
),

final_data AS (
    SELECT
        *,
        -- Derived fields
        CASE 
            WHEN deaths = 0 THEN kills + assists
            ELSE ROUND((kills + assists) / deaths::float, 2)
        END as kda,
        
        -- Damage per gold ratio
        CASE 
            WHEN gold_earned > 0 THEN ROUND(total_damage_dealt / gold_earned::float, 4)
            ELSE NULL
        END as damage_per_gold,
        
        -- Vision score per minute
        CASE 
            WHEN game_duration > 0 THEN ROUND(vision_score / (game_duration / 60.0), 2)
            ELSE NULL
        END as vision_score_per_minute,
        
        -- Performance tier based on KDA
        CASE 
            WHEN deaths = 0 THEN 'Perfect'
            WHEN (kills + assists) / deaths::float >= 3.0 THEN 'Excellent'
            WHEN (kills + assists) / deaths::float >= 2.0 THEN 'Good'
            WHEN (kills + assists) / deaths::float >= 1.0 THEN 'Average'
            ELSE 'Poor'
        END as performance_tier
        
    FROM participant_data
)

SELECT * FROM final_data 