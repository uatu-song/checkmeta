"""
META Fantasy League Simulator - Full Simulation Runner
Run a match day simulation using the real data and simulation engine
"""

import os
import sys
import time
from typing import Dict, List, Any

# Import configuration
from config import get_config

# Import main simulator
try:
    from meta_simulator import MetaLeagueSimulator
except ImportError:
    print("Error: Could not import MetaLeagueSimulator. Make sure meta_simulator.py is in the same directory.")
    sys.exit(1)

def main():
    """Main function to run a simulation with real data"""
    print("\n" + "=" * 70)
    print("META FANTASY LEAGUE SIMULATOR - FULL SIMULATION".center(70))
    print("=" * 70 + "\n")
    
    # Get configuration
    config = get_config()
    
    # Create simulator instance
    simulator = MetaLeagueSimulator()
    
    # Activate advanced features (if available)
    try:
        print("Activating advanced features...")
        simulator.activate_advanced_features()
    except Exception as e:
        print(f"Warning: Could not activate advanced features: {e}")
    
    # Ask which day to run
    day = get_day_selection(config)
    
    # Load lineup data
    match_date = get_match_date(day)
    lineup_data = load_lineup_data(config, match_date)
    
    if not lineup_data:
        print("Error: Failed to load lineup data.")
        return
    
    # Run the match day simulation
    run_match_day(simulator, day, lineup_data)

def get_day_selection(config):
    """Get day selection from user"""
    current_day = config.date.get("current_day", 1)
    
    print(f"Current match day in config: Day {current_day}")
    
    try:
        selection = input("Enter day number to run (or press Enter for current day): ")
        if selection.strip():
            day = int(selection)
            if day < 1 or day > 20:
                print("Invalid day number. Using current day.")
                return current_day
            return day
        return current_day
    except ValueError:
        print("Invalid input. Using current day.")
        return current_day

def get_match_date(day_number):
    """Calculate match date based on match day number"""
    # Reference date: April 7, 2025 (Monday) - Day 1
    import datetime
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

def load_lineup_data(config, match_date):
    """Load lineup data from Excel file"""
    from utils.loaders import load_lineups_from_excel
    
    lineup_file = config.paths.get("default_lineup_file", "data/lineups/All Lineups 1.xlsx")
    
    # Convert match_date to expected sheet format
    import datetime
    date_obj = datetime.datetime.strptime(match_date, "%Y-%m-%d")
    day_sheet = date_obj.strftime("%-m/%-d/%y")  # Format: M/D/YY (no leading zeros)
    
    print(f"Loading lineups from: {lineup_file}")
    print(f"Looking for sheet matching: {day_sheet}")
    
    # Try to load lineups
    try:
        teams = load_lineups_from_excel(lineup_file, day_sheet)
        
        # Process bench assignments
        for team_id, characters in teams.items():
            process_bench_assignments(characters)
            
        total_characters = sum(len(team) for team in teams.values())
        active_characters = sum(sum(1 for char in team if char.get("is_active", False)) for team in teams.values())
        print(f"Successfully loaded {total_characters} characters ({active_characters} active) across {len(teams)} teams")
        
        return teams
    except Exception as e:
        print(f"Error loading lineups: {e}")
        import traceback
        traceback.print_exc()
        return None
        
def process_bench_assignments(characters):
    """Process bench assignments for a team"""
    # First, mark all as inactive by default
    for char in characters:
        char["is_active"] = False
        
    # Get all roles present in the team
    roles = set(char.get("role", "") for char in characters)
    
    # Process by role priority (Field Leader first, then others)
    priority_order = ["FL", "VG", "EN", "SV", "RG", "GO", "PO"]
    assigned_count = 0
    
    # First pass: Assign by priority roles until we have 8 active
    for role in priority_order:
        if role in roles and assigned_count < 8:
            for char in characters:
                if char.get("role", "") == role and not char.get("is_active", False):
                    char["is_active"] = True
                    assigned_count += 1
                    
                    # Check if we've reached 8 active
                    if assigned_count >= 8:
                        break
    
    # Second pass: If we still don't have 8 active, assign anyone remaining
    if assigned_count < 8:
        for char in characters:
            if not char.get("is_active", False):
                char["is_active"] = True
                assigned_count += 1
                
                # Check if we've reached 8 active
                if assigned_count >= 8:
                    break
    
    # Log results
    active_chars = [char for char in characters if char.get("is_active", False)]
    bench_chars = [char for char in characters if not char.get("is_active", False)]
    
    print(f"  Team has {len(active_chars)}/8 active characters and {len(bench_chars)} on bench")

def run_match_day(simulator, day_number, teams):
    """Run a full match day simulation using real simulation engine"""
    start_time = time.time()
    config = get_config()
    
    # Get match date
    match_date = get_match_date(day_number)
    
    # Print header
    print(f"\n{'='*60}")
    print(f"MATCH DAY {day_number} - {match_date}".center(60))
    print(f"{'='*60}")
    
    # Get matchups for this day
    matchups = config.get_matchups_for_day(day_number)
    
    if not matchups:
        print(f"No matchups scheduled for day {day_number}")
        return
    
    # Display matchups
    print(f"\nScheduled Matchups:")
    for i, (team_a_id, team_b_id) in enumerate(matchups):
        team_a_name = config.get_team_name(team_a_id)
        team_b_name = config.get_team_name(team_b_id)
        print(f"  {i+1}. {team_a_name} vs {team_b_name}")
    print()
    
    # Process matchups
    results = []
    
    for i, (team_a_id, team_b_id) in enumerate(matchups):
        # Normalize team IDs
        team_a_id = normalize_team_id(team_a_id)
        team_b_id = normalize_team_id(team_b_id)
        
        # Get team names
        team_a_name = config.get_team_name(team_a_id)
        team_b_name = config.get_team_name(team_b_id)
        
        print(f"\nMatch {i+1}: {team_a_name} vs {team_b_name}")
        print("-" * 40)
        
        # Get team data
        team_a = teams.get(team_a_id, [])
        team_b = teams.get(team_b_id, [])
        
        if not team_a or not team_b:
            print(f"  Error: Missing team data for {team_a_id} or {team_b_id}")
            continue
        
        # Debug team information
        team_a_active = [char for char in team_a if char.get("is_active", False)]
        team_b_active = [char for char in team_b if char.get("is_active", False)]
        
        print(f"  {team_a_name}: {len(team_a_active)}/8 active characters")
        for idx, char in enumerate(team_a_active):
            print(f"    {idx+1}. {char['name']} ({char['role']})")
            
        print(f"  {team_b_name}: {len(team_b_active)}/8 active characters")
        for idx, char in enumerate(team_b_active):
            print(f"    {idx+1}. {char['name']} ({char['role']})")
        
        # Simulate match using real simulation engine
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

def display_match_result(result):
    """Display match result in a readable format"""
    print(f"  Result: {result.get('winning_team', 'Unknown')} wins")
    print(f"  Score: {result.get('team_a_wins', 0)} - {result.get('team_b_wins', 0)}")
    
    # Get convergence count
    convergence_count = result.get("convergence_count", 0)
    if not convergence_count and "convergence_logs" in result:
        convergence_count = len(result["convergence_logs"])
    
    # Get trait activations
    trait_activations = result.get("trait_activations", 0)
    if not trait_activations and "trait_logs" in result:
        trait_activations = len(result["trait_logs"])
    
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
        print(f"  Top performer: {top_performer['name']} - {top_performer.get('stat_type', 'damage')}: {top_performer.get('value', 0)}")
    
    # Print active/KO counts
    team_a_active = [c for c in result.get('character_results', []) if c.get('team', '') == 'A' and c.get('was_active', False)]
    team_a_ko = [c for c in team_a_active if c.get('is_ko', False)]
    
    team_b_active = [c for c in result.get('character_results', []) if c.get('team', '') == 'B' and c.get('was_active', False)]
    team_b_ko = [c for c in team_b_active if c.get('is_ko', False)]
    
    print(f"  {result.get('team_a_name', 'Team A')}: {len(team_a_active) - len(team_a_ko)}/{len(team_a_active)} active")
    print(f"  {result.get('team_b_name', 'Team B')}: {len(team_b_active) - len(team_b_ko)}/{len(team_b_active)} active")