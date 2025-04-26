#!/usr/bin/env python3
"""
META Fantasy League Simulator - Main Execution
Main script for running the META Fantasy League Simulator
"""

import os
import sys
import json
import datetime
from meta_simulator import MetaLeagueSimulator, get_day_matchups
from data.loaders import load_lineups_from_excel

def run_simulation(day_number=1, lineup_file="data/lineups/All_Lineups.xlsx", stockfish_path="/usr/local/bin/stockfish"):
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
        matchups = get_day_matchups(day_number)
        
        print(f"\nCreated {len(matchups)} matchups:")
        for team_a_id, team_b_id in matchups:
            if team_a_id in teams and team_b_id in teams:
                team_a_name = teams[team_a_id][0]['team_name']
                team_b_name = teams[team_b_id][0]['team_name']
                print(f"  {team_a_name} vs {team_b_name}")
            else:
                print(f"  {team_a_id} vs {team_b_id} (teams not found)")
        
        # Initialize the simulator
        simulator = MetaLeagueSimulator(stockfish_path)
        simulator.current_day = day_number
        
        # Run the matches
        results = []
        for team_a_id, team_b_id in matchups:
            # Skip if teams not found
            if team_a_id not in teams or team_b_id not in teams:
                print(f"Skipping matchup {team_a_id} vs {team_b_id} - teams not found")
                continue
                
            print(f"\nSimulating: {teams[team_a_id][0]['team_name']} vs {teams[team_b_id][0]['team_name']}")
            result = simulator.simulate_match(teams[team_a_id], teams[team_b_id], show_details=True)
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
    stockfish_path = "/usr/local/bin/stockfish"
    
    if len(sys.argv) > 1:
        try:
            day_number = int(sys.argv[1])
        except ValueError:
            print(f"Invalid day number: {sys.argv[1]}")
            print("Using default day number: 1")
    
    if len(sys.argv) > 2:
        lineup_file = sys.argv[2]
    
    if len(sys.argv) > 3:
        stockfish_path = sys.argv[3]
    
    print(f"Using lineup file: {lineup_file}")
    print(f"Simulating day: {day_number}")
    print(f"Using Stockfish path: {stockfish_path}")
    
    # Run the simulation
    run_simulation(day_number=day_number, lineup_file=lineup_file, stockfish_path=stockfish_path)