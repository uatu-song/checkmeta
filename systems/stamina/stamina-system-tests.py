"""
META Fantasy League Simulator - Stamina System Tests
===================================================

Comprehensive test suite for the stamina system with unit and integration tests.
"""

import unittest
import json
import os
import datetime
from unittest.mock import MagicMock, patch

# Import the StaminaSystem
from stamina_system import StaminaSystem

class TestStaminaSystem(unittest.TestCase):
    """Test suite for the StaminaSystem class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create mock config and registry
        self.config = {
            "paths": {
                "stamina_config": "tests/stamina_config_test.json",
                "stamina_data": "tests/stamina_data_test.json"
            }
        }
        
        self.registry = MagicMock()
        
        # Create mock event system
        self.event_system = MagicMock()
        self.registry.get.return_value = self.event_system
        
        # Create test directory if it doesn't exist
        os.makedirs("tests", exist_ok=True)
        
        # Create stamina system
        self.stamina_system = StaminaSystem(self.config, self.registry)
        
        # Initialize with default config
        self.stamina_system.stamina_config = self.stamina_system._get_default_config()
        
        # Create test character
        self.character = {
            "id": "test_char_1",
            "name": "Test Character",
            "team_id": "team_1",
            "aDUR": 60  # Above average durability
        }
        
        # Test match context
        self.match_context = {
            "match_id": "test_match_1",
            "round": 1
        }
    
    def tearDown(self):
        """Clean up after each test"""
        # Remove test files
        if os.path.exists("tests/stamina_config_test.json"):
            os.remove("tests/stamina_config_test.json")
        
        if os.path.exists("tests/stamina_data_test.json"):
            os.remove("tests/stamina_data_test.json")
    
    def test_initialization(self):
        """Test character stamina initialization"""
        # Test initialization
        stamina = self.stamina_system.initialize_character_stamina(self.character)
        
        # Stamina should be slightly above base due to DUR
        self.assertGreater(stamina, 100)
        self.assertLessEqual(stamina, 105)
        
        # Should have empty stamina log
        self.assertEqual(len(self.character["stamina_log"]), 0)
        
        # Should have empty effects list
        self.assertIn("effects", self.character)
        self.assertEqual(len(self.character["effects"]), 0)
    
    def test_stamina_cost(self):
        """Test applying stamina costs"""
        # Initialize character
        initial_stamina = self.stamina_system.initialize_character_stamina(self.character)
        
        # Apply standard move cost
        self.stamina_system.apply_stamina_cost(
            self.character, 
            1.0, 
            "standard_move", 
            self.match_context
        )
        
        # Stamina should decrease
        self.assertLess(self.character["stamina"], initial_stamina)
        
        # Should have a log entry
        self.assertEqual(len(self.character["stamina_log"]), 1)
        
        # Event should be emitted
        self.event_system.emit.assert_called_once()
        
        # Apply trait activation cost
        old_stamina = self.character["stamina"]
        self.stamina_system.apply_stamina_cost(
            self.character,
            5.0,
            "trait_activation:powerful_attack",
            self.match_context
        )
        
        # Stamina should decrease more
        self.assertLess(self.character["stamina"], old_stamina)
        
        # Should have another log entry
        self.assertEqual(len(self.character["stamina_log"]), 2)
        
        # Event should be emitted again
        self.assertEqual(self.event_system.emit.call_count, 2)
    
    def test_cost_calculation(self):
        """Test stamina cost calculation based on attributes"""
        # Initialize character with different DUR values
        high_dur_char = {
            "id": "high_dur",
            "name": "High Durability",
            "aDUR": 80  # High durability
        }
        
        low_dur_char = {
            "id": "low_dur",
            "name": "Low Durability",
            "aDUR": 30  # Low durability
        }
        
        # Calculate costs
        high_dur_cost = self.stamina_system._calculate_actual_cost(
            high_dur_char, 10.0, "standard_move"
        )
        
        low_dur_cost = self.stamina_system._calculate_actual_cost(
            low_dur_char, 10.0, "standard_move"
        )
        
        # High durability should have lower cost
        self.assertLess(high_dur_cost, low_dur_cost)
        
        # Test trait activation costs
        high_cost = self.stamina_system._calculate_actual_cost(
            self.character, 10.0, "trait_activation:ultimate_power"
        )
        
        low_cost = self.stamina_system._calculate_actual_cost(
            self.character, 10.0, "trait_activation:quick_jab"
        )
        
        # Ultimate power should cost more if trait system returns different categories
        trait_system = MagicMock()
        trait_system.get_trait_cost_category.side_effect = lambda name: "extreme" if name == "ultimate_power" else "low"
        self.registry.get.return_value = trait_system
        
        # Mock trait_system to test cost categories
        with patch.object(self.registry, 'get', return_value=trait_system):
            high_cost = self.stamina_system._calculate_actual_cost(
                self.character, 10.0, "trait_activation:ultimate_power"
            )
            
            low_cost = self.stamina_system._calculate_actual_cost(
                self.character, 10.0, "trait_activation:quick_jab"
            )
            
            # Ultimate power should cost more
            self.assertGreater(high_cost, low_cost)
    
    def test_stamina_effects(self):
        """Test stamina effects at different thresholds"""
        # Initialize character
        self.stamina_system.initialize_character_stamina(self.character)
        
        # Test at different stamina levels
        for stamina_level, expected_effects in [
            (100, 0),  # Full stamina: no effects
            (50, 0),   # Above first threshold: no effects
            (55, 1),   # Just below first threshold: minor fatigue
            (35, 3),   # Below second threshold: moderate fatigue effects
            (15, 5)    # Below third threshold: severe fatigue effects
        ]:
            self.character["stamina"] = stamina_level
            effects = self.stamina_system.apply_stamina_effects(
                self.character, self.match_context
            )
            
            # Check effect count
            if expected_effects == 0:
                self.assertEqual(len(effects), 0, f"At stamina {stamina_level}, expected no effects")
            else:
                self.assertGreaterEqual(len(effects), expected_effects, 
                                      f"At stamina {stamina_level}, expected at least {expected_effects} effects")
    
    def test_stamina_recovery(self):
        """Test stamina recovery mechanics"""
        # Initialize character at low stamina
        self.stamina_system.initialize_character_stamina(self.character)
        self.character["stamina"] = 30
        
        # Apply recovery
        recovery = self.stamina_system.apply_stamina_recovery(
            self.character, self.match_context
        )
        
        # Should recover some stamina
        self.assertGreater(recovery, 0)
        self.assertGreater(self.character["stamina"], 30)
        
        # Event should be emitted
        args, _ = self.event_system.emit.call_args
        self.assertEqual(args[0]["type"], "stamina_recovery")
        
        # Test recovery with severe fatigue effect
        self.character["stamina"] = 15
        self.stamina_system.apply_stamina_effects(self.character, self.match_context)
        
        old_stamina = self.character["stamina"]
        recovery = self.stamina_system.apply_stamina_recovery(
            self.character, self.match_context
        )
        
        # Should recover less with severe fatigue
        self.assertLess(recovery, self.stamina_system.stamina_config["base_recovery"])
    
    def test_end_of_round_effects(self):
        """Test end of round stamina effects"""
        # Initialize character
        self.stamina_system.initialize_character_stamina(self.character)
        initial_stamina = self.character["stamina"]
        
        # Apply end of round effects
        self.stamina_system.apply_end_of_round_effects(
            [self.character], self.match_context
        )
        
        # Should have decay and recovery
        # Net might be positive or negative depending on config
        self.assertNotEqual(self.character["stamina"], initial_stamina)
        
        # Should have at least two log entries (decay and recovery)
        self.assertGreaterEqual(len(self.character["stamina_log"]), 2)
    
    def test_trait_usage_checks(self):
        """Test checks for trait usage based on stamina"""
        # Initialize character
        self.stamina_system.initialize_character_stamina(self.character)
        
        # With full stamina, should be able to use traits
        can_use, reason = self.stamina_system.can_use_trait(
            self.character, "some_trait", 10.0
        )
        self.assertTrue(can_use)
        
        # With low stamina, might not be able to use high-cost traits
        self.character["stamina"] = 5
        can_use, reason = self.stamina_system.can_use_trait(
            self.character, "some_trait", 10.0
        )
        self.assertFalse(can_use)
        
        # With severe fatigue, should not be able to use high-cost traits
        self.character["stamina"] = 15
        self.stamina_system.apply_stamina_effects(self.character, self.match_context)
        
        # Mock trait_system to test cost categories
        trait_system = MagicMock()
        trait_system.get_trait_cost_category.return_value = "high"
        
        with patch.object(self.registry, 'get', return_value=trait_system):
            can_use, reason = self.stamina_system.can_use_trait(
                self.character, "high_cost_trait", 5.0
            )
            self.assertFalse(can_use)
    
    def test_trait_chance_modifier(self):
        """Test trait chance modification due to stamina"""
        # Initialize character
        self.stamina_system.initialize_character_stamina(self.character)
        
        # Full stamina: no modifier
        base_chance = 0.8
        modified = self.stamina_system.calculate_trait_chance_modifier(
            self.character, base_chance
        )
        self.assertEqual(modified, base_chance)
        
        # Low stamina (40% threshold): reduced chance
        self.character["stamina"] = 35
        self.stamina_system.apply_stamina_effects(self.character, self.match_context)
        
        modified = self.stamina_system.calculate_trait_chance_modifier(
            self.character, base_chance
        )
        self.assertLess(modified, base_chance)
    
    def test_resignation_chance(self):
        """Test resignation chance calculation due to extreme fatigue"""
        # Initialize character
        self.stamina_system.initialize_character_stamina(self.character)
        
        # Full stamina: no chance
        chance = self.stamina_system.calculate_resignation_chance(self.character)
        self.assertEqual(chance, 0.0)
        
        # Extreme fatigue: some chance
        self.character["stamina"] = 15
        self.stamina_system.apply_stamina_effects(self.character, self.match_context)
        
        chance = self.stamina_system.calculate_resignation_chance(self.character)
        self.assertGreater(chance, 0.0)
        
        # Very low stamina: higher chance
        self.character["stamina"] = 5
        self.stamina_system.apply_stamina_effects(self.character, self.match_context)
        
        higher_chance = self.stamina_system.calculate_resignation_chance(self.character)
        self.assertGreater(higher_chance, chance)
    
    def test_persist_between_matches(self):
        """Test stamina persistence between matches"""
        # Initialize character
        self.stamina_system.initialize_character_stamina(self.character)
        self.character["stamina"] = 50  # Set to a known value
        
        # End match
        self.stamina_system.process_match_end(
            self.character, "win", self.match_context
        )
        
        # Check persistence
        self.assertIn(self.character["id"], self.stamina_system.persistent_stamina)
        self.assertEqual(
            self.stamina_system.persistent_stamina[self.character["id"]]["stamina"], 
            50
        )
        
        # Initialize again (should use persisted value)
        self.character["stamina"] = 100  # Set to a different value
        new_stamina = self.stamina_system.initialize_character_stamina(self.character)
        
        # Should use persisted value
        self.assertEqual(new_stamina, 50)
    
    def test_overnight_recovery(self):
        """Test overnight stamina recovery"""
        # Setup persistent data
        character_id = "test_char_1"
        self.stamina_system.persistent_stamina = {
            character_id: {
                "stamina": 30,
                "last_match_date": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
                "last_match_id": "old_match"
            }
        }
        
        # Create a mock date for "today"
        today = datetime.datetime.now().isoformat()
        
        # Mock datetime to return a specific "now"
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.datetime.fromisoformat(today)
            mock_datetime.fromisoformat = datetime.datetime.fromisoformat
            
            # Initialize character (should apply overnight recovery)
            self.stamina_system.initialize_character_stamina(self.character)
            
            # Should have recovered stamina
            self.assertGreater(self.character["stamina"], 30)
    
    def test_calibration_methods(self):
        """Test calibration methods for balance adjustments"""
        # Test decay multiplier
        original = self.stamina_system.stamina_config["decay_multiplier"]
        result = self.stamina_system.set_decay_multiplier(1.5)
        self.assertTrue(result)
        self.assertEqual(self.stamina_system.stamina_config["decay_multiplier"], 1.5)
        
        # Test invalid value
        result = self.stamina_system.set_decay_multiplier(3.0)  # Above max
        self.assertFalse(result)
        self.assertEqual(self.stamina_system.stamina_config["decay_multiplier"], 1.5)
        
        # Test low stamina damage percent
        result = self.stamina_system.set_low_stamina_damage_percent(30)
        self.assertTrue(result)
        
        # Check threshold effects updated
        for threshold, effects in self.stamina_system.stamina_config["thresholds"].items():
            for effect in effects:
                if effect["id"] == "moderate_fatigue" and effect["effect"] == "damage_penalty":
                    self.assertEqual(effect["value"], 0.3)  # 30%
                elif effect["id"] == "severe_fatigue" and effect["effect"] == "damage_penalty":
                    self.assertEqual(effect["value"], 0.6)  # 60% (double)

if __name__ == "__main__":
    unittest.main()
