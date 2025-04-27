"""
META Fantasy League - Convergence Balancing System
Handles convergence targeting and distribution for fair gameplay
"""

from typing import List, Dict, Any, Tuple
import random

class ConvergenceBalancer:
    """System for ensuring fair convergence distribution and targeting"""
    
    def __init__(self):
        """Initialize the convergence balancer"""
        # Maximum convergences per role type (as percentage of total)
        self.role_convergence_limits = {
            "FL": 0.3,   # Field Leaders can receive up to 30% of convergences
            "VG": 0.25,  # Vanguards up to 25%
            "EN": 0.25,  # Enforcers up to 25%
            "RG": 0.2,   # Rangers up to 20%
            "GO": 0.2,   # Ghost Operatives up to 20%
            "PO": 0.2,   # Psi Operatives up to 20%
            "SV": 0.3    # Sovereigns up to 30%
        }
        
        # Default limit for other roles
        self.default_role_limit = 0.2  # 20% of convergences
        
        # Minimum guarantee of at least 1 convergence per character
        self.min_guaranteed = True
    
    def distribute_targets(self, characters, total_convergences=10):
        """Distribute convergence targets fairly across characters
        
        Args:
            characters: List of characters
            total_convergences: Total expected convergences
            
        Returns:
            Dict: Maximum convergences allowed per role
        """
        # Count roles
        role_counts = {}
        for char in characters:
            role = char.get("role", "Unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Calculate maximum convergences per role
        max_per_role = {}
        
        for role, count in role_counts.items():
            # Get role limit percentage
            limit_pct = self.role_convergence_limits.get(role, self.default_role_limit)
            
            # Calculate maximum for this role
            role_max = max(1, int(total_convergences * limit_pct))
            
            # If multiple characters have same role, distribute evenly
            if count > 1:
                char_max = max(1, role_max // count)
            else:
                char_max = role_max
            
            max_per_role[role] = char_max
        
        return max_per_role
    
    def balance_convergence_selections(self, potential_convergences, max_convergences=10):
        """Balance convergence selections from potential candidates
        
        Args:
            potential_convergences: List of potential convergences
            max_convergences: Maximum convergences to select
            
        Returns:
            List: Selected convergences
        """
        # If not enough potential convergences, return all
        if len(potential_convergences) <= max_convergences:
            return potential_convergences
        
        # Collect targeting statistics
        char_targets = {}
        for conv in potential_convergences:
            # Count targets for each character
            for char_key in ["a_char", "b_char"]:
                char = conv.get(char_key)
                if char:
                    char_id = char.get("id", "unknown")
                    char_targets[char_id] = char_targets.get(char_id, 0) + 1
        
        # Calculate character targeting imbalance
        char_imbalance = {}
        for char_id, target_count in char_targets.items():
            # Higher imbalance = more targeted than average
            average = len(potential_convergences) / len(char_targets)
            imbalance = target_count / average
            char_imbalance[char_id] = imbalance
        
        # Score each convergence for balance
        scored_convergences = []
        for conv in potential_convergences:
            # Calculate balance score (lower is better)
            balance_score = 0
            
            # Add targeting balance component
            char_a = conv.get("a_char")
            char_b = conv.get("b_char")
            
            if char_a and char_b:
                char_a_id = char_a.get("id", "unknown")
                char_b_id = char_b.get("id", "unknown")
                
                # Use targeting imbalance in score
                a_imbalance = char_imbalance.get(char_a_id, 1.0)
                b_imbalance = char_imbalance.get(char_b_id, 1.0)
                
                # Characters that are already heavily targeted get higher scores
                balance_score += (a_imbalance + b_imbalance) / 2
            
            # Add compelling combat component (closer rolls = more interesting)
            a_roll = conv.get("a_roll", 0)
            b_roll = conv.get("b_roll", 0)
            roll_diff = abs(a_roll - b_roll)
            
            # More interesting convergences (closer matches) get lower scores
            excitement_factor = max(1, 50 - roll_diff) / 50
            balance_score -= excitement_factor  # Lower score for exciting matchups
            
            # Add completed object to scored list
            scored_convergences.append({
                "convergence": conv,
                "balance_score": balance_score
            })
        
        # Sort by balance score (lower is better)
        scored_convergences.sort(key=lambda x: x["balance_score"])
        
        # Take the best balanced convergences
        selected = [item["convergence"] for item in scored_convergences[:max_convergences]]
        
        return selected
    
    def distribute_convergence_damage(self, convergences, total_damage_cap=None):
        """Distribute damage from convergences fairly
        
        Args:
            convergences: List of convergences
            total_damage_cap: Optional cap on total damage across all convergences
            
        Returns:
            List: Convergences with adjusted damage
        """
        # If empty or no cap, return as is
        if not convergences or not total_damage_cap:
            return convergences
        
        # Calculate total damage
        total_damage = sum(c.get("base_damage", 0) for c in convergences)
        
        # If under cap, no adjustment needed
        if total_damage <= total_damage_cap:
            return convergences
        
        # Calculate scaling factor
        scale_factor = total_damage_cap / total_damage
        
        # Adjust damage in each convergence
        adjusted = []
        for conv in convergences:
            adjusted_conv = conv.copy()
            base_damage = conv.get("base_damage", 0)
            adjusted_conv["base_damage"] = base_damage * scale_factor
            adjusted.append(adjusted_conv)
        
        return adjusted
    
    def ensure_fair_targeting(self, team_a, team_b, convergence_log, max_per_char=3):
        """Ensure fair targeting across characters
        
        Args:
            team_a: Team A characters
            team_b: Team B characters
            convergence_log: Log of convergences
            max_per_char: Maximum convergences per character
            
        Returns:
            Dict: Targeting statistics
        """
        # Count targeting per character
        targeting = {}
        
        # Initialize counts for all characters
        for char in team_a + team_b:
            char_id = char.get("id", "unknown")
            targeting[char_id] = {
                "targeted": 0,
                "as_winner": 0,
                "as_loser": 0,
                "damage_taken": 0,
                "damage_dealt": 0,
                "character": char
            }
        
        # Count from convergence log
        for conv in convergence_log:
            # Extract character IDs
            winner = conv.get("winner")
            loser = conv.get("loser")
            
            if not winner or not loser:
                continue
                
            winner_id = winner.get("id", "unknown")
            loser_id = loser.get("id", "unknown")
            
            # Update targeting stats
            if winner_id in targeting:
                targeting[winner_id]["as_winner"] += 1
                targeting[winner_id]["damage_dealt"] += conv.get("base_damage", 0)
            
            if loser_id in targeting:
                targeting[loser_id]["as_loser"] += 1
                targeting[loser_id]["targeted"] += 1
                targeting[loser_id]["damage_taken"] += conv.get("reduced_damage", 0)
        
        # Check for over-targeted characters
        over_targeted = []
        for char_id, stats in targeting.items():
            if stats["targeted"] > max_per_char:
                over_targeted.append({
                    "character_id": char_id,
                    "name": stats["character"].get("name", "Unknown"),
                    "targeted": stats["targeted"],
                    "damage_taken": stats["damage_taken"]
                })
        
        return {
            "targeting_stats": targeting,
            "over_targeted": over_targeted,
            "balanced": len(over_targeted) == 0
        }
    
    def suggest_balance_adjustments(self, team_a, team_b, convergence_log):
        """Suggest balance adjustments based on convergence patterns
        
        Args:
            team_a: Team A characters
            team_b: Team B characters
            convergence_log: Log of convergences
            
        Returns:
            Dict: Suggested balance adjustments
        """
        # Analyze targeting patterns
        targeting = self.ensure_fair_targeting(team_a, team_b, convergence_log)
        
        # Calculate team imbalance
        team_a_damage = sum(
            stats["damage_taken"] 
            for char_id, stats in targeting["targeting_stats"].items()
            if stats["character"] in team_a
        )
        
        team_b_damage = sum(
            stats["damage_taken"] 
            for char_id, stats in targeting["targeting_stats"].items()
            if stats["character"] in team_b
        )
        
        # Calculate damage ratio
        damage_ratio = team_a_damage / team_b_damage if team_b_damage > 0 else float('inf')
        
        # Check for severe imbalance (one team taking >2x damage)
        team_imbalance = abs(1 - damage_ratio) > 1.0
        
        # Generate suggested adjustments
        adjustments = []
        
        # Address over-targeted characters
        for char in targeting["over_targeted"]:
            adjustments.append({
                "type": "character",
                "target": char["character_id"],
                "name": char["name"],
                "adjustment": "Reduce convergence targeting probability",
                "severity": "high" if char["targeted"] > 5 else "medium"
            })
        
        # Address team imbalance
        if team_imbalance:
            disadvantaged_team = "A" if team_a_damage > team_b_damage else "B"
            adjustments.append({
                "type": "team",
                "target": f"Team {disadvantaged_team}",
                "adjustment": "Reduce overall damage intake",
                "severity": "high" if abs(1 - damage_ratio) > 2 else "medium"
            })
        
        return {
            "team_a_damage": team_a_damage,
            "team_b_damage": team_b_damage,
            "damage_ratio": damage_ratio,
            "team_imbalance": team_imbalance,
            "suggested_adjustments": adjustments
        }