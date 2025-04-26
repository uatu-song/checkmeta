#!/usr/bin/env python3
"""
META Fantasy League Simulator - Main Execution
Main script for running the META Fantasy League Simulator
"""

import os
import sys
import json
import datetime
from MetaLeagueSimulator import MetaLeagueSimulator
from simulation.matchups import create_team_matchups

def run_with_team_matchups(day_number=1, lineup_file="All Lineups (1).xlsx"):
    """Run the simulation with team-based matchups"""
    print(f"=== META Fantasy League Simulation - Day {day_number} ===")
    
    # Initialize the simulator
    simulator = MetaLeagueSimulator()
    
    # Load lineups using our data manager
    date_string = f"4/7/25"  # Format for day sheet
    print(f"Loading lineups for {date_string}...")

    try:
        matchups = create_team_matchups(teams, day_number)
    
    # If no matchups were created, use fixed matchups
    if not matchups:
        print("Using fixed matchups as fallback...")
        from fixed_matchups import get_day_matchups
        matchups = get_day_matchups(day_number)
except Exception as e:
    print(f"Error creating matchups: {e}")
    print("Using fixed matchups as fallback...")
    from fixed_matchups import get_day_matchups
    matchups = get_day_matchups(day_number)

print(f"\nCreated {len(matchups)} matchups:")
for team_a_id, team_b_id in matchups:
    team_a_name = teams[team_a_id][0]['team_name'] if team_a_id in teams else f"Team {team_a_id}"
    team_b_name = teams[team_b_id][0]['team_name'] if team_b_id in teams else f"Team {team_b_id}"
    print(f"  {team_a_name} vs {team_b_name}")
    except FileNotFoundError:
        print(f"ERROR: Could not find lineup file at the expected location.")
        print(f"Please ensure the file '{lineup_file}' exists in the data/lineups directory.")
        print(f"Exiting simulation.")
        return None
    except Exception as e:
        print(f"ERROR: Could not load teams: {e}")
        print(f"Exiting simulation.")
        return None
    
    print(f"\nLoaded {len(teams)} teams:")
    for team_id, team_chars in teams.items():
        # Check if we're dealing with Character objects or dictionary data
        if hasattr(team_chars[0], 'team_name'):
            # Character objects
            team_name = team_chars[0].team_name
        else:
            # Dictionary data
            team_name = team_chars[0]['team_name']
            
        print(f"  {team_id}: {team_name} - {len(team_chars)} characters")
    
    # Create team-based matchups
    matchups = create_team_matchups(teams, day_number)
    
    if not matchups:
        print("No valid matchups could be created. Please check your team data.")
        return None
    
    print(f"\nCreated {len(matchups)} matchups:")
    for team_a_id, team_b_id in matchups:
        # Get team names
        if hasattr(teams[team_a_id][0], 'team_name'):
            team_a_name = teams[team_a_id][0].team_name
            team_b_name = teams[team_b_id][0].team_name
        else:
            team_a_name = teams[team_a_id][0]['team_name']
            team_b_name = teams[team_b_id][0]['team_name']
            
        print(f"  {team_a_name} vs {team_b_name}")
    
    # Run the matches
    results = []
    for team_a_id, team_b_id in matchups:
        # Get team names
        if hasattr(teams[team_a_id][0], 'team_name'):
            team_a_name = teams[team_a_id][0].team_name
            team_b_name = teams[team_b_id][0].team_name
        else:
            team_a_name = teams[team_a_id][0]['team_name']
            team_b_name = teams[team_b_id][0]['team_name']
            
        print(f"\nSimulating: {team_a_name} vs {team_b_name}")
        result = simulator.simulate_match(teams[team_a_id], teams[team_b_id], show_details=True)
        results.append(result)
    
    # Save results
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{results_dir}/day_{day_number}_results_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {filename}")
    
    return results

if __name__ == "__main__":
    # Get command line arguments
    day_number = 1
    lineup_file = "All Lineups (1).xlsx"  # Updated with correct parentheses
    
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
    run_with_team_matchups(day_number=day_number, lineup_file=lineup_file)