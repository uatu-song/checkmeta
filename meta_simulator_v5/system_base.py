"""
META Fantasy League Simulator - System Base
Base class for all simulator subsystems
"""

import logging
from typing import Dict, List, Any, Optional

class SystemBase:
    """Base class for all simulator systems"""
    
    def __init__(self, name: str, registry=None):
        """Initialize the system
        
        Args:
            name: System name
            registry: Optional system registry
        """
        self.name = name
        self.registry = registry
        self.active = False
        self.logger = logging.getLogger(f"system.{name}")
        self.dependencies = []
    
    def activate(self) -> bool:
        """Activate the system
        
        Returns:
            bool: Activation success
        """
        if self.active:
            return True
            
        self.logger.info(f"Activating {self.name} system")
        
        # Check dependencies if registry is available
        if self.registry:
            for dep in self.dependencies:
                if not self.registry.is_active(dep):
                    self.logger.error(f"Cannot activate {self.name}: Dependency {dep} not active")
                    return False
        
        try:
            # Call implementation-specific activation
            result = self._activate_implementation()
            
            if result:
                self.active = True
                self.logger.info(f"{self.name} system activated successfully")
            else:
                self.logger.error(f"Failed to activate {self.name} system")
            
            return result
        except Exception as e:
            self.logger.error(f"Error activating {self.name}: {e}")
            return False
    
    def _activate_implementation(self) -> bool:
        """Implementation-specific activation logic
        
        Returns:
            bool: Activation success
        """
        # Override in subclass
        return True
    
    def deactivate(self) -> bool:
        """Deactivate the system
        
        Returns:
            bool: Deactivation success
        """
        if not self.active:
            return True
            
        self.logger.info(f"Deactivating {self.name} system")
        
        try:
            # Call implementation-specific deactivation
            result = self._deactivate_implementation()
            
            if result:
                self.active = False
                self.logger.info(f"{self.name} system deactivated successfully")
            else:
                self.logger.error(f"Failed to deactivate {self.name} system")
            
            return result
        except Exception as e:
            self.logger.error(f"Error deactivating {self.name}: {e}")
            return False
    
    def _deactivate_implementation(self) -> bool:
        """Implementation-specific deactivation logic
        
        Returns:
            bool: Deactivation success
        """
        # Override in subclass if needed
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of the system
        
        Returns:
            dict: System status
        """
        return {
            "name": self.name,
            "active": self.active,
            "dependencies": self.dependencies
        }