"""
Event System for META Fantasy League Simulator
Provides a pub/sub model for systems to emit and listen for events
"""

import time
import logging
import json
import os
from typing import Dict, List, Any, Callable, Optional, Set, Tuple
from collections import defaultdict

from system_base import SystemBase

class EventSystem(SystemBase):
    """
    Event system for emitting and subscribing to events across the simulator
    
    Key features:
    - Publish/subscribe model for loose coupling between systems
    - Event filtering based on conditions
    - Event logging for analytics
    - Stats tracking event hooks
    """
    
    def __init__(self, config):
        """Initialize the event system"""
        super().__init__(config)
        self.name = "event_system"
        self.logger = logging.getLogger("META_SIMULATOR.EventSystem")
        
        # Event handlers dictionary (event_name -> list of handlers)
        self.handlers = defaultdict(list)
        
        # Cache for commonly used systems
        self.stat_tracker = None
        
        # Event log storage
        self.event_log = []
        self.event_log_path = self.config.get("paths.event_logs_dir", "logs/events")
        os.makedirs(self.event_log_path, exist_ok=True)
        
        # Track rStats events separately
        self.rstats_events = defaultdict(int)
        
        # Initialize state
        self.active = False
        self.logger.info("Event system initialized")
    
    def activate(self):
        """Activate the event system"""
        self.active = True
        self.logger.info("Event system activated")
        return True
    
    def deactivate(self):
        """Deactivate the event system"""
        self.active = False
        self.logger.info("Event system deactivated")
        return True
    
    def is_active(self):
        """Check if the event system is active"""
        return self.active
    
    def register_handler(self, event_name: str, handler: Callable, filter_func: Optional[Callable] = None) -> None:
        """
        Register a handler for an event
        
        Args:
            event_name: The name of the event to listen for
            handler: Callback function to execute when event is emitted
            filter_func: Optional function to filter events
        """
        self.handlers[event_name].append({
            "handler": handler,
            "filter": filter_func
        })
        self.logger.debug(f"Registered handler for event: {event_name}")
    
    def unregister_handler(self, event_name: str, handler: Callable) -> bool:
        """
        Unregister a handler for an event
        
        Args:
            event_name: The name of the event
            handler: The handler function to remove
            
        Returns:
            bool: True if handler was removed, False otherwise
        """
        if event_name not in self.handlers:
            return False
        
        initial_count = len(self.handlers[event_name])
        self.handlers[event_name] = [h for h in self.handlers[event_name] if h["handler"] != handler]
        
        removed = initial_count > len(self.handlers[event_name])
        if removed:
            self.logger.debug(f"Unregistered handler for event: {event_name}")
        
        return removed
    
    def emit(self, event_name: str, data: Dict[str, Any]) -> int:
        """
        Emit an event
        
        Args:
            event_name: The name of the event to emit
            data: Data associated with the event
            
        Returns:
            int: Number of handlers that processed the event
        """
        if not self.active:
            self.logger.warning(f"Event system is not active, ignoring event: {event_name}")
            return 0
        
        # Add metadata to event
        event_data = data.copy()
        event_data["_event_name"] = event_name
        event_data["_timestamp"] = time.time()
        
        # Log the event
        self._log_event(event_name, event_data)
        
        # Track rStats events
        if event_name.startswith("rstats."):
            stat_name = event_name[7:]  # Remove "rstats." prefix
            self.rstats_events[stat_name] += 1
        
        # Special handling for specific events
        if event_name == "convergence_triggered" or event_name == "assist_given":
            self._process_rstats_event(event_name, event_data)
        
        # Get handlers for this event
        handlers = self.handlers.get(event_name, [])
        if not handlers:
            return 0
        
        # Call each handler if it passes the filter
        handler_count = 0
        for handler_info in handlers:
            handler = handler_info["handler"]
            filter_func = handler_info["filter"]
            
            # Apply filter if one exists
            if filter_func and not filter_func(event_data):
                continue
            
            try:
                handler(event_data)
                handler_count += 1
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_name}: {e}")
        
        return handler_count
    
    def _log_event(self, event_name: str, event_data: Dict[str, Any]) -> None:
        """Log an event for analytics"""
        # Only store essentials to save space
        compact_data = {
            "event": event_name,
            "timestamp": event_data["_timestamp"],
            "data": self._compact_event_data(event_data)
        }
        
        # Add to in-memory log (limited size)
        self.event_log.append(compact_data)
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-1000:]
        
        # Log high-priority events to file
        if self.config.get("events.detailed_logging", False):
            self._write_event_to_log(compact_data)
    
    def _compact_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a compact version of event data for logging"""
        # Extract only essential fields from complex objects
        compact = {}
        
        # Process each field
        for key, value in event_data.items():
            # Skip metadata fields
            if key.startswith("_"):
                continue
                
            # Handle character objects
            if key == "character" and isinstance(value, dict):
                compact["character_id"] = value.get("id", "unknown")
                compact["character_name"] = value.get("name", "Unknown")
            # Handle target character objects
            elif key == "target" and isinstance(value, dict):
                compact["target_id"] = value.get("id", "unknown")
                compact["target_name"] = value.get("name", "Unknown")
            # Handle match context
            elif key == "match_context" and isinstance(value, dict):
                compact["match_id"] = value.get("match_id", "unknown")
                compact["round"] = value.get("round", 0)
            # Simple values
            elif isinstance(value, (str, int, float, bool)) or value is None:
                compact[key] = value
            # Skip complex objects
            else:
                compact[key] = str(type(value))
        
        return compact
    
    def _write_event_to_log(self, event_data: Dict[str, Any]) -> None:
        """Write an event to the log file"""
        try:
            timestamp = time.strftime("%Y%m%d", time.localtime(event_data["timestamp"]))
            log_file = os.path.join(self.event_log_path, f"events_{timestamp}.jsonl")
            
            with open(log_file, "a") as f:
                f.write(json.dumps(event_data) + "\n")
        except Exception as e:
            self.logger.error(f"Error writing event to log: {e}")
    
    def _process_rstats_event(self, event_name: str, event_data: Dict[str, Any]) -> None:
        """Process events specifically for rStats tracking"""
        # Lazy load stat_tracker if needed
        if not self.stat_tracker:
            from system_registry import SystemRegistry
            registry = SystemRegistry()
            self.stat_tracker = registry.get("stat_tracker")
        
        if not self.stat_tracker:
            return
        
        character = event_data.get("character")
        if not character:
            return
        
        # Process convergence_triggered event
        if event_name == "convergence_triggered":
            # Update rStats for convergence initiator
            self.stat_tracker.update_character_stat(
                character, 
                "CONVERGENCES_INITIATED", 
                1, 
                "add"
            )
            
            target = event_data.get("target")
            if target:
                # Update rStats for convergence target
                self.stat_tracker.update_character_stat(
                    target,
                    "CONVERGENCES_RECEIVED",
                    1,
                    "add"
                )
        
        # Process assist_given event
        elif event_name == "assist_given":
            # Update rStats for character giving assist
            self.stat_tracker.update_character_stat(
                character,
                "ASSISTS",
                1,
                "add"
            )
            
            # Mark this character as a supporter in the match context
            match_context = event_data.get("match_context")
            if match_context:
                if "supporter_ids" not in match_context:
                    match_context["supporter_ids"] = set()
                
                match_context["supporter_ids"].add(character.get("id"))
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get statistics about events processed"""
        return {
            "total_events": len(self.event_log),
            "rstats_events": dict(self.rstats_events),
            "active": self.active
        }
    
    def save_persistent_data(self) -> None:
        """Save event statistics for persistence"""
        try:
            stats_file = os.path.join(self.event_log_path, "event_stats.json")
            with open(stats_file, "w") as f:
                json.dump({
                    "rstats_events": dict(self.rstats_events),
                    "timestamp": time.time()
                }, f, indent=2)
            self.logger.info("Event statistics saved")
        except Exception as e:
            self.logger.error(f"Error saving event statistics: {e}")
    
    def export_state(self) -> Dict[str, Any]:
        """Export state for backup"""
        return {
            "rstats_events": dict(self.rstats_events),
            "active": self.active,
            "timestamp": time.time()
        }