"""
META Fantasy League Simulator - Match Summary Stamina Integration
================================================================

This module integrates the stamina system with match summaries and implements
stamina event emission for full simulation tracking.
"""

import os
import json
import datetime
import logging
from typing import Dict, List, Any, Optional

# Import system components
from system_base import SystemBase
from system_registry import SystemRegistry
from config_manager import ConfigurationManager
from stamina_system import StaminaSystem

class MatchSummaryStaminaIntegration:
    """Integrates stamina system with match summaries and handles event emission"""
    
    def __init__(self, config, registry):
        """Initialize the integration"""
        self.config = config
        self.registry = registry
        self.logger = logging.getLogger("MatchSummaryStamina")
        
        # Ensure required systems are available
        self.stamina_system = registry.get("stamina_system")
        if not self.stamina_system:
            raise ValueError("Stamina system not available in registry")
        
        self.event_system = registry.get("event_system")
        if not self.event_system:
            self.logger.warning("Event system not available, event emission disabled")
        
        self.match_visualizer = registry.get("match_visualizer")
        if not self.match_visualizer:
            self.logger.warning("Match visualizer not available, visualization disabled")
    
    def enhance_match_summary(self, match_results: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance match results with stamina information
        
        Args:
            match_results: The match results dictionary
            
        Returns:
            Enhanced match results with stamina information
        """
        if "character_results" not in match_results:
            self.logger.warning("No character results found in match results")
            return match_results
        
        # Create a copy to avoid modifying the original
        enhanced_results = match_results.copy()
        
        # Add stamina section to summary
        enhanced_results["stamina_summary"] = self._create_stamina_summary(match_results)
        
        # Enhance character results with stamina details
        enhanced_results["character_results"] = self._enhance_character_results(
            match_results["character_results"]
        )
        
        # Add stamina-specific key events
        enhanced_results["key_events"] = self._extract_key_stamina_events(match_results)
        
        return enhanced_results
    
    def _create_stamina_summary(self, match_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of stamina status for the match
        
        Args:
            match_results: The match results
            
        Returns:
            Stamina summary
        """
        stamina_logs = match_results.get("stamina_logs", [])
        character_results = match_results.get("character_results", [])
        
        # Group by team
        team_a_chars = [c for c in character_results if c.get("team") == "A"]
        team_b_chars = [c for c in character_results if c.get("team") == "B"]
        
        # Calculate team averages
        team_a_avg = sum(c.get("stamina", 0) for c in team_a_chars) / max(len(team_a_chars), 1)
        team_b_avg = sum(c.get("stamina", 0) for c in team_b_chars) / max(len(team_b_chars), 1)
        
        # Count fatigue effects by team
        team_a_effects = {
            "minor_fatigue": sum(1 for c in team_a_chars if any(e.startswith("stamina:minor_fatigue") for e in c.get("effects", []))),
            "moderate_fatigue": sum(1 for c in team_a_chars if any(e.startswith("stamina:moderate_fatigue") for e in c.get("effects", []))),
            "severe_fatigue": sum(1 for c in team_a_chars if any(e.startswith("stamina:severe_fatigue") for e in c.get("effects", [])))
        }
        
        team_b_effects = {
            "minor_fatigue": sum(1 for c in team_b_chars if any(e.startswith("stamina:minor_fatigue") for e in c.get("effects", []))),
            "moderate_fatigue": sum(1 for c in team_b_chars if any(e.startswith("stamina:moderate_fatigue") for e in c.get("effects", []))),
            "severe_fatigue": sum(1 for c in team_b_chars if any(e.startswith("stamina:severe_fatigue") for e in c.get("effects", [])))
        }
        
        # Find highest and lowest stamina characters
        if team_a_chars:
            highest_a = max(team_a_chars, key=lambda c: c.get("stamina", 0))
            lowest_a = min(team_a_chars, key=lambda c: c.get("stamina", 0))
        else:
            highest_a = lowest_a = {"character_name": "N/A", "stamina": 0}
            
        if team_b_chars:
            highest_b = max(team_b_chars, key=lambda c: c.get("stamina", 0))
            lowest_b = min(team_b_chars, key=lambda c: c.get("stamina", 0))
        else:
            highest_b = lowest_b = {"character_name": "N/A", "stamina": 0}
        
        # Count stamina-related events
        event_counts = {}
        for log in stamina_logs:
            event_type = log.get("reason", "unknown")
            if event_type not in event_counts:
                event_counts[event_type] = 0
            event_counts[event_type] += 1
        
        # Determine which team managed stamina better
        stamina_advantage = "A" if team_a_avg > team_b_avg else "B" if team_b_avg > team_a_avg else "Even"
        
        return {
            "team_a_avg_stamina": round(team_a_avg, 1),
            "team_b_avg_stamina": round(team_b_avg, 1),
            "team_a_effects": team_a_effects,
            "team_b_effects": team_b_effects,
            "highest_stamina_a": {
                "character_name": highest_a.get("character_name", "Unknown"),
                "stamina": highest_a.get("stamina", 0)
            },
            "lowest_stamina_a": {
                "character_name": lowest_a.get("character_name", "Unknown"),
                "stamina": lowest_a.get("stamina", 0)
            },
            "highest_stamina_b": {
                "character_name": highest_b.get("character_name", "Unknown"),
                "stamina": highest_b.get("stamina", 0)
            },
            "lowest_stamina_b": {
                "character_name": lowest_b.get("character_name", "Unknown"),
                "stamina": lowest_b.get("stamina", 0)
            },
            "event_counts": event_counts,
            "stamina_advantage": stamina_advantage
        }
    
    def _enhance_character_results(self, character_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance character results with detailed stamina information
        
        Args:
            character_results: The character results list
            
        Returns:
            Enhanced character results
        """
        enhanced_results = []
        
        for character in character_results:
            # Create a copy of the character result
            enhanced_char = character.copy()
            
            # Skip if no stamina data
            if "stamina" not in enhanced_char:
                enhanced_results.append(enhanced_char)
                continue
            
            # Add stamina details
            stamina = enhanced_char.get("stamina", 0)
            
            # Calculate stamina status
            if stamina <= 20:
                stamina_status = "Severe Fatigue"
            elif stamina <= 40:
                stamina_status = "Moderate Fatigue"
            elif stamina <= 60:
                stamina_status = "Minor Fatigue"
            else:
                stamina_status = "Normal"
            
            # Extract stamina log if available
            stamina_log = enhanced_char.get("stamina_log", [])
            
            # Calculate key metrics if log available
            if stamina_log:
                initial_stamina = stamina_log[0].get("stamina", 100) if stamina_log else 100
                stamina_drained = initial_stamina - stamina
                highest_cost = max(
                    (log.get("cost", 0) for log in stamina_log if "cost" in log), 
                    default=0
                )
                highest_cost_event = next(
                    (log.get("reason", "unknown") for log in stamina_log 
                     if log.get("cost", 0) == highest_cost),
                    "unknown"
                )
                recovery_gained = sum(
                    log.get("recovery", 0) for log in stamina_log if "recovery" in log
                )
            else:
                initial_stamina = 100
                stamina_drained = 0
                highest_cost = 0
                highest_cost_event = "unknown"
                recovery_gained = 0
            
            # Calculate trait constraint
            trait_constraint = "None"
            for effect in enhanced_char.get("effects", []):
                if effect == "stamina:trait_restriction":
                    trait_constraint = "Reduced Chance"
                elif effect == "stamina:trait_lockout":
                    trait_constraint = "High-Cost Locked"
            
            # Add detailed stamina section
            enhanced_char["stamina_details"] = {
                "status": stamina_status,
                "initial": initial_stamina,
                "final": stamina,
                "drained": round(stamina_drained, 1),
                "drained_percent": round((stamina_drained / initial_stamina) * 100, 1) if initial_stamina else 0,
                "highest_cost": highest_cost,
                "highest_cost_event": highest_cost_event,
                "recovery_gained": round(recovery_gained, 1),
                "trait_constraint": trait_constraint
            }
            
            enhanced_results.append(enhanced_char)
        
        return enhanced_results
    
    def _extract_key_stamina_events(self, match_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key stamina events from the match
        
        Args:
            match_results: The match results
            
        Returns:
            List of key stamina events
        """
        stamina_logs = match_results.get("stamina_logs", [])
        key_events = []
        
        # Process all stamina logs to find key events
        for log in stamina_logs:
            character_id = log.get("character_id", "unknown")
            character_name = log.get("character_name", "Unknown")
            team_id = log.get("team_id", "unknown")
            reason = log.get("reason", "unknown")
            turn = log.get("turn", 0)
            
            # Check if this is a significant event
            significant = False
            event_description = ""
            
            # High cost events
            if "cost" in log and log["cost"] >= 5.0:
                significant = True
                event_description = f"{character_name} expended {log['cost']} stamina for {reason}"
            
            # Threshold crossing events (only detect if we have stamina_remaining)
            if "stamina_remaining" in log:
                stamina = log["stamina_remaining"]
                
                # Check if crossed thresholds
                for threshold in [60, 40, 20]:
                    # Check if this log entry crossed a threshold
                    # We'd need the previous state to do this perfectly, but can approximate
                    if stamina <= threshold and "cost" in log and stamina + log["cost"] > threshold:
                        significant = True
                        
                        if threshold == 60:
                            effect = "minor fatigue"
                        elif threshold == 40:
                            effect = "moderate fatigue"
                        elif threshold == 20:
                            effect = "severe fatigue"
                            
                        event_description = f"{character_name} entered {effect} state with {stamina} stamina remaining"
            
            # Add to key events if significant
            if significant:
                key_events.append({
                    "type": "stamina",
                    "character_id": character_id,
                    "character_name": character_name,
                    "team_id": team_id,
                    "turn": turn,
                    "description": event_description
                })
        
        return key_events
    
    def emit_stamina_analytics_event(self, match_id: str, enhanced_results: Dict[str, Any]) -> bool:
        """Emit stamina analytics events for the match
        
        Args:
            match_id: The match ID
            enhanced_results: The enhanced match results
            
        Returns:
            True if events were emitted, False otherwise
        """
        if not self.event_system:
            self.logger.warning("Event system not available, cannot emit events")
            return False
        
        try:
            # Emit overall stamina analytics event
            self.event_system.emit({
                "type": "stamina_analytics",
                "match_id": match_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "team_a_avg": enhanced_results["stamina_summary"]["team_a_avg_stamina"],
                "team_b_avg": enhanced_results["stamina_summary"]["team_b_avg_stamina"],
                "team_a_fatigue_count": sum(enhanced_results["stamina_summary"]["team_a_effects"].values()),
                "team_b_fatigue_count": sum(enhanced_results["stamina_summary"]["team_b_effects"].values()),
                "stamina_advantage": enhanced_results["stamina_summary"]["stamina_advantage"]
            })
            
            # Emit individual character stamina events
            for character in enhanced_results["character_results"]:
                if "stamina_details" in character:
                    self.event_system.emit({
                        "type": "character_stamina_analytics",
                        "match_id": match_id,
                        "character_id": character.get("character_id", "unknown"),
                        "character_name": character.get("character_name", "Unknown"),
                        "team_id": character.get("team_id", "unknown"),
                        "team": character.get("team", "Unknown"),
                        "timestamp": datetime.datetime.now().isoformat(),
                        "initial_stamina": character["stamina_details"]["initial"],
                        "final_stamina": character["stamina_details"]["final"],
                        "stamina_drained": character["stamina_details"]["drained"],
                        "drained_percent": character["stamina_details"]["drained_percent"],
                        "highest_cost": character["stamina_details"]["highest_cost"],
                        "highest_cost_event": character["stamina_details"]["highest_cost_event"],
                        "status": character["stamina_details"]["status"],
                        "trait_constraint": character["stamina_details"]["trait_constraint"]
                    })
            
            return True
        except Exception as e:
            self.logger.error(f"Error emitting stamina analytics events: {e}")
            return False
    
    def generate_match_stamina_report(self, match_id: str, enhanced_results: Dict[str, Any]) -> Optional[str]:
        """Generate a stamina-focused match report
        
        Args:
            match_id: The match ID
            enhanced_results: The enhanced match results
            
        Returns:
            Path to the generated report, or None if generation failed
        """
        if not self.match_visualizer:
            self.logger.warning("Match visualizer not available, cannot generate report")
            return None
        
        try:
            # Create stamina-focused report data
            report_data = {
                "match_id": match_id,
                "team_a_name": enhanced_results.get("team_a_name", "Team A"),
                "team_b_name": enhanced_results.get("team_b_name", "Team B"),
                "stamina_summary": enhanced_results.get("stamina_summary", {}),
                "character_results": enhanced_results.get("character_results", []),
                "key_stamina_events": [e for e in enhanced_results.get("key_events", []) 
                                      if e.get("type") == "stamina"]
            }
            
            # Generate report using match visualizer
            if hasattr(self.match_visualizer, "generate_stamina_report"):
                # If the visualizer has a dedicated stamina report method
                report_path = self.match_visualizer.generate_stamina_report(report_data)
            else:
                # Fall back to standard report method
                report_path = self._generate_fallback_stamina_report(match_id, report_data)
            
            return report_path
        except Exception as e:
            self.logger.error(f"Error generating stamina report: {e}")
            return None
    
    def _generate_fallback_stamina_report(self, match_id: str, report_data: Dict[str, Any]) -> str:
        """Generate a fallback stamina report if the visualizer doesn't support it
        
        Args:
            match_id: The match ID
            report_data: The report data
            
        Returns:
            Path to the generated report
        """
        # Create report directory
        reports_dir = self.config.get("paths.reports_dir", "results/reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate report file path
        report_path = os.path.join(reports_dir, f"{match_id}_stamina_report.md")
        
        # Generate markdown report
        with open(report_path, 'w') as f:
            # Header
            f.write(f"# Stamina Report: {report_data['team_a_name']} vs {report_data['team_b_name']}\n\n")
            
            # Overall summary
            summary = report_data["stamina_summary"]
            f.write("## Overall Stamina Summary\n\n")
            f.write(f"**Team {report_data['team_a_name']}**: {summary['team_a_avg_stamina']} average stamina\n")
            f.write(f"**Team {report_data['team_b_name']}**: {summary['team_b_avg_stamina']} average stamina\n")
            f.write(f"**Stamina Advantage**: Team {summary['stamina_advantage']}\n\n")
            
            # Fatigue effects
            f.write("### Fatigue Effects\n\n")
            f.write("| Team | Minor Fatigue | Moderate Fatigue | Severe Fatigue |\n")
            f.write("|------|--------------|------------------|----------------|\n")
            f.write(f"| {report_data['team_a_name']} | {summary['team_a_effects']['minor_fatigue']} | {summary['team_a_effects']['moderate_fatigue']} | {summary['team_a_effects']['severe_fatigue']} |\n")
            f.write(f"| {report_data['team_b_name']} | {summary['team_b_effects']['minor_fatigue']} | {summary['team_b_effects']['moderate_fatigue']} | {summary['team_b_effects']['severe_fatigue']} |\n\n")
            
            # Stamina extremes
            f.write("### Stamina Extremes\n\n")
            f.write(f"**Highest Stamina {report_data['team_a_name']}**: {summary['highest_stamina_a']['character_name']} ({summary['highest_stamina_a']['stamina']})\n")
            f.write(f"**Lowest Stamina {report_data['team_a_name']}**: {summary['lowest_stamina_a']['character_name']} ({summary['lowest_stamina_a']['stamina']})\n")
            f.write(f"**Highest Stamina {report_data['team_b_name']}**: {summary['highest_stamina_b']['character_name']} ({summary['highest_stamina_b']['stamina']})\n")
            f.write(f"**Lowest Stamina {report_data['team_b_name']}**: {summary['lowest_stamina_b']['character_name']} ({summary['lowest_stamina_b']['stamina']})\n\n")
            
            # Event counts
            f.write("### Stamina Event Counts\n\n")
            f.write("| Event Type | Count |\n")
            f.write("|------------|-------|\n")
            for event_type, count in summary.get("event_counts", {}).items():
                f.write(f"| {event_type} | {count} |\n")
            f.write("\n")
            
            # Character details
            f.write("## Character Stamina Details\n\n")
            f.write("| Character | Team | Final Stamina | Status | Drained % | Highest Cost Action |\n")
            f.write("|-----------|------|--------------|--------|-----------|--------------------|\n")
            
            for character in report_data["character_results"]:
                if "stamina_details" in character:
                    details = character["stamina_details"]
                    f.write(f"| {character['character_name']} | {character['team']} | {details['final']} | {details['status']} | {details['drained_percent']}% | {details['highest_cost_event']} ({details['highest_cost']}) |\n")
            f.write("\n")
            
            # Key events
            f.write("## Key Stamina Events\n\n")
            for event in report_data.get("key_stamina_events", []):
                f.write(f"- **Round {event['turn']}**: {event['description']}\n")
        
        return report_path
    
    def integrate_with_day_summary(self, day_number: int, day_results: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate stamina data with day summary
        
        Args:
            day_number: The day number
            day_results: The day results
            
        Returns:
            Enhanced day results with stamina data
        """
        # Create a copy to avoid modifying the original
        enhanced_day_results = day_results.copy()
        
        # Extract match results
        matches = enhanced_day_results.get("matches", [])
        
        # Aggregate stamina data across all matches
        team_stamina = {}
        team_effects = {}
        character_stamina = {}
        
        for match in matches:
            # Get team IDs
            team_a_id = match.get("team_a_id", "unknown")
            team_b_id = match.get("team_b_id", "unknown")
            
            # Initialize if not already present
            if team_a_id not in team_stamina:
                team_stamina[team_a_id] = []
            if team_b_id not in team_stamina:
                team_stamina[team_b_id] = []
            if team_a_id not in team_effects:
                team_effects[team_a_id] = {"minor": 0, "moderate": 0, "severe": 0}
            if team_b_id not in team_effects:
                team_effects[team_b_id] = {"minor": 0, "moderate": 0, "severe": 0}
            
            # Extract stamina data from match
            if "stamina_summary" in match:
                # Add team averages
                team_stamina[team_a_id].append(match["stamina_summary"]["team_a_avg_stamina"])
                team_stamina[team_b_id].append(match["stamina_summary"]["team_b_avg_stamina"])
                
                # Add team effects
                team_effects[team_a_id]["minor"] += match["stamina_summary"]["team_a_effects"]["minor_fatigue"]
                team_effects[team_a_id]["moderate"] += match["stamina_summary"]["team_a_effects"]["moderate_fatigue"]
                team_effects[team_a_id]["severe"] += match["stamina_summary"]["team_a_effects"]["severe_fatigue"]
                
                team_effects[team_b_id]["minor"] += match["stamina_summary"]["team_b_effects"]["minor_fatigue"]
                team_effects[team_b_id]["moderate"] += match["stamina_summary"]["team_b_effects"]["moderate_fatigue"]
                team_effects[team_b_id]["severe"] += match["stamina_summary"]["team_b_effects"]["severe_fatigue"]
            
            # Extract character stamina data
            for character in match.get("character_results", []):
                if "stamina_details" not in character:
                    continue
                
                character_id = character.get("character_id", "unknown")
                
                # Initialize if not already present
                if character_id not in character_stamina:
                    character_stamina[character_id] = {
                        "character_name": character.get("character_name", "Unknown"),
                        "team_id": character.get("team_id", "unknown"),
                        "team": character.get("team", "Unknown"),
                        "matches": 0,
                        "initial_stamina": 0,
                        "final_stamina": 0,
                        "statuses": []
                    }
                
                # Add match data
                character_stamina[character_id]["matches"] += 1
                character_stamina[character_id]["initial_stamina"] = character["stamina_details"]["initial"]
                character_stamina[character_id]["final_stamina"] = character["stamina_details"]["final"]
                character_stamina[character_id]["statuses"].append(character["stamina_details"]["status"])
        
        # Calculate team averages
        team_stamina_avg = {}
        for team_id, stamina_values in team_stamina.items():
            if stamina_values:
                team_stamina_avg[team_id] = sum(stamina_values) / len(stamina_values)
            else:
                team_stamina_avg[team_id] = 0
        
        # Add stamina summary to day results
        enhanced_day_results["stamina_summary"] = {
            "team_stamina_avg": team_stamina_avg,
            "team_effects": team_effects,
            "character_stamina": character_stamina
        }
        
        # Return enhanced results
        return enhanced_day_results
    
    def generate_day_stamina_report(self, day_number: int, enhanced_day_results: Dict[str, Any]) -> Optional[str]:
        """Generate a stamina-focused day report
        
        Args:
            day_number: The day number
            enhanced_day_results: The enhanced day results
            
        Returns:
            Path to the generated report, or None if generation failed
        """
        # Create report directory
        reports_dir = self.config.get("paths.reports_dir", "results/reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate report file path
        report_path = os.path.join(reports_dir, f"day{day_number}_stamina_report.md")
        
        try:
            # Generate markdown report
            with open(report_path, 'w') as f:
                # Header
                f.write(f"# Day {day_number} Stamina Report\n\n")
                
                # Date and weekday
                f.write(f"**Date**: {enhanced_day_results.get('date', 'Unknown')}\n")
                f.write(f"**Weekday**: {enhanced_day_results.get('weekday', 'Unknown')}\n\n")
                
                # Team stamina overview
                f.write("## Team Stamina Overview\n\n")
                f.write("| Team | Average Stamina | Minor Fatigue Events | Moderate Fatigue Events | Severe Fatigue Events |\n")
                f.write("|------|----------------|----------------------|-------------------------|------------------------|\n")
                
                team_data = enhanced_day_results.get("teams", {})
                stamina_summary = enhanced_day_results.get("stamina_summary", {})
                team_stamina_avg = stamina_summary.get("team_stamina_avg", {})
                team_effects = stamina_summary.get("team_effects", {})
                
                for team_id, avg_stamina in sorted(team_stamina_avg.items(), key=lambda x: x[1], reverse=True):
                    team_name = team_data.get(team_id, {}).get("name", team_id)
                    effects = team_effects.get(team_id, {"minor": 0, "moderate": 0, "severe": 0})
                    
                    f.write(f"| {team_name} | {avg_stamina:.1f} | {effects['minor']} | {effects['moderate']} | {effects['severe']} |\n")
                
                f.write("\n")
                
                # Character stamina
                f.write("## Character Stamina Status\n\n")
                f.write("| Character | Team | Final Stamina | Status |\n")
                f.write("|-----------|------|--------------|--------|\n")
                
                character_stamina = stamina_summary.get("character_stamina", {})
                
                # Sort by final stamina
                sorted_chars = sorted(
                    character_stamina.items(), 
                    key=lambda x: x[1]["final_stamina"], 
                    reverse=True
                )
                
                for char_id, char_data in sorted_chars:
                    # Get most severe status
                    statuses = char_data.get("statuses", [])
                    status = "Normal"
                    if "Severe Fatigue" in statuses:
                        status = "Severe Fatigue"
                    elif "Moderate Fatigue" in statuses:
                        status = "Moderate Fatigue"
                    elif "Minor Fatigue" in statuses:
                        status = "Minor Fatigue"
                    
                    team_name = team_data.get(char_data.get("team_id", "unknown"), {}).get("name", char_data.get("team", "Unknown"))
                    
                    f.write(f"| {char_data['character_name']} | {team_name} | {char_data['final_stamina']:.1f} | {status} |\n")
                
                f.write("\n")
                
                # Match summary
                f.write("## Match Stamina Summary\n\n")
                
                for i, match in enumerate(enhanced_day_results.get("matches", []), 1):
                    team_a_name = match.get("team_a_name", "Team A")
                    team_b_name = match.get("team_b_name", "Team B")
                    
                    f.write(f"### Match {i}: {team_a_name} vs {team_b_name}\n\n")
                    
                    if "stamina_summary" in match:
                        summary = match["stamina_summary"]
                        
                        f.write(f"**Team {team_a_name}**: {summary['team_a_avg_stamina']} average stamina\n")
                        f.write(f"**Team {team_b_name}**: {summary['team_b_avg_stamina']} average stamina\n")
                        f.write(f"**Stamina Advantage**: Team {summary['stamina_advantage']}\n\n")
                        
                        # Key events
                        key_events = [e for e in match.get("key_events", []) if e.get("type") == "stamina"]
                        
                        if key_events:
                            f.write("**Key Stamina Events**:\n\n")
                            for event in key_events:
                                f.write(f"- **Round {event['turn']}**: {event['description']}\n")
                            f.write("\n")
                    else:
                        f.write("No stamina data available for this match.\n\n")
            
            return report_path
        except Exception as e:
            self.logger.error(f"Error generating day stamina report: {e}")
            return None


# Example usage
def integrate_with_day_1_match_summaries(config_path=None):
    """Example of integrating with Day 1 match summaries"""
    # Initialize configuration
    config = ConfigurationManager(config_path)
    
    # Create registry
    registry = SystemRegistry()
    
    # Initialize stamina system
    stamina_system = StaminaSystem(config, registry)
    registry.register("stamina_system", stamina_system)
    
    # Initialize mock event system
    class MockEventSystem:
        def emit(self, event):
            print(f"Event emitted: {event['type']}")
            return True
    
    registry.register("event_system", MockEventSystem())
    
    # Initialize mock match visualizer
    class MockMatchVisualizer:
        def generate_match_reports(self, match_data):
            print(f"Generated match report for {match_data['match_id']}")
            return ["reports/mock_report.md"]
    
    registry.register("match_visualizer", MockMatchVisualizer())
    
    # Initialize integration
    integration = MatchSummaryStaminaIntegration(config, registry)
    
    # Create mock match results
    match_results = {
        "match_id": "day1_match1_team_a_vs_team_b",
        "day": 1,
        "match_number": 1,
        "team_a_name": "Team Alpha",
        "team_b_name": "Team Beta",
        "team_a_id": "team_a",
        "team_b_id": "team_b",
        "result": "win",  # Team A won
        "winning_team": "Team Alpha",
        "character_results": [
            # Team A characters
            {
                "character_id": "char_a1",
                "character_name": "Alice",
                "team": "A",
                "team_id": "team_a",
                "was_active": True,
                "is_ko": False,
                "HP": 80,
                "stamina": 65,
                "result": "win",
                "effects": []
            },
            {
                "character_id": "char_a2",
                "character_name": "Bob",
                "team": "A",
                "team_id": "team_a",
                "was_active": True,
                "is_ko": False,
                "HP": 70,
                "stamina": 45,
                "result": "win",
                "effects": ["stamina:minor_fatigue", "stamina:trait_restriction"]
            },
            # Team B characters
            {
                "character_id": "char_b1",
                "character_name": "Charlie",
                "team": "B",
                "team_id": "team_b",
                "was_active": True,
                "is_ko": False,
                "HP": 60,
                "stamina": 35,
                "result": "loss",
                "effects": ["stamina:minor_fatigue", "stamina:moderate_fatigue"]
            },
            {
                "character_id": "char_b2",
                "character_name": "Diana",
                "team": "B",
                "team_id": "team_b",
                "was_active": True,
                "is_ko": True,
                "HP": 0,
                "stamina": 15,
                "result": "loss",
                "effects": ["stamina:minor_fatigue", "stamina:moderate_fatigue", "stamina:severe_fatigue"]
            }
        ],
        "stamina_logs": [
            # Sample logs
            {
                "character_id": "char_a1",
                "character_name": "Alice",
                "team_id": "team_a",
                "turn": 3,
                "cost": 5.0,
                "reason": "trait_activation:power_strike",
                "stamina_remaining": 75.0
            },
            {
                "character_id": "char_b2",
                "character_name": "Diana",
                "team_id": "team_b",
                "turn": 5,
                "cost": 8.0,
                "reason": "convergence_target",
                "stamina_remaining": 35.0
            }
        ]
    }
    
    # Enhance match summary
    enhanced_results = integration.enhance_match_summary(match_results)
    
    # Emit stamina analytics events
    integration.emit_stamina_analytics_event(
        enhanced_results["match_id"], 
        enhanced_results
    )
    
    # Generate stamina report
    report_path = integration.generate_match_stamina_report(
        enhanced_results["match_id"], 
        enhanced_results
    )
    
    print(f"Generated stamina report: {report_path}")
    
    # Create mock day results
    day_results = {
        "day": 1,
        "date": "2025-04-29",
        "weekday": "Monday",
        "matches": [enhanced_results],
        "teams": {
            "team_a": {"name": "Team Alpha", "division": "A"},
            "team_b": {"name": "Team Beta", "division": "B"}
        }
    }
    
    # Integrate with day summary
    enhanced_day_results = integration.integrate_with_day_summary(1, day_results)
    
    # Generate day stamina report
    day_report_path = integration.generate_day_stamina_report(1, enhanced_day_results)
    
    print(f"Generated day stamina report: {day_report_path}")
    
    return enhanced_day_results

if __name__ == "__main__":
    # Run example
    integrate_with_day_1_match_summaries()
