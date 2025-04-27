"""
META Fantasy League Simulator - Buffered Damage System
Handles damage calculation and application with fairness
"""

from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from config import get_config

class BufferedDamageSystem:
    """System for handling damage with buffered application for fairness"""
    
    def __init__(self):
        """Initialize the buffered damage system"""
        self.config = get_config()
        self.damage_buffer = defaultdict(list)
        self.ko_buffer = defaultdict(list)
        self.healing_buffer = defaultdict(list)
        
        # Get damage parameters from config
        self.base_damage_reduction = self.config.simulation.get("base_damage_reduction", 35)
        self.max_damage_reduction = self.config.simulation.get("max_damage_reduction", 75)
        self.max_damage_per_hit = self.config.simulation.get("max_damage_per_hit", 30)
    
    def clear_buffers(self):
        """Clear all damage buffers"""
        self.damage_buffer.clear()
        self.ko_buffer.clear()
        self.healing_buffer.clear()
    
    def queue_damage(self, target_id, source_id, amount, damage_type="normal", context=None):
        """Queue damage to be applied later
        
        Args:
            target_id: Target character ID
            source_id: Source character ID
            amount: Damage amount
            damage_type: Type of damage
            context: Additional context
            
        Returns:
            bool: Success status
        """
        # Cap damage at maximum
        amount = min(amount, self.max_damage_per_hit)
        
        # Create damage entry
        damage_entry = {
            "source_id": source_id,
            "amount": amount,
            "type": damage_type,
            "context": context or {}
        }
        
        # Add to buffer
        self.damage_buffer[target_id].append(damage_entry)
        return True
    
    def queue_healing(self, target_id, source_id, amount, healing_type="normal", context=None):
        """Queue healing to be applied later
        
        Args:
            target_id: Target character ID
            source_id: Source character ID
            amount: Healing amount
            healing_type: Type of healing
            context: Additional context
            
        Returns:
            bool: Success status
        """
        # Create healing entry
        healing_entry = {
            "source_id": source_id,
            "amount": amount,
            "type": healing_type,
            "context": context or {}
        }
        
        # Add to buffer
        self.healing_buffer[target_id].append(healing_entry)
        return True
    
    def queue_ko(self, target_id, source_id, ko_type="damage", context=None):
        """Queue knockout to be applied later
        
        Args:
            target_id: Target character ID
            source_id: Source character ID
            ko_type: Type of knockout
            context: Additional context
            
        Returns:
            bool: Success status
        """
        # Create KO entry
        ko_entry = {
            "source_id": source_id,
            "type": ko_type,
            "context": context or {}
        }
        
        # Add to buffer
        self.ko_buffer[target_id].append(ko_entry)
        return True
    
    def apply_buffered_damage(self, teams):
        """Apply all buffered damage to characters
        
        Args:
            teams: Dictionary of team characters
            
        Returns:
            dict: Damage application results
        """
        results = {
            "damage_applied": [],
            "kos_applied": [],
            "healing_applied": []
        }
        
        # First apply all healing
        for target_id, healing_list in self.healing_buffer.items():
            target = self._find_character(teams, target_id)
            
            if not target:
                continue
            
            # Apply healing
            for healing in healing_list:
                self._apply_healing(target, healing)
                results["healing_applied"].append({
                    "target_id": target_id,
                    "target_name": target.get("name", "Unknown"),
                    "source_id": healing["source_id"],
                    "amount": healing["amount"],
                    "type": healing["type"]
                })
        
        # Then apply all damage
        for target_id, damage_list in self.damage_buffer.items():
            target = self._find_character(teams, target_id)
            
            if not target:
                continue
            
            # Apply damage
            for damage in damage_list:
                applied = self._apply_damage(target, damage)
                results["damage_applied"].append({
                    "target_id": target_id,
                    "target_name": target.get("name", "Unknown"),
                    "source_id": damage["source_id"],
                    "amount": damage["amount"],
                    "reduced_amount": applied["reduced_amount"],
                    "type": damage["type"]
                })
        
        # Finally apply all KOs
        for target_id, ko_list in self.ko_buffer.items():
            target = self._find_character(teams, target_id)
            
            if not target:
                continue
            
            # Apply KO
            for ko in ko_list:
                if not target.get("is_ko", False):
                    target["is_ko"] = True
                    target["HP"] = 0
                    
                    results["kos_applied"].append({
                        "target_id": target_id,
                        "target_name": target.get("name", "Unknown"),
                        "source_id": ko["source_id"],
                        "type": ko["type"]
                    })
        
        # Clear buffers
        self.clear_buffers()
        
        return results
    
    def _find_character(self, teams, char_id):
        """Find character by ID across teams
        
        Args:
            teams: Dictionary of team characters
            char_id: Character ID to find
            
        Returns:
            dict: Character or None
        """
        for team_chars in teams.values():
            for char in team_chars:
                if char.get("id") == char_id:
                    return char
        
        return None
    
    def _apply_damage(self, character, damage):
        """Apply damage to a character
        
        Args:
            character: Character to damage
            damage: Damage entry
            
        Returns:
            dict: Damage application results
        """
        # Calculate damage reduction
        reduction = self.base_damage_reduction
        
        # Apply attribute bonuses to reduction
        dur_val = character.get("aDUR", 5)
        res_val = character.get("aRES", 5)
        
        if dur_val > 5:
            reduction += (dur_val - 5) * 3  # 3% per point above 5
        
        if res_val > 5:
            reduction += (res_val - 5) * 2  # 2% per point above 5
        
        # Cap reduction
        reduction = min(reduction, self.max_damage_reduction)
        
        # Calculate reduced damage
        reduced_amount = damage["amount"] * (1 - reduction / 100.0)
        reduced_amount = max(1, reduced_amount)  # Minimum 1 damage
        
        # Apply to HP
        current_hp = character.get("HP", 100)
        new_hp = max(0, current_hp - reduced_amount)
        character["HP"] = new_hp
        
        # Check for KO
        if new_hp == 0 and not character.get("is_ko", False):
            character["is_ko"] = True
            
            # Add to KO buffer
            self.queue_ko(
                character.get("id", "unknown"),
                damage["source_id"],
                "damage",
                damage["context"]
            )
        
        # Return results
        return {
            "original_amount": damage["amount"],
            "reduced_amount": reduced_amount,
            "new_hp": new_hp,
            "is_ko": character.get("is_ko", False)
        }
    
    def _apply_healing(self, character, healing):
        """Apply healing to a character
        
        Args:
            character: Character to heal
            healing: Healing entry
            
        Returns:
            dict: Healing application results
        """
        # Skip if character is KO'd
        if character.get("is_ko", False):
            return {"applied": False, "reason": "character_ko"}
        
        # Apply healing
        current_hp = character.get("HP", 0)
        new_hp = min(100, current_hp + healing["amount"])
        character["HP"] = new_hp
        
        # Return results
        return {
            "amount": healing["amount"],
            "applied": True,
            "new_hp": new_hp
        }