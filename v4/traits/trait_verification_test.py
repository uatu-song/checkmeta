"""
META Fantasy League Simulator - Trait Verification Test
Standalone script to verify trait loading from CSV
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("TraitVerification")

# Try to import the necessary modules
try:
    # First try to import from the local directory
    sys.path.append('.')
    from enhanced_trait_loader import TraitLoader
    from enhanced_trait_system import EnhancedTraitSystem
except ImportError:
    logger.error("Could not import enhanced trait modules")
    logger.error("Make sure enhanced_trait_loader.py and enhanced_trait_system.py are in the current directory")
    sys.exit(1)

def check_trait_file_exists(file_path: str) -> bool:
    """
    Check if the trait catalog file exists
    
    Args:
        file_path: Path to trait catalog file
        
    Returns:
        bool: True if file exists
    """
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        logger.info(f"Found trait catalog: {file_path} ({file_size} bytes)")
        return True
    else:
        logger.error(f"Trait catalog not found: {file_path}")
        return False

def find_trait_catalog() -> Optional[str]:
    """
    Find the trait catalog file in common locations
    
    Returns:
        str: Path to trait catalog file, or None if not found
    """
    # Common locations to check
    common_paths = [
        "data/traits/SimEngine v2  full_trait_catalog_export.csv",
        "SimEngine v2  full_trait_catalog_export.csv",
        "full_trait_catalog_export.csv",
        "../data/traits/SimEngine v2  full_trait_catalog_export.csv",
        "../../data/traits/SimEngine v2  full_trait_catalog_export.csv"
    ]
    
    for path in common_paths:
        if check_trait_file_exists(path):
            return path
    
    return None

def test_trait_loader() -> bool:
    """
    Test the TraitLoader functionality
    
    Returns:
        bool: True if testing succeeds
    """
    logger.info("=== Testing TraitLoader ===")
    
    # Find trait catalog file
    trait_file = find_trait_catalog()
    
    if not trait_file:
        logger.error("Could not find trait catalog file")
        return False
    
    try:
        # Create a trait loader with the found file
        trait_loader = TraitLoader()
        trait_loader.trait_file = trait_file
        
        # Load traits
        traits = trait_loader.load_traits()
        
        # Check that traits were loaded
        trait_count = len(traits)
        logger.info(f"Loaded {trait_count} traits")
        
        if trait_count == 0:
            logger.error("No traits loaded")
            return False
        elif trait_count < 41:
            logger.warning(f"Only {trait_count}/41 traits loaded")
        
        # Validate traits
        validation_report = trait_loader.validate_traits()
        
        # Print trait summary
        trait_loader.print_trait_summary()
        
        # Print validation report
        success_percentage = validation_report.get("success_percentage", 0)
        logger.info(f"Validation success: {success_percentage:.1f}%")
        
        missing_fields = validation_report.get("missing_fields", [])
        if missing_fields:
            logger.warning(f"{len(missing_fields)} traits have missing fields")
            for item in missing_fields[:3]:  # Show first 3
                logger.warning(f"  {item['trait_id']}: Missing {', '.join(item['missing'])}")
                
        invalid_traits = validation_report.get("invalid_traits", [])
        if invalid_traits:
            logger.warning(f"{len(invalid_traits)} traits have validation issues")
            for item in invalid_traits[:3]:  # Show first 3
                logger.warning(f"  {item['trait_id']}: {item['issue']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing TraitLoader: {e}")
        return False

def test_enhanced_trait_system() -> bool:
    """
    Test the EnhancedTraitSystem functionality
    
    Returns:
        bool: True if testing succeeds
    """
    logger.info("\n=== Testing EnhancedTraitSystem ===")
    
    try:
        # Create enhanced trait system
        enhanced_system = EnhancedTraitSystem()
        
        # Check trait count
        trait_count = enhanced_system.get_trait_count()
        logger.info(f"Enhanced system loaded {trait_count} traits")
        
        if trait_count == 0:
            logger.error("No traits loaded in enhanced system")
            return False
            
        # Get all trait IDs
        trait_ids = enhanced_system.get_all_trait_ids()
        logger.info(f"First 10 trait IDs: {trait_ids[:10]}")
        
        # Test character trait assignment
        test_character = {
            "name": "Test Character",
            "aDUR": 8,
            "aOP": 7,
            "aAM": 6
        }
        
        # Test for operations character
        assigned_traits_ops = enhanced_system.assign_traits_to_character(
            test_character, "o", "FL"
        )
        logger.info(f"Assigned traits (Operations): {assigned_traits_ops}")
        
        # Test for intelligence character
        assigned_traits_int = enhanced_system.assign_traits_to_character(
            test_character, "i", "PO"
        )
        logger.info(f"Assigned traits (Intelligence): {assigned_traits_int}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing EnhancedTraitSystem: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting trait verification test")
    
    # Test trait loader
    loader_success = test_trait_loader()
    
    # Test enhanced trait system
    system_success = test_enhanced_trait_system()
    
    # Overall result
    if loader_success and system_success:
        logger.info("\n✅ All tests passed successfully")
        return 0
    else:
        logger.error("\n❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())