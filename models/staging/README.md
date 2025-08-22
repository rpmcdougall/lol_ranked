# Staging Models

This directory contains staging models that clean and standardize raw data from the ETL process before it moves to the core data models.

## Overview

Staging models serve as the first layer of data transformation in our dbt project. They:
- Clean and validate raw data from CSV files
- Add derived fields and calculations
- Standardize data types and formats
- Apply basic business logic
- Prepare data for downstream models

## Models

### `stg_lol_ranked_matches`
**Purpose**: Main staging model for ranked match data
**Source**: `etl_raw.lol_ranked_matches` (CSV from ETL process)

**Key Features**:
- Cleans and validates match metadata
- Adds derived fields like `winning_team_id`, `game_duration_minutes`
- Calculates participant KDA ratios
- Groups regions for analysis
- Extracts major patch versions

**Derived Fields**:
- `winning_team_id`: ID of the winning team (1 or 2)
- `game_duration_minutes`: Game duration converted to minutes
- `participant_1_kda`: KDA ratio for the representative participant
- `major_patch`: Major patch version (e.g., "14.1")
- `region_group`: Geographic region grouping

### `stg_lol_participants`
**Purpose**: Staging model for participant data
**Source**: `etl_raw.lol_ranked_matches` (extracted participant data)

**Key Features**:
- Normalizes participant information
- Calculates performance metrics
- Assigns performance tiers based on KDA
- Currently handles one participant per match (expandable)

**Derived Fields**:
- `kda`: Kill/Death/Assist ratio
- `damage_per_gold`: Damage efficiency metric
- `vision_score_per_minute`: Vision control efficiency
- `performance_tier`: Categorical performance rating

### `stg_lol_teams`
**Purpose**: Staging model for team data
**Source**: `etl_raw.lol_ranked_matches` (extracted team data)

**Key Features**:
- Normalizes team information (creates separate rows for each team)
- Calculates objective-based metrics
- Provides team performance scoring

**Derived Fields**:
- `total_objectives`: Sum of all objectives secured
- `objectives_per_minute`: Objective efficiency rate
- `first_objectives_count`: Number of first objectives secured
- `objective_score`: Weighted objective performance score

## Data Quality Tests

All staging models include comprehensive data quality tests defined in `schema.yml`:

### Source Tests
- **Uniqueness**: Match IDs are unique
- **Not Null**: Required fields are populated
- **Accepted Values**: Categorical fields have valid values
- **Range Tests**: Numeric fields are within expected ranges

### Model Tests
- **Business Logic**: Derived fields meet business rules
- **Data Completeness**: Required derived fields are populated
- **Value Validation**: Calculated metrics are reasonable

## Usage

### Running Staging Models
```bash
# Run all staging models
dbt run --select staging

# Run specific staging model
dbt run --select stg_lol_ranked_matches

# Run with tests
dbt build --select staging
```

### Testing
```bash
# Test staging models
dbt test --select staging

# Test specific model
dbt test --select stg_lol_ranked_matches
```

## Data Flow

```
ETL CSV Files → Source Definition → Staging Models → Core Models → Marts
```

1. **ETL Process**: Generates CSV files with raw match data
2. **Source Definition**: `etl_raw.lol_ranked_matches` references CSV data
3. **Staging Models**: Clean, validate, and enrich the data
4. **Core Models**: Transform into dimensional models
5. **Marts**: Create business-ready datasets

## Future Enhancements

### Participant Data Expansion
Currently, the ETL process only includes one participant per match in the CSV. Future enhancements could:
- Include all 10 participants per match
- Create separate participant staging models
- Add role-based participant analysis

### Additional Metrics
Potential new derived fields:
- Win rate calculations
- Champion performance metrics
- Team composition analysis
- Meta game insights

### Data Quality Improvements
- Add more sophisticated validation rules
- Implement data freshness monitoring
- Create custom test macros for business logic

## Dependencies

- **dbt-utils**: For additional test macros (`is_positive`, `is_non_negative`)
- **Raw CSV Data**: From ETL process in Google Cloud Storage
- **Source Configuration**: Defined in `schema.yml`

## Notes

- All staging models are materialized as views for performance and flexibility
- Models include `_loaded_at` and `_source` metadata fields for data lineage
- Error handling and data quality checks are built into the models
- Models are designed to be idempotent and rerunnable 