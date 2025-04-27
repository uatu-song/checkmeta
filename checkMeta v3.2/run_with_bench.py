"""
META Fantasy League Simulator - Bench-Aware Runner
Runs simulation with proper bench handling
"""

import os
import sys
import time
import json
import datetime
import pandas as pd

# Try to import meta_simulator
try:
    from meta_simulator import MetaLeagueSimulator
except ImportError:
    print("Error: Could not import MetaLeagueSimulator. Make sure meta_simulator.py is in the same directory.")
    sys.exit(1)

def main():
    """Main function to run a simulation with real data"""
    print("\n" + "=" * 70)
    print("META FANTASY LEAGUE SIMULATOR - BENCH-AWARE RUNNER".center(70))
    print("=" * 70 + "\n")
    
    # Get day number
    day = get_day_selection()
    
    # Get match date
    match_date = get_match_date(day)
    
    # Load teams from lineup file with proper bench handling
    teams = load_teams_with_bench("data/lineups/All Lineups 1.xlsx", match_date)
    
    if not teams:
        print("Error: Failed to load team data")
        return
    
    # Run matches
    run_matches(teams, day, match_date)

def get_day_selection():
    """Get day selection from user"""
    current_day = 1  # Default to day 1
    
    try:
        selection = input("Enter day number to run (or press Enter for day 1): ")
        if selection.strip():
            day = int(selection)
            if day < 1 or day > 20:
                print("Invalid day number. Using day 1.")
                return current_day
            return day
        return current_day
    except ValueError:
        print("Invalid input. Using day 1.")
        return current_day

def get_match_date(day_number):
    """Calculate match date based on match day number"""
    # Reference date: April 7, 2025 (Monday) - Day 1
    reference_date = datetime.datetime(2025, 4, 7)
    
    # Day 1 is April 7, 2025
    if day_number == 1:
        return reference_date.strftime("%Y-%m-%d")
    
    # Add business days for future dates
    current_date = reference_date
    days_added = 0
    
    while days_added < day_number - 1:
        current_date += datetime.timedelta(days=1)
        # Skip weekends (5=Saturday, 6=Sunday)
        if current_date.weekday() < 5:
            days_added += 1
    
    return current_date.strftime("%Y-%m-%d")

def load_teams_with_bench(lineup_file, match_date):
    """Load team lineups with proper bench handling"""
    # Convert match_date to expected sheet format
    date_obj = datetime.datetime.strptime(match_date, "%Y-%m-%d")
    day_sheet = date_obj.strftime("%-m/%-d/%y")  # Format: M/D/YY (no leading zeros)
    
    print(f"Loading lineups from: {lineup_file}")
    print(f"Looking for sheet matching: {day_sheet}")
    
    try:
        # First check if file exists
        if not os.path.exists(lineup_file):
            print(f"Error: File '{lineup_file}' does not exist")
            return {}
        
        # Get all sheet names
        xls = pd.ExcelFile(lineup_file)
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
        df = pd.read_excel(lineup_file, sheet_name=selected_sheet)
        
        # Print column names for debugging
        print(f"Columns in sheet: {df.columns.tolist()}")
        
        # Check for deployment/bench column
        deploy_column = None
        bench_column = None
        
        possible_deploy_columns = ['Deploy', 'Deployment', 'deployRoster', 'Active', 'isActive']
        possible_bench_columns = ['Bench', 'isBench', 'Reserve', 'isReserve']
        
        for col in possible_deploy_columns:
            if col in df.columns:
                deploy_column = col
                print(f"Found deployment column: {col}")
                break
                
        for col in possible_bench_columns:
            if col in df.columns:
                bench_column = col
                print(f"Found bench column: {col}")
                break
        
        if not deploy_column and not bench_column:
            print("Warning: No deploy or bench column found, will use role-based selection")
        
        # Map column names for other data
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
                print(f"Warning: Could not find any column to map to '{required_col}'")
        
        # Organize by teams
        teams = {}
        
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
            
            # Normalize role
            role = map_position_to_role(role)
            
            # Get division
            division = get_division_from_role(role)
            
            # Determine if character is active or bench
            is_active = True  # Default to active
            
            # Check bench/deploy columns
            if deploy_column is not None:
                deploy_value = row.get(deploy_column)
                if not pd.isna(deploy_value):
                    # Treat as active if any non-empty value
                    is_active = bool(deploy_value)
                    
            if bench_column is not None:
                bench_value = row.get(bench_column)
                if not pd.isna(bench_value):
                    # If bench column has any non-empty value, mark as bench
                    if bench_value:
                        is_active = False
            
            # Get team name
            team_name = f"Team {team_id[1:]}"
            if 'Team' in df.columns and not pd.isna(row.get('Team')):
                team_name = f"Team {row.get('Team')}"
            
            # Create character dictionary
            character = {
                'id': f"{team_id}_{len(teams[team_id])}",
                'name': char_name,
                'team_id': team_id,
                'team_name': team_name,
                'role': role,
                'division': division,
                'HP': 100,
                'stamina': 100,
                'life': 100,
                'morale': 50,
                'traits': [],
                'rStats': {},
                'xp_total': 0,
                'is_active': is_active,
                'is_ko': False
            }
            
            # Add stats - use default values
            for stat in ['STR', 'SPD', 'FS', 'LDR', 'DUR', 'RES', 'WIL', 'OP', 'AM', 'SBY']:
                character[f"a{stat}"] = 5
            
            # Try to get Rank as a value for stats
            if 'Rank' in df.columns and not pd.isna(row.get('Rank')):
                try:
                    rank = int(row.get('Rank'))
                    # Scale rank to stats (assuming rank is 1-10)
                    stat_value = min(10, max(1, rank))
                    # Apply to key stats
                    character["aSTR"] = stat_value
                    character["aSPD"] = stat_value
                    character["aOP"] = stat_value
                except:
                    pass
            
            # Add traits based on Primary Type
            if 'Primary Type' in df.columns and not pd.isna(row.get('Primary Type')):
                primary_type = str(row.get('Primary Type')).lower()
                
                # Map primary types to traits
                type_to_trait = {
                    'tech': ['genius', 'armor'],
                    'energy': ['genius', 'tactical'],
                    'cosmic': ['shield', 'healing'],
                    'mutant': ['agile', 'stretchy'],
                    'bio': ['agile', 'spider-sense'],
                    'mystic': ['tactical', 'healing'],
                    'skill': ['tactical', 'spider-sense']
                }
                
                # Assign traits based on primary type
                for type_key, traits in type_to_trait.items():
                    if type_key in primary_type:
                        character['traits'] = traits
                        break
                
                # Default traits if no match
                if not character['traits']:
                    character['traits'] = ['genius', 'tactical']
            else:
                # Default traits if no primary type
                character['traits'] = ['genius', 'tactical']
            
            teams[team_id].append(character)
        
        # Ensure exactly 8 active characters per team
        for team_id, team_chars in teams.items():
            ensure_eight_active_characters(team_chars)
        
        # Log team info
        print(f"Successfully loaded {sum(len(team) for team in teams.values())} characters across {len(teams)} teams")
        for team_id, team_chars in teams.items():
            active_count = sum(1 for char in team_chars if char.get('is_active', False))
            print(f"  Team {team_id}: {active_count}/8 active, {len(team_chars) - active_count} bench")
        
        return teams
        
    except Exception as e:
        print(f"Error loading lineups from Excel: {e}")
        import traceback
        traceback.print_exc()
        return {}

def ensure_eight_active_characters(characters):
    """Ensure exactly 8 characters are marked as active"""
    if not characters:
        return
        
    # Count how many are marked as active
    active_count = sum(1 for char in characters if char.get('is_active', False))
    
    # If already exactly 8, we're done
    if active_count == 8:
        return
        
    # If too many active, deactivate extras
    if active_count > 8:
        # Sort by role importance (least important first)
        role_priority = {"FL": 10, "VG": 9, "EN": 8, "SV": 7, "RG": 6, "GO": 5, "PO": 4}
        
        # Sort characters by priority (lowest first)
        sorted_chars = sorted(
            [c for c in characters if c.get('is_active', False)],
            key=lambda x: role_priority.get(x.get('role', ''), 0)
        )
        
        # Deactivate the lowest priority characters
        for char in sorted_chars[:active_count - 8]:
            char['is_active'] = False
            print(f"  Deactivating {char['name']} ({char['role']}) to reach 8 active limit")
    
    # If too few active, activate some from bench
    elif active_count < 8:
        # Get inactive characters
        inactive_chars = [c for c in characters if not c.get('is_active', False)]
        
        # Sort by role importance (most important first)
        role_priority = {"FL": 10, "VG": 9, "EN": 8, "SV": 7, "RG": 6, "GO": 5, "PO": 4}
        
        # Sort characters by priority (highest first)
        sorted_chars = sorted(
            inactive_chars,
            key=lambda x: role_priority.get(x.get('role', ''), 0),
            reverse=True
        )
        
        # Activate the highest priority characters
        for char in sorted_chars[:8 - active_count]:
            char['is_active'] = True
            print(f"  Activating {char['name']} ({char['role']}) to reach 8 active minimum")

def run_matches(teams, day_number, match_date):
    """Run matches for all scheduled teams"""
    start_time = time.time()
    
    # Define matchups for this day - hardcoded for example
    day_matchups = {
        1: [
            ("t001", "t002"),  # Xavier's School vs Brotherhood
            ("t004", "t003"),  # Fantastic Four vs Avengers
            ("t005", "t006"),  # Hellfire Club vs Asgardians
            ("t008", "t007"),  # Mutant Underground vs Shield Ops
            ("t009", "t010")   # X-Force vs The Illuminati
        ],
        2: [
            ("t001", "t003"),  # Xavier's School vs Avengers
            ("t004", "t006"),  # Fantastic Four vs Asgardians
            ("t005", "t007"),  # Hellfire Club vs Shield Ops
            ("t008", "t010"),  # Mutant Underground vs The Illuminati
            ("t009", "t002")   # X-Force vs Brotherhood
        ],
        3: [
            ("t001", "t006"),  # Xavier's School vs Asgardians
            ("t004", "t007"),  # Fantastic Four vs Shield Ops
            ("t005", "t010"),  # Hellfire Club vs The Illuminati
            ("t008", "t002"),  # Mutant Underground vs Brotherhood
            ("t009", "t003")   # X-Force vs Avengers
        ],
        4: [
            ("t001", "t007"),  # Xavier's School vs Shield Ops
            ("t004", "t010"),  # Fantastic Four vs The Illuminati
            ("t005", "t002"),  # Hellfire Club vs Brotherhood
            ("t008", "t003"),  # Mutant Underground vs Avengers
            ("t009", "t006")   # X-Force vs Asgardians
        ],
        5: [
            ("t001", "t010"),  # Xavier's School vs The Illuminati
            ("t004", "t002"),  # Fantastic Four vs Brotherhood
            ("t005", "t003"),  # Hellfire Club vs Avengers
            ("t008", "t006"),  # Mutant Underground vs Asgardians
            ("t009", "t007")   # X-Force vs Shield Ops
        ]
    }
    
    # Get matchups for this day
    matchups = day_matchups.get(day_number, [])
    
    if not matchups:
        print(f"No matchups scheduled for day {day_number}")
        return
    
    # Team name mapping
    team_names = {
        "t001": "Xavier's School", 
        "t002": "Brotherhood", 
        "t003": "Avengers", 
        "t004": "Fantastic Four", 
        "t005": "Hellfire Club", 
        "t006": "Asgardians", 
        "t007": "Shield Ops", 
        "t008": "Mutant Underground", 
        "t009": "X-Force", 
        "t010": "The Illuminati"
    }
    
    # Display matchups
    print(f"\nScheduled Matchups:")
    for i, (team_a_id, team_b_id) in enumerate(matchups):
        team_a_name = team_names.get(team_a_id, f"Team {team_a_id[1:]}")
        team_b_name = team_names.get(team_b_id, f"Team {team_b_id[1:]}")
        print(f"  {i+1}. {team_a_name} vs {team_b_name}")
    print()
    
    # Create simulator
    try:
        simulator = MetaLeagueSimulator()
    except Exception as e:
        print(f"Error creating simulator: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Process matchups
    results = []
    
    for i, (team_a_id, team_b_id) in enumerate(matchups):
        # Normalize team IDs
        team_a_id = normalize_team_id(team_a_id)
        team_b_id = normalize_team_id(team_b_id)
        
        # Get team names
        team_a_name = team_names.get(team_a_id, f"Team {team_a_id[1:]}")
        team_b_name = team_names.get(team_b_id, f"Team {team_b_id[1:]}")
        
        print(f"\nMatch {i+1}: {team_a_name} vs {team_b_name}")
        print("-" * 40)
        
        # Get team data
        team_a = teams.get(team_a_id, [])
        team_b = teams.get(team_b_id, [])
        
        if not team_a or not team_b:
            print(f"  Error: Missing team data for {team_a_id} or {team_b_id}")
            continue
        
        # Filter active characters
        team_a_active = [char for char in team_a if char.get("is_active", False)]
        team_b_active = [char for char in team_b if char.get("is_active", False)]
        
        print(f"  {team_a_name}: {len(team_a_active)}/8 active characters")
        for idx, char in enumerate(team_a_active):
            print(f"    {idx+1}. {char['name']} ({char['role']})")
            
        print(f"  {team_b_name}: {len(team_b_active)}/8 active characters")
        for idx, char in enumerate(team_b_active):
            print(f"    {idx+1}. {char['name']} ({char['role']})")
        
        # Simulate match
        try:
            # Only pass active characters to the simulator
            match_result = simulator.simulate_match(team_a_active, team_b_active, show_details=True)
            
            # Add team names to result for reporting
            match_result["team_a_name"] = team_a_name
            match_result["team_b_name"] = team_b_name
            match_result["team_a_id"] = team_a_id
            match_result["team_b_id"] = team_b_id
            
            results.append(match_result)
            
            # Display result
            display_match_result(match_result)
            
        except Exception as e:
            print(f"  Error simulating match: {e}")
            import traceback
            traceback.print_exc()
    
    # Save results to file
    save_match_results(results, day_number, match_date)
    
    # Print summary
    elapsed_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"MATCH DAY {day_number} SUMMARY".center(60))
    print(f"{'='*60}")
    print(f"Matches completed: {len(results)}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print(f"Results saved to results directory")
    print(f"{'='*60}\n")

def display_match_result(result):
    """Display match result in a readable format"""
    # Extract winning team
    winner = result.get("winner", "Unknown")
    if winner == "Team A":
        winning_team = result.get("team_a_name", "Team A")
    elif winner == "Team B":
        winning_team = result.get("team_b_name", "Team B")
    else:
        winning_team = "Draw"
    
    print(f"  Result: {winning_team} wins")
    print(f"  Score: {result.get('team_a_wins', 0)} - {result.get('team_b_wins', 0)}")
    
    # Get convergence count
    convergence_count = result.get("convergence_count", 0)
    if not convergence_count and "convergence_logs" in result:
        convergence_count = len(result.get("convergence_logs", []))
    
    # Get trait activations
    trait_activations = result.get("trait_activations", 0)
    if not trait_activations and "trait_logs" in result:
        trait_activations = len(result.get("trait_logs", []))
    
    print(f"  Key statistics:")
    print(f"    - Convergences: {convergence_count}")
    print(f"    - Trait activations: {trait_activations}")
    
    # Find top performer if available
    top_performer = None
    if "top_performer" in result and result["top_performer"]:
        top_performer = result["top_performer"]
    else:
        # Try to find from character results
        max_damage = 0
        for char in result.get("character_results", []):
            damage = 0
            if "rStats" in char:
                damage += char["rStats"].get("rDD", 0)
                damage += char["rStats"].get("rDDo", 0)
                damage += char["rStats"].get("rDDi", 0)
                
            if damage > max_damage:
                max_damage = damage
                top_performer = {
                    "name": char["character_name"],
                    "value": damage,
                    "stat_type": "damage"
                }
    
    if top_performer:
        print(f"  Top performer: {top_performer.get('name', 'Unknown')} - {top_performer.get('stat_type', 'damage')}: {top_performer.get('value', 0)}")
    
    # Print active/KO counts
    team_a_active = [c for c in result.get('character_results', []) if c.get('team', '') == 'A' and c.get('was_active', False)]
    team_a_ko = [c for c in team_a_active if c.get('is_ko', False)]
    
    team_b_active = [c for c in result.get('character_results', []) if c.get('team', '') == 'B' and c.get('was_active', False)]
    team_b_ko = [c for c in team_b_active if c.get('is_ko', False)]
    
    print(f"  {result.get('team_a_name', 'Team A')}: {len(team_a_active) - len(team_a_ko)}/{len(team_a_active)} active")
    print(f"  {result.get('team_b_name', 'Team B')}: {len(team_b_active) - len(team_b_ko)}/{len(team_b_active)} active")

def save_match_results(results, day_number, match_date):
    """Save match results to files"""
    # Create directories if needed
    ensure_directory_exists("results")
    ensure_directory_exists("results/reports")
    
    # Get timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create summary file
    summary_path = os.path.join("results/reports", f"matchday_{day_number}_{timestamp}.json")
    
    # Create summary data
    summary_data = {
        "day": day_number,
        "date": match_date,
        "timestamp": timestamp,
        "matches": len(results),
        "results": results
    }
    
    # Save to file
    try:
        with open(summary_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        print(f"Results saved to {summary_path}")
    except Exception as e:
        print(f"Error saving results: {e}")
        
        # Try emergency save
        try:
            emergency_path = os.path.join("results", f"emergency_matchday_{day_number}_{timestamp}.json")
            with open(emergency_path, 'w') as f:
                json.dump(summary_data, f, indent=2)
            print(f"Emergency backup saved to {emergency_path}")
        except Exception as e2:
            print(f"Emergency save also failed: {e2}")

def ensure_directory_exists(dirpath):
    """Ensure directory exists, create if needed"""
    try:
        os.makedirs(dirpath, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory: {e}")
        return False

def normalize_team_id(team_id):
    """Normalize team ID for consistent comparison"""
    # Ensure string type
    team_id = str(team_id)
    
    # Remove non-alphanumeric characters
    team_id = ''.join(c for c in team_id if c.isalnum())
    
    # Ensure it starts with 't' (case insensitive)
    if not team_id.lower().startswith('t'):
        team_id = 't' + team_id
    
    # Convert to lowercase for consistent comparison
    return team_id.lower()

def map_position_to_role(position):
    """Map position name to standardized role code"""
    position = str(position).upper().strip()
    
    # Standard position mappings
    position_map = {
        "FIELD LEADER": "FL",
        "VANGUARD": "VG",
        "ENFORCER": "EN",
        "RANGER": "RG",
        "GHOST OPERATIVE": "GO",
        "PSI OPERATIVE": "PO",
        "SOVEREIGN": "SV"
    }
    
    # Check for exact matches
    if position in position_map:
        return position_map[position]
    
    # Check for partial matches
    for key, value in position_map.items():
        if key in position:
            return value
    
    # Check if already a valid role code
    valid_roles = ["FL", "VG", "EN", "RG", "GO", "PO", "SV"]
    if position in valid_roles:
        return position
    
    # Default
    return "FL"

def get_division_from_role(role):
    """Map role to division"""
    operations_roles = ["FL", "VG", "EN"]
    intelligence_roles = ["RG", "GO", "PO", "SV"]
    
    if role in operations_roles:
        return "o"
    elif role in intelligence_roles:
        return "i"
    else:
        return "o"  # Default to operations

# Run the script when executed
if __name__ == "__main__":
    main()