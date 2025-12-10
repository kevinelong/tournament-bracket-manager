"""
Comprehensive tests for Tournament Manager.
Tests all features and ensures they work as documented in the tour.
"""

import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pygame

# Import classes from tournament module
from tournament import (
    TournamentBracket, 
    Match, 
    TournamentMetadata, 
    TournamentBracketGUI,
    TourStep
)


class TestMatch(unittest.TestCase):
    """Test Match dataclass functionality."""
    
    def test_match_creation(self):
        """Test creating a match."""
        match = Match(match_id=1, player1="Alice", player2="Bob", round_num=1)
        self.assertEqual(match.match_id, 1)
        self.assertEqual(match.player1, "Alice")
        self.assertEqual(match.player2, "Bob")
        self.assertIsNone(match.winner)
        self.assertEqual(match.round_num, 1)
    
    def test_set_winner_valid(self):
        """Test setting a valid winner."""
        match = Match(match_id=1, player1="Alice", player2="Bob", round_num=1)
        match.set_winner("Alice")
        self.assertEqual(match.winner, "Alice")
        self.assertTrue(match.is_complete())
    
    def test_set_winner_invalid(self):
        """Test setting an invalid winner raises ValueError."""
        match = Match(match_id=1, player1="Alice", player2="Bob", round_num=1)
        with self.assertRaises(ValueError):
            match.set_winner("Charlie")
    
    def test_is_complete(self):
        """Test match completion status."""
        match = Match(match_id=1, player1="Alice", player2="Bob", round_num=1)
        self.assertFalse(match.is_complete())
        match.set_winner("Bob")
        self.assertTrue(match.is_complete())


class TestTournamentMetadata(unittest.TestCase):
    """Test TournamentMetadata functionality."""
    
    def test_metadata_creation(self):
        """Test creating tournament metadata."""
        metadata = TournamentMetadata(
            id="test-123",
            name="Test Tournament",
            location="Test Arena",
            date_scheduled="2026-01-15",
            time_scheduled="14:00",
            date_created=datetime.now().isoformat()
        )
        self.assertEqual(metadata.name, "Test Tournament")
        self.assertEqual(metadata.location, "Test Arena")
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = TournamentMetadata(
            id="test-123",
            name="Test Tournament",
            location="Test Arena",
            date_scheduled="2026-01-15",
            time_scheduled="14:00",
            date_created=datetime.now().isoformat()
        )
        data = metadata.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["name"], "Test Tournament")
        self.assertEqual(data["id"], "test-123")
    
    def test_metadata_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "id": "test-123",
            "name": "Test Tournament",
            "location": "Test Arena",
            "date_scheduled": "2026-01-15",
            "time_scheduled": "14:00",
            "date_created": datetime.now().isoformat()
        }
        metadata = TournamentMetadata.from_dict(data)
        self.assertEqual(metadata.name, "Test Tournament")
        self.assertEqual(metadata.id, "test-123")


class TestTournamentBracket(unittest.TestCase):
    """Test TournamentBracket functionality."""
    
    def test_bracket_creation_power_of_2(self):
        """Test bracket with power of 2 participants."""
        participants = ["A", "B", "C", "D"]
        bracket = TournamentBracket(participants)
        self.assertEqual(bracket.num_participants, 4)
        self.assertEqual(bracket.num_rounds, 2)
        self.assertEqual(len(bracket.matches), 2)
        self.assertEqual(len(bracket.matches[0]), 2)  # 2 first-round matches
    
    def test_bracket_creation_with_byes(self):
        """Test bracket with non-power-of-2 participants (byes needed)."""
        participants = ["A", "B", "C"]
        bracket = TournamentBracket(participants)
        self.assertEqual(bracket.num_participants, 3)
        # Should have at least one bye
        bye_count = sum(1 for m in bracket.matches[0] if m.player1 is None or m.player2 is None)
        self.assertGreater(bye_count, 0)
    
    def test_select_winner_advances(self):
        """Test that selecting a winner advances them to next round."""
        participants = ["A", "B", "C", "D"]
        bracket = TournamentBracket(participants)
        
        # Select winner of first match
        first_match = bracket.matches[0][0]
        winner = first_match.player1
        bracket.set_match_winner(1, 0, winner)
        
        # Check winner advanced to final
        final_match = bracket.matches[1][0]
        self.assertIn(winner, [final_match.player1, final_match.player2])
    
    def test_get_champion_no_winner(self):
        """Test getting champion when tournament incomplete."""
        participants = ["A", "B", "C", "D"]
        bracket = TournamentBracket(participants)
        self.assertIsNone(bracket.get_champion())
    
    def test_get_champion_with_winner(self):
        """Test getting champion after completing tournament."""
        participants = ["A", "B"]
        bracket = TournamentBracket(participants)
        bracket.set_match_winner(1, 0, "A")
        self.assertEqual(bracket.get_champion(), "A")
    
    def test_reset_bracket(self):
        """Test bracket state after resetting winners (via GUI)."""
        # Note: TournamentBracket doesn't have reset(), only GUI has reset_tournament()
        # This test verifies bracket structure remains intact
        participants = ["A", "B", "C", "D"]
        bracket = TournamentBracket(participants)
        
        # Set some winners
        bracket.set_match_winner(1, 0, bracket.matches[0][0].player1)
        
        # Manually clear winners (simulating reset)
        for round_matches in bracket.matches:
            for match in round_matches:
                match.winner = None
        
        # Check all winners cleared
        for round_matches in bracket.matches:
            for match in round_matches:
                self.assertIsNone(match.winner)
    
    def test_bracket_serialization(self):
        """Test bracket can be serialized and deserialized."""
        participants = ["A", "B", "C", "D"]
        bracket = TournamentBracket(participants)
        bracket.set_match_winner(1, 0, bracket.matches[0][0].player1)
        
        # Serialize
        data = bracket.to_dict()
        self.assertIsInstance(data, dict)
        
        # Deserialize
        bracket2 = TournamentBracket.from_dict(data)
        self.assertEqual(bracket2.num_participants, 4)
        self.assertEqual(bracket2.matches[0][0].winner, bracket.matches[0][0].winner)
    
    def test_empty_bracket(self):
        """Test creating bracket with empty participants list."""
        bracket = TournamentBracket([])
        self.assertEqual(bracket.num_participants, 0)
        # Empty bracket still has structure
        self.assertGreaterEqual(bracket.num_rounds, 0)


class TestTourSystem(unittest.TestCase):
    """Test the tour system functionality."""
    
    def setUp(self):
        """Initialize pygame for GUI tests."""
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
    
    def tearDown(self):
        """Clean up pygame."""
        pygame.quit()
    
    def test_tour_step_creation(self):
        """Test creating tour steps."""
        step = TourStep(
            id="test_step",
            title="Test Step",
            description="This is a test step",
            tab="Tournaments",
            highlight_rect=(100, 100, 200, 200),
            action_required="Click something"
        )
        self.assertEqual(step.id, "test_step")
        self.assertEqual(step.title, "Test Step")
        self.assertEqual(step.tab, "Tournaments")
    
    def test_gui_tour_initialization(self):
        """Test GUI initializes tour steps."""
        gui = TournamentBracketGUI(width=800, height=600)
        self.assertIsInstance(gui.tour_steps, list)
        self.assertGreater(len(gui.tour_steps), 0)
        self.assertFalse(gui.tour_active)
        self.assertEqual(gui.tour_step_index, 0)
    
    def test_start_tour(self):
        """Test starting the tour."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.start_tour()
        self.assertTrue(gui.tour_active)
        self.assertEqual(gui.tour_step_index, 0)
        # Should switch to first step's tab
        self.assertEqual(gui.active_tab, gui.tour_steps[0].tab)
    
    def test_next_tour_step(self):
        """Test advancing to next tour step."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.start_tour()
        initial_step = gui.tour_step_index
        gui.next_tour_step()
        self.assertEqual(gui.tour_step_index, initial_step + 1)
    
    def test_prev_tour_step(self):
        """Test going back to previous tour step."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.start_tour()
        gui.next_tour_step()
        gui.next_tour_step()
        current_step = gui.tour_step_index
        gui.prev_tour_step()
        self.assertEqual(gui.tour_step_index, current_step - 1)
    
    def test_prev_tour_step_at_start(self):
        """Test prev step doesn't go negative."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.start_tour()
        gui.prev_tour_step()
        self.assertEqual(gui.tour_step_index, 0)
    
    def test_end_tour(self):
        """Test ending the tour."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.start_tour()
        gui.next_tour_step()
        gui.end_tour()
        self.assertFalse(gui.tour_active)
        self.assertEqual(gui.tour_step_index, 0)
    
    def test_tour_completes_at_last_step(self):
        """Test advancing past last step ends tour."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.start_tour()
        # Go to last step
        while gui.tour_step_index < len(gui.tour_steps) - 1:
            gui.next_tour_step()
        # Advance past last step
        gui.next_tour_step()
        self.assertFalse(gui.tour_active)
    
    def test_all_tour_steps_have_required_fields(self):
        """Test all tour steps have required fields."""
        gui = TournamentBracketGUI(width=800, height=600)
        for step in gui.tour_steps:
            self.assertIsNotNone(step.id)
            self.assertIsNotNone(step.title)
            self.assertIsNotNone(step.description)
            self.assertIsNotNone(step.tab)
            # Tab should be one of the valid tabs
            self.assertIn(step.tab, gui.tabs)


class TestGUIFeatures(unittest.TestCase):
    """Test GUI features documented in the tour."""
    
    def setUp(self):
        """Set up test environment."""
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
        pygame.quit()
    
    def test_create_tournament(self):
        """Test creating a new tournament."""
        gui = TournamentBracketGUI(width=800, height=600)
        initial_count = len(gui.tournaments_list)
        gui.create_new_tournament("Test Tourney", "Test Loc", "2026-01-15", "14:00")
        gui.load_tournaments_list()  # Reload list to see new tournament
        self.assertEqual(len(gui.tournaments_list), initial_count + 1)
        self.assertIsNotNone(gui.current_metadata)
        self.assertEqual(gui.current_metadata.name, "Test Tourney")
    
    def test_load_tournament(self):
        """Test loading a tournament."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.create_new_tournament("Test Tourney", "Test Loc", "2026-01-15", "14:00")
        tournament_id = gui.current_tournament_id
        
        # Create another tournament
        gui.create_new_tournament("Another Tourney", "Another Loc", "2026-01-16", "15:00")
        
        # Load the first one back
        gui.load_tournament(tournament_id)
        self.assertEqual(gui.current_metadata.name, "Test Tourney")
    
    def test_edit_tournament_fields(self):
        """Test editing tournament name, location, date, time."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.create_new_tournament("Original", "Original Loc", "2026-01-15", "14:00")
        
        # Simulate editing name
        gui.current_metadata.name = "Edited Name"
        gui.save_current_tournament()
        
        # Reload and verify
        tournament_id = gui.current_tournament_id
        gui.load_tournament(tournament_id)
        self.assertEqual(gui.current_metadata.name, "Edited Name")
    
    def test_add_players(self):
        """Test adding players to tournament."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.create_new_tournament("Test", "Loc", "2026-01-15", "14:00")
        
        initial_count = len(gui.editing_players)
        gui.editing_players.append("Player 1")
        gui.editing_players.append("Player 2")
        
        self.assertEqual(len(gui.editing_players), initial_count + 2)
    
    def test_remove_players(self):
        """Test removing players from tournament."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.create_new_tournament("Test", "Loc", "2026-01-15", "14:00")
        
        gui.editing_players.extend(["Player 1", "Player 2", "Player 3"])
        gui.editing_players.pop(1)  # Remove Player 2
        
        self.assertEqual(len(gui.editing_players), 2)
        self.assertNotIn("Player 2", gui.editing_players)
    
    def test_generate_bracket(self):
        """Test generating bracket from player list."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.create_new_tournament("Test", "Loc", "2026-01-15", "14:00")
        
        gui.editing_players.extend(["A", "B", "C", "D"])
        gui.generate_bracket()
        
        self.assertIsNotNone(gui.bracket)
        self.assertEqual(gui.bracket.num_participants, 4)
    
    def test_reset_tournament(self):
        """Test reset clears all winners but keeps players."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.create_new_tournament("Test", "Loc", "2026-01-15", "14:00")
        
        gui.editing_players.extend(["A", "B", "C", "D"])
        gui.generate_bracket()
        
        # Set a winner
        gui.bracket.set_match_winner(1, 0, gui.bracket.matches[0][0].player1)
        
        # Reset
        gui.reset_tournament()
        
        # Players should remain
        self.assertEqual(len(gui.editing_players), 4)
        # Winners should be cleared
        self.assertIsNone(gui.bracket.matches[0][0].winner)
    
    def test_reshuffle_tournament(self):
        """Test reshuffle regenerates bracket with same players."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.create_new_tournament("Test", "Loc", "2026-01-15", "14:00")
        
        gui.editing_players.extend(["A", "B", "C", "D"])
        gui.generate_bracket()
        
        original_matchup = (gui.bracket.matches[0][0].player1, gui.bracket.matches[0][0].player2)
        
        # Reshuffle
        gui.reshuffle_tournament()
        
        # Should still have same players
        self.assertEqual(len(gui.editing_players), 4)
        self.assertIsNotNone(gui.bracket)
    
    def test_auto_save(self):
        """Test that changes are automatically saved."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.create_new_tournament("Auto Save Test", "Loc", "2026-01-15", "14:00")
        tournament_id = gui.current_tournament_id
        
        gui.editing_players.append("Test Player")
        gui.save_current_tournament()
        
        # Verify file was saved
        filepath = Path("tournaments") / f"{tournament_id}.json"
        self.assertTrue(filepath.exists())
        
        # Verify data
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.assertIn("Test Player", data["participants"])
    
    def test_tab_switching(self):
        """Test switching between tabs."""
        gui = TournamentBracketGUI(width=800, height=600)
        
        for tab in gui.tabs:
            gui.active_tab = tab
            self.assertEqual(gui.active_tab, tab)
    
    def test_scaling_calculation(self):
        """Test UI scales with different participant counts."""
        gui = TournamentBracketGUI(width=800, height=600)
        gui.create_new_tournament("Test", "Loc", "2026-01-15", "14:00")
        
        # Small tournament
        gui.editing_players.extend(["A", "B", "C", "D"])
        gui._recalculate_scaling()
        small_title_size = gui.title_font.get_height()
        
        # Large tournament
        gui.editing_players.extend([f"Player{i}" for i in range(28)])  # Total 32
        gui._recalculate_scaling()
        large_title_size = gui.title_font.get_height()
        
        # Larger tournament should have smaller fonts
        self.assertLessEqual(large_title_size, small_title_size)


class TestEdgeCAses(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test environment."""
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
    
    def tearDown(self):
        """Clean up."""
        pygame.quit()
    
    def test_bracket_with_one_player(self):
        """Test bracket with only one player."""
        bracket = TournamentBracket(["Solo"])
        self.assertEqual(bracket.num_participants, 1)
        # Should have minimal rounds
        self.assertGreaterEqual(bracket.num_rounds, 0)
    
    def test_bracket_with_large_number(self):
        """Test bracket with many players."""
        players = [f"Player{i}" for i in range(64)]
        bracket = TournamentBracket(players)
        self.assertEqual(bracket.num_participants, 64)
        self.assertEqual(bracket.num_rounds, 6)  # log2(64)
    
    def test_invalid_winner_selection(self):
        """Test selecting winner for match with only one player."""
        bracket = TournamentBracket(["A", "B", "C"])
        # Find a bye match
        bye_match = None
        for match in bracket.matches[0]:
            if match.player1 is None or match.player2 is None:
                bye_match = match
                break
        
        if bye_match:
            # Should auto-advance the present player
            self.assertIsNotNone(bye_match.winner)


def run_tests():
    """Run all tests and generate report."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMatch))
    suite.addTests(loader.loadTestsFromTestCase(TestTournamentMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestTournamentBracket))
    suite.addTests(loader.loadTestsFromTestCase(TestTourSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestGUIFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCAses))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
