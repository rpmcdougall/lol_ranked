# League of Legends Ranked Analytics Platform

A comprehensive data analytics platform for League of Legends ranked match data, featuring automated data collection, transformation, and analysis using modern data engineering practices.

## 🏗️ Project Overview

This platform consists of multiple components working together to collect, process, and analyze League of Legends ranked match data:

- **ETL Pipeline**: Automated data collection from Riot Games API
- **Data Warehouse**: Structured data storage and transformation
- **Analytics**: Data modeling and analysis using dbt
- **Visualization**: Data insights and reporting

## 📁 Project Structure

```
lol_ranked/
├── etl/                    # Data extraction and loading
│   ├── etl.py             # Main ETL script
│   ├── Dockerfile         # Container configuration
│   ├── requirements.txt   # Python dependencies
│   ├── test_etl.py        # Unit tests
│   └── README.md          # ETL documentation
├── models/                 # dbt data models
│   ├── staging/           # Staging models (data cleaning)
│   │   ├── stg_lol_ranked_matches.sql
│   │   ├── stg_lol_participants.sql
│   │   ├── stg_lol_teams.sql
│   │   ├── schema.yml     # Model definitions and tests
│   │   └── README.md      # Staging documentation
│   └── example/           # Example models
├── tests/                  # dbt data tests
├── macros/                 # dbt macros
├── snapshots/              # dbt snapshots
├── seeds/                  # dbt seed data
├── analyses/               # dbt analyses
├── dbt_project.yml         # dbt project configuration
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Data Collection (ETL)

First, set up and run the ETL pipeline to collect data:

```bash
# Navigate to ETL directory
cd etl

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys

# Run the ETL pipeline
python etl.py
```

For detailed ETL setup instructions, see [etl/README.md](etl/README.md).

### 2. Data Transformation (dbt)

Once you have data, transform it using dbt:

```bash
# Install dbt (if not already installed)
pip install dbt-core dbt-bigquery  # or dbt-snowflake, dbt-postgres, etc.

# Initialize dbt (first time only)
dbt init

# Run data models
dbt run

# Test data quality
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

## 🔧 Components

### ETL Pipeline (`etl/`)

- **Purpose**: Extract ranked match data from Riot Games API
- **Features**:
  - Multi-region data collection
  - Rate limiting and error handling
  - Google Cloud Storage integration
  - Docker containerization
  - Comprehensive logging and monitoring

- **Technologies**: Python, cassiopeia, pandas, Google Cloud Storage
- **Output**: JSON and CSV files with match data

### Data Models (`models/`)

- **Purpose**: Transform raw data into analytics-ready tables
- **Features**:
  - Staging models for data cleaning and validation
  - Dimensional modeling
  - Data quality tests
  - Incremental processing
  - Documentation

- **Technologies**: dbt, SQL
- **Output**: Clean, structured data warehouse tables

#### Staging Models (`models/staging/`)
- **`stg_lol_ranked_matches`**: Main staging model for match data
- **`stg_lol_participants`**: Participant data normalization
- **`stg_lol_teams`**: Team data with performance metrics
- **Comprehensive testing**: Data quality and business logic validation

### Data Tests (`tests/`)

- **Purpose**: Ensure data quality and integrity
- **Features**:
  - Uniqueness tests
  - Not null tests
  - Custom business logic tests
  - Data freshness monitoring

### Macros (`macros/`)

- **Purpose**: Reusable SQL logic and utilities
- **Features**:
  - Common transformations
  - Utility functions
  - Best practices implementation

## 📊 Data Flow

```
Riot Games API → ETL Pipeline → Google Cloud Storage → dbt → Data Warehouse → Analytics
```

1. **Extract**: ETL script fetches ranked match data from Riot API
2. **Load**: Data is uploaded to Google Cloud Storage
3. **Transform**: dbt models transform raw data into analytics-ready tables
4. **Analyze**: Data is available for reporting and analysis

## 🛠️ Technology Stack

### Data Collection
- **Python 3.11+**: Core programming language
- **cassiopeia**: Riot Games API wrapper
- **pandas**: Data manipulation
- **Google Cloud Storage**: Data storage
- **Docker**: Containerization

### Data Transformation
- **dbt**: Data transformation and modeling
- **SQL**: Data manipulation language
- **BigQuery/Snowflake/PostgreSQL**: Data warehouse

### Infrastructure
- **Google Cloud Platform**: Cloud infrastructure
- **Docker Compose**: Container orchestration
- **Git**: Version control

## 📈 Data Schema

The platform collects and processes the following data:

### Match Data
- Match metadata (ID, region, queue, season)
- Game statistics (duration, version, mode)
- Participant information (summoners, champions, stats)
- Team objectives (towers, dragons, barons)

### Analytics Dimensions
- **Time**: Match timestamps, seasons, patches
- **Geography**: Regions, platforms
- **Players**: Summoners, champions, ranks
- **Gameplay**: Queues, modes, objectives

## 🔐 Security & Configuration

### Environment Variables

Required for ETL:
- `RIOT_API_KEY`: Riot Games API authentication
- `GCLOUD_PROJECT_ID`: Google Cloud project
- `GCLOUD_BUCKET`: Storage bucket

For Google Cloud Storage authentication, you have three options:

1. **Service Account with Environment Variables** (Recommended):
   - Set all `GCLOUD_*` environment variables (see `etl/env.example`)
   - Use `python create_service_account.py` to generate credentials file
   - More secure, no credential files in version control

2. **Direct Service Account File**:
   - Set `GCLOUD_CREDENTIALS_PATH` to point to your service account JSON file

3. **Application Default Credentials**:
   - Use `gcloud auth application-default login` for development

### Security Best Practices
- Never commit API keys or credentials
- Use environment variables for configuration
- Implement proper IAM roles and permissions
- Regular security audits and updates

## 🧪 Testing

### ETL Testing
```bash
cd etl
python run_tests.py
```

### dbt Testing
```bash
dbt test
dbt run --full-refresh
```

## 📚 Documentation

- [ETL Documentation](etl/README.md) - Complete ETL setup and usage guide
- [dbt Documentation](https://docs.getdbt.com/) - Official dbt documentation
- [Riot Games API](https://developer.riotgames.com/) - API reference

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Guidelines
- Follow Python PEP 8 style guide
- Write comprehensive tests
- Document new features
- Update relevant README files

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
1. Check the troubleshooting sections in component READMEs
2. Review logs for detailed error messages
3. Verify configuration and environment variables
4. Open an issue with detailed information

### Common Issues
- **API Rate Limiting**: ETL handles this automatically
- **Authentication Errors**: Verify API keys and credentials
- **Data Quality Issues**: Run dbt tests to identify problems
- **Performance Issues**: Check resource allocation and optimization

## 🚀 Deployment

### Production Deployment
1. Set up Google Cloud infrastructure
2. Configure service accounts and permissions
3. Deploy ETL pipeline with Docker
4. Set up dbt scheduling and monitoring
5. Implement data quality monitoring

### Monitoring
- ETL execution logs and metrics
- dbt run status and performance
- Data freshness and quality alerts
- API rate limit monitoring

---

**Note**: This is a data engineering project focused on League of Legends analytics. Ensure compliance with Riot Games API terms of service and data usage policies.
