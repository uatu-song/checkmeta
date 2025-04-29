#!/usr/bin/env python3
"""
META Simulator v4.2.1 Runner
Script to run the META Fantasy League Simulator with all components properly integrated
"""

import os
import sys
import argparse
import logging
import json
import datetime
from typing import Dict, Any, Optional
from config_utils import load_config

# Import the simulator
# Import removed to fix circular dependency

# Import the integration patch
from final_integration import apply_final_integration_patches

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or use defaults
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Configuration dictionary
    """
    if config_path and os.path.exists(config_path):
        print(f"Loading configuration from {config_path}")
        with open(config_path, 'r') as f:
            return json.load(f)
    
    # Return default config path
    default_config = os.path.join("config", "default_config.json")
    if os.path.exists(default_config):
        print(f"Loading default configuration from {default_config}")
        with open(default_config, 'r') as f:
            return json.load(f)
    
    print("No configuration file found, using built-in defaults")
    return {}

def setup_logging(config: Dict[str, Any]) -> None:
    """
    Set up logging configuration
    
    Args:
        config: Configuration dictionary
    """
    log_dir = config.get("paths", {}).get("logs_dir", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_level = config.get("logging", {}).get("level", "INFO")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"meta_sim_runner_{timestamp}.log")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    print(f"Logging to {log_file}")

def run_day_simulation(simulator, day_number: int, quiet: bool = False) -> None:
    """
    Run simulation for a specific day
    
    Args:
        simulator: Simulator instance
        day_number: Day number to simulate
        quiet: Whether to suppress detailed output
    """
    print(f"\nSimulating day {day_number}...")
    try:
        result = simulator.simulate_day(day_number, not quiet)
        print(f"Day {day_number} simulation completed successfully")
        
        # Print summary
        if not quiet:
            matches = result.get("matches", [])
            print(f"\nResults summary for day {day_number}:")
            print(f"Matches played: {len(matches)}")
            
            for i, match in enumerate(matches, 1):
                team_a = match.get("team_a_name", "Team A")
                team_b = match.get("team_b_name", "Team B")
                winner = match.get("winning_team", "Unknown")
                print(f"  Match {i}: {team_a} vs {team_b} - Winner: {winner}")
    
    except Exception as e:
        print(f"Error simulating day {day_number}: {e}")
        sys.exit(1)

def run_range_simulation(simulator, start_day: int, end_day: int, quiet: bool = False) -> None:
    """
    Run simulation for a range of days
    
    Args:
        simulator: Simulator instance
        start_day: Starting day number
        end_day: Ending day number
        quiet: Whether to suppress detailed output
    """
    print(f"\nSimulating days {start_day} through {end_day}...")
    try:
        result = simulator.run_simulation(start_day, end_day, not quiet)
        print(f"Range simulation completed successfully")
        
        # Print summary
        if not quiet and "stats" in result:
            print(f"\nResults summary for days {start_day}-{end_day}:")
            for day, day_stats in result["stats"].items():
                matches_played = day_stats.get("matches_played", 0)
                print(f"  Day {day}: {matches_played} matches played")
        
        print(f"\nFinal results saved to: {result.get('final_stats', ['Unknown'])[0]}")
    
    except Exception as e:
        print(f"Error in range simulation: {e}")
        sys.exit(1)

def run_match_simulation(simulator, team_a_id: str, team_b_id: str, day_number: int = 1, quiet: bool = False) -> None:
    """
    Run simulation for a specific match
    
    Args:
        simulator: Simulator instance
        team_a_id: Team A ID
        team_b_id: Team B ID
        day_number: Day number for the match
        quiet: Whether to suppress detailed output
    """
    print(f"\nSimulating match: {team_a_id} vs {team_b_id} on day {day_number}...")
    
    try:
        # Get data loader
        data_loader = simulator.registry.get("data_loader")
        if not data_loader:
            print("Error: Data loader not available")
            sys.exit(1)
        
        # Load lineups
        lineups = data_loader.load_lineups(day_number)
        
        # Get team lineups
        team_a = lineups.get(team_a_id, [])
        team_b = lineups.get(team_b_id, [])
        
        if not team_a:
            print(f"Error: Team {team_a_id} not found in lineups for day {day_number}")
            sys.exit(1)
        
        if not team_b:
            print(f"Error: Team {team_b_id} not found in lineups for day {day_number}")
            sys.exit(1)
        
        # Simulate match
        result = simulator.simulate_match(team_a, team_b, day_number, 1, not quiet)
        
        # Print summary
        team_a_name = result.get("team_a_name", team_a_id)
        team_b_name = result.get("team_b_name", team_b_id)
        winner = result.get("winning_team", "Unknown")
        team_a_wins = result.get("team_a_wins", 0)
        team_b_wins = result.get("team_b_wins", 0)
        
        print(f"\nMatch result: {team_a_name} {team_a_wins} - {team_b_wins} {team_b_name}")
        print(f"Winner: {winner}")
        print(f"Rounds played: {result.get('rounds', 0)}")
        print(f"\nPGN file: {result.get('pgn_file', 'None')}")
        print(f"Match report: {result.get('summary_file', 'None')}")
        
    except Exception as e:
        print(f"Error in match simulation: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="META Fantasy League Simulator v4.2.1 Runner")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--day", type=int, help="Simulate a specific day")
    parser.add_argument("--range", help="Simulate a range of days (format: start-end)")
    parser.add_argument("--match", help="Simulate a specific match (format: team_a_id,team_b_id)")
    parser.add_argument("--match-day", type=int, default=1, help="Day number for match simulation")
    parser.add_argument("--quiet", action="store_true", help="Suppress detailed output")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Set up logging
    setup_logging(config)
    
    print("Initializing META Fantasy League Simulator v4.2.1...")
    
    # Create simulator instance
    simulator = MetaLeagueSimulatorV4_2_1(args.config)
    
    # Apply integration patches
    print("Applying integration patches...")
    simulator = apply_final_integration_patches(simulator)
    
    # Determine what to simulate
    if args.match:
        # Simulate a specific match
        team_a_id, team_b_id = args.match.split(',')
        run_match_simulation(simulator, team_a_id, team_b_id, args.match_day, args.quiet)
        
    elif args.range:
        # Simulate a range of days
        start, end = map(int, args.range.split('-'))
        run_range_simulation(simulator, start, end, args.quiet)
        
    elif args.day:
        # Simulate a specific day
        run_day_simulation(simulator, args.day, args.quiet)
        
    else:
        # Default: simulate day 1
        run_day_simulation(simulator, 1, args.quiet)
    
    print("\nSimulation completed successfully")

if __name__ == "__main__":
    main()