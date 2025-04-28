"""
META Fantasy League Simulator - Injury System Demo
Demonstrates the Injury System functionality
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

logger = logging.getLogger("InjurySystemDemo")

def create_test_character(char_id: str, name: str, role: str, team_id: str, attributes: Dict[str, int] = None) -> Dict[str, Any]:
    """Create a test character for demonstration
    
    Args:
        char_id: Character ID
        name: Character name
        role: Character role
        team_id: Team ID
        attributes: Optional custom attributes
        
    Returns:
        dict: Test character data
    """
    # Default attributes
    default_attributes = {
        "aSTR": 5,
        "aSPD": 5,
        "aDUR": 5,
        "aWIL": 5,
        "aFS": 5,
        "aLDR": 5,
        "aOP": 5,
        "aAM": 5,
        "aRES": 5,
        "aSBY": 5
    }
    
    # Override with custom attributes if provided
    if attributes:
        default_attributes.update(attributes)
    
    return {
        "id": char_id,
        "name": name,
        "role": role,
        "team_id": team_id,
        "team_name": f"Team {team_id[1:]}",
        **default_attributes,
        "was_active": True,
        "is_active": True,
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
    # Create convergence logs
    convergence_logs = []
    
    # Add some sample convergences
    for i, char in enumerate(characters):
        # Make every other character lose convergences
        if i % 2 == 0:
            # Create 3 convergence losses
            for j in range(3):
                opponent = characters[(i + j + 1) % len(characters)]
                convergence_logs.append({
                    "square": f"e{j+2}",
                    "a_character": char["name"],
                    "b_character": opponent["name"],
                    "a_roll": 30,
                    "b_roll": 60,
                    "winner": opponent["name"],
                    "loser": char["name"],
                    "damage": 15,
                    "reduced_damage": 10,
                    "outcome": "success"
                })
        else:
            # Create a win
            opponent = characters[(i + 1) % len(characters)]
            convergence_logs.append({
                "square": f"d{i+2}",
                "a_character": char["name"],
                "b_character": opponent["name"],
                "a_roll": 70,
                "b_roll": 40,
                "winner": char["name"],
                "loser": opponent["name"],
                "damage": 20,
                "reduced_damage": 15,
                "outcome": "success"
            })
    
    return {
        "match_id": "test_match_001",
        "day": 1,
        "team_a_id": "t001",
        "team_b_id": "t002",
        "team_a_name": "Team 001",
        "team_b_name": "Team 002",
        "winner": "Team A",
        "winning_team": "Team 001",
        "character_results": characters,
        "convergence_logs": convergence_logs
    }

def run_injury_system_demo():
    """Run the injury system demonstration"""
    try:
        # Import injury system
        sys.path.append('.')
        from injury_system import InjurySystem, InjurySeverity
        
        logger.info("=== INJURY SYSTEM DEMO ===")
        
        # Create injury system
        injury_system = InjurySystem()
        
        # Create test persistence directory
        persistence_dir = "data/persistence"
        os.makedirs(persistence_dir, exist_ok=True)
        
        # Create test characters with different attribute levels
        characters = [
            # Standard character (average stats)
            create_test_character("t001_1", "Alice", "FL", "t001"),
            
            # High durability character (less likely to be injured)
            create_test_character("t001_2", "Bob", "VG", "t001", {"aDUR": 8}),
            
            # High resilience character (less severe injuries)
            create_test_character("t002_1", "Charlie", "RG", "t002", {"aRES": 9}),
            
            # High stability character (faster recovery)
            create_test_character("t002_2", "Diana", "SV", "t002", {"aSBY": 8}),
            
            # Injury-prone character (low DUR, RES, SBY)
            create_test_character("t003_1", "Eve", "GO", "t003", {"aDUR": 3, "aRES": 2, "aSBY": 3})
        ]
        
        # Modify results to increase injury chances
        characters[0]["is_ko"] = True  # Alice is KO'd
        characters[2]["HP"] = 15  # Charlie has low health
        characters[4]["is_ko"] = True  # Eve is KO'd
        
        # Show initial character states
        logger.info("Initial character states:")
        for char in characters:
            logger.info(f"  {char['name']} ({char['role']})")
            special_attrs = {k: v for k, v in char.items() if k in ["aDUR", "aRES", "aSBY"]}
            logger.info(f"    Stats: {special_attrs}")
            if char.get("is_ko", False):
                logger.info(f"    Status: KO'd")
            elif char.get("HP", 100) < 20:
                logger.info(f"    Status: Low health ({char['HP']} HP)")
        
        # Create test match result
        match_result = create_test_match_result(characters)
        
        # Process injuries
        logger.info("\nProcessing post-match injuries:")
        injury_results = injury_system.handle_post_match_injuries(match_result)
        
        # Show injury results
        new_injuries = injury_results["new_injuries"]
        logger.info(f"New injuries: {len(new_injuries)}")
        
        for injury in new_injuries:
            char_name = injury["character_name"]
            injury_type = injury["injury_type"]
            severity = injury["severity"]
            recovery = injury["recovery_matches"]
            logger.info(f"  {char_name} - {injury_type} ({severity})")
            logger.info(f"    Recovery time: {recovery} matches")
            logger.info(f"    Attribute penalties: {injury['attribute_penalties']}")
        
        # Generate injury report
        logger.info("\nInjury Report:")
        report = injury_system.generate_injury_report_text()
        print(report)
        
        # Demonstrate applying injury effects
        logger.info("\nApplying injury effects:")
        
        for char in characters:
            char_id = char.get("id", "unknown")
            
            # Skip non-injured characters
            if char_id not in injury_system.injured_reserve:
                continue
            
            # Store original attributes for comparison
            original_attrs = {k: v for k, v in char.items() if k.startswith('a')}
            
            # Apply injury effects
            effects = injury_system.apply_injury_effects(char)
            
            # Show effects
            logger.info(f"  {char['name']} - {effects['injury_type']} ({effects['severity']})")
            logger.info(f"    Matches remaining: {effects['matches_remaining']}")
            
            # Show attribute changes
            modified_attrs = {k: v for k, v in char.items() if k.startswith('a')}
            for attr, value in modified_attrs.items():
                if attr in original_attrs and original_attrs[attr] != value:
                    logger.info(f"    {attr}: {original_attrs[attr]} -> {value}")
        
        # Demonstrate recovery
        logger.info("\nSimulating recovery (advancing 1 match day):")
        recovered = injury_system.update_recovery_progress(2)
        
        # Show recovered characters
        if recovered:
            logger.info(f"Recovered: {len(recovered)}")
            for recovery in recovered:
                char_name = recovery["character_name"]
                injury_type = recovery["injury_type"]
                logger.info(f"  {char_name} recovered from {injury_type}")
        else:
            logger.info("No characters recovered")
        
        # Generate updated injury report
        logger.info("\nUpdated Injury Report:")
        updated_report = injury_system.generate_injury_report_text()
        print(updated_report)
        
        # Demonstrate manually adding an injury
        logger.info("\nManually adding an injury:")
        
        # Get a character who isn't injured yet
        non_injured = next((c for c in characters if not injury_system.is_character_injured(c)), None)
        
        if non_injured:
            # Add manual injury
            manual_injury = injury_system.manually_add_injury(
                non_injured,
                "Broken Arm",
                InjurySeverity.MAJOR,
                5
            )
            
            logger.info(f"  Added {manual_injury['injury_type']} to {non_injured['name']}")
            logger.info(f"    Severity: {manual_injury['severity']}")
            logger.info(f"    Recovery: {manual_injury['recovery_matches']} matches")
            logger.info(f"    Penalties: {manual_injury['attribute_penalties']}")
        
        # Save IR list
        injury_system._save_ir_list()
        
        # Check loading
        logger.info("\nTesting IR list persistence:")
        
        # Create new injury system instance
        new_system = InjurySystem()
        
        # Check if IR list was loaded
        ir_count = len(new_system.injured_reserve)
        logger.info(f"  Loaded {ir_count} injuries from persistence")
        
        # Show how DUR, RES, and SBY affect injuries
        logger.info("\nAttribute Impact Analysis:")
        logger.info("  DUR (Durability) - Reduces injury chance")
        logger.info("  RES (Resilience) - Reduces injury severity")
        logger.info("  SBY (Stability) - Speeds up recovery time")
        
        logger.info("\nExample impacts:")
        logger.info("  DUR 3 vs DUR 8: ~25% difference in injury chance")
        logger.info("  RES 3 vs RES 8: Regular injury might be 1 severity level lower")
        logger.info("  SBY 3 vs SBY 8: ~30% reduction in recovery time")
        
        logger.info("\n=== INJURY SYSTEM DEMO COMPLETE ===")
        
    except ImportError:
        logger.error("Could not import Injury System")
        logger.error("Make sure injury_system.py is in the current directory")
        return False
    except Exception as e:
        logger.error(f"Error running injury system demo: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_injury_system_demo()
    sys.exit(0 if success else 1)