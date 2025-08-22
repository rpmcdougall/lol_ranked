#!/usr/bin/env python3
"""
League of Legends Ranked Match Data ETL Script
Fetches ranked match data from Riot Games API using cassiopeia library
with proper rate limiting and data grouping by region, rank, and season.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from dataclasses import dataclass, asdict
from collections import defaultdict

import cassiopeia as cass
from cassiopeia import Summoner, Match, MatchHistory, Queue, Region, Platform

# Google Cloud Storage imports
try:
    from google.cloud import storage
    from google.auth.exceptions import DefaultCredentialsError
    GCLOUD_AVAILABLE = True
except ImportError:
    GCLOUD_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RankedMatchData:
    """Data class for storing ranked match information"""
    match_id: str
    region: str
    platform: str
    queue_id: int
    queue_name: str
    season: int
    game_version: str
    game_creation: datetime
    game_duration: int
    participants: List[Dict[str, Any]]
    teams: List[Dict[str, Any]]
    game_mode: str
    game_type: str
    map_id: int

class LoLDataETL:
    """League of Legends Data ETL class"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ETL process with API key and rate limiting configuration
        
        Args:
            api_key: Riot Games API key. If None, will try to get from environment variable
        """
        self.api_key = api_key or os.getenv('RIOT_API_KEY')
        if not self.api_key:
            raise ValueError("Riot API key is required. Set RIOT_API_KEY environment variable or pass as parameter.")
        
        # Configure cassiopeia with API key and rate limiting
        cass.set_riot_api_key(self.api_key)
        
        # Configure rate limiting (Riot API has 100 requests per 2 minutes for development API keys)
        # For production, you might want to use a different rate limit
        cass.set_default_region(Region.north_america)
        
        # Set up rate limiting configuration
        cass.apply_settings({
            "global": {
                "version_from_match": "version",
                "default_region": "NA",
                "request_timeout": 30,
                "request_storage": "sqlite",
                "request_storage_path": "cassiopeia_cache.db"
            },
            "plugins": {
                "global": {
                    "default_region": "NA",
                    "request_timeout": 30
                }
            }
        })
        
        # Define regions to fetch data from
        self.regions = [
            Region.north_america,
            Region.europe_west,
            Region.korea,
            Region.latin_america_north,
            Region.latin_america_south,
            Region.brazil,
            Region.japan,
            Region.russia,
            Region.turkey,
            Region.oceania,
            Region.europe_nordic_and_east,
            Region.southeast_asia
        ]
        
        # Define ranked queues to fetch
        self.ranked_queues = [
            Queue.ranked_solo_fives,
            Queue.ranked_flex_fives
        ]
        
        logger.info("LoL Data ETL initialized successfully")
    
    def get_ranked_queues_info(self) -> Dict[int, str]:
        """Get information about ranked queues"""
        queues_info = {}
        for queue in self.ranked_queues:
            try:
                queues_info[queue.value] = queue.name
                logger.info(f"Queue: {queue.name} (ID: {queue.value})")
            except Exception as e:
                logger.warning(f"Could not get info for queue {queue}: {e}")
        return queues_info
    
    def fetch_summoner_by_rank(self, region: Region, tier: str, division: str = "I", page: int = 1) -> List[Summoner]:
        """
        Fetch summoners by their rank tier and division
        
        Args:
            region: The region to search in
            tier: Rank tier (IRON, BRONZE, SILVER, GOLD, PLATINUM, DIAMOND, MASTER, GRANDMASTER, CHALLENGER)
            division: Rank division (I, II, III, IV)
            page: Page number for pagination
            
        Returns:
            List of summoners at the specified rank
        """
        try:
            # Set region for this request
            cass.set_default_region(region)
            
            # Get challenger league (for challenger tier)
            if tier.upper() == "CHALLENGER":
                league = cass.get_challenger_league(queue=Queue.ranked_solo_fives, region=region)
                return [entry.summoner for entry in league.entries[:10]]  # Limit to 10 summoners
            
            # Get grandmaster league (for grandmaster tier)
            elif tier.upper() == "GRANDMASTER":
                league = cass.get_grandmaster_league(queue=Queue.ranked_solo_fives, region=region)
                return [entry.summoner for entry in league.entries[:10]]  # Limit to 10 summoners
            
            # For other tiers, we need to search differently
            # This is a simplified approach - in practice you might need to use different methods
            else:
                logger.warning(f"Fetching summoners for tier {tier} not fully implemented")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching summoners for {tier} {division} in {region}: {e}")
            return []
    
    def fetch_match_history(self, summoner: Summoner, queue: Queue, count: int = 10) -> List[Match]:
        """
        Fetch match history for a summoner
        
        Args:
            summoner: The summoner to get match history for
            queue: The queue type to filter by
            count: Number of matches to fetch
            
        Returns:
            List of matches
        """
        try:
            match_history = summoner.match_history
            # Filter by queue and limit count
            matches = [match for match in match_history[:count] if match.queue == queue]
            return matches
        except Exception as e:
            logger.error(f"Error fetching match history for summoner {summoner.name}: {e}")
            return []
    
    def extract_match_data(self, match: Match, region: str, platform: str) -> Optional[RankedMatchData]:
        """
        Extract relevant data from a match
        
        Args:
            match: The match object
            region: The region the match was played in
            platform: The platform the match was played on
            
        Returns:
            RankedMatchData object or None if extraction fails
        """
        try:
            # Extract participant data
            participants = []
            for participant in match.participants:
                participant_data = {
                    'summoner_id': participant.summoner.id if participant.summoner else None,
                    'summoner_name': participant.summoner.name if participant.summoner else None,
                    'champion_id': participant.champion.id if participant.champion else None,
                    'champion_name': participant.champion.name if participant.champion else None,
                    'team_id': participant.team.id if participant.team else None,
                    'kills': participant.stats.kills if participant.stats else 0,
                    'deaths': participant.stats.deaths if participant.stats else 0,
                    'assists': participant.stats.assists if participant.stats else 0,
                    'gold_earned': participant.stats.gold_earned if participant.stats else 0,
                    'total_damage_dealt': participant.stats.total_damage_dealt if participant.stats else 0,
                    'vision_score': participant.stats.vision_score if participant.stats else 0,
                    'win': participant.stats.win if participant.stats else False
                }
                participants.append(participant_data)
            
            # Extract team data
            teams = []
            for team in match.teams:
                team_data = {
                    'team_id': team.id,
                    'win': team.win,
                    'first_blood': team.first_blood,
                    'first_tower': team.first_tower,
                    'first_inhibitor': team.first_inhibitor,
                    'first_baron': team.first_baron,
                    'first_dragon': team.first_dragon,
                    'first_rift_herald': team.first_rift_herald,
                    'tower_kills': team.tower_kills,
                    'inhibitor_kills': team.inhibitor_kills,
                    'baron_kills': team.baron_kills,
                    'dragon_kills': team.dragon_kills,
                    'rift_herald_kills': team.rift_herald_kills
                }
                teams.append(team_data)
            
            return RankedMatchData(
                match_id=str(match.id),
                region=region,
                platform=platform,
                queue_id=match.queue.value if match.queue else 0,
                queue_name=match.queue.name if match.queue else "Unknown",
                season=match.season,
                game_version=match.version,
                game_creation=match.creation,
                game_duration=match.duration.seconds if match.duration else 0,
                participants=participants,
                teams=teams,
                game_mode=match.mode.name if match.mode else "Unknown",
                game_type=match.type.name if match.type else "Unknown",
                map_id=match.map.id if match.map else 0
            )
            
        except Exception as e:
            logger.error(f"Error extracting data from match {match.id}: {e}")
            return None
    
    def save_data_to_json(self, data: List[RankedMatchData], filename: str):
        """Save match data to JSON file"""
        try:
            # Convert dataclass objects to dictionaries
            data_dicts = [asdict(match_data) for match_data in data]
            
            # Convert datetime objects to strings for JSON serialization
            for match_dict in data_dicts:
                match_dict['game_creation'] = match_dict['game_creation'].isoformat()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_dicts, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {e}")
    
    def save_data_to_csv(self, data: List[RankedMatchData], filename: str):
        """Save match data to CSV file"""
        try:
            # Flatten the data for CSV format
            flattened_data = []
            
            for match_data in data:
                base_record = {
                    'match_id': match_data.match_id,
                    'region': match_data.region,
                    'platform': match_data.platform,
                    'queue_id': match_data.queue_id,
                    'queue_name': match_data.queue_name,
                    'season': match_data.season,
                    'game_version': match_data.game_version,
                    'game_creation': match_data.game_creation,
                    'game_duration': match_data.game_duration,
                    'game_mode': match_data.game_mode,
                    'game_type': match_data.game_type,
                    'map_id': match_data.map_id
                }
                
                # Add team data
                for i, team in enumerate(match_data.teams):
                    team_prefix = f'team_{i+1}_'
                    for key, value in team.items():
                        base_record[team_prefix + key] = value
                
                # Add participant data (first participant as representative)
                if match_data.participants:
                    participant = match_data.participants[0]
                    for key, value in participant.items():
                        base_record[f'participant_1_{key}'] = value
                
                flattened_data.append(base_record)
            
            df = pd.DataFrame(flattened_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            
            logger.info(f"Data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {e}")
    
    def upload_to_gcloud_storage(self, local_file_path: str, bucket_name: str = None, blob_name: str = None) -> bool:
        """
        Upload a file to Google Cloud Storage
        
        Args:
            local_file_path: Path to the local file to upload
            bucket_name: Name of the GCS bucket (from GCLOUD_BUCKET env var if not provided)
            blob_name: Name for the blob in GCS (uses filename if not provided)
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        if not GCLOUD_AVAILABLE:
            logger.warning("Google Cloud Storage not available. Install google-cloud-storage package.")
            return False
        
        try:
            # Get configuration from environment variables
            project_id = os.getenv('GCLOUD_PROJECT_ID')
            credentials_path = os.getenv('GCLOUD_CREDENTIALS_PATH')
            bucket_name = bucket_name or os.getenv('GCLOUD_BUCKET')
            
            if not bucket_name:
                logger.error("GCLOUD_BUCKET environment variable is required for Google Cloud Storage upload")
                return False
            
            # Initialize the client
            if credentials_path:
                # Use service account credentials file
                client = storage.Client.from_service_account_json(credentials_path, project=project_id)
                logger.info(f"Using service account credentials from {credentials_path}")
            else:
                # Use default credentials (Application Default Credentials)
                try:
                    client = storage.Client(project=project_id)
                    logger.info("Using Application Default Credentials")
                except DefaultCredentialsError:
                    logger.error("No Google Cloud credentials found. Set GCLOUD_CREDENTIALS_PATH or configure ADC.")
                    return False
            
            # Get bucket
            bucket = client.bucket(bucket_name)
            
            # Determine blob name
            if not blob_name:
                blob_name = os.path.basename(local_file_path)
            
            # Create blob and upload
            blob = bucket.blob(blob_name)
            
            # Upload the file
            blob.upload_from_filename(local_file_path)
            
            # Set metadata
            blob.metadata = {
                'uploaded_at': datetime.now().isoformat(),
                'source': 'lol_ranked_etl',
                'file_type': 'csv' if local_file_path.endswith('.csv') else 'json'
            }
            blob.patch()
            
            logger.info(f"Successfully uploaded {local_file_path} to gs://{bucket_name}/{blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading {local_file_path} to Google Cloud Storage: {e}")
            return False
    
    def upload_data_files_to_gcloud(self, json_filename: str, csv_filename: str) -> Dict[str, bool]:
        """
        Upload both JSON and CSV files to Google Cloud Storage
        
        Args:
            json_filename: Path to the JSON file
            csv_filename: Path to the CSV file
            
        Returns:
            Dict with upload results for each file
        """
        results = {}
        
        # Upload JSON file
        if os.path.exists(json_filename):
            json_blob_name = f"json/{os.path.basename(json_filename)}"
            results['json'] = self.upload_to_gcloud_storage(json_filename, blob_name=json_blob_name)
        else:
            logger.warning(f"JSON file {json_filename} not found, skipping upload")
            results['json'] = False
        
        # Upload CSV file
        if os.path.exists(csv_filename):
            csv_blob_name = f"csv/{os.path.basename(csv_filename)}"
            results['csv'] = self.upload_to_gcloud_storage(csv_filename, blob_name=csv_blob_name)
        else:
            logger.warning(f"CSV file {csv_filename} not found, skipping upload")
            results['csv'] = False
        
        return results
    
    def run_etl(self, max_matches_per_region: int = 50, tiers: List[str] = None):
        """
        Run the complete ETL process
        
        Args:
            max_matches_per_region: Maximum number of matches to fetch per region
            tiers: List of tiers to fetch data for (default: all tiers)
        """
        if tiers is None:
            tiers = ["CHALLENGER", "GRANDMASTER", "MASTER", "DIAMOND", "PLATINUM"]
        
        logger.info("Starting LoL Ranked Match Data ETL process")
        
        all_match_data = []
        queues_info = self.get_ranked_queues_info()
        
        for region in self.regions:
            logger.info(f"Processing region: {region}")
            
            try:
                # Set region for this iteration
                cass.set_default_region(region)
                platform = region.platform
                
                matches_found = 0
                
                for tier in tiers:
                    if matches_found >= max_matches_per_region:
                        break
                    
                    logger.info(f"Fetching data for {tier} tier in {region}")
                    
                    # Get summoners for this tier
                    summoners = self.fetch_summoner_by_rank(region, tier)
                    
                    for summoner in summoners:
                        if matches_found >= max_matches_per_region:
                            break
                        
                        # Fetch matches for each queue type
                        for queue in self.ranked_queues:
                            if matches_found >= max_matches_per_region:
                                break
                            
                            matches = self.fetch_match_history(summoner, queue, count=5)
                            
                            for match in matches:
                                if matches_found >= max_matches_per_region:
                                    break
                                
                                match_data = self.extract_match_data(match, str(region), str(platform))
                                if match_data:
                                    all_match_data.append(match_data)
                                    matches_found += 1
                                    
                                    if matches_found % 10 == 0:
                                        logger.info(f"Processed {matches_found} matches in {region}")
                
                logger.info(f"Completed processing {region}. Found {matches_found} matches.")
                
            except Exception as e:
                logger.error(f"Error processing region {region}: {e}")
                continue
        
        # Save the data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_filename = f"lol_ranked_matches_{timestamp}.json"
        self.save_data_to_json(all_match_data, json_filename)
        
        # Save as CSV
        csv_filename = f"lol_ranked_matches_{timestamp}.csv"
        self.save_data_to_csv(all_match_data, csv_filename)
        
        # Upload files to Google Cloud Storage
        logger.info("Uploading files to Google Cloud Storage...")
        upload_results = self.upload_data_files_to_gcloud(json_filename, csv_filename)
        
        # Log upload results
        for file_type, success in upload_results.items():
            if success:
                logger.info(f"✅ {file_type.upper()} file uploaded successfully")
            else:
                logger.warning(f"❌ {file_type.upper()} file upload failed")
        
        # Generate summary statistics
        self.generate_summary_statistics(all_match_data)
        
        logger.info(f"ETL process completed. Processed {len(all_match_data)} matches total.")
    
    def generate_summary_statistics(self, data: List[RankedMatchData]):
        """Generate and log summary statistics"""
        if not data:
            logger.warning("No data to generate statistics for")
            return
        
        # Group by region
        region_stats = defaultdict(int)
        queue_stats = defaultdict(int)
        season_stats = defaultdict(int)
        
        for match in data:
            region_stats[match.region] += 1
            queue_stats[match.queue_name] += 1
            season_stats[match.season] += 1
        
        logger.info("=== SUMMARY STATISTICS ===")
        logger.info(f"Total matches processed: {len(data)}")
        
        logger.info("\nMatches by Region:")
        for region, count in sorted(region_stats.items()):
            logger.info(f"  {region}: {count}")
        
        logger.info("\nMatches by Queue:")
        for queue, count in sorted(queue_stats.items()):
            logger.info(f"  {queue}: {count}")
        
        logger.info("\nMatches by Season:")
        for season, count in sorted(season_stats.items()):
            logger.info(f"  Season {season}: {count}")

def main():
    """Main function to run the ETL process"""
    try:
        # Get API key from environment variable
        api_key = os.getenv('RIOT_API_KEY')
        if not api_key:
            logger.error("RIOT_API_KEY environment variable is not set")
            raise ValueError("RIOT_API_KEY environment variable is required")
        
        logger.info("Retrieved API key from environment variable")
        
        # Initialize ETL process with API key
        etl = LoLDataETL(api_key=api_key)
        
        # Run ETL with conservative limits to respect rate limits
        etl.run_etl(
            max_matches_per_region=20,  # Conservative limit
            tiers=["CHALLENGER", "GRANDMASTER"]  # Start with high-tier players
        )
        
    except Exception as e:
        logger.error(f"ETL process failed: {e}")
        raise

if __name__ == "__main__":
    main()
