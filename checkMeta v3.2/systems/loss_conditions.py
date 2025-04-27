"""
META Fantasy League Simulator - Loss Condition System
Handles team loss conditions with balanced criteria
"""

from typing import Dict, List, Any, Optional, Tuple
from config import get_config

class LossConditionSystem:
    """System for handling balanced team loss conditions"""
    
    def __init__(self):
        """Initialize the loss condition system"""
        self.config = get_config()
        
        # Get loss condition thresholds from config
        self.ko_threshold = self.config.simulation.get("ko_threshold", 3)
        self.team_hp_threshold = self.config.simulation.get("team_hp_threshold", 25)
    
    def check_team_loss(self, team):
        """Check if a team has met loss conditions
        
        Args:
            team: Team characters
            
        Returns:
            tuple: (lost, reason, details)
        """
        # Apply all checks
        fl_check = self._check_field_leader_ko(team)
        ko_check = self._check_ko_count(team)
        hp_check = self._check_team_hp(team)
        
        # Aggregate results
        if fl_check[0]:
            return fl_check
        
        if ko_check[0]:
            return ko_check
        
        if hp_check[0]:
            return hp_check
        
        # No loss conditions met
        return (False, None, {})
    
    def _check_field_leader_ko(self, team):
        """Check if Field Leader is knocked out
        
        Args:
            team: Team characters
            
        Returns:
            tuple: (lost, reason, details)
        """
        # Find Field Leader
        field_leader = None
        for char in team:
            if char.get("role") == "FL" and char.get("is_active", True):
                field_leader = char
                break
        
        # Check if Field Leader exists and is KO'd
        if field_leader and field_leader.get("is_ko", False):
            return (
                True,
                "field_leader_ko",
                {"character": field_leader["name"]}
            )
        
        # No Field Leader or not KO'd
        return (False, None, {})
    
    def _check_ko_count(self, team):
        """Check if KO count exceeds threshold
        
        Args:
            team: Team characters
            
        Returns:
            tuple: (lost, reason, details)
        """
        # Count KO'd characters
        ko_count = sum(1 for char in team if char.get("is_ko", False) and char.get("is_active", True))
        
        # Check against threshold
        if ko_count >= self.ko_threshold:
            return (
                True,
                "ko_threshold",
                {"ko_count": ko_count, "threshold": self.ko_threshold}
            )
        
        # Threshold not met
        return (False, None, {})
    
    def _check_team_hp(self, team):
        """Check if team HP is below threshold
        
        Args:
            team: Team characters
            
        Returns:
            tuple: (lost, reason, details)
        """
        # Calculate team HP percentage
        active_chars = [char for char in team if char.get("is_active", True)]
        
        if not active_chars:
            return (True, "no_active_characters", {})
        
        total_hp = sum(char.get("HP", 0) for char in active_chars)
        max_hp = len(active_chars) * 100  # Assuming max HP is 100 per character
        
        hp_percentage = (total_hp / max_hp) * 100 if max_hp > 0 else 0
        
        # Check against threshold
        if hp_percentage <= self.team_hp_threshold:
            return (
                True,
                "team_hp_threshold",
                {"hp_percentage": hp_percentage, "threshold": self.team_hp_threshold}
            )
        
        # Threshold not met
        return (False, None, {})
    
    def get_loss_reason_text(self, reason, details):
        """Get human-readable text for loss reason
        
        Args:
            reason: Loss reason code
            details: Loss details
            
        Returns:
            str: Human-readable loss reason
        """
        if reason == "field_leader_ko":
            return f"Field Leader {details.get('character', 'Unknown')} was knocked out"
        
        elif reason == "ko_threshold":
            return f"Team suffered {details.get('ko_count', 0)} knockouts (threshold: {details.get('threshold', 0)})"
        
        elif reason == "team_hp_threshold":
            return f"Team HP fell to {details.get('hp_percentage', 0):.1f}% (threshold: {details.get('threshold', 0)}%)"
        
        elif reason == "no_active_characters":
            return "No active characters remaining"
        
        return "Unknown loss condition"