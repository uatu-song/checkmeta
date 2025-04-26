#!/usr/bin/env python3
# reorganize_meta_sim.py

import os
import shutil
from pathlib import Path
import sys

def create_directories(base_dir):
    """Create the required directory structure"""
    directories = [
        "config",
        "data/lineups",
        "data/traits",
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
    """Move files to their appropriate locations"""
    # Define file mappings: (source, destination)
    file_mappings = [
        # Config files
        ("config/game_config.py", "config/game_config.py"),
        ("config/openings.py", "config/openings.py"),
        
        # Data files
        ("data/Attribute Stats.csv", "data/Attribute_Stats.csv"),
        ("data/lineups/All Lineups (1).xlsx", "data/lineups/All_Lineups.xlsx"),
        ("checkMeta_modularized/Master Roster.csv", "data/Master_Roster.csv"),
        ("data/traits/SimEngine v2 - full_trait_catalog_export.csv", "data/traits/trait_catalog.csv"),
        
        # Models
        ("models/character.py", "models/character.py"),
        ("models/team.py", "models/team.py"),
        ("models/match.py", "models/match.py"),
        
        # Results (preserve existing)
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
        
        # Main entry point
        ("main.py", "main.py"),
        ("README.md", "README.md")
    ]
    
    for source, destination in file_mappings:
        source_path = os.path.join(base_dir, source)
        dest_path = os.path.join(base_dir, destination)
        
        # Check if source exists
        if os.path.exists(source_path):
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, dest_path)
            print(f"Copied: {source} -> {destination}")
        else:
            print(f"Warning: Source file not found: {source}")

def create_new_files(base_dir):
    """Create new files needed for the project"""
    # Create rstat_manager.py in systems
    rstat_manager_path = os.path.join(base_dir, "systems/rstat_manager.py")
    with open(rstat_manager_path, "w") as f:
        f.write("""# systems/rstat_manager.py

import csv
import os
import datetime
from collections import defaultdict

class RStatManager:
    \"\"\"
    Manages recording and tracking of rStats based on the correct original design.
    \"\"\"
    
    def __init__(self):
        \"\"\"Initialize the rStat Manager with the canonical rStat definitions\"\"\"
        # Dictionary to store all unit stats
        self.unit_stats = defaultdict(lambda: defaultdict(int))
        
        # Basic canonical rStats
        self.canonical_rstats = {
            # General stats (shared across divisions)
            "DD": "Damage Dealt",
            "DS": "Damage Sustained",
            "OTD": "Opponent Takedown",
            "AST": "Assists",
            "ULT": "Ultimate Ability Uses",
            "LVS": "Lives Saved",
            "LLS": "Lives Lost",
            "CTT": "Critical Hits",
            "EVS": "Evasions",
            "FFD": "Friendly Fire Damage",
            "FFI": "Friendly Fire Incidents",
            "HLG": "Healing Provided",
            "LKO": "Loss by KO",
            "WIN": "Matches Won",
            "LOSS": "Matches Lost",
            "DRAW": "Matches Drawn",
            "CVG_WIN": "Convergence Wins",
            "CVG_LOSS": "Convergence Losses",
            
            # Operations division specific
            "RTDo": "Ranged Takedowns",
            "CQTo": "Close Quarters Takedowns",
            "BRXo": "Breach Executions",
            "HWIo": "Heavy Weapons Impact",
            "MOTo": "Multi Opponent Takedowns",
            "AMBo": "Ambush Successes",
            
            # Intelligence division specific
            "MBi": "Mental Battles",
            "ILSi": "Illusion Success",
            "FEi": "Forced Errors",
            "DSRi": "Disruption Effect",
            "INFi": "Infiltration Success",
            "RSPi": "Remote System Penetrations"
        }
        
        # Team-level stats
        self.team_stats = defaultdict(lambda: defaultdict(int))
        self.team_stat_categories = {
            "FL_SUB": "Field Leader Substitutions",
            "FL_DOWN": "Field Leader Knocked Down",
            "TOTAL_WIN": "Total Team Wins",
            "TOTAL_LOSS": "Total Team Losses"
        }
    
    # Add your other methods here...
""")
        print(f"Created: systems/rstat_manager.py")
    
    # Create sally_floyd.py in systems
    sally_floyd_path = os.path.join(base_dir, "systems/sally_floyd.py")
    with open(sally_floyd_path, "w") as f:
        f.write("""# systems/sally_floyd.py

import datetime
import os
import json
import random
from pathlib import Path

# Friendly name map for teams
friendly_name_map = {
    'T001': "Xavier's School", 
    'T002': 'Brotherhood', 
    'T003': 'Avengers', 
    'T004': 'Fantastic Four', 
    'T005': 'Hellfire Club', 
    'T006': 'Asgardians', 
    'T007': 'Shield Ops', 
    'T008': 'Mutant Underground', 
    'T009': 'X-Force', 
    'T010': 'The Illuminati'
}

def generate_sally_report(match_data, match_date=None):
    \"\"\"
    Generate a narrative report based on match data.
    
    Parameters:
    - match_data: Dictionary containing match results
    - match_date: Date of the match (default: today)
    
    Returns:
    - Dictionary with narrative report sections
    \"\"\"
    if match_date is None:
        match_date = datetime.datetime.now()
    
    # Extract key performers
    top_damage_dealer = None
    top_damage = 0
    top_ko = None
    most_kos = 0
    
    for result in match_data.get("character_results", []):
        # Track damage dealers
        damage = result.get("rDD", 0)
        if damage > top_damage:
            top_damage = damage
            top_damage_dealer = result
            
        # Track KOs
        kos = result.get("rOTD", 0)
        if kos > most_kos:
            most_kos = kos
            top_ko = result
    
    # Generate narrative sections
    team_dd = friendly_name_map.get(
        top_damage_dealer.get("team_id", "unknown") if top_damage_dealer else "unknown",
        "an unnamed team"
    )
    
    cinematic = f"{top_damage_dealer['name']} of {team_dd} unleashed {top_damage}00 damage — most of the league froze just watching." if top_damage_dealer else "The battlefield was surprisingly quiet today."
    
    tragedy = f"{top_ko['name']} dropped opponents like they were practice dummies. {most_kos} confirmed takedowns." if top_ko else "No standout performers today."
    
    # Generate random elements for flavor
    broken = random.choice([
        "Magik and Deadpool triggered simultaneous MBi flashes — no one's sure what the Overlay saw, but the Undercurrent twitched.",
        "Reality stuttered twice during the third quarter. Logs show a temporal anomaly that repaired itself.",
        "Three separate convergence points froze mid-calculation. The system thinks it's normal. It's not normal."
    ])
    
    traits = random.choice([
        "Godmode, Diamond Conversion, and Phoenix Fire all triggered ULTs today. The grid burned like it was finals.",
        "Someone went full Ultimate. The logs claim it was authorized. Half the spectators disagree.",
        "Trait cascades rippled across four separate engagements. This shouldn't be possible with current tech."
    ])
    
    overlays = random.choice([
        "One sim log shows Nova KO'd. Another shows him KO'ing. Sally can't verify either.",
        "The official log and what spectators saw don't match up. Again.",
        "Multiple timeline threads detected. Someone's messing with the simulation parameters."
    ])
    
    return {
        "match_date": match_date.strftime("%B %d, %Y"),
        "overlay_date": match_date.strftime("Week %W"),
        "undercurrent_code": f"UC-{match_date.strftime('%Y%m%d')}-FLOYD",
        "opening_paragraph": "Today, the Nexus battlefield felt cracked — not broken, not bent, just... trembling. Fighters blinked through timelines, and half the crowd was watching something that wasn't happening yet.",
        "cinematic_moment": cinematic,
        "broken_moment": broken,
        "tragedy_moment": tragedy,
        "trait_glitches": traits,
        "overlay_vs_undercurrent": overlays,
        "closing_quote": random.choice([
            "I saw what I saw. Doesn't mean I understood it.",
            "We logged it. The sim denied it. Typical Tuesday.",
            "If reality's fraying, I hope I'm at least writing in the margins."
        ])
    }

def save_sally_report(report, output_dir="reports/AARs"):
    \"\"\"
    Save a Sally Floyd report to a markdown file.
    
    Parameters:
    - report: Report dictionary from generate_sally_report
    - output_dir: Directory to save the report
    
    Returns:
    - Path to the saved file
    \"\"\"
    # Create directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create filename
    filename = f"SallyFloyd_AAR_{report['undercurrent_code']}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Format report as markdown
    markdown = f"# Sally Floyd — Embedded Dispatch\\n"
    markdown += f"**{report['overlay_date']}**\\n\\n"
    
    markdown += f"{report['opening_paragraph']}\\n\\n"
    
    markdown += f"### Standout Moments\\n\\n"
    markdown += f"**Cinematic:** {report['cinematic_moment']}\\n\\n"
    markdown += f"**Breakdown:** {report['broken_moment']}\\n\\n"
    markdown += f"**Tactical:** {report['tragedy_moment']}\\n\\n"
    
    markdown += f"### Anomalies\\n\\n"
    markdown += f"{report['trait_glitches']}\\n\\n"
    markdown += f"{report['overlay_vs_undercurrent']}\\n\\n"
    
    markdown += f"—\\n\\n"
    markdown += f"*\"{report['closing_quote']}\"*\\n\\n"
    markdown += f"*– Sally Floyd*"
    
    # Write to file
    with open(filepath, "w") as f:
        f.write(markdown)
    
    return filepath

def process_match_results(results_file, output_dir="reports/AARs"):
    \"\"\"
    Process a match results file and generate a Sally Floyd report.
    
    Parameters:
    - results_file: Path to the match results JSON file
    - output_dir: Directory to save the report
    
    Returns:
    - Path to the saved report
    \"\"\"
    # Load match results
    with open(results_file, "r") as f:
        results = json.load(f)
    
    # Extract date from filename
    date_str = os.path.basename(results_file).split("_")[1]
    match_date = datetime.datetime.strptime(date_str, "%Y%m%d")
    
    # Generate report
    report = generate_sally_report(results, match_date)
    
    # Save report
    return save_sally_report(report, output_dir)
""")
        print(f"Created: systems/sally_floyd.py")
    
    # Create pgn_recorder.py in utils
    pgn_recorder_path = os.path.join(base_dir, "utils/pgn_recorder.py")
    with open(pgn_recorder_path, "w") as f:
        f.write("""# utils/pgn_recorder.py

import os
import chess.pgn
import datetime
import shutil

class PGNRecorder:
    def __init__(self, base_dir="pgn_records"):
        self.base_dir = base_dir
        self.games = {}
        os.makedirs(self.base_dir, exist_ok=True)

    def initialize_game(self, unit_id, unit_name, team_name, event_name, day_number):
        game = chess.pgn.Game()
        game.headers["Event"] = event_name
        game.headers["Site"] = "Metachess Arena"
        game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        game.headers["Round"] = str(day_number)
        game.headers["White"] = unit_name
        game.headers["Black"] = "Generic AI"
        game.headers["Team"] = team_name
        self.games[unit_id] = {
            "game": game,
            "node": game
        }

    def record_move(self, unit_id, move_uci):
        if unit_id not in self.games:
            raise ValueError(f"No active game for unit {unit_id}")
        move = chess.Move.from_uci(move_uci)
        board = self.games[unit_id]["node"].board()
        if move not in board.legal_moves:
            raise ValueError(f"Illegal move {move_uci} for unit {unit_id}")
        self.games[unit_id]["node"] = self.games[unit_id]["node"].add_variation(move)

    def export_pgns(self, timestamp=None):
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(self.base_dir, timestamp)
        os.makedirs(output_dir, exist_ok=True)

        for unit_id, game_data in self.games.items():
            game = game_data["game"]
            pgn_path = os.path.join(output_dir, f"{unit_id}.pgn")
            with open(pgn_path, "w", encoding="utf-8") as f:
                exporter = chess.pgn.FileExporter(f)
                game.accept(exporter)

    def purge_old_records(self, days_to_keep=7):
        now = datetime.datetime.now()
        for folder in os.listdir(self.base_dir):
            folder_path = os.path.join(self.base_dir, folder)
            if os.path.isdir(folder_path):
                folder_time = datetime.datetime.fromtimestamp(os.path.getmtime(folder_path))
                if (now - folder_time).days > days_to_keep:
                    shutil.rmtree(folder_path)
""")
        print(f"Created: utils/pgn_recorder.py")

def main():
    """Main function to reorganize the project"""
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = "."  # Current directory
    
    print(f"Reorganizing project in: {base_dir}")
    
    # Create the directory structure
    create_directories(base_dir)
    
    # Move files to their appropriate locations
    move_files(base_dir)
    
    # Create new files
    create_new_files(base_dir)
    
    print("\nProject reorganization complete!")
    print("Note: This script copies files to their new locations but doesn't delete the originals.")
    print("Once you've verified everything is in place, you can remove the old files manually.")

if __name__ == "__main__":
    main()