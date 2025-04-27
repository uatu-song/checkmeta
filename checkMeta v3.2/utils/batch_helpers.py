"""
META Fantasy League Simulator - Batch Helpers
Provides utilities for batch processing of matches
"""

import time
import os
from typing import Dict, List, Any, Optional, Tuple, Generator
from config import get_config

def create_match_batches(matchups, batch_size=None):
    """Create batches of matches for processing
    
    Args:
        matchups: List of match tuples
        batch_size: Optional batch size override
        
    Returns:
        List: List of batches (each containing matchup tuples)
    """
    config = get_config()
    batch_size = batch_size or config.simulation["max_batch_size"]
    
    # Ensure batch size is valid
    batch_size = max(1, min(batch_size, len(matchups)))
    
    # Create batches
    batches = []
    for i in range(0, len(matchups), batch_size):
        batches.append(matchups[i:i + batch_size])
    
    return batches

def process_match_batch(batch, simulator, show_progress=True):
    """Process a batch of matches
    
    Args:
        batch: Batch of matchup tuples
        simulator: Simulator instance
        show_progress: Whether to show progress output
        
    Returns:
        List: Batch results
    """
    results = []
    
    for i, (team_a_id, team_b_id) in enumerate(batch):
        if show_progress:
            print(f"Processing match {i+1}/{len(batch)}: {team_a_id} vs {team_b_id}")
        
        # Get team data
        team_a = simulator.teams.get(team_a_id, [])
        team_b = simulator.teams.get(team_b_id, [])
        
        if not team_a or not team_b:
            print(f"Error: Missing teams for matchup ({team_a_id} vs {team_b_id})")
            continue
        
        # Run simulation
        try:
            match_result = simulator.simulate_match(team_a, team_b, show_details=False)
            results.append(match_result)
            
            if show_progress:
                winner = match_result.get("winning_team", "Unknown")
                print(f"  Result: {winner} wins")
        except Exception as e:
            print(f"Error simulating match: {e}")
    
    return results

def batch_generator(items, batch_size=None) -> Generator:
    """Create a generator for batch processing
    
    Args:
        items: List of items to process
        batch_size: Optional batch size override
        
    Returns:
        Generator: Yields batches of items
    """
    config = get_config()
    batch_size = batch_size or config.simulation["max_batch_size"]
    
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def estimate_processing_time(num_matches, avg_time_per_match=5.0):
    """Estimate processing time for matches
    
    Args:
        num_matches: Number of matches to process
        avg_time_per_match: Average time per match in seconds
        
    Returns:
        tuple: (estimated_total_seconds, formatted_time_string)
    """
    total_seconds = num_matches * avg_time_per_match
    
    # Format time
    if total_seconds < 60:
        time_str = f"{total_seconds:.1f} seconds"
    elif total_seconds < 3600:
        minutes = total_seconds / 60
        time_str = f"{minutes:.1f} minutes"
    else:
        hours = total_seconds / 3600
        time_str = f"{hours:.1f} hours"
    
    return total_seconds, time_str