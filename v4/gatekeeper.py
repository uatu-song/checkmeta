"""
META Fantasy League Simulator - Enhanced Gatekeeper
Validation system for ensuring simulation integrity
"""

import os
import logging
import datetime
from typing import Dict, List, Any, Optional

class EnhancedGatekeeper:
    """Enhanced validation system for META League Simulator"""
    
    def __init__(self, config, registry):
        """Initialize the gatekeeper
        
        Args:
            config: Configuration manager
            registry: System registry
        """
        self.config = config
        self.registry = registry
        self.errors = []
        self.warnings = []
        self.logger = logging.getLogger("system.gatekeeper")
        
    def validate_system_dependencies(self) -> None:
        """Validate that all system dependencies are properly registered"""
        systems = self.registry.get_systems()
        
        for name, system in systems.items():
            for dep in system.dependencies:
                if dep not in systems:
                    self.errors.append(f"System '{name}' depends on unregistered system '{dep}'")
    
    def validate_data_integrity(self) -> None:
        """Validate data files integrity"""
        # Check if data loader is available
        data_loader = self.registry.get("data_loader")
        if not data_loader or not self.registry.is_active("data_loader"):
            self.errors.append("Data loader system not available or not active")
            return
            
        # Validate team data structure
        try:
            # Get day 1 for validation
            day_number = 1
            teams = data_loader.load_lineups(day_number)
            
            for team_id, chars in teams.items():
                # Must have exactly 8 active players
                active_chars = [c for c in chars if c.get("is_active", True)]
                required_count = self.config.get("simulation.teams_per_match", 8)
                
                if len(active_chars) != required_count:
                    self.errors.append(f"Team {team_id} has {len(active_chars)} active characters, required {required_count}")
        except Exception as e:
            self.errors.append(f"Error validating team data: {e}")
        
        # Validate division setup
        try:
            divisions = data_loader.load_divisions()
            
            # Check if we have both required divisions
            undercurrent = self.config.get("divisions.undercurrent", "undercurrent")
            overlay = self.config.get("divisions.overlay", "overlay")
            
            undercurrent_teams = [t for t, d in divisions.items() if d.lower() == undercurrent.lower()]
            overlay_teams = [t for t, d in divisions.items() if d.lower() == overlay.lower()]
            
            if not undercurrent_teams:
                self.errors.append(f"No teams found in {undercurrent} division")
            
            if not overlay_teams:
                self.errors.append(f"No teams found in {overlay} division")
            
            # Verify minimum teams for matches
            matches_per_day = self.config.get("simulation.matches_per_day", 5)
            
            if len(undercurrent_teams) < matches_per_day:
                self.errors.append(f"Not enough teams in {undercurrent} division for {matches_per_day} matches per day")
            
            if len(overlay_teams) < matches_per_day:
                self.errors.append(f"Not enough teams in {overlay} division for {matches_per_day} matches per day")
        except Exception as e:
            self.errors.append(f"Error validating division data: {e}")
    
    def validate_config_consistency(self) -> None:
        """Validate configuration consistency"""
        # Check required files exist
        for key, path in self.config.config_data.get("paths", {}).items():
            if key.endswith('_file') and not os.path.exists(path):
                self.errors.append(f"Config file path '{key}' points to non-existent file: {path}")
        
        # Check configuration schema
        schema_errors = self.config.validate_all()
        for error in schema_errors:
            self.errors.append(error)
    
    def validate_stockfish(self) -> None:
        """Validate Stockfish configuration if enabled"""
        if self.config.get("features.use_stockfish", False):
            stockfish_path = self.config.get("paths.stockfish_path")
            
            if not stockfish_path:
                self.warnings.append("Stockfish enabled but path not set")
                return
                
            if not os.path.exists(stockfish_path):
                self.errors.append(f"Stockfish path invalid: {stockfish_path}")
    
    def run_pre_simulation_checks(self) -> bool:
        """Run all checks that should pass before simulation starts
        
        Returns:
            bool: True if checks passed
        """
        self.errors = []
        self.warnings = []
        
        self.logger.info("Running pre-simulation checks")
        
        # Run checks
        self.validate_system_dependencies()
        self.validate_config_consistency()
        self.validate_stockfish()
        
        # Only run data checks if registry has data_loader
        if self.registry.get("data_loader"):
            self.validate_data_integrity()
        
        # Log results
        if self.errors:
            self.logger.error("\n[ENHANCED GATEKEEPER BLOCKED SIMULATION]")
            for err in self.errors:
                self.logger.error(f"🚫 {err}")
            
            if self.warnings:
                self.logger.warning("\nWARNINGS:")
                for warn in self.warnings:
                    self.logger.warning(f"⚠️ {warn}")
                    
            return False
        elif self.warnings:
            self.logger.warning("\n[ENHANCED GATEKEEPER PASSED WITH WARNINGS]")
            for warn in self.warnings:
                self.logger.warning(f"⚠️ {warn}")
            self.logger.info("Simulation can proceed, but please address warnings.")
            return True
        else:
            self.logger.info("✅ Enhanced Gatekeeper: All checks passed. Simulation ready.")
            return True