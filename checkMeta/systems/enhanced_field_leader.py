"""
META Fantasy League - Enhanced Field Leader System
Handles Field Leader enhancements and specialized abilities
"""

from typing import List, Dict, Any, Tuple

class FieldLeaderEnhancer:
    """System for enhancing Field Leaders with better durability and special traits"""
    
    def __init__(self):
        """Initialize the Field Leader enhancer"""
        self.fl_trait = "field_leader_resilience"
        self.fl_trait_description = "Enhanced durability and resilience as a Field Leader"
        
        # Field Leader HP bonus percentage
        self.fl_hp_bonus = 25  # 25% bonus HP
        
        # Field Leader stamina bonus percentage
        self.fl_stamina_bonus = 20  # 20% bonus stamina
        
        # Field Leader exclusive traits
        self.fl_exclusive_traits = [
            "field_leader_resilience",
            "tactical_genius",
            "rallying_presence",
            "strategic_vision"
        ]
    
    def enhance_field_leaders(self, team_a, team_b) -> Tuple[List, List]:
        """Enhance Field Leaders on both teams
        
        This function applies specialized enhancements to Field Leaders,
        making them more durable and giving them special traits.
        
        Args:
            team_a: List of team A characters
            team_b: List of team B characters
            
        Returns:
            Tuple: Enhanced team A and team B
        """
        # Create deep copies to avoid modifying originals
        team_a_enhanced = [char.copy() for char in team_a]
        team_b_enhanced = [char.copy() for char in team_b]
        
        # Apply enhancements to team A
        self._enhance_team_field_leader(team_a_enhanced)
        
        # Apply enhancements to team B
        self._enhance_team_field_leader(team_b_enhanced)
        
        return team_a_enhanced, team_b_enhanced
    
    def _enhance_team_field_leader(self, team):
        """Enhance the Field Leader of a team
        
        Args:
            team: List of team characters
        """
        # Find the Field Leader
        field_leader = None
        for char in team:
            if char.get("role") == "FL":
                field_leader = char
                break
        
        # If no Field Leader found, nothing to enhance
        if not field_leader:
            return
        
        # Apply HP enhancement
        base_hp = field_leader.get("HP", 100)
        enhanced_hp = base_hp * (1 + self.fl_hp_bonus / 100.0)
        field_leader["HP"] = enhanced_hp
        
        # Apply stamina enhancement
        base_stamina = field_leader.get("stamina", 100)
        enhanced_stamina = base_stamina * (1 + self.fl_stamina_bonus / 100.0)
        field_leader["stamina"] = enhanced_stamina
        
        # Add Field Leader resilience trait if not present
        if "traits" not in field_leader:
            field_leader["traits"] = []
            
        if self.fl_trait not in field_leader["traits"]:
            field_leader["traits"].append(self.fl_trait)
        
        # Apply team-specific trait enhancement
        self._apply_team_trait_enhancement(field_leader, team)
    
    def _apply_team_trait_enhancement(self, field_leader, team):
        """Apply team-specific trait enhancement to Field Leader
        
        Args:
            field_leader: Field Leader character
            team: List of team characters
        """
        # Count number of each role in the team
        role_counts = {}
        for char in team:
            role = char.get("role", "Unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Determine team composition type
        operations_roles = ["VG", "EN"]
        intel_roles = ["RG", "GO", "PO", "SV"]
        
        operations_count = sum(role_counts.get(role, 0) for role in operations_roles)
        intel_count = sum(role_counts.get(role, 0) for role in intel_roles)
        
        # Apply specialized bonus based on team composition
        if operations_count > intel_count:
            # Operations-heavy team - tactical leader
            self._add_tactical_leader_bonus(field_leader)
        elif intel_count > operations_count:
            # Intelligence-heavy team - strategic leader
            self._add_strategic_leader_bonus(field_leader)
        else:
            # Balanced team - balanced leader
            self._add_balanced_leader_bonus(field_leader)
    
    def _add_tactical_leader_bonus(self, field_leader):
        """Add tactical leader bonuses for operations-focused teams
        
        Args:
            field_leader: Field Leader character
        """
        # Enhance STR and DUR attributes
        field_leader["aSTR"] = min(10, field_leader.get("aSTR", 5) + 1)
        field_leader["aDUR"] = min(10, field_leader.get("aDUR", 5) + 1)
        
        # Add tactical traits if needed
        tactical_traits = ["tactical", "shield"]
        for trait in tactical_traits:
            if trait not in field_leader.get("traits", []):
                field_leader["traits"].append(trait)
    
    def _add_strategic_leader_bonus(self, field_leader):
        """Add strategic leader bonuses for intelligence-focused teams
        
        Args:
            field_leader: Field Leader character
        """
        # Enhance FS and WIL attributes
        field_leader["aFS"] = min(10, field_leader.get("aFS", 5) + 1)
        field_leader["aWIL"] = min(10, field_leader.get("aWIL", 5) + 1)
        
        # Add strategic traits if needed
        strategic_traits = ["genius", "tactical"]
        for trait in strategic_traits:
            if trait not in field_leader.get("traits", []):
                field_leader["traits"].append(trait)
    
    def _add_balanced_leader_bonus(self, field_leader):
        """Add balanced leader bonuses for balanced teams
        
        Args:
            field_leader: Field Leader character
        """
        # Enhance LDR and DUR attributes
        field_leader["aLDR"] = min(10, field_leader.get("aLDR", 5) + 1)
        field_leader["aRES"] = min(10, field_leader.get("aRES", 5) + 1)
        
        # Add balanced traits if needed
        balanced_traits = ["tactical", "healing"]
        for trait in balanced_traits:
            if trait not in field_leader.get("traits", []):
                field_leader["traits"].append(trait)
    
    def handle_field_leader_substitution(self, team):
        """Handle Field Leader substitution when original FL is KO'd
        
        Args:
            team: List of team characters
            
        Returns:
            dict: Substitution results
        """
        # Find current Field Leader
        current_fl = None
        for char in team:
            if char.get("role") == "FL":
                current_fl = char
                break
        
        # If no Field Leader or not KO'd, no substitution needed
        if not current_fl or not current_fl.get("is_ko", False):
            return {"substitution": False}
        
        # Find best substitute based on Leadership attribute
        best_substitute = None
        highest_ldr = -1
        
        for char in team:
            # Skip KO'd characters and current FL
            if char.get("is_ko", False) or char == current_fl:
                continue
                
            ldr = char.get("aLDR", 0)
            if ldr > highest_ldr:
                highest_ldr = ldr
                best_substitute = char
        
        # If no suitable substitute, return failure
        if not best_substitute:
            return {"substitution": False, "reason": "No suitable substitute"}
        
        # Perform substitution
        # 1. Mark current FL as no longer FL
        current_fl["original_role"] = current_fl["role"]
        current_fl["role"] = current_fl["role"] + "-KO"
        
        # 2. Mark substitute as acting FL
        best_substitute["original_role"] = best_substitute["role"]
        best_substitute["role"] = "FL-SUB"
        
        # 3. Apply partial FL bonuses to substitute
        self._apply_substitute_bonuses(best_substitute)
        
        return {
            "substitution": True,
            "original_fl": current_fl["name"],
            "substitute": best_substitute["name"],
            "substitute_original_role": best_substitute["original_role"]
        }
    
    def _apply_substitute_bonuses(self, substitute):
        """Apply partial Field Leader bonuses to substitute
        
        Args:
            substitute: Substitute character
        """
        # Apply reduced HP bonus (50% of normal FL bonus)
        substitute["HP"] = min(100, substitute["HP"] * (1 + self.fl_hp_bonus / 200.0))
        
        # Apply reduced stamina bonus (50% of normal FL bonus)
        substitute["stamina"] = min(100, substitute["stamina"] * (1 + self.fl_stamina_bonus / 200.0))
        
        # Add temporary FL trait
        if "traits" not in substitute:
            substitute["traits"] = []
            
        if self.fl_trait not in substitute["traits"]:
            substitute["traits"].append("emergency_leadership")
            
        # Apply emergency leadership bonuses
        substitute["aLDR"] = min(10, substitute.get("aLDR", 5) + 1)