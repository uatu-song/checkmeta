"""
META Fantasy League - Advanced Feature Manager
Coordinates activation and integration of advanced simulator features
"""

import os
from typing import Dict, Any, List

class AdvancedFeatureManager:
    """Manager for activating and coordinating advanced simulator features"""
    
    def __init__(self, simulator):
        """Initialize the advanced feature manager
        
        Args:
            simulator: Reference to the main simulator instance
        """
        self.simulator = simulator
        self.features = {
            "traits": {"active": False, "module": None},
            "xp": {"active": False, "module": None},
            "stockfish": {"active": False, "module": None},
            "morale": {"active": False, "module": None}
        }
    
    def activate_all_features(self):
        """Activate all advanced features
        
        Returns:
            dict: Activation results
        """
        results = {}
        
        # Activate each feature
        results["traits"] = self.activate_trait_system()
        results["xp"] = self.activate_xp_system()
        results["stockfish"] = self.activate_stockfish()
        results["morale"] = self.activate_morale_system()
        
        # Log activation results
        print("===== Advanced Features Activation Results =====")
        for feature, status in results.items():
            print(f"{feature.capitalize()}: {'✅ Activated' if status else '❌ Failed'}")
        
        return results
    
    def activate_trait_system(self):
        """Activate enhanced trait system
        
        Returns:
            bool: Activation success status
        """
        try:
            from systems.enhanced_trait_system import EnhancedTraitSystem
            
            # Initialize enhanced trait system
            self.features["traits"]["module"] = EnhancedTraitSystem()
            
            # Replace simulator's trait system
            self.simulator.trait_system = self.features["traits"]["module"]
            
            self.features["traits"]["active"] = True
            print("Enhanced Trait System activated")
            return True
        except Exception as e:
            print(f"Error activating Enhanced Trait System: {e}")
            self.features["traits"]["active"] = False
            return False
    
    def activate_xp_system(self):
        """Activate XP progression system
        
        Returns:
            bool: Activation success status
        """
        try:
            from systems.xp_progression_system import XPProgressionSystem
            
            # Initialize XP system
            self.features["xp"]["module"] = XPProgressionSystem()
            
            # Add to simulator
            self.simulator.xp_system = self.features["xp"]["module"]
            
            self.features["xp"]["active"] = True
            print("XP Progression System activated")
            return True
        except Exception as e:
            print(f"Error activating XP Progression System: {e}")
            self.features["xp"]["active"] = False
            return False
    
    def activate_stockfish(self):
        """Activate Stockfish integration
        
        Returns:
            bool: Activation success status
        """
        try:
            from systems.stockfish_integration import StockfishIntegration
            
            # Initialize Stockfish integration
            self.features["stockfish"]["module"] = StockfishIntegration(
                stockfish_path=self.simulator.stockfish_path
            )
            
            # Add to simulator
            self.simulator.stockfish_integration = self.features["stockfish"]["module"]
            self.simulator.stockfish_available = self.features["stockfish"]["module"].stockfish_available
            
            # Replace move selection method
            self.simulator._select_move = self.features["stockfish"]["module"].select_move
            
            self.features["stockfish"]["active"] = True
            print("Stockfish Integration activated")
            return True
        except Exception as e:
            print(f"Error activating Stockfish Integration: {e}")
            self.features["stockfish"]["active"] = False
            return False
    
    def activate_morale_system(self):
        """Activate morale system
        
        Returns:
            bool: Activation success status
        """
        try:
            from systems.morale_system import MoraleSystem
            
            # Initialize morale system
            self.features["morale"]["module"] = MoraleSystem()
            
            # Add to simulator
            self.simulator.morale_system = self.features["morale"]["module"]
            
            # Initialize morale for active teams
            self._initialize_team_morale()
            
            self.features["morale"]["active"] = True
            print("Morale System activated")
            return True
        except Exception as e:
            print(f"Error activating Morale System: {e}")
            self.features["morale"]["active"] = False
            return False
    
    def _initialize_team_morale(self):
        """Initialize morale for all active teams"""
        if not self.features["morale"]["active"]:
            return
        
        # Get all active teams
        for team_id, characters in self.simulator.teams.items():
            count = self.features["morale"]["module"].initialize_character_morale(characters)
            print(f"Initialized morale for {count} characters in team {team_id}")
    
    def get_status_report(self):
        """Get detailed status report of all features
        
        Returns:
            dict: Status report
        """
        report = {
            "features": {},
            "active_count": 0,
            "total_count": len(self.features)
        }
        
        for feature, data in self.features.items():
            # Get module-specific details
            details = {}
            
            if feature == "traits" and data["active"]:
                details["trait_count"] = len(data["module"].traits)
            elif feature == "xp" and data["active"]:
                details["max_level"] = len(data["module"].level_thresholds)
            elif feature == "stockfish" and data["active"]:
                details["stockfish_path"] = data["module"].stockfish_path
            elif feature == "morale" and data["active"]:
                details["morale_levels"] = list(data["module"].morale_thresholds.keys())
            
            # Add to report
            report["features"][feature] = {
                "active": data["active"],
                "details": details
            }
            
            if data["active"]:
                report["active_count"] += 1
        
        # Calculate activation percentage
        report["activation_percentage"] = (report["active_count"] / report["total_count"]) * 100
        
        return report