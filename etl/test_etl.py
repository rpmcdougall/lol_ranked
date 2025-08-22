#!/usr/bin/env python3
"""
Unit tests for League of Legends ETL script
Tests the LoLDataETL class and its methods with proper mocking.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import os
import json
import tempfile
import shutil
from datetime import datetime
from typing import List, Dict, Any

import cassiopeia as cass
from cassiopeia import Summoner, Match, Queue, Region, Platform

# Import the ETL module
from etl import LoLDataETL, RankedMatchData


class TestRankedMatchData(unittest.TestCase):
    """Test cases for RankedMatchData dataclass"""
    
    def test_ranked_match_data_creation(self):
        """Test creating a RankedMatchData instance"""
        # Create sample data
        match_data = RankedMatchData(
            match_id="123456789",
            region="NA",
            platform="NA1",
            queue_id=420,
            queue_name="Ranked Solo/Duo",
            season=14,
            game_version="14.1.1",
            game_creation=datetime(2024, 1, 15, 10, 30, 0),
            game_duration=1800,
            participants=[],
            teams=[],
            game_mode="CLASSIC",
            game_type="MATCHED_GAME",
            map_id=11
        )
        
        # Verify all fields are set correctly
        self.assertEqual(match_data.match_id, "123456789")
        self.assertEqual(match_data.region, "NA")
        self.assertEqual(match_data.platform, "NA1")
        self.assertEqual(match_data.queue_id, 420)
        self.assertEqual(match_data.queue_name, "Ranked Solo/Duo")
        self.assertEqual(match_data.season, 14)
        self.assertEqual(match_data.game_version, "14.1.1")
        self.assertEqual(match_data.game_duration, 1800)
        self.assertEqual(match_data.game_mode, "CLASSIC")
        self.assertEqual(match_data.game_type, "MATCHED_GAME")
        self.assertEqual(match_data.map_id, 11)


class TestLoLDataETL(unittest.TestCase):
    """Test cases for LoLDataETL class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_api_key = "test-api-key-12345"
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock environment variable
        self.env_patcher = patch.dict(os.environ, {'RIOT_API_KEY': self.test_api_key})
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('etl.cass')
    def test_init_with_api_key_parameter(self, mock_cass):
        """Test ETL initialization with API key parameter"""
        etl = LoLDataETL(api_key="custom-key")
        
        # Verify API key is set
        self.assertEqual(etl.api_key, "custom-key")
        
        # Verify cassiopeia was configured
        mock_cass.set_riot_api_key.assert_called_once_with("custom-key")
        mock_cass.set_default_region.assert_called_once()
        mock_cass.apply_settings.assert_called_once()
    
    @patch('etl.cass')
    def test_init_with_environment_variable(self, mock_cass):
        """Test ETL initialization with environment variable"""
        etl = LoLDataETL()
        
        # Verify API key is set from environment
        self.assertEqual(etl.api_key, self.test_api_key)
        
        # Verify cassiopeia was configured
        mock_cass.set_riot_api_key.assert_called_once_with(self.test_api_key)
    
    def test_init_without_api_key(self):
        """Test ETL initialization without API key raises error"""
        # Remove environment variable
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                LoLDataETL()
            
            self.assertIn("Riot API key is required", str(context.exception))
    
    @patch('etl.cass')
    def test_get_ranked_queues_info(self, mock_cass):
        """Test getting ranked queues information"""
        etl = LoLDataETL()
        
        # Mock queue objects
        mock_queue1 = Mock()
        mock_queue1.value = 420
        mock_queue1.name = "Ranked Solo/Duo"
        
        mock_queue2 = Mock()
        mock_queue2.value = 440
        mock_queue2.name = "Ranked Flex"
        
        etl.ranked_queues = [mock_queue1, mock_queue2]
        
        # Call the method
        result = etl.get_ranked_queues_info()
        
        # Verify result
        expected = {
            420: "Ranked Solo/Duo",
            440: "Ranked Flex"
        }
        self.assertEqual(result, expected)
    
    @patch('etl.cass')
    def test_fetch_summoner_by_rank_challenger(self, mock_cass):
        """Test fetching challenger summoners"""
        etl = LoLDataETL()
        
        # Mock challenger league
        mock_league = Mock()
        mock_entry1 = Mock()
        mock_entry1.summoner = Mock()
        mock_entry2 = Mock()
        mock_entry2.summoner = Mock()
        mock_league.entries = [mock_entry1, mock_entry2]
        
        mock_cass.get_challenger_league.return_value = mock_league
        
        # Call the method
        result = etl.fetch_summoner_by_rank(Region.north_america, "CHALLENGER")
        
        # Verify result
        self.assertEqual(len(result), 2)
        mock_cass.get_challenger_league.assert_called_once_with(
            queue=Queue.ranked_solo_fives, 
            region=Region.north_america
        )
    
    @patch('etl.cass')
    def test_fetch_summoner_by_rank_grandmaster(self, mock_cass):
        """Test fetching grandmaster summoners"""
        etl = LoLDataETL()
        
        # Mock grandmaster league
        mock_league = Mock()
        mock_entry1 = Mock()
        mock_entry1.summoner = Mock()
        mock_league.entries = [mock_entry1]
        
        mock_cass.get_grandmaster_league.return_value = mock_league
        
        # Call the method
        result = etl.fetch_summoner_by_rank(Region.north_america, "GRANDMASTER")
        
        # Verify result
        self.assertEqual(len(result), 1)
        mock_cass.get_grandmaster_league.assert_called_once_with(
            queue=Queue.ranked_solo_fives, 
            region=Region.north_america
        )
    
    @patch('etl.cass')
    def test_fetch_summoner_by_rank_other_tiers(self, mock_cass):
        """Test fetching summoners for other tiers (not implemented)"""
        etl = LoLDataETL()
        
        # Call the method for a tier that's not fully implemented
        result = etl.fetch_summoner_by_rank(Region.north_america, "DIAMOND")
        
        # Verify result is empty list
        self.assertEqual(result, [])
    
    def test_fetch_match_history(self):
        """Test fetching match history for a summoner"""
        etl = LoLDataETL()
        
        # Mock summoner and match history
        mock_summoner = Mock()
        mock_match1 = Mock()
        mock_match1.queue = Queue.ranked_solo_fives
        mock_match2 = Mock()
        mock_match2.queue = Queue.ranked_flex_fives
        mock_match3 = Mock()
        mock_match3.queue = Queue.ranked_solo_fives
        
        mock_summoner.match_history = [mock_match1, mock_match2, mock_match3]
        
        # Call the method
        result = etl.fetch_match_history(mock_summoner, Queue.ranked_solo_fives, count=2)
        
        # Verify result (should only include solo queue matches, limited to 2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], mock_match1)
        self.assertEqual(result[1], mock_match3)
    
    def test_extract_match_data_success(self):
        """Test successful extraction of match data"""
        etl = LoLDataETL()
        
        # Mock match object
        mock_match = Mock()
        mock_match.id = 123456789
        mock_match.queue = Mock()
        mock_match.queue.value = 420
        mock_match.queue.name = "Ranked Solo/Duo"
        mock_match.season = 14
        mock_match.version = "14.1.1"
        mock_match.creation = datetime(2024, 1, 15, 10, 30, 0)
        mock_match.duration = Mock()
        mock_match.duration.seconds = 1800
        mock_match.mode = Mock()
        mock_match.mode.name = "CLASSIC"
        mock_match.type = Mock()
        mock_match.type.name = "MATCHED_GAME"
        mock_match.map = Mock()
        mock_match.map.id = 11
        
        # Mock participants
        mock_participant = Mock()
        mock_participant.summoner = Mock()
        mock_participant.summoner.id = "summoner123"
        mock_participant.summoner.name = "TestPlayer"
        mock_participant.champion = Mock()
        mock_participant.champion.id = 1
        mock_participant.champion.name = "Annie"
        mock_participant.team = Mock()
        mock_participant.team.id = 100
        mock_participant.stats = Mock()
        mock_participant.stats.kills = 5
        mock_participant.stats.deaths = 2
        mock_participant.stats.assists = 8
        mock_participant.stats.gold_earned = 15000
        mock_participant.stats.total_damage_dealt = 25000
        mock_participant.stats.vision_score = 25
        mock_participant.stats.win = True
        
        mock_match.participants = [mock_participant]
        
        # Mock teams
        mock_team = Mock()
        mock_team.id = 100
        mock_team.win = True
        mock_team.first_blood = True
        mock_team.first_tower = True
        mock_team.first_inhibitor = False
        mock_team.first_baron = True
        mock_team.first_dragon = True
        mock_team.first_rift_herald = False
        mock_team.tower_kills = 8
        mock_team.inhibitor_kills = 1
        mock_team.baron_kills = 1
        mock_team.dragon_kills = 3
        mock_team.rift_herald_kills = 0
        
        mock_match.teams = [mock_team]
        
        # Call the method
        result = etl.extract_match_data(mock_match, "NA", "NA1")
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result.match_id, "123456789")
        self.assertEqual(result.region, "NA")
        self.assertEqual(result.platform, "NA1")
        self.assertEqual(result.queue_id, 420)
        self.assertEqual(result.queue_name, "Ranked Solo/Duo")
        self.assertEqual(result.season, 14)
        self.assertEqual(result.game_version, "14.1.1")
        self.assertEqual(result.game_duration, 1800)
        self.assertEqual(result.game_mode, "CLASSIC")
        self.assertEqual(result.game_type, "MATCHED_GAME")
        self.assertEqual(result.map_id, 11)
        
        # Verify participant data
        self.assertEqual(len(result.participants), 1)
        participant = result.participants[0]
        self.assertEqual(participant['summoner_id'], "summoner123")
        self.assertEqual(participant['summoner_name'], "TestPlayer")
        self.assertEqual(participant['champion_id'], 1)
        self.assertEqual(participant['champion_name'], "Annie")
        self.assertEqual(participant['kills'], 5)
        self.assertEqual(participant['deaths'], 2)
        self.assertEqual(participant['assists'], 8)
        self.assertEqual(participant['gold_earned'], 15000)
        self.assertEqual(participant['total_damage_dealt'], 25000)
        self.assertEqual(participant['vision_score'], 25)
        self.assertTrue(participant['win'])
        
        # Verify team data
        self.assertEqual(len(result.teams), 1)
        team = result.teams[0]
        self.assertEqual(team['team_id'], 100)
        self.assertTrue(team['win'])
        self.assertTrue(team['first_blood'])
        self.assertTrue(team['first_tower'])
        self.assertFalse(team['first_inhibitor'])
        self.assertTrue(team['first_baron'])
        self.assertTrue(team['first_dragon'])
        self.assertFalse(team['first_rift_herald'])
        self.assertEqual(team['tower_kills'], 8)
        self.assertEqual(team['inhibitor_kills'], 1)
        self.assertEqual(team['baron_kills'], 1)
        self.assertEqual(team['dragon_kills'], 3)
        self.assertEqual(team['rift_herald_kills'], 0)
    
    def test_extract_match_data_with_missing_attributes(self):
        """Test extraction with missing match attributes"""
        etl = LoLDataETL()
        
        # Mock match object with missing attributes
        mock_match = Mock()
        mock_match.id = 123456789
        mock_match.queue = None
        mock_match.season = 14
        mock_match.version = "14.1.1"
        mock_match.creation = datetime(2024, 1, 15, 10, 30, 0)
        mock_match.duration = None
        mock_match.mode = None
        mock_match.type = None
        mock_match.map = None
        mock_match.participants = []
        mock_match.teams = []
        
        # Call the method
        result = etl.extract_match_data(mock_match, "NA", "NA1")
        
        # Verify result handles missing attributes gracefully
        self.assertIsNotNone(result)
        self.assertEqual(result.queue_id, 0)
        self.assertEqual(result.queue_name, "Unknown")
        self.assertEqual(result.game_duration, 0)
        self.assertEqual(result.game_mode, "Unknown")
        self.assertEqual(result.game_type, "Unknown")
        self.assertEqual(result.map_id, 0)
    
    def test_save_data_to_json(self):
        """Test saving data to JSON file"""
        etl = LoLDataETL()
        
        # Create sample match data
        match_data = RankedMatchData(
            match_id="123456789",
            region="NA",
            platform="NA1",
            queue_id=420,
            queue_name="Ranked Solo/Duo",
            season=14,
            game_version="14.1.1",
            game_creation=datetime(2024, 1, 15, 10, 30, 0),
            game_duration=1800,
            participants=[],
            teams=[],
            game_mode="CLASSIC",
            game_type="MATCHED_GAME",
            map_id=11
        )
        
        data = [match_data]
        filename = os.path.join(self.temp_dir, "test_matches.json")
        
        # Call the method
        etl.save_data_to_json(data, filename)
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(filename))
        
        with open(filename, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(len(saved_data), 1)
        self.assertEqual(saved_data[0]['match_id'], "123456789")
        self.assertEqual(saved_data[0]['region'], "NA")
        self.assertEqual(saved_data[0]['queue_id'], 420)
    
    def test_save_data_to_csv(self):
        """Test saving data to CSV file"""
        etl = LoLDataETL()
        
        # Create sample match data with participants and teams
        match_data = RankedMatchData(
            match_id="123456789",
            region="NA",
            platform="NA1",
            queue_id=420,
            queue_name="Ranked Solo/Duo",
            season=14,
            game_version="14.1.1",
            game_creation=datetime(2024, 1, 15, 10, 30, 0),
            game_duration=1800,
            participants=[{
                'summoner_id': 'summoner123',
                'summoner_name': 'TestPlayer',
                'champion_id': 1,
                'champion_name': 'Annie',
                'team_id': 100,
                'kills': 5,
                'deaths': 2,
                'assists': 8,
                'gold_earned': 15000,
                'total_damage_dealt': 25000,
                'vision_score': 25,
                'win': True
            }],
            teams=[{
                'team_id': 100,
                'win': True,
                'first_blood': True,
                'first_tower': True,
                'first_inhibitor': False,
                'first_baron': True,
                'first_dragon': True,
                'first_rift_herald': False,
                'tower_kills': 8,
                'inhibitor_kills': 1,
                'baron_kills': 1,
                'dragon_kills': 3,
                'rift_herald_kills': 0
            }],
            game_mode="CLASSIC",
            game_type="MATCHED_GAME",
            map_id=11
        )
        
        data = [match_data]
        filename = os.path.join(self.temp_dir, "test_matches.csv")
        
        # Call the method
        etl.save_data_to_csv(data, filename)
        
        # Verify file was created
        self.assertTrue(os.path.exists(filename))
        
        # Read CSV and verify content
        import pandas as pd
        df = pd.read_csv(filename)
        
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['match_id'], "123456789")
        self.assertEqual(df.iloc[0]['region'], "NA")
        self.assertEqual(df.iloc[0]['queue_id'], 420)
        self.assertEqual(df.iloc[0]['team_1_team_id'], 100)
        self.assertEqual(df.iloc[0]['participant_1_summoner_name'], "TestPlayer")
    
    def test_generate_summary_statistics(self):
        """Test generating summary statistics"""
        etl = LoLDataETL()
        
        # Create sample data
        match_data1 = RankedMatchData(
            match_id="123456789",
            region="NA",
            platform="NA1",
            queue_id=420,
            queue_name="Ranked Solo/Duo",
            season=14,
            game_version="14.1.1",
            game_creation=datetime(2024, 1, 15, 10, 30, 0),
            game_duration=1800,
            participants=[],
            teams=[],
            game_mode="CLASSIC",
            game_type="MATCHED_GAME",
            map_id=11
        )
        
        match_data2 = RankedMatchData(
            match_id="987654321",
            region="EUW",
            platform="EUW1",
            queue_id=440,
            queue_name="Ranked Flex",
            season=14,
            game_version="14.1.1",
            game_creation=datetime(2024, 1, 15, 11, 30, 0),
            game_duration=2000,
            participants=[],
            teams=[],
            game_mode="CLASSIC",
            game_type="MATCHED_GAME",
            map_id=11
        )
        
        data = [match_data1, match_data2]
        
        # Call the method (this should not raise any exceptions)
        etl.generate_summary_statistics(data)
    
    def test_generate_summary_statistics_empty_data(self):
        """Test generating summary statistics with empty data"""
        etl = LoLDataETL()
        
        # Call the method with empty data
        etl.generate_summary_statistics([])
        # Should not raise any exceptions
    
    @patch('etl.cass')
    @patch('builtins.open', create=True)
    @patch('json.dump')
    @patch('pandas.DataFrame.to_csv')
    def test_run_etl_integration(self, mock_to_csv, mock_json_dump, mock_open, mock_cass):
        """Test the complete ETL process integration"""
        etl = LoLDataETL()
        
        # Mock the necessary methods
        etl.fetch_summoner_by_rank = Mock(return_value=[])
        etl.fetch_match_history = Mock(return_value=[])
        etl.extract_match_data = Mock(return_value=None)
        etl.save_data_to_json = Mock()
        etl.save_data_to_csv = Mock()
        etl.generate_summary_statistics = Mock()
        
        # Mock datetime for consistent timestamp
        with patch('etl.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240115_103000"
            
            # Call the method
            etl.run_etl(max_matches_per_region=5, tiers=["CHALLENGER"])
        
        # Verify the process completed without errors
        etl.save_data_to_json.assert_called_once()
        etl.save_data_to_csv.assert_called_once()
        etl.generate_summary_statistics.assert_called_once()


class TestETLMainFunction(unittest.TestCase):
    """Test cases for the main function"""
    
    @patch('etl.LoLDataETL')
    def test_main_function_success(self, mock_etl_class):
        """Test main function executes successfully"""
        # Mock the ETL class
        mock_etl_instance = Mock()
        mock_etl_class.return_value = mock_etl_instance
        
        # Import and run main function
        from etl import main
        main()
        
        # Verify ETL was initialized and run
        mock_etl_class.assert_called_once()
        mock_etl_instance.run_etl.assert_called_once_with(
            max_matches_per_region=20,
            tiers=["CHALLENGER", "GRANDMASTER"]
        )
    
    @patch('etl.LoLDataETL')
    def test_main_function_exception_handling(self, mock_etl_class):
        """Test main function handles exceptions properly"""
        # Mock the ETL class to raise an exception
        mock_etl_class.side_effect = Exception("Test error")
        
        # Import and run main function
        from etl import main
        
        # Should raise the exception
        with self.assertRaises(Exception):
            main()


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestRankedMatchData))
    test_suite.addTest(unittest.makeSuite(TestLoLDataETL))
    test_suite.addTest(unittest.makeSuite(TestETLMainFunction))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite) 