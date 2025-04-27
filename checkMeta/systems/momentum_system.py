"""
META Fantasy League - Momentum System
Handles team momentum tracking and comeback mechanics
"""

from typing import List, Dict, Any, Tuple

class MomentumSystem:
    """System for tracking team momentum and applying comeback mechanics"""
    
    def __init__(self):
        """Initialize the momentum system"""
        # Momentum state thresholds
        self.momentum_thresholds = {
            "crash": -3,     # Value <= -3 is crash state
            "building": 3    # Value >= 3 is building state
        }
        
        # Momentum effects
        self.momentum_effects = {
            "crash": {
                "damage_reduction": 15,    # Additional damage reduction %
                "recovery": 2,             # Additional HP/stamina recovery
                "trait_bonus": 10,         # % bonus to trait activation
                "revival_chance": 10       # % bonus to KO recovery
            },
            "building": {
                "damage_bonus": 10,        # % bonus to damage
                "trait_bonus": 5,          # % bonus to trait activation
                "stamina_discount": 10     # % discount on stamina costs
            },
            "stable": {
                # No special effects
            }
        }
        
        # Score tracking
        self.score_tracking = {
            "team_a": [],  # List of win/loss results
            "team_b": []   # List of win/loss results
        }
        
        # Current state
        self.current_momentum = {
            "team_a": {"state": "stable", "value": 0},
            "team_b": {"state": "stable", "value": 0}
        }
    
    def update_momentum(self, team_a, team_b, match_context, show_details=False):
        """Update momentum for both teams and apply effects
        
        Args:
            team_a: List of team A characters
            team_b: List of team B characters
            match_context: Match context with result tracking
            show_details: Whether to show detailed output
            
        Returns:
            Dict: Updated momentum and effects
        """
        # Get team status
        team_a_status = self._calculate_team_status(team_a)
        team_b_status = self._calculate_team_status(team_b)
        
        # Calculate relative team strengths
        team_a_strength = self._calculate_relative_strength(team_a_status)
        team_b_strength = self._calculate_relative_strength(team_b_status)
        
        # Calculate momentum shift
        momentum_shift = self._calculate_momentum_shift(team_a_strength, team_b_strength)
        
        # Update momentum values with bounded values
        team_a_momentum = self._update_team_momentum("team_a", momentum_shift)
        team_b_momentum = self._update_team_momentum("team_b", -momentum_shift)
        
        # Check for comebacks
        comeback_active = False
        comeback_team = None
        
        # Comeback is active if a team is behind in score but has building momentum
        team_a_wins = match_context.get("team_a_wins", 0)
        team_b_wins = match_context.get("team_b_wins", 0)
        
        if team_a_wins < team_b_wins and team_a_momentum["state"] == "building":
            comeback_active = True
            comeback_team = "A"
        elif team_b_wins < team_a_wins and team_b_momentum["state"] == "building":
            comeback_active = True
            comeback_team = "B"
        
        # Apply momentum effects to characters
        self._apply_momentum_effects(team_a, team_a_momentum)
        self._apply_momentum_effects(team_b, team_b_momentum)
        
        # Add special comeback effects if active
        if comeback_active:
            self._apply_comeback_effects(team_a if comeback_team == "A" else team_b)
        
        if show_details:
            self._log_momentum_status(team_a_momentum, team_b_momentum, comeback_active, comeback_team)
        
        # Store updated values in match context
        match_context["team_a_momentum"] = team_a_momentum
        match_context["team_b_momentum"] = team_b_momentum
        match_context["comeback_active"] = comeback_active
        match_context["comeback_team"] = comeback_team
        
        # Return effects summary
        return {
            "team_a_momentum": team_a_momentum,
            "team_b_momentum": team_b_momentum,
            "comeback_active": comeback_active,
            "team": comeback_team
        }
    
    def _calculate_team_status(self, team):
        """Calculate team status metrics
        
        Args:
            team: List of team characters
            
        Returns:
            Dict: Team status metrics
        """
        status = {
            "total": len(team),
            "active": 0,
            "ko": 0,
            "hp_percentage": 0,
            "stamina_percentage": 0
        }
        
        # Safety check
        if status["total"] == 0:
            return status
        
        # Calculate active/KO counts and HP/stamina percentages
        total_hp = 0
        total_stamina = 0
        
        for char in team:
            if not char.get("is_ko", False):
                status["active"] += 1
            else:
                status["ko"] += 1
            
            total_hp += char.get("HP", 0)
            total_stamina += char.get("stamina", 0)
        
        # Calculate percentages
        status["hp_percentage"] = total_hp / (status["total"] * 100)
        status["stamina_percentage"] = total_stamina / (status["total"] * 100)
        
        return status
    
    def _calculate_relative_strength(self, status):
        """Calculate relative team strength based on status
        
        Args:
            status: Team status metrics
            
        Returns:
            float: Relative strength value (0-1)
        """
        # Safety check
        if status["total"] == 0:
            return 0
        
        # Calculate relative strength based on active percentage and HP
        active_ratio = status["active"] / status["total"]
        
        # Weight active ratio and HP percentage equally
        strength = (active_ratio + status["hp_percentage"]) / 2
        
        return strength
    
    def _calculate_momentum_shift(self, team_a_strength, team_b_strength):
        """Calculate momentum shift based on team strengths
        
        Args:
            team_a_strength: Team A strength value
            team_b_strength: Team B strength value
            
        Returns:
            float: Momentum shift value
        """
        # Calculate strength difference
        diff = team_a_strength - team_b_strength
        
        # Scale to appropriate shift values
        # Significant advantage (30%+ difference)
        if diff >= 0.3:
            return 1.0  # Strong shift towards team A
        elif diff <= -0.3:
            return -1.0  # Strong shift towards team B
        
        # Moderate advantage (10-30% difference)
        elif diff >= 0.1:
            return 0.5  # Moderate shift towards team A
        elif diff <= -0.1:
            return -0.5  # Moderate shift towards team B
        
        # Minor advantage (0-10% difference)
        else:
            return diff * 2  # Minor shift proportional to difference
    
    def _update_team_momentum(self, team_key, shift):
        """Update momentum value for a team
        
        Args:
            team_key: Team identifier ("team_a" or "team_b")
            shift: Momentum shift value
            
        Returns:
            Dict: Updated momentum data
        """
        # Get current momentum
        current = self.current_momentum[team_key]["value"]
        
        # Apply shift with bounds
        new_value = max(-5, min(5, current + shift))
        
        # Determine state based on new value
        if new_value <= self.momentum_thresholds["crash"]:
            state = "crash"
        elif new_value >= self.momentum_thresholds["building"]:
            state = "building"
        else:
            state = "stable"
        
        # Store updated values
        self.current_momentum[team_key] = {
            "state": state,
            "value": new_value
        }
        
        return self.current_momentum[team_key]
    
    def _apply_momentum_effects(self, team, momentum):
        """Apply momentum effects to a team
        
        Args:
            team: List of team characters
            momentum: Momentum data for team
        """
        # Get effects for this momentum state
        state = momentum["state"]
        effects = self.momentum_effects.get(state, {})
        
        # Apply to each character
        for char in team:
            # Skip KO'd characters
            if char.get("is_ko", False):
                continue
            
            # Set momentum state and value
            char["momentum_state"] = state
            char["momentum_value"] = momentum["value"]
            
            # Apply damage reduction (for crash state)
            if "damage_reduction" in effects:
                char["momentum_reduction"] = effects["damage_reduction"]
            
            # Apply damage bonus (for building state)
            if "damage_bonus" in effects:
                char["momentum_damage"] = effects["damage_bonus"]
            
            # Apply trait activation bonus
            if "trait_bonus" in effects:
                char["momentum_trait"] = effects["trait_bonus"]
            
            # Apply stamina discount
            if "stamina_discount" in effects:
                char["momentum_stamina"] = effects["stamina_discount"]
            
            # Apply recovery bonus
            if "recovery" in effects:
                char["momentum_recovery"] = effects["recovery"]
    
    def _apply_comeback_effects(self, team):
        """Apply special comeback effects to a team
        
        Args:
            team: List of team characters
        """
        for char in team:
            # Skip KO'd characters
            if char.get("is_ko", False):
                continue
            
            # Enhanced damage reduction (stacks with crash reduction)
            reduction_bonus = char.get("momentum_reduction", 0) + 10
            char["momentum_reduction"] = reduction_bonus
            
            # Enhanced trait activation
            trait_bonus = char.get("momentum_trait", 0) + 15
            char["momentum_trait"] = trait_bonus
            
            # Apply "comeback" flag for other systems
            char["comeback_active"] = True
    
    def _log_momentum_status(self, team_a_momentum, team_b_momentum, comeback_active, comeback_team):
        """Log momentum status details
        
        Args:
            team_a_momentum: Team A momentum data
            team_b_momentum: Team B momentum data
            comeback_active: Whether comeback is active
            comeback_team: Team with active comeback
        """
        print(f"MOMENTUM UPDATE:")
        print(f"  Team A: {team_a_momentum['state']} ({team_a_momentum['value']})")
        print(f"  Team B: {team_b_momentum['state']} ({team_b_momentum['value']})")
        
        if comeback_active:
            print(f"  COMEBACK ACTIVE for Team {comeback_team}!")
    
    def track_match_result(self, team_a_wins, team_b_wins):
        """Track match result for momentum calculation
        
        Args:
            team_a_wins: Number of Team A wins
            team_b_wins: Number of Team B wins
            
        Returns:
            Dict: Updated score tracking
        """
        # Determine match outcome
        if team_a_wins > team_b_wins:
            result = "team_a_win"
        elif team_b_wins > team_a_wins:
            result = "team_b_win"
        else:
            result = "draw"
        
        # Add to tracking
        self.score_tracking["team_a"].append(result)
        self.score_tracking["team_b"].append(result)
        
        # Keep only last 5 results
        if len(self.score_tracking["team_a"]) > 5:
            self.score_tracking["team_a"] = self.score_tracking["team_a"][-5:]
            self.score_tracking["team_b"] = self.score_tracking["team_b"][-5:]
        
        return self.score_tracking
    
    def calculate_streak_bonus(self, team_key):
        """Calculate momentum bonus based on win/loss streak
        
        Args:
            team_key: Team identifier ("team_a" or "team_b")
            
        Returns:
            float: Streak-based momentum bonus
        """
        # Get recent results
        results = self.score_tracking[team_key]
        
        if not results:
            return 0
        
        # Count consecutive wins/losses
        streak = 1
        streak_type = results[-1]
        
        for i in range(len(results)-2, -1, -1):
            if results[i] == streak_type:
                streak += 1
            else:
                break
        
        # Calculate bonus
        bonus = 0
        
        # Winning streak
        if streak_type == f"{team_key}_win":
            # Building momentum for winners
            bonus = min(3, streak * 0.5)
        else:
            # Crash momentum for losers
            bonus = max(-3, streak * -0.5)
        
        return bonus