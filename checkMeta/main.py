#!/usr/bin/env python3
"""
Main entry point for META Fantasy League Simulator
"""

import os
import sys
import argparse
from meta_simulator.simulation.matchups import create_team_matchups
from meta_simulator.data.loaders import load_lineups_from_excel, create_sample_teams
from meta_simulator.systems.simulator import MetaLeagueSimulator

def main():
    """Main function for running the META Fantasy League Simulator"""
    parser = argparse.ArgumentParser(description='META Fantasy League Simulator')
    parser.add_argument('--lineup-file', default='lineups.xlsx', help='Path to lineup Excel file')
    parser.add_argument('--day', type=int, default=1, help='Simulation day number')
    parser.add_argument('--details', action='store_true', help='Show detailed simulation output')
    args = parser.parse_args()
    
    print(f"=== META Fantasy League Simulation - Day {args.day} ===")
    
    # Initialize the simulator
    simulator = MetaLeagueSimulator()
    
    # Load lineups from Excel
    date_string = f"4/7/{25 + args.day - 1}"  # Format for the day
    print(f"Loading lineups from {args.lineup_file} for {date_string}...")

    try:
        teams = load_lineups_from_excel(args.lineup_file, date_string)
    except Exception as e:
        print(f"ERROR: Could not load teams from {args.lineup_file}: {e}")
        print("Creating sample teams as fallback...")
        teams = create_sample_teams()
    
    print(f"\nLoaded {len(teams)} teams:")
    for team_id, team in teams.items():
        print(f"  {team_id}: {team[0].team_name} - {len(team)} characters")
    
    # Create team-based matchups
    matchups = create_team_matchups(teams, args.day)
    
    print(f"\nCreated {len(matchups)} matchups:")
    for team_a_id, team_b_id in matchups:
        print(f"  {teams[team_a_id][0].team_name} vs {teams[team_b_id][0].team_name}")
    
    # Run the matches
    results = []
    for team_a_id, team_b_id in matchups:
        print(f"\nSimulating: {teams[team_a_id][0].team_name} vs {teams[team_b_id][0].team_name}")
        result = simulator.simulate_match(teams[team_a_id], teams[team_b_id], show_details=args.details)
        results.append(result)
    
    # Save results
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    simulator.export_results(results, f"{results_dir}/day_{args.day}_results.json")
    
    print(f"\nResults saved to {results_dir}/day_{args.day}_results.json")
    
    return results

if __name__ == "__main__":
    main()

###############################
