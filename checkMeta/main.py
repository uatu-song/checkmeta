#!/usr/bin/env python3
"""
META Fantasy League Simulator - Main Execution
Main script for running the META Fantasy League Simulator
"""

import os
import sys
import json
import datetime
import random
import math
import pandas as pd

def load_lineups_from_excel(file_path, day_sheet="4/7/25"):
    """Load character lineups from an Excel file"""
    try:
        print(f"Attempting to load from: {file_path}")
        
        # First check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist")
            raise FileNotFoundError(f"File '{file_path}' does not exist")
        
        # Get all sheet names to debug
        xls = pd.ExcelFile(file_path)
        available_sheets = xls.sheet_names
        print(f"Available sheets in Excel file: {available_sheets}")
        
        # Try to find a matching sheet
        day_sheet_clean = day_sheet.replace('/', '')
        matching_sheets = [s for s in available_sheets if day_sheet_clean in s.replace('/', '').replace('-', '')]
        selected_sheet = None
        
        if day_sheet in available_sheets:
            selected_sheet = day_sheet
            print(f"Found exact match for sheet: {day_sheet}")
        elif matching_sheets:
            selected_sheet = matching_sheets[0]
            print(f"Found partial match for sheet: {selected_sheet}")
        else:
            # Fall back to first sheet
            selected_sheet = available_sheets[0]
            print(f"No matching sheet found. Using first sheet: {selected_sheet}")
        
        # Load the selected sheet
        print(f"Loading data from sheet: {selected_sheet}")
        df = pd.read_excel(file_path, sheet_name=selected_sheet)
        
        # Print column names for debugging
        print(f"Columns in sheet: {df.columns.tolist()}")
        
        # Map column names based on what's available
        column_mapping = {
            'team_id': ['Team', 'team_id', 'team', 'team id', 'teamid', 'tid'],
            'name': ['Nexus Being', 'name', 'character', 'character name', 'char_name', 'character_name'],
            'role': ['Position', 'PositionFull', 'role', 'position', 'char_role', 'character_role']
        }
        
        # Create new columns with required names based on available columns
        for required_col, possible_cols in column_mapping.items():
            found = False
            for col in possible_cols:
                if col in df.columns:
                    print(f"Mapping '{col}' to '{required_col}'")
                    df[required_col] = df[col]
                    found = True
                    break
            
            if not found:
                print(f"Error: Could not find any column to map to '{required_col}'")
                raise ValueError(f"Could not find any column to map to '{required_col}'")
        
        # Organize by teams
        teams = {}
        valid_rows = 0
        
        for _, row in df.iterrows():
            # Skip completely empty rows
            if pd.isna(row.get('team_id', None)) and pd.isna(row.get('name', None)):
                continue
                
            team_id = str(row.get('team_id', '')).strip()
            
            # Skip rows with empty team_id
            if not team_id or pd.isna(team_id):
                continue
                
            # Clean team_id format if needed (some Excel exports add '.0')
            if team_id.endswith('.0'):
                team_id = team_id[:-2]
            
            # Ensure team_id starts with 't' 
            if not team_id.startswith('t'):
                team_id = 't' + team_id
            
            if team_id not in teams:
                teams[team_id] = []
            
            # Get character name
            char_name = str(row.get('name', f"Character {len(teams[team_id])}")).strip()
            if not char_name or pd.isna(char_name):
                char_name = f"Character {len(teams[team_id])}"
            
            # Get role
            role = str(row.get('role', 'FL')).strip()
            if not role or pd.isna(role):
                role = 'FL'
            
            # Get team name (from Team column or construct from team_id)
            team_name = None
            if 'Team' in df.columns and not pd.isna(row.get('Team')):
                team_name = f"Team {row.get('Team')}"
            else:
                team_name = f"Team {team_id[1:]}"  # Remove 't' prefix for name
            
            # Create character dictionary
            character = {
                'id': f"{team_id}_{len(teams[team_id])}",
                'name': char_name,
                'team_id': team_id,
                'team_name': team_name,
                'role': role,
                'division': 'o',  # Default to operations
                'HP': 100,
                'stamina': 100,
                'life': 100,
                'morale': 50,
                'traits': [],
                'rStats': {},
                'xp_total': 0
            }
            
            # Add stats - use default values
            for stat in ['STR', 'SPD', 'FS', 'LDR', 'DUR', 'RES', 'WIL', 'OP', 'AM', 'SBY']:
                character[f"a{stat}"] = 5
            
            teams[team_id].append(character)
            valid_rows += 1
        
        print(f"Successfully loaded {valid_rows} characters across {len(teams)} teams")
        
        # If no valid teams loaded, return error
        if not teams:
            raise ValueError("No valid teams found in the Excel file")
        
        return teams
    except Exception as e:
        print(f"Error loading lineups from Excel: {e}")
        import traceback
        traceback.print_exc()
        raise e  # Re-raise to ensure the error is propagated

def create_team_matchups(teams, day_number):
    """Create matchups for the META League based on team numbers"""
    # Get all team IDs and sort them numerically
    all_team_ids = list(teams.keys())
    
    # Sort by team number
    all_team_ids.sort(key=lambda x: int(x[1:]) if x[1:].isdigit() else 999)
    
    print(f"All team IDs: {all_team_ids}")
    
    # Calculate number of active teams
    total_teams = len(all_team_ids)
    
    # Check if we have enough teams
    if total_teams <= 1:
        print("Not enough teams for matchups")
        return []
    
    # For odd number of teams, add a dummy team (represents a bye)
    if total_teams % 2 == 1:
        all_team_ids.append("dummy")
        total_teams += 1
    
    # Calculate rotation for current day
    rotation = (day_number - 1) % (total_teams - 1)
    
    # Create the rotated schedule
    # First team stays fixed, others rotate
    remaining_teams = all_team_ids[1:]
    
    if rotation > 0:
        remaining_teams = remaining_teams[-(rotation):] + remaining_teams[:-(rotation)]
    
    # Create schedule
    schedule = []
    fixed_team = all_team_ids[0]
    
    # Combine fixed team with first rotated team
    if remaining_teams[0] != "dummy" and fixed_team != "dummy":
        schedule.append((fixed_team, remaining_teams[0]))
    
    # Pair up the rest of the teams
    for i in range(1, len(remaining_teams) // 2):
        team_a = remaining_teams[i]
        team_b = remaining_teams[total_teams - 1 - i]
        
        if team_a != "dummy" and team_b != "dummy":
            schedule.append((team_a, team_b))
    
    print(f"Generated {len(schedule)} matchups for day {day_number}")
    
    # Ensure we have exactly 5 matches if possible
    while len(schedule) > 5:
        schedule.pop()  # Remove excess matches
    
    return schedule

def get_day_matchups(day_number):
    """Return fixed matchups for a specific day"""
    # Standard matchups for a 10-team league
    all_matchups = {
        # Day 1: Standard pairing
        1: [
            ("tT001", "t002"),
            ("tT004", "t003"),
            ("tT005", "t006"),
            ("tT008", "t007"),
            ("tT009", "t010")
        ],
        # Day 2: Rotate for different matchups
        2: [
            ("tT001", "t003"),
            ("tT004", "t006"),
            ("tT005", "t007"),
            ("tT008", "t010"),
            ("tT009", "t002")
        ],
        # Day 3: Another rotation
        3: [
            ("tT001", "t006"),
            ("tT004", "t007"),
            ("tT005", "t010"),
            ("tT008", "t002"),
            ("tT009", "t003")
        ],
        # Day 4
        4: [
            ("tT001", "t007"),
            ("tT004", "t010"),
            ("tT005", "t002"),
            ("tT008", "t003"),
            ("tT009", "t006")
        ],
        # Day 5
        5: [
            ("tT001", "t010"),
            ("tT004", "t002"),
            ("tT005", "t003"),
            ("tT008", "t006"),
            ("tT009", "t007")
        ]
    }
    
    if day_number not in all_matchups:
        print(f"Warning: No predefined matchups for day {day_number}, using day 1 matchups")
        return all_matchups[1]
    
    return all_matchups[day_number]

def simulate_match(team_a, team_b):
    """Simple match simulation function"""
    # This is a greatly simplified version that just returns random results
    # In a real implementation, this would use your chess-based simulation logic
    
    print(f"Simulating match between {team_a[0]['team_name']} and {team_b[0]['team_name']}")
    
    # Determine winner randomly for this simple example
    team_a_wins = random.randint(0, 5)
    team_b_wins = random.randint(0, 5)
    
    if team_a_wins > team_b_wins:
        winner = "Team A"
        winning_team = team_a[0]['team_name']
    elif team_b_wins > team_a_wins:
        winner = "Team B"
        winning_team = team_b[0]['team_name']
    else:
        winner = "Draw"
        winning_team = "None"
    
    print(f"Result: {team_a[0]['team_name']} {team_a_wins} - {team_b_wins} {team_b[0]['team_name']}")
    print(f"Winner: {winning_team}")
    
    # Create result dictionary
    result = {
        "team_a_name": team_a[0]['team_name'],
        "team_b_name": team_b[0]['team_name'],
        "team_a_wins": team_a_wins,
        "team_b_wins": team_b_wins,
        "winner": winner,
        "winning_team": winning_team,
        "character_results": []
    }
    
    # Add character results
    for character in team_a:
        result["character_results"].append({
            "team": "A",
            "character_id": character["id"],
            "character_name": character["name"],
            "result": random.choice(["win", "loss", "draw"]),
            "final_hp": random.randint(0, 100),
            "final_stamina": random.randint(0, 100),
            "final_life": 100,
            "is_ko": random.random() < 0.2,  # 20% chance of KO
            "is_dead": False,
            "was_active": True
        })
    
    for character in team_b:
        result["character_results"].append({
            "team": "B",
            "character_id": character["id"],
            "character_name": character["name"],
            "result": random.choice(["win", "loss", "draw"]),
            "final_hp": random.randint(0, 100),
            "final_stamina": random.randint(0, 100),
            "final_life": 100,
            "is_ko": random.random() < 0.2,  # 20% chance of KO
            "is_dead": False,
            "was_active": True
        })
    
    return result

def run_simulation(day_number=1, lineup_file="data/lineups/All_Lineups.xlsx"):
    """Run the simulation with team-based matchups"""
    print(f"=== META Fantasy League Simulation - Day {day_number} ===")
    
    try:
        # Get absolute path for lineup file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        lineup_path = os.path.join(current_dir, lineup_file)
        print(f"Looking for lineup file at: {lineup_path}")
        
        # Load lineups from Excel
        date_string = "4/7/25"  # Format for day sheet
        print(f"Loading lineups for {date_string}...")
        teams = load_lineups_from_excel(lineup_path, date_string)
        
        print(f"\nLoaded {len(teams)} teams:")
        for team_id, team in teams.items():
            print(f"  {team_id}: {team[0]['team_name']} - {len(team)} characters")
        
        # Create team-based matchups
        try:
            matchups = create_team_matchups(teams, day_number)
        except Exception as e:
            print(f"Error creating matchups: {e}")
            print("Using fixed matchups as fallback...")
            matchups = get_day_matchups(day_number)
        
        # If no matchups were created, use fixed matchups
        if not matchups:
            print("Using fixed matchups as fallback...")
            matchups = get_day_matchups(day_number)
        
        print(f"\nCreated {len(matchups)} matchups:")
        for team_a_id, team_b_id in matchups:
            if team_a_id in teams and team_b_id in teams:
                team_a_name = teams[team_a_id][0]['team_name']
                team_b_name = teams[team_b_id][0]['team_name']
                print(f"  {team_a_name} vs {team_b_name}")
            else:
                print(f"  {team_a_id} vs {team_b_id} (teams not found)")
        
        # Run the matches
        results = []
        for team_a_id, team_b_id in matchups:
            # Skip if teams not found
            if team_a_id not in teams or team_b_id not in teams:
                print(f"Skipping matchup {team_a_id} vs {team_b_id} - teams not found")
                continue
                
            result = simulate_match(teams[team_a_id], teams[team_b_id])
            results.append(result)
        
        # Save results
        results_dir = os.path.join(current_dir, "results")
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{results_dir}/day_{day_number}_results_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {filename}")
        
        return results
        
    except FileNotFoundError as e:
        print(f"ERROR: File not found: {e}")
        print(f"Please ensure the file '{lineup_file}' exists in the data/lineups directory.")
        print(f"Current directory: {os.path.abspath(os.curdir)}")
        print(f"Exiting simulation.")
        return None
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        print(f"Exiting simulation.")
        return None

if __name__ == "__main__":
    # Get command line arguments
    day_number = 1
    lineup_file = "data/lineups/All_Lineups.xlsx"
    
    if len(sys.argv) > 1:
        try:
            day_number = int(sys.argv[1])
        except ValueError:
            print(f"Invalid day number: {sys.argv[1]}")
            print("Using default day number: 1")
    
    if len(sys.argv) > 2:
        lineup_file = sys.argv[2]
    
    print(f"Using lineup file: {lineup_file}")
    print(f"Simulating day: {day_number}")
    
    # Run the simulation
    run_simulation(day_number=day_number, lineup_file=lineup_file)