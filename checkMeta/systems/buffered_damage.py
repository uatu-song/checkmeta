"""
META Fantasy League - Buffered Damage System
Handles damage calculations with buffering to prevent first-mover advantage
"""

from typing import List, Dict, Any

class BufferedDamageSystem:
    """System for buffering damage calculations to ensure fairness"""
    
    def __init__(self):
        """Initialize the buffered damage system"""
        self.damage_buffer = []
    
    def buffer_calculations(self, convergences, base_reduction, max_reduction, damage_cap=None):
        """Buffer damage calculations for later application
        
        This function takes convergence data, calculates resulting damage
        but doesn't apply it immediately. Instead, it returns a buffer of
        damage events that can be applied later, after all calculations are done.
        
        Args:
            convergences: List of convergence data
            base_reduction: Base damage reduction percentage
            max_reduction: Maximum damage reduction percentage
            damage_cap: Optional cap on maximum damage per hit
            
        Returns:
            List: Buffered damage events ready for application
        """
        # Clear existing buffer
        self.damage_buffer = []
        
        # Calculate damage for each convergence
        for conv in convergences:
            # Extract relevant data
            winner = conv.get("winner")
            loser = conv.get("loser")
            base_damage = conv.get("base_damage", 0)
            
            if not winner or not loser or base_damage <= 0:
                continue
            
            # Calculate reduction based on loser's traits and stats
            reduction = self._calculate_damage_reduction(loser, base_reduction, max_reduction)
            
            # Apply reduction
            reduced_damage = max(1, base_damage * (1 - reduction/100.0))
            
            # Apply damage cap if specified
            if damage_cap:
                reduced_damage = min(reduced_damage, damage_cap)
            
            # Add to buffer
            self.damage_buffer.append({
                "target": loser,
                "source": winner,
                "base_damage": base_damage,
                "damage": reduced_damage,
                "reduction": reduction
            })
        
        return self.damage_buffer
    
    def process_convergences(self, convergences, base_reduction, max_reduction, damage_cap=None):
        """Process convergences with buffered damage calculations
        
        This function processes convergence data and prepares it with
        calculated damage, ready for application.
        
        Args:
            convergences: List of convergence data
            base_reduction: Base damage reduction percentage
            max_reduction: Maximum damage reduction percentage
            damage_cap: Optional cap on maximum damage per hit
            
        Returns:
            List: Processed convergences with calculated damage
        """
        processed = []
        
        for conv in convergences:
            # Extract key information
            winner = conv.get("winner")
            loser = conv.get("loser")
            base_damage = conv.get("base_damage", 0)
            
            if not winner or not loser or base_damage <= 0:
                continue
            
            # Calculate reduction based on loser's traits and stats
            reduction = self._calculate_damage_reduction(loser, base_reduction, max_reduction)
            
            # Apply reduction
            reduced_damage = max(1, base_damage * (1 - reduction/100.0))
            
            # Apply damage cap if specified
            if damage_cap:
                reduced_damage = min(reduced_damage, damage_cap)
            
            # Create processed convergence
            processed_conv = conv.copy()  # Copy original data
            processed_conv.update({
                "reduction": reduction,
                "reduced_damage": reduced_damage
            })
            
            processed.append(processed_conv)
        
        return processed
    
    def apply_buffered_damage(self, character, damage_event):
        """Apply a buffered damage event to a character
        
        Args:
            character: Character to apply damage to
            damage_event: Damage event data
            
        Returns:
            dict: Result of damage application
        """
        # Apply damage to HP
        damage = damage_event.get("damage", 0)
        current_hp = character.get("HP", 100)
        new_hp = max(0, current_hp - damage)
        character["HP"] = new_hp
        
        # Track damage in stats
        character.setdefault("rStats", {})
        character["rStats"]["rDS"] = character["rStats"].get("rDS", 0) + damage
        
        # Update source character stats
        source = damage_event.get("source")
        if source:
            source.setdefault("rStats", {})
            source["rStats"]["rDD"] = source["rStats"].get("rDD", 0) + damage
        
        # Apply stamina damage if HP is depleted
        stamina_damage = 0
        is_ko = False
        
        if new_hp == 0:
            # Calculate stamina damage (30% of overflow)
            stamina_damage = (damage - current_hp) * 0.3
            
            # Apply to stamina
            current_stamina = character.get("stamina", 100)
            new_stamina = max(0, current_stamina - stamina_damage)
            character["stamina"] = new_stamina
            
            # Check for KO
            if new_stamina == 0:
                character["is_ko"] = True
                is_ko = True
                
                # If source character exists, update KO stats
                if source:
                    source.setdefault("rStats", {})
                    source["rStats"]["rOTD"] = source["rStats"].get("rOTD", 0) + 1
        
        return {
            "damage": damage,
            "stamina_damage": stamina_damage,
            "new_hp": new_hp,
            "is_ko": is_ko
        }
    
    def _calculate_damage_reduction(self, character, base_reduction, max_reduction):
        """Calculate damage reduction percentage for a character
        
        Args:
            character: Character to calculate reduction for
            base_reduction: Base damage reduction percentage
            max_reduction: Maximum damage reduction percentage
            
        Returns:
            float: Calculated damage reduction percentage
        """
        # Start with base reduction
        reduction = base_reduction
        
        # Add durability bonus
        dur_bonus = max(0, character.get("aDUR", 5) - 5) * 3  # +3% per point above 5
        
        # Add resilience bonus
        res_bonus = max(0, character.get("aRES", 5) - 5) * 2  # +2% per point above 5
        
        # Apply attribute bonuses
        reduction += (dur_bonus + res_bonus)
        
        # Apply trait-based reduction
        for trait_name in character.get("traits", []):
            trait_bonus = self._get_trait_reduction(trait_name)
            reduction += trait_bonus
        
        # Check for Field Leader Resilience trait
        if "field_leader_resilience" in character.get("traits", []) and character.get("role") == "FL":
            reduction += 15  # Additional 15% for Field Leaders
        
        # Apply current state modifiers
        momentum_state = character.get("momentum_state", "stable")
        if momentum_state == "crash":
            # Extra protection in crash state
            reduction += 10
        
        # Cap reduction at maximum
        reduction = min(reduction, max_reduction)
        
        return reduction
    
    def _get_trait_reduction(self, trait_name):
        """Get damage reduction from a trait
        
        Args:
            trait_name: Name of trait
            
        Returns:
            float: Damage reduction percentage
        """
        # Map traits to reduction values
        trait_reductions = {
            "armor": 25,
            "shield": 30,
            "healing": 10,
            "tactical": 5,
            "field_leader_resilience": 40
        }
        
        return trait_reductions.get(trait_name, 0)