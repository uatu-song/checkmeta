"""
META Fantasy League - Parity Testing Utility
Provides tools for testing and validating simulation fairness
"""

import os
import json
import time
import random
import datetime
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Tuple

class ParityTester:
    """Utility for testing and validating simulation fairness"""
    
    def __init__(self, simulator):
        """Initialize the parity tester
        
        Args:
            simulator: META League Simulator instance
        """
        self.simulator = simulator
        self.results_dir = "results/parity_tests"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def run_mirrored_tests(self, team_a, team_b, iterations=10, save_results=True):
        """Run mirrored tests to check for position bias
        
        This test runs matches with teams in normal position, then swaps
        their positions and runs again to check for first player advantage.
        
        Args:
            team_a: Team A characters
            team_b: Team B characters
            iterations: Number of test iterations
            save_results: Whether to save results to file
            
        Returns:
            Dict: Test results and statistics
        """
        print(f"Running mirrored parity tests ({iterations} iterations)...")
        results = {
            "a_as_a_wins": 0,
            "b_as_b_wins": 0,
            "a_as_b_wins": 0,
            "b_as_a_wins": 0,
            "details": []
        }
        
        # Run normal configuration tests
        for i in range(iterations):
            print(f"Normal configuration - iteration {i+1}/{iterations}")
            
            # Create deep copies to avoid modifying originals
            team_a_copy = [char.copy() for char in team_a]
            team_b_copy = [char.copy() for char in team_b]
            
            # Run match
            match_result = self.simulator.simulate_match(team_a_copy, team_b_copy, show_details=False)
            
            # Record result
            if match_result["winner"] == "Team A":
                results["a_as_a_wins"] += 1
            else:
                results["b_as_b_wins"] += 1
                
            results["details"].append({
                "config": "normal",
                "winner": match_result["winner"],
                "team_a_wins": match_result["team_a_wins"],
                "team_b_wins": match_result["team_b_wins"]
            })
        
        # Run mirrored configuration tests
        for i in range(iterations):
            print(f"Mirrored configuration - iteration {i+1}/{iterations}")
            
            # Create deep copies to avoid modifying originals
            team_a_copy = [char.copy() for char in team_a]
            team_b_copy = [char.copy() for char in team_b]
            
            # Swap team names and IDs to ensure proper tracking
            for char in team_a_copy:
                char["original_team_id"] = char["team_id"]
                char["original_team_name"] = char["team_name"]
                char["team_id"] = "swapped_b"
                char["team_name"] = "Team B (swapped)"
            
            for char in team_b_copy:
                char["original_team_id"] = char["team_id"]
                char["original_team_name"] = char["team_name"]
                char["team_id"] = "swapped_a"
                char["team_name"] = "Team A (swapped)"
            
            # Run match with swapped positions
            match_result = self.simulator.simulate_match(team_b_copy, team_a_copy, show_details=False)
            
            # Record result (accounting for team swap)
            if match_result["winner"] == "Team A":
                # Team B playing as Team A won
                results["b_as_a_wins"] += 1
            else:
                # Team A playing as Team B won
                results["a_as_b_wins"] += 1
                
            results["details"].append({
                "config": "mirrored",
                "winner": match_result["winner"],
                "team_a_wins": match_result["team_a_wins"],
                "team_b_wins": match_result["team_b_wins"]
            })
        
        # Calculate statistics
        results["team_a_total_wins"] = results["a_as_a_wins"] + results["a_as_b_wins"]
        results["team_b_total_wins"] = results["b_as_b_wins"] + results["b_as_a_wins"]
        
        results["position_a_wins"] = results["a_as_a_wins"] + results["b_as_a_wins"]
        results["position_b_wins"] = results["b_as_b_wins"] + results["a_as_b_wins"]
        
        total_matches = iterations * 2
        
        results["team_a_win_rate"] = (results["team_a_total_wins"] / total_matches) * 100
        results["team_b_win_rate"] = (results["team_b_total_wins"] / total_matches) * 100
        
        results["position_a_win_rate"] = (results["position_a_wins"] / total_matches) * 100
        results["position_b_win_rate"] = (results["position_b_wins"] / total_matches) * 100
        
        # Calculate advantage percentages (how far from 50%)
        results["team_advantage_pct"] = abs(50 - results["team_a_win_rate"])
        results["position_advantage_pct"] = abs(50 - results["position_a_win_rate"])
        
        # Save results
        if save_results:
            self._save_test_results(results, "mirrored_test")
        
        # Print summary
        self._print_mirrored_test_summary(results)
        
        return results
    
    def run_repeated_tests(self, team_a, team_b, iterations=10, save_results=True):
        """Run repeated tests to check for random variation
        
        Args:
            team_a: Team A characters
            team_b: Team B characters
            iterations: Number of test iterations
            save_results: Whether to save results to file
            
        Returns:
            Dict: Test results and statistics
        """
        print(f"Running repeated parity tests ({iterations} iterations)...")
        results = {
            "team_a_wins": 0,
            "team_b_wins": 0,
            "draws": 0,
            "details": []
        }
        
        # Run match multiple times
        for i in range(iterations):
            print(f"Iteration {i+1}/{iterations}")
            
            # Create deep copies to avoid modifying originals
            team_a_copy = [char.copy() for char in team_a]
            team_b_copy = [char.copy() for char in team_b]
            
            # Run match
            match_result = self.simulator.simulate_match(team_a_copy, team_b_copy, show_details=False)
            
            # Record result
            if match_result["winner"] == "Team A":
                results["team_a_wins"] += 1
            elif match_result["winner"] == "Team B":
                results["team_b_wins"] += 1
            else:
                results["draws"] += 1
                
            # Store detailed result
            results["details"].append({
                "iteration": i + 1,
                "winner": match_result["winner"],
                "team_a_wins": match_result["team_a_wins"],
                "team_b_wins": match_result["team_b_wins"],
                "character_results": match_result["character_results"]
            })
        
        # Calculate statistics
        total_matches = iterations
        
        results["team_a_win_rate"] = (results["team_a_wins"] / total_matches) * 100
        results["team_b_win_rate"] = (results["team_b_wins"] / total_matches) * 100
        results["draw_rate"] = (results["draws"] / total_matches) * 100
        
        # Calculate standard deviation
        a_wins_list = [1 if detail["winner"] == "Team A" else 0 for detail in results["details"]]
        results["win_rate_std_dev"] = self._calculate_std_dev(a_wins_list) * 100
        
        # Calculate character KO rates
        results["character_ko_rates"] = self._calculate_character_ko_rates(results["details"])
        
        # Save results
        if save_results:
            self._save_test_results(results, "repeated_test")
        
        # Print summary
        self._print_repeated_test_summary(results)
        
        return results
    
    def run_comprehensive_tests(self, teams, iterations=5, save_results=True):
        """Run comprehensive parity tests across multiple team matchups
        
        Args:
            teams: Dictionary of teams by team_id
            iterations: Number of iterations per test
            save_results: Whether to save results to file
            
        Returns:
            Dict: Comprehensive test results
        """
        print(f"Running comprehensive parity tests across multiple teams...")
        team_ids = list(teams.keys())
        
        # Ensure we have enough teams
        if len(team_ids) < 2:
            print("Not enough teams for comprehensive tests")
            return {"error": "Not enough teams"}
        
        # Create matchups (each team vs. each other team)
        matchups = []
        for i in range(len(team_ids)):
            for j in range(i+1, len(team_ids)):
                matchups.append((team_ids[i], team_ids[j]))
        
        print(f"Testing {len(matchups)} matchups with {iterations} iterations each...")
        
        # Initialize results
        results = {
            "matchups": [],
            "team_win_rates": {},
            "position_advantage": 0,
            "details": []
        }
        
        # Initialize team counters
        for team_id in team_ids:
            results["team_win_rates"][team_id] = {
                "matches": 0,
                "wins": 0,
                "win_rate": 0
            }
        
        # Test each matchup
        for team_a_id, team_b_id in matchups:
            team_a = teams[team_a_id]
            team_b = teams[team_b_id]
            
            # Run mirrored test
            matchup_result = self.run_mirrored_tests(team_a, team_b, iterations, False)
            
            # Update matchup results
            results["matchups"].append({
                "team_a_id": team_a_id,
                "team_b_id": team_b_id,
                "team_a_win_rate": matchup_result["team_a_win_rate"],
                "team_b_win_rate": matchup_result["team_b_win_rate"],
                "position_advantage_pct": matchup_result["position_advantage_pct"]
            })
            
            # Update team win rates
            results["team_win_rates"][team_a_id]["matches"] += iterations * 2
            results["team_win_rates"][team_b_id]["matches"] += iterations * 2
            
            results["team_win_rates"][team_a_id]["wins"] += matchup_result["team_a_total_wins"]
            results["team_win_rates"][team_b_id]["wins"] += matchup_result["team_b_total_wins"]
            
            # Add to overall position advantage
            results["position_advantage"] += matchup_result["position_advantage_pct"]
            
            # Add details
            results["details"].append(matchup_result)
        
        # Calculate averages
        if results["matchups"]:
            results["position_advantage_pct"] = results["position_advantage"] / len(results["matchups"])
            
            # Calculate team win rates
            for team_id in results["team_win_rates"]:
                if results["team_win_rates"][team_id]["matches"] > 0:
                    win_rate = (results["team_win_rates"][team_id]["wins"] / 
                               results["team_win_rates"][team_id]["matches"]) * 100
                    results["team_win_rates"][team_id]["win_rate"] = win_rate
        
        # Save results
        if save_results:
            self._save_test_results(results, "comprehensive_test")
        
        # Print summary
        self._print_comprehensive_test_summary(results)
        
        return results
    
    def visualize_results(self, results, test_type="mirrored", save_path=None):
        """Generate visualization of test results
        
        Args:
            results: Test results data
            test_type: Type of test results
            save_path: Path to save visualization
            
        Returns:
            str: Path to saved visualization if applicable
        """
        if test_type == "mirrored":
            return self._visualize_mirrored_results(results, save_path)
        elif test_type == "repeated":
            return self._visualize_repeated_results(results, save_path)
        elif test_type == "comprehensive":
            return self._visualize_comprehensive_results(results, save_path)
        else:
            print(f"Unknown test type: {test_type}")
            return None
    
    def _visualize_mirrored_results(self, results, save_path=None):
        """Visualize mirrored test results
        
        Args:
            results: Mirrored test results
            save_path: Path to save visualization
        """
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Bar data
            labels = ['Team A Win %', 'Team B Win %', 'Position A Win %', 'Position B Win %']
            values = [
                results["team_a_win_rate"],
                results["team_b_win_rate"],
                results["position_a_win_rate"],
                results["position_b_win_rate"]
            ]
            
            x = np.arange(len(labels))
            width = 0.5
            
            # Create bars
            bars = plt.bar(x, values, width, color=['blue', 'orange', 'green', 'red'])
            
            # Add perfect parity line
            plt.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='Perfect Parity')
            
            # Labels and title
            plt.ylabel('Win Rate (%)')
            plt.title('Mirrored Test Results - Team vs Position Win Rates')
            plt.xticks(x, labels)
            plt.legend()
            
            # Add values on top of bars
            for i, bar in enumerate(bars):
                plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                        f'{values[i]:.1f}%', ha='center')
            
            # Add advantage annotations
            plt.figtext(0.5, 0.01, 
                       f'Team Advantage: {results["team_advantage_pct"]:.1f}% | ' +
                       f'Position Advantage: {results["position_advantage_pct"]:.1f}%',
                       ha='center', fontsize=10, bbox={"facecolor":"orange", "alpha":0.1, "pad":5})
            
            plt.tight_layout()
            
            # Save if path provided
            if save_path:
                plt.savefig(save_path)
                print(f"Visualization saved to {save_path}")
                return save_path
            else:
                plt.show()
                return None
                
        except ImportError:
            print("Matplotlib not available for visualization")
            return None
    
    def _visualize_repeated_results(self, results, save_path=None):
        """Visualize repeated test results
        
        Args:
            results: Repeated test results
            save_path: Path to save visualization
        """
        try:
            import matplotlib.pyplot as plt
            
            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            
            # Plot win distribution
            labels = ['Team A Wins', 'Team B Wins', 'Draws']
            sizes = [
                results["team_a_wins"],
                results["team_b_wins"],
                results["draws"]
            ]
            colors = ['blue', 'orange', 'gray']
            
            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                   shadow=True, startangle=90)
            ax1.axis('equal')
            ax1.set_title('Match Outcome Distribution')
            
            # Plot character KO rates
            ko_rates = results["character_ko_rates"]
            
            if ko_rates:
                char_names = [item["name"] for item in ko_rates]
                ko_pcts = [item["ko_rate"] for item in ko_rates]
                teams = [item["team"] for item in ko_rates]
                
                # Create colors based on team
                team_colors = ['blue' if team == 'A' else 'orange' for team in teams]
                
                # Sort by team and KO rate
                indices = sorted(range(len(ko_rates)), 
                                key=lambda i: (teams[i] != 'A', -ko_pcts[i]))
                
                char_names = [char_names[i] for i in indices]
                ko_pcts = [ko_pcts[i] for i in indices]
                team_colors = [team_colors[i] for i in indices]
                
                # Plot horizontal bar chart
                y_pos = range(len(char_names))
                ax2.barh(y_pos, ko_pcts, color=team_colors)
                ax2.set_yticks(y_pos)
                ax2.set_yticklabels(char_names)
                ax2.invert_yaxis()  # Labels read top-to-bottom
                ax2.set_xlabel('KO Rate (%)')
                ax2.set_title('Character KO Rates')
                
                # Add values on bars
                for i, v in enumerate(ko_pcts):
                    ax2.text(v + 1, i, f"{v:.1f}%", va='center')
            
            plt.tight_layout()
            
            # Save if path provided
            if save_path:
                plt.savefig(save_path)
                print(f"Visualization saved to {save_path}")
                return save_path
            else:
                plt.show()
                return None
                
        except ImportError:
            print("Matplotlib not available for visualization")
            return None
    
    def _visualize_comprehensive_results(self, results, save_path=None):
        """Visualize comprehensive test results
        
        Args:
            results: Comprehensive test results
            save_path: Path to save visualization
        """
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Plot team win rates
            team_ids = list(results["team_win_rates"].keys())
            win_rates = [results["team_win_rates"][team_id]["win_rate"] for team_id in team_ids]
            
            # Sort by win rate
            indices = sorted(range(len(win_rates)), key=lambda i: -win_rates[i])
            team_ids = [team_ids[i] for i in indices]
            win_rates = [win_rates[i] for i in indices]
            
            # Plot horizontal bar chart
            y_pos = range(len(team_ids))
            bars = ax1.barh(y_pos, win_rates, color='blue')
            ax1.set_yticks(y_pos)
            ax1.set_yticklabels(team_ids)
            ax1.invert_yaxis()  # Labels read top-to-bottom
            ax1.set_xlabel('Win Rate (%)')
            ax1.set_title('Team Win Rates')
            
            # Add perfect parity line
            ax1.axvline(x=50, color='r', linestyle='--', alpha=0.5, label='Perfect Parity')
            
            # Add values on bars
            for i, v in enumerate(win_rates):
                ax1.text(v + 1, i, f"{v:.1f}%", va='center')
            
            # Plot matchup position advantages
            if results["matchups"]:
                matchup_labels = [f"{m['team_a_id']} vs {m['team_b_id']}" for m in results["matchups"]]
                position_advantages = [m["position_advantage_pct"] for m in results["matchups"]]
                
                # Sort by advantage
                indices = sorted(range(len(position_advantages)), key=lambda i: -position_advantages[i])
                matchup_labels = [matchup_labels[i] for i in indices]
                position_advantages = [position_advantages[i] for i in indices]
                
                # Plot horizontal bar chart
                y_pos = range(len(matchup_labels))
                bars = ax2.barh(y_pos, position_advantages, color='green')
                ax2.set_yticks(y_pos)
                ax2.set_yticklabels(matchup_labels)
                ax2.invert_yaxis()  # Labels read top-to-bottom
                ax2.set_xlabel('Position Advantage (%)')
                ax2.set_title('Matchup Position Advantages')
                
                # Add values on bars
                for i, v in enumerate(position_advantages):
                    ax2.text(v + 0.5, i, f"{v:.1f}%", va='center')
            
            # Add overall position advantage annotation
            plt.figtext(0.5, 0.01, 
                       f'Overall Position Advantage: {results["position_advantage_pct"]:.1f}%',
                       ha='center', fontsize=12, bbox={"facecolor":"green", "alpha":0.1, "pad":5})
            
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            
            # Save if path provided
            if save_path:
                plt.savefig(save_path)
                print(f"Visualization saved to {save_path}")
                return save_path
            else:
                plt.show()
                return None
                
        except ImportError:
            print("Matplotlib not available for visualization")
            return None
    
    def _save_test_results(self, results, test_type):
        """Save test results to file
        
        Args:
            results: Test results data
            test_type: Type of test
            
        Returns:
            str: Path to saved results file
        """
        # Generate filename with timestamp
        timestamp = int(time.time())
        filename = f"{test_type}_{timestamp}.json"
        file_path = os.path.join(self.results_dir, filename)
        
        # Save results as JSON
        with open(file_path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"Test results saved to {file_path}")
        return file_path
    
    def _print_mirrored_test_summary(self, results):
        """Print summary of mirrored test results
        
        Args:
            results: Mirrored test results
        """
        print("\n=== MIRRORED TEST SUMMARY ===")
        print(f"Team A win rate: {results['team_a_win_rate']:.1f}%")
        print(f"Team B win rate: {results['team_b_win_rate']:.1f}%")
        print(f"Position A win rate: {results['position_a_win_rate']:.1f}%")
        print(f"Position B win rate: {results['position_b_win_rate']:.1f}%")
        print(f"Team advantage: {results['team_advantage_pct']:.1f}%")
        print(f"Position advantage: {results['position_advantage_pct']:.1f}%")
        
        # Interpretation
        if results["position_advantage_pct"] > 10:
            print("\nINTERPRETATION: Significant position advantage detected!")
        elif results["position_advantage_pct"] > 5:
            print("\nINTERPRETATION: Moderate position advantage detected.")
        else:
            print("\nINTERPRETATION: No significant position advantage detected.")
    
    def _print_repeated_test_summary(self, results):
        """Print summary of repeated test results
        
        Args:
            results: Repeated test results
        """
        print("\n=== REPEATED TEST SUMMARY ===")
        print(f"Team A win rate: {results['team_a_win_rate']:.1f}%")
        print(f"Team B win rate: {results['team_b_win_rate']:.1f}%")
        print(f"Draw rate: {results['draw_rate']:.1f}%")
        print(f"Win rate standard deviation: {results['win_rate_std_dev']:.1f}%")
        
        # Interpretation
        if abs(results["team_a_win_rate"] - 50) > 20:
            print("\nINTERPRETATION: Teams are significantly imbalanced!")
        elif abs(results["team_a_win_rate"] - 50) > 10:
            print("\nINTERPRETATION: Teams show moderate imbalance.")
        else:
            print("\nINTERPRETATION: Teams appear relatively balanced.")
    
    def _print_comprehensive_test_summary(self, results):
        """Print summary of comprehensive test results
        
        Args:
            results: Comprehensive test results
        """
        print("\n=== COMPREHENSIVE TEST SUMMARY ===")
        print(f"Overall position advantage: {results['position_advantage_pct']:.1f}%")
        
        # Team win rates
        print("\nTeam Win Rates:")
        for team_id, stats in sorted(
            results["team_win_rates"].items(), 
            key=lambda x: -x[1]["win_rate"]
        ):
            print(f"  {team_id}: {stats['win_rate']:.1f}% ({stats['wins']}/{stats['matches']})")
        
        # Matchup position advantages
        if results["matchups"]:
            print("\nMatchup Position Advantages:")
            for matchup in sorted(
                results["matchups"],
                key=lambda x: -x["position_advantage_pct"]
            ):
                print(f"  {matchup['team_a_id']} vs {matchup['team_b_id']}: {matchup['position_advantage_pct']:.1f}%")
        
        # Overall interpretation
        if results["position_advantage_pct"] > 10:
            print("\nINTERPRETATION: Significant position advantage detected across matchups!")
        elif results["position_advantage_pct"] > 5:
            print("\nINTERPRETATION: Moderate position advantage detected across matchups.")
        else:
            print("\nINTERPRETATION: No significant position advantage detected across matchups.")
    
    def _calculate_std_dev(self, values):
        """Calculate standard deviation
        
        Args:
            values: List of values
            
        Returns:
            float: Standard deviation
        """
        if not values:
            return 0
            
        # Calculate mean
        mean = sum(values) / len(values)
        
        # Calculate sum of squared differences
        sq_diff_sum = sum((x - mean) ** 2 for x in values)
        
        # Calculate variance and standard deviation
        variance = sq_diff_sum / len(values)
        std_dev = variance ** 0.5
        
        return std_dev
    
    def _calculate_character_ko_rates(self, match_details):
        """Calculate character KO rates across matches
        
        Args:
            match_details: List of match details
            
        Returns:
            List: Character KO rate statistics
        """
        # Initialize character tracking
        character_stats = {}
        
        # Process all matches
        for match in match_details:
            for char_result in match.get("character_results", []):
                char_id = char_result.get("character_id", "unknown")
                char_name = char_result.get("character_name", "Unknown")
                char_team = char_result.get("team", "Unknown")
                is_ko = char_result.get("is_ko", False)
                
                # Initialize if new character
                if char_id not in character_stats:
                    character_stats[char_id] = {
                        "id": char_id,
                        "name": char_name,
                        "team": char_team,
                        "matches": 0,
                        "ko_count": 0
                    }
                
                # Update stats
                character_stats[char_id]["matches"] += 1
                if is_ko:
                    character_stats[char_id]["ko_count"] += 1
        
        # Calculate KO rates
        ko_rates = []
        for char_id, stats in character_stats.items():
            if stats["matches"] > 0:
                ko_rate = (stats["ko_count"] / stats["matches"]) * 100
                
                ko_rates.append({
                    "id": char_id,
                    "name": stats["name"],
                    "team": stats["team"],
                    "matches": stats["matches"],
                    "ko_count": stats["ko_count"],
                    "ko_rate": ko_rate
                })
        
        # Sort by KO rate (descending)
        ko_rates.sort(key=lambda x: -x["ko_rate"])
        
        return ko_rates