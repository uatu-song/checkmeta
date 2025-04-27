"""
META Fantasy League - Loss Condition System
Handles team loss conditions with improved balance and fairness
"""

from typing import List, Dict, Any, Tuple

class LossConditionSystem:
    """System for checking team loss conditions with improved balance"""
    
    def __init__(self):
        """Initialize the loss condition system"""
        # Required KO count for team loss
        self.ko_threshold = 3  # Team loses if 3 characters are KO'd
        
        # Required KOs for Field Leader + additional characters
        self.fl_plus_ko_threshold = 2  # FL + 1 more character
        
        # Team HP percentage threshold for loss
        self.team_hp_threshold = 25  # Team loses if total HP falls below 25%
        
        # Team active percentage threshold for loss
        self.active_threshold = 0.35  # Team loses if less than 35% active
    
    def check_team_loss(self, team) -> Tuple[bool, str]:
        """Check if a team has met any loss conditions
        
        Args:
            team: List of team characters
            
        Returns:
            Tuple: (is_loss, reason)
        """
        # Count KOs and active characters
        ko_count = 0
        active_count = 0
        total_count = 0
        
        # Track Field Leader status
        fl_ko = False
        
        # Track team HP
        total_hp = 0
        max_possible_hp = 0
        
        for char in team:
            total_count += 1
            
            # Check if active
            if not char.get("is_ko", False):
                active_count += 1
            else:
                ko_count += 1
                
                # Check if Field Leader
                if char.get("role") == "FL":
                    fl_ko = True
            
            # Add to HP totals
            total_hp += char.get("HP", 0)
            max_possible_hp += 100  # Assuming max HP is 100
        
        # No characters, automatic loss
        if total_count == 0:
            return True, "No characters"
        
        # Check condition 1: Multiple KOs threshold
        if ko_count >= self.ko_threshold:
            return True, f"KO threshold reached ({ko_count}/{total_count})"
        
        # Check condition 2: Field Leader KO + additional characters
        if fl_ko and ko_count >= self.fl_plus_ko_threshold:
            return True, f"Field Leader KO + {ko_count-1} additional KOs"
        
        # Check condition 3: Team HP threshold
        hp_percentage = (total_hp / max_possible_hp) * 100
        if hp_percentage < self.team_hp_threshold:
            return True, f"Team HP below threshold ({hp_percentage:.1f}%)"
        
        # Check condition 4: Active character threshold
        active_percentage = (active_count / total_count) * 100
        if active_percentage < (self.active_threshold * 100):
            return True, f"Active characters below threshold ({active_percentage:.1f}%)"
        
        # No loss conditions met
        return False, "Team still viable"
    
    def check_match_end_conditions(self, team_a, team_b) -> Tuple[bool, str, str]:
        """Check if either team has met loss conditions
        
        Args:
            team_a: List of team A characters
            team_b: List of team B characters
            
        Returns:
            Tuple: (is_match_over, winner, reason)
        """
        # Check team A
        team_a_loss, team_a_reason = self.check_team_loss(team_a)
        
        # Check team B
        team_b_loss, team_b_reason = self.check_team_loss(team_b)
        
        # Determine match outcome
        if team_a_loss and team_b_loss:
            # Both teams lost, determine winner by remaining HP
            team_a_hp = sum(char.get("HP", 0) for char in team_a)
            team_b_hp = sum(char.get("HP", 0) for char in team_b)
            
            if team_a_hp > team_b_hp:
                return True, "Team A", f"Both teams reached loss conditions, but Team A has more HP ({team_a_hp} vs {team_b_hp})"
            elif team_b_hp > team_a_hp:
                return True, "Team B", f"Both teams reached loss conditions, but Team B has more HP ({team_b_hp} vs {team_a_hp})"
            else:
                return True, "Draw", "Both teams reached loss conditions with equal HP"
                
        elif team_a_loss:
            return True, "Team B", f"Team A loss: {team_a_reason}"
            
        elif team_b_loss:
            return True, "Team A", f"Team B loss: {team_b_reason}"
            
        # Match continues
        return False, "", ""
    
    def get_team_status(self, team) -> Dict[str, Any]:
        """Get detailed team status information
        
        Args:
            team: List of team characters
            
        Returns:
            Dict: Team status details
        """
        status = {
            "total": 0,
            "active": 0,
            "ko": 0,
            "fl_ko": False,
            "total_hp": 0,
            "max_hp": 0,
            "hp_percentage": 0,
            "active_percentage": 0
        }
        
        for char in team:
            status["total"] += 1
            
            # Count active characters
            if not char.get("is_ko", False):
                status["active"] += 1
            else:
                status["ko"] += 1
                
                # Check if Field Leader
                if char.get("role") == "FL":
                    status["fl_ko"] = True
            
            # Add to HP totals
            status["total_hp"] += char.get("HP", 0)
            status["max_hp"] += 100  # Assuming max HP is 100
        
        # Calculate percentages
        if status["max_hp"] > 0:
            status["hp_percentage"] = (status["total_hp"] / status["max_hp"]) * 100
        
        if status["total"] > 0:
            status["active_percentage"] = (status["active"] / status["total"]) * 100
        
        return status
    
    def check_character_defeat(self, character) -> Tuple[bool, str]:
        """Check if a character is defeated
        
        Args:
            character: Character to check
            
        Returns:
            Tuple: (is_defeated, reason)
        """
        # Check HP
        if character.get("HP", 0) <= 0:
            # Check stamina
            if character.get("stamina", 0) <= 0:
                return True, "HP and stamina depleted"
            else:
                return False, "HP depleted but has stamina"
        
        # Check other defeat conditions
        if character.get("is_ko", False):
            return True, "Character is KO'd"
            
        if character.get("is_dead", False):
            return True, "Character is dead"
        
        # Character is still viable
        return False, "Character is active"