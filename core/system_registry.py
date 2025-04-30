"""
META Fantasy League Simulator - System Registry
Central registry for all simulator systems with dependency tracking
"""

import logging
from typing import Dict, List, Any, Optional, Type
from collections import defaultdict

# Import base system class
from system_base import SystemBase

class SystemRegistry:
    """Central registry for all simulator systems"""
    
    def __init__(self):
        """Initialize the system registry"""
        self._systems = {}
        self._dependencies = defaultdict(list)
        self._activation_status = {}
        self.logger = logging.getLogger("system.registry")
    
    def register(self, name: str, system: SystemBase, dependencies: Optional[List[str]] = None) -> SystemBase:
        """Register a system with its dependencies
        
        Args:
            name: System name
            system: System instance
            dependencies: List of dependency system names
            
        Returns:
            SystemBase: Registered system
        """
        # Register system
        self._systems[name] = system
        
        # Store dependencies
        deps = dependencies or []
        self._dependencies[name] = deps
        
        # Set initial activation status
        self._activation_status[name] = False
        
        # Set dependencies on system
        system.dependencies = deps
        system.registry = self
        
        self.logger.info(f"Registered system: {name} with dependencies: {deps}")
        
        return system
    
    def activate(self, name: str) -> bool:
        """Activate a system and its dependencies
        
        Args:
            name: Name of system to activate
            
        Returns:
            bool: Activation success
        """
        if name not in self._systems:
            self.logger.error(f"Cannot activate unknown system: {name}")
            return False
            
        # Skip if already active
        if self._activation_status.get(name, False):
            return True
            
        self.logger.info(f"Activating system and dependencies: {name}")
        
        # Activate dependencies first
        for dep in self._dependencies[name]:
            if not self._activation_status.get(dep, False):
                dep_success = self.activate(dep)
                if not dep_success:
                    self.logger.error(f"Failed to activate dependency {dep} for {name}")
                    return False
        
        # Activate the system
        system = self._systems[name]
        success = system.activate()
        
        if success:
            self._activation_status[name] = True
            self.logger.info(f"Successfully activated system: {name}")
        else:
            self.logger.error(f"Failed to activate system: {name}")
        
        return success
    
    def deactivate(self, name: str) -> bool:
        """Deactivate a system
        
        Args:
            name: Name of system to deactivate
            
        Returns:
            bool: Deactivation success
        """
        if name not in self._systems:
            self.logger.error(f"Cannot deactivate unknown system: {name}")
            return False
            
        # Skip if already inactive
        if not self._activation_status.get(name, False):
            return True
            
        self.logger.info(f"Deactivating system: {name}")
        
        # Check for dependent systems
        dependents = []
        for system_name, deps in self._dependencies.items():
            if name in deps and self._activation_status.get(system_name, False):
                dependents.append(system_name)
        
        # Deactivate dependents first
        for dependent in dependents:
            dep_success = self.deactivate(dependent)
            if not dep_success:
                self.logger.error(f"Failed to deactivate dependent {dependent} for {name}")
                return False
        
        # Deactivate the system
        system = self._systems[name]
        success = system.deactivate()
        
        if success:
            self._activation_status[name] = False
            self.logger.info(f"Successfully deactivated system: {name}")
        else:
            self.logger.error(f"Failed to deactivate system: {name}")
        
        return success
    
    def get(self, name: str) -> Optional[SystemBase]:
        """Get a registered system
        
        Args:
            name: System name
            
        Returns:
            SystemBase: System instance or None if not found
        """
        return self._systems.get(name)
    
    def is_active(self, name: str) -> bool:
        """Check if a system is active
        
        Args:
            name: System name
            
        Returns:
            bool: True if system is active
        """
        return self._activation_status.get(name, False)
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get activation status of all systems
        
        Returns:
            dict: Status report
        """
        return {
            name: {
                "active": status,
                "dependencies": self._dependencies[name]
            }
            for name, status in self._activation_status.items()
        }
    
    def get_systems(self) -> Dict[str, SystemBase]:
        """Get all registered systems
        
        Returns:
            dict: All registered systems
        """
        return self._systems.copy()