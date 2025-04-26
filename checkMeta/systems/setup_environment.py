# setup_environment.py

import os
import shutil
from pathlib import Path

def create_directories(base_dir):
    """Create the required directory structure."""
    directories = [
        "config",
        "data/lineups",
        "data/traits",
        "data/teams",  # Added teams directory
        "models",
        "results",
        "reports/AARs",
        "systems",
        "utils",
        "simulator"
    ]
    
    for directory in directories:
        Path(os.path.join(base_dir, directory)).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def move_files(base_dir):
    """Move files to their appropriate locations."""
    file_mappings = [
        # Config files
        ("config/game_config.py", "config/game_config.py"),
        ("config/openings.py", "config/openings.py"),
        
        # Data files
        ("data/Attribute Stats.csv", "data/Attribute_Stats.csv"),
        ("data/lineups/All Lineups (1).xlsx", "data/lineups/All_Lineups.xlsx"),
        ("checkMeta_modularized/Master Roster.csv", "data/Master_Roster.csv"),
        ("data/traits/SimEngine v2 - full_trait_catalog_export.csv", "data/traits/trait_catalog.csv"),
        ("SimEngine v3 teamIDs 1.csv", "data/teams/team_ids.csv"),  # Added team ID file
        
        # Models
        ("models/character.py", "models/character.py"),
        ("models/team.py", "models/team.py"),
        ("models/match.py", "models/match.py"),
        
        # Results
        ("results/day_1_results_20250425_220321.json", "results/day_1_results_20250425_220321.json"),
        
        # Systems
        ("systems/chess_engine.py", "systems/chess_engine.py"),
        ("systems/morale.py", "systems/morale.py"),
        ("systems/traits.py", "systems/traits.py"),
        ("simulation/convergence.py", "systems/convergence.py"),
        ("checkMeta_modularized/systems/experience.py", "systems/experience.py"),
        
        # Utils
        ("utils/helpers.py", "utils/helpers.py"),
        ("checkMeta_modularized/utils/data_loader.py", "utils/data_loader.py"),
        ("checkMeta_modularized/utils/match_helpers.py", "utils/match_helpers.py"),
        
        # Simulator
        ("checkMeta_modularized/simulator/meta_league_simulator.py", "simulator/meta_league_simulator.py"),
        
        # Reports
        ("sally_floyd.py", "reports/sally_floyd.py"),  # Added Sally Floyd report generator
        
        # Main Entry Point
        ("main.py", "main.py"),
        ("README.md", "README.md")
    ]
    
    for source, destination in file_mappings:
        source_path = os.path.join(base_dir, source)
        dest_path = os.path.join(base_dir, destination)
        
        if os.path.exists(source_path):
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(source_path, dest_path)
            print(f"Copied: {source} -> {destination}")
        else:
            print(f"Warning: Source file not found: {source}")