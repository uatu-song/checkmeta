"""
META Fantasy League Simulator - XP System Demo
Demonstrates the XP Progression System functionality
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("XPSystemDemo")

def create_test_character(char_id: str, name: str, role: str, team_id: str) -> Dict[str, Any]:
    """Create a test character for demonstration
    
    Args:
        char_id: Character ID
        name: Character name
        role: Character role
        team_id: Team ID
        
    Returns:
        dict: Test character data
    """
    return {
        "id": char_id,
        "name": name,
        "role": role,
        "team_id": team_id,
        "team_name": f"Team {team_id[1:]}",
        "aSTR": 5,
        "aSPD": 5,
        "aDUR": 5,
        "aWIL": 5,
        "aFS": 5,
        "aLDR": 5,
        "aOP": 5,
        "aAM": 5,
        "aRES": 5,
        "aSBY": 5,
        "was_active": True,
        "is_ko": False,
        "result": "win",
        "rStats": {
            "rCVo": 2,
            "rOTD": 1,
            "rDDo": 50,
            "rHLG": 20
        }
    }

def create_test_match_result(characters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a test match result for demonstration
    
    Args:
        characters: List of characters in the match
        
    Returns:
        dict: Test match result data
    """
    return {
        "match_id": "test_match_001",
        "day": 1,
        "team_a_id": "t001",
        "team_b_id": "t002",
        "team_a_name": "Team 001",
        "team_b_name": "Team 002",
        "winner": "Team A",
        "winning_team": "Team 001",
        "character_results": characters
    }

def run_xp_system_demo():
    """Run the XP system demonstration"""
    try:
        # Import XP progression system
        sys.path.append('.')
        from xp_progression_system import XPProgressionSystem
        
        logger.info("=== XP PROGRESSION SYSTEM DEMO ===")
        
        # Create XP system
        xp_system = XPProgressionSystem()
        
        # Create test persistence directory
        persistence_dir = "data/persistence"
        os.makedirs(persistence_dir, exist_ok=True)
        
        # Create test characters
        characters = [
            create_test_character("t001_1", "Alice", "FL", "t001"),
            create_test_character("t001_2", "Bob", "VG", "t001"),
            create_test_character("t002_1", "Charlie", "RG", "t002"),
            create_test_character("t002_2", "Diana", "SV", "t002")
        ]
        
        # Modify results to show variety
        characters[1]["result"] = "loss"  # Bob loses
        characters[2]["result"] = "draw"  # Charlie draws
        characters[3]["rStats"]["rMBi"] = 3  # Diana has Mind Breaks
        
        # Show initial character states
        logger.info("Initial character states:")
        for char in characters:
            logger.info(f"  {char['name']} (Level 1)")
        
        # Create test match result
        match_result = create_test_match_result(characters)
        
        # Run match XP processing
        logger.info("\nProcessing match XP:")
        xp_results = xp_system.process_match_results(match_result)
        
        # Show XP results
        for char_prog in xp_results["character_progression"]:
            char_name = char_prog["character_name"]
            xp_earned = char_prog["xp_earned"]
            level_ups = char_prog["level_ups"]
            new_level = char_prog["new_level"]
            
            if level_ups > 0:
                logger.info(f"  {char_name} earned {xp_earned} XP and leveled up to {new_level}!")
                
                # Show stat increases
                increases = []
                for attr, value in char_prog["stat_increases"].items():
                    increases.append(f"{attr[1:]}+{value}")
                
                if increases:
                    logger.info(f"    Stat increases: {', '.join(increases)}")
            else:
                logger.info(f"  {char_name} earned {xp_earned} XP")
        
        # Show XP breakdown for a character
        logger.info("\nXP breakdown for Alice:")
        alice_breakdown = next(p for p in xp_results["character_progression"] if p["character_name"] == "Alice")["xp_breakdown"]
        
        for source, amount in alice_breakdown.items():
            logger.info(f"  {source}: {amount} XP")
        
        # Process a second match to demonstrate progression
        logger.info("\nProcessing second match:")
        
        # Update rStats to simulate a different match outcome
        for char in characters:
            char["rStats"]["rCVo"] = char["rStats"].get("rCVo", 0) + 1
            char["rStats"]["rDDo"] = char["rStats"].get("rDDo", 0) + 20
        
        # Process second match
        match_result["match_id"] = "test_match_002"
        match_result["day"] = 2
        xp_results_2 = xp_system.process_match_results(match_result)
        
        # Show second match results
        for char_prog in xp_results_2["character_progression"]:
            char_name = char_prog["character_name"]
            xp_earned = char_prog["xp_earned"]
            level_ups = char_prog["level_ups"]
            new_level = char_prog["new_level"]
            
            if level_ups > 0:
                logger.info(f"  {char_name} earned {xp_earned} XP and leveled up to {new_level}!")
                
                # Show stat increases
                increases = []
                for attr, value in char_prog["stat_increases"].items():
                    increases.append(f"{attr[1:]}+{value}")
                
                if increases:
                    logger.info(f"    Stat increases: {', '.join(increases)}")
            else:
                logger.info(f"  {char_name} earned {xp_earned} XP")
        
        # Generate progression report
        logger.info("\nProgression Report for Alice:")
        alice = next(char for char in characters if char["name"] == "Alice")
        alice_report = xp_system.generate_character_progression_report(alice)
        print(alice_report)
        
        # Print persistence file paths
        logger.info("\nCharacter progression saved to:")
        for char in characters:
            file_path = xp_system.save_character_progression(char)
            logger.info(f"  {char['name']}: {file_path}")
        
        # Test loading progression
        logger.info("\nTesting progression loading:")
        test_char = create_test_character("t001_1", "Alice", "FL", "t001")
        test_char["level"] = 1  # Reset level
        test_char["xp_total"] = 0  # Reset XP
        
        # Load saved progression
        updated_char = xp_system.apply_progression_to_character(test_char)
        
        logger.info(f"  Before loading: Level 1, XP 0")
        logger.info(f"  After loading: Level {updated_char['level']}, XP {updated_char['xp_total']}")
        
        # Show attribute growth potential
        logger.info("\nAttribute Growth Potential for Alice:")
        growth_potential = xp_system.get_growth_potential(alice)
        
        for attr, potential in sorted(growth_potential.items(), key=lambda x: x[1], reverse=True):
            if potential > 0:
                logger.info(f"  {attr[1:]}: {potential:.2f} potential growth")
        
        logger.info("\n=== XP PROGRESSION SYSTEM DEMO COMPLETE ===")
        
    except ImportError:
        logger.error("Could not import XP progression system")
        logger.error("Make sure xp_progression_system.py is in the current directory")
        return False
    except Exception as e:
        logger.error(f"Error running XP system demo: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_xp_system_demo()
    sys.exit(0 if success else 1)