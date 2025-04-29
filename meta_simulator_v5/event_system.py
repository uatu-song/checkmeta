"""
META Fantasy League Simulator - Event System
Centralized event dispatching system
"""

import logging
from typing import Dict, List, Any, Callable, Optional
from collections import defaultdict
from system_base import SystemBase

class EventSystem(SystemBase):
    """Centralized event dispatching system"""
    
    def __init__(self, registry=None):
        """Initialize the event system"""
        super().__init__("event_system", registry)
        self.handlers = defaultdict(list)
    
    def _activate_implementation(self) -> bool:
        """Activate the event system"""
        return True
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event type
        
        Args:
            event_type: Event type identifier
            handler: Function to call when event occurs
        """
        if handler not in self.handlers[event_type]:
            self.handlers[event_type].append(handler)
            self.logger.debug(f"Handler subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type
        
        Args:
            event_type: Event type identifier
            handler: Function to unsubscribe
        """
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
            self.logger.debug(f"Handler unsubscribed from event: {event_type}")
    
    def dispatch(self, event_type: str, **kwargs) -> None:
        """Dispatch an event to all handlers
        
        Args:
            event_type: Event type identifier
            **kwargs: Event data
        """
        if event_type not in self.handlers:
            self.logger.debug(f"No handlers for event: {event_type}")
            return
            
        self.logger.debug(f"Dispatching event: {event_type} with {len(self.handlers[event_type])} handlers")
        
        for handler in self.handlers[event_type]:
            try:
                handler(**kwargs)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_type}: {e}")
    
    def get_handler_count(self, event_type: str) -> int:
        """Get number of handlers for an event type
        
        Args:
            event_type: Event type identifier
            
        Returns:
            int: Number of handlers
        """
        return len(self.handlers.get(event_type, []))