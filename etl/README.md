# League of Legends Ranked Match Data ETL

This ETL (Extract, Transform, Load) script fetches ranked match data from the Riot Games API using the cassiopeia library and uploads the results to Google Cloud Storage.

## Features

- 🌍 **Multi-Region Support**: Fetches data from 12 major League of Legends regions
- 🏆 **Rank-Based Collection**: Focuses on high-tier players (Challenger, Grandmaster, etc.)
- 📊 **Comprehensive Data**: Extracts match details, participant stats, team objectives, and more
- ☁️ **Cloud Storage**: Automatically uploads results to Google Cloud Storage
- 🔄 **Rate Limiting**: Respects Riot API limits with proper rate limiting
- 📈 **Multiple Formats**: Outputs both JSON and CSV formats
- 🐳 **Docker Support**: Containerized deployment ready

## Prerequisites

- Python 3.11 or higher
- Riot Games API key
- Google Cloud Storage bucket (optional)
- Docker (optional, for containerized deployment)

## Installation

### 1. Clone and Setup

```bash
# Navigate to the etl directory
cd etl

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Environment Variables Setup

Create a `.env` file in the etl directory or set environment variables directly:

```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file with your actual values
nano .env
```

#### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `RIOT_API_KEY` | Your Riot Games API key | `RGAPI-12345678-1234-1234-1234-123456789abc` |

#### Optional Google Cloud Storage Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GCLOUD_PROJECT_ID` | Google Cloud Project ID | `my-gcp-project-123` |
| `GCLOUD_BUCKET` | GCS bucket name | `lol-ranked-data` |
| `GCLOUD_CREDENTIALS_PATH` | Path to service account JSON | `/path/to/service-account.json` |

#### Service Account Environment Variables (for create_service_account.py)

| Variable | Description | Example |
|----------|-------------|---------|
| `GCLOUD_TYPE` | Service account type | `service_account` |
| `GCLOUD_PRIVATE_KEY_ID` | Private key identifier | `abc123def456...` |
| `GCLOUD_PRIVATE_KEY` | Private key content | `-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n` |
| `GCLOUD_CLIENT_EMAIL` | Service account email | `my-service@project.iam.gserviceaccount.com` |
| `GCLOUD_CLIENT_ID` | Client identifier | `123456789012345678901` |
| `GCLOUD_AUTH_URI` | OAuth2 auth URI | `https://accounts.google.com/o/oauth2/auth` |
| `GCLOUD_TOKEN_URI` | OAuth2 token URI | `https://oauth2.googleapis.com/token` |
| `GCLOUD_AUTH_PROVIDER_X509_CERT_URL` | Auth provider cert URL | `https://www.googleapis.com/oauth2/v1/certs` |
| `GCLOUD_CLIENT_X509_CERT_URL` | Client cert URL | `https://www.googleapis.com/robot/v1/metadata/x509/...` |
| `GCLOUD_UNIVERSE_DOMAIN` | Universe domain | `googleapis.com` |

### 3. Google Cloud Storage Setup (Optional)

If you want to upload files to Google Cloud Storage:

#### Option A: Service Account with Environment Variables (Recommended)

1. Create a service account in Google Cloud Console
2. Download the JSON credentials file
3. Extract the values from the JSON file and set them as environment variables
4. Generate the service account file at runtime:

```bash
# Set all required GCLOUD_* environment variables (see env.example)
# Then generate the service account file
python create_service_account.py
```

This approach is more secure as it doesn't require storing credential files.

#### Option B: Direct Service Account File

1. Create a service account in Google Cloud Console
2. Download the JSON credentials file
3. Set the environment variable:
   ```bash
   export GCLOUD_CREDENTIALS_PATH="/path/to/your/service-account-key.json"
   ```

#### Option C: Application Default Credentials (Development)

```bash
# Install gcloud CLI and authenticate
gcloud auth application-default login
```

## Usage

### Basic Usage

```bash
# Run the ETL script
python etl.py
```

### Service Account Setup

If you want to use Google Cloud Storage with a service account, you can generate the credentials file from environment variables:

```bash
# 1. Set up environment variables (see env.example for all required variables)
export GCLOUD_TYPE="service_account"
export GCLOUD_PROJECT_ID="your-project-id"
export GCLOUD_PRIVATE_KEY_ID="your-private-key-id"
export GCLOUD_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_KEY_CONTENT\n-----END PRIVATE KEY-----\n"
export GCLOUD_CLIENT_EMAIL="your-service@project.iam.gserviceaccount.com"
# ... set all other required GCLOUD_* variables

# 2. Generate the service account file
python create_service_account.py

# 3. Run the ETL script (it will automatically use the generated file)
python etl.py
```

**Security Benefits:**
- No credential files stored in version control
- Credentials can be managed as environment variables
- File permissions automatically set to 600 (owner read/write only)
- Validation ensures proper service account structure

### Docker Usage

#### Option A: With Service Account Generator (Recommended)

```bash
# Build the Docker image
docker build -t lol-etl .

# Run with all GCLOUD_* environment variables
docker run -e RIOT_API_KEY="your-riot-key" \
           -e GCLOUD_PROJECT_ID="your-project" \
           -e GCLOUD_BUCKET="your-bucket" \
           -e GCLOUD_TYPE="service_account" \
           -e GCLOUD_PRIVATE_KEY_ID="your-private-key-id" \
           -e GCLOUD_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_KEY_CONTENT\n-----END PRIVATE KEY-----\n" \
           -e GCLOUD_CLIENT_EMAIL="your-service@project.iam.gserviceaccount.com" \
           -e GCLOUD_CLIENT_ID="your-client-id" \
           -e GCLOUD_AUTH_URI="https://accounts.google.com/o/oauth2/auth" \
           -e GCLOUD_TOKEN_URI="https://oauth2.googleapis.com/token" \
           -e GCLOUD_AUTH_PROVIDER_X509_CERT_URL="https://www.googleapis.com/oauth2/v1/certs" \
           -e GCLOUD_CLIENT_X509_CERT_URL="https://www.googleapis.com/robot/v1/metadata/x509/..." \
           lol-etl
```

#### Option B: With Pre-existing Service Account File

```bash
# Build the Docker image
docker build -t lol-etl .

# Run with mounted credentials file
docker run -e RIOT_API_KEY="your-riot-key" \
           -e GCLOUD_PROJECT_ID="your-project" \
           -e GCLOUD_BUCKET="your-bucket" \
           -v /path/to/credentials:/app/credentials \
           -e GCLOUD_CREDENTIALS_PATH="/app/credentials/service-account.json" \
           lol-etl
```

### Docker Compose (Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  etl:
    build: .
    environment:
      # Riot API
      - RIOT_API_KEY=${RIOT_API_KEY}
      
      # Google Cloud Storage
      - GCLOUD_PROJECT_ID=${GCLOUD_PROJECT_ID}
      - GCLOUD_BUCKET=${GCLOUD_BUCKET}
      
      # Service Account (all GCLOUD_* variables will be used to generate credentials)
      - GCLOUD_TYPE=${GCLOUD_TYPE}
      - GCLOUD_PRIVATE_KEY_ID=${GCLOUD_PRIVATE_KEY_ID}
      - GCLOUD_PRIVATE_KEY=${GCLOUD_PRIVATE_KEY}
      - GCLOUD_CLIENT_EMAIL=${GCLOUD_CLIENT_EMAIL}
      - GCLOUD_CLIENT_ID=${GCLOUD_CLIENT_ID}
      - GCLOUD_AUTH_URI=${GCLOUD_AUTH_URI}
      - GCLOUD_TOKEN_URI=${GCLOUD_TOKEN_URI}
      - GCLOUD_AUTH_PROVIDER_X509_CERT_URL=${GCLOUD_AUTH_PROVIDER_X509_CERT_URL}
      - GCLOUD_CLIENT_X509_CERT_URL=${GCLOUD_CLIENT_X509_CERT_URL}
      - GCLOUD_UNIVERSE_DOMAIN=${GCLOUD_UNIVERSE_DOMAIN}
    restart: unless-stopped
```

Then run:
```bash
# Set up your .env file with all required variables
cp env.example .env
# Edit .env with your actual values

# Run the ETL pipeline
docker-compose up
```

## Configuration

### ETL Parameters

The script can be customized by modifying the `main()` function in `etl.py`:

```python
# Conservative settings (default)
etl.run_etl(
    max_matches_per_region=20,  # Matches per region
    tiers=["CHALLENGER", "GRANDMASTER"]  # Rank tiers to fetch
)

# More aggressive settings
etl.run_etl(
    max_matches_per_region=100,
    tiers=["CHALLENGER", "GRANDMASTER", "MASTER", "DIAMOND"]
)
```

### Supported Regions

The script fetches data from these regions:
- North America (NA)
- Europe West (EUW)
- Korea (KR)
- Latin America North (LAN)
- Latin America South (LAS)
- Brazil (BR)
- Japan (JP)
- Russia (RU)
- Turkey (TR)
- Oceania (OCE)
- Europe Nordic & East (EUNE)
- Southeast Asia (SEA)

### Supported Queues

- Ranked Solo/Duo (Queue ID: 420)
- Ranked Flex (Queue ID: 440)

## Output

### Local Files

The script generates timestamped files:
- `lol_ranked_matches_YYYYMMDD_HHMMSS.json` - Complete structured data
- `lol_ranked_matches_YYYYMMDD_HHMMSS.csv` - Flattened data for analysis
- `etl.log` - Detailed execution log

### Google Cloud Storage Structure

If GCS upload is enabled, files are organized as:
```
gs://your-bucket/
├── json/
│   └── lol_ranked_matches_20240115_103000.json
└── csv/
    └── lol_ranked_matches_20240115_103000.csv
```

### Data Schema

Each match record includes:

#### Match Information
- `match_id`: Unique match identifier
- `region`: Game region
- `platform`: Platform identifier
- `queue_id`: Queue type ID
- `queue_name`: Queue type name
- `season`: Game season
- `game_version`: Game patch version
- `game_creation`: Match creation timestamp
- `game_duration`: Match duration in seconds
- `game_mode`: Game mode (CLASSIC)
- `game_type`: Game type (MATCHED_GAME)
- `map_id`: Map identifier

#### Participant Data
- `summoner_id`: Player's summoner ID
- `summoner_name`: Player's summoner name
- `champion_id`: Champion ID
- `champion_name`: Champion name
- `kills`, `deaths`, `assists`: KDA stats
- `gold_earned`: Total gold earned
- `total_damage_dealt`: Damage dealt
- `vision_score`: Vision control score
- `win`: Win/loss result

#### Team Data
- `team_id`: Team identifier
- `win`: Team victory status
- `first_blood`, `first_tower`, etc.: Objective firsts
- `tower_kills`, `inhibitor_kills`, etc.: Objective counts

## Testing

Run the unit tests to verify functionality:

```bash
# Run all tests
python run_tests.py

# Run with pytest
pytest test_etl.py -v

# Run specific test
python run_tests.py --test TestLoLDataETL.test_init_with_api_key_parameter
```

## Monitoring and Logging

The script provides comprehensive logging:

- **File Logging**: All logs are saved to `etl.log`
- **Console Output**: Real-time progress updates
- **Error Handling**: Graceful error recovery with detailed error messages
- **Summary Statistics**: Data distribution reports by region, queue, and season

### Log Levels

- `INFO`: General progress and successful operations
- `WARNING`: Non-critical issues (missing files, API limits)
- `ERROR`: Critical failures that may affect data collection

## Rate Limiting

The script respects Riot API rate limits:
- **Development API Keys**: 100 requests per 2 minutes
- **Production API Keys**: Higher limits available
- **Automatic Throttling**: Built-in delays between requests
- **Error Recovery**: Handles rate limit errors gracefully

## Troubleshooting

### Common Issues

#### 1. API Key Issues
```
Error: Riot API key is required
```
**Solution**: Set the `RIOT_API_KEY` environment variable with a valid key.

#### 2. Google Cloud Storage Issues
```
Error: No Google Cloud credentials found
```
**Solution**: Either set `GCLOUD_CREDENTIALS_PATH` or run `gcloud auth application-default login`.

**For Service Account Generator Issues:**
```
Error: Missing required environment variables
```
**Solution**: Ensure all required `GCLOUD_*` environment variables are set. See `env.example` for the complete list.

```
Error: Invalid private key format
```
**Solution**: Make sure `GCLOUD_PRIVATE_KEY` includes the full private key with `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` markers.

#### 3. Rate Limiting
```
Error: 429 Too Many Requests
```
**Solution**: The script handles this automatically, but you can reduce `max_matches_per_region` for more conservative collection.

#### 4. Missing Dependencies
```
Error: No module named 'cassiopeia'
```
**Solution**: Install dependencies with `pip install -r requirements.txt`.

### Getting Help

1. Check the `etl.log` file for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure your Riot API key is valid and has the necessary permissions
4. For Google Cloud issues, verify your credentials and bucket permissions

## Security Considerations

- **API Keys**: Never commit API keys to version control
- **Credentials**: Store Google Cloud credentials securely
- **Environment Variables**: Use `.env` files or secure environment variable management
- **Docker**: Use Docker secrets for production deployments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs in `etl.log`
3. Open an issue with detailed error information 