"""
System Integrator for META Fantasy League Simulator
Handles system lifecycle management and cross-system communication

Version: 5.1.0 - Guardian Compliant
"""

import os
import json
import logging
import datetime
import importlib
from typing import Dict, List, Any, Optional, Set, Tuple, Type
from collections import defaultdict

class SystemIntegrator:
    """
    System Integrator for META Fantasy League Simulator
    
    Manages system lifecycle, dependencies, and cross-system communications.
    Implements centralized system startup, shutdown, and connection logic.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the system integrator
        
        Args:
            config_path: Path to configuration file
        """
        # Set up logging
        self.logger = logging.getLogger("META_SIMULATOR.SystemIntegrator")
        
        # Load configuration
        self.config = self._load_configuration(config_path)
        
        # Initialize registry
        self.registry = {}
        
        # Track system dependencies
        self.dependencies = {}
        
        # Track system states
        self.system_states = {}
        
        # Configuration for system loading
        self.system_config = self.config.get("systems", {})
        
        # Initialize event system early (needed by all systems)
        self._initialize_event_system()
        
        self.logger.info("System integrator initialized")
    
    def _load_configuration(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            if not os.path.isfile(config_path):
                self.logger.error(f"Configuration file not found: {config_path}")
                return {}
                
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Apply environment-specific overrides if present
            env = os.environ.get("META_ENV", "development")
            env_config_path = os.path.join(os.path.dirname(config_path), f"config.{env}.json")
            
            if os.path.isfile(env_config_path):
                with open(env_config_path, 'r') as f:
                    env_config = json.load(f)
                    
                # Merge configurations
                self._merge_configs(config, env_config)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return {}
    
    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> None:
        """
        Merge configuration dictionaries
        
        Args:
            base_config: Base configuration
            override_config: Override configuration
        """
        for key, value in override_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_configs(base_config[key], value)
            else:
                base_config[key] = value
    
    def _initialize_event_system(self) -> None:
        """Initialize the event system"""
        try:
            # Import event system
            from event.event_system import EventSystem
            
            # Create event system
            event_system = EventSystem(self.config)
            
            # Register in registry
            self.registry["event_system"] = event_system
            
            # Activate event system
            if hasattr(event_system, "activate"):
                event_system.activate()
            
            # Update system state
            self.system_states["event_system"] = {
                "status": "active",
                "initialized_at": datetime.datetime.now().isoformat()
            }
            
            self.logger.info("Event system initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing event system: {e}")
    
    def initialize_all_systems(self) -> bool:
        """
        Initialize all systems specified in configuration
        
        Returns:
            True if all systems initialized successfully, False otherwise
        """
        try:
            # Get list of systems to initialize
            systems_to_init = self.system_config.get("load_at_startup", [])
            
            # Initialize each system
            success = True
            for system_name in systems_to_init:
                if not self.initialize_system(system_name):
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error initializing all systems: {e}")
            return False
    
    def initialize_system(self, system_name: str) -> bool:
        """
        Initialize a specific system
        
        Args:
            system_name: Name of system to initialize
            
        Returns:
            True if system initialized successfully, False otherwise
        """
        try:
            # Check if system already initialized
            if system_name in self.registry:
                self.logger.info(f"System {system_name} already initialized")
                return True
                
            # Get system configuration
            system_info = self.system_config.get("definitions", {}).get(system_name)
            if not system_info:
                self.logger.error(f"System {system_name} not defined in configuration")
                return False
                
            # Check dependencies
            dependencies = system_info.get("dependencies", [])
            for dep in dependencies:
                if dep not in self.registry:
                    # Try to initialize dependency first
                    if not self.initialize_system(dep):
                        self.logger.error(f"Failed to initialize dependency {dep} for system {system_name}")
                        return False
            
            # Get module and class names
            module_path = system_info.get("module")
            class_name = system_info.get("class")
            
            if not module_path or not class_name:
                self.logger.error(f"Invalid configuration for system {system_name}")
                return False
                
            # Import module
            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                self.logger.error(f"Error importing module {module_path}: {e}")
                return False
                
            # Get system class
            if not hasattr(module, class_name):
                self.logger.error(f"Class {class_name} not found in module {module_path}")
                return False
                
            system_class = getattr(module, class_name)
            
            # Create system instance
            try:
                # Prepare args for system constructor
                args = []
                kwargs = {"config": self.config}
                
                # Add registry reference if needed
                if system_info.get("needs_registry", False):
                    kwargs["registry"] = self.get_registry_reference()
                
                # Add specific dependencies if needed
                for dep in dependencies:
                    if dep in self.registry:
                        # Determine if dependency should be added as positional arg
                        if system_info.get("dependency_as_kwarg", True):
                            kwargs[dep] = self.registry[dep]
                        else:
                            args.append(self.registry[dep])
                
                # Create instance
                system_instance = system_class(*args, **kwargs)
                
            except Exception as e:
                self.logger.error(f"Error creating instance of {class_name}: {e}")
                return False
                
            # Register system
            self.registry[system_name] = system_instance
            
            # Store dependencies
            self.dependencies[system_name] = dependencies
            
            # Activate system
            if hasattr(system_instance, "activate"):
                try:
                    system_instance.activate()
                except Exception as e:
                    self.logger.warning(f"Error activating system {system_name}: {e}")
            
            # Update system state
            self.system_states[system_name] = {
                "status": "active",
                "initialized_at": datetime.datetime.now().isoformat(),
                "dependencies": dependencies,
                "class": class_name,
                "module": module_path
            }
            
            # Emit system initialization event
            self._emit_system_event("system_initialized", {
                "system_name": system_name,
                "dependencies": dependencies,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            self.logger.info(f"System {system_name} initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing system {system_name}: {e}")
            return False
    
    def shutdown_system(self, system_name: str) -> bool:
        """
        Shutdown a specific system
        
        Args:
            system_name: Name of system to shutdown
            
        Returns:
            True if system shutdown successfully, False otherwise
        """
        try:
            # Check if system is initialized
            if system_name not in self.registry:
                self.logger.warning(f"System {system_name} not initialized")
                return True
                
            # Check if other systems depend on this one
            dependents = self._get_dependent_systems(system_name)
            if dependents:
                self.logger.warning(f"Cannot shutdown system {system_name}, other systems depend on it: {dependents}")
                return False
                
            # Get system instance
            system = self.registry[system_name]
            
            # Deactivate system
            if hasattr(system, "deactivate"):
                try:
                    system.deactivate()
                except Exception as e:
                    self.logger.warning(f"Error deactivating system {system_name}: {e}")
            
            # Save persistent data if needed
            if hasattr(system, "save_persistent_data"):
                try:
                    system.save_persistent_data()
                except Exception as e:
                    self.logger.warning(f"Error saving persistent data for system {system_name}: {e}")
            
            # Remove from registry
            del self.registry[system_name]
            
            # Update system state
            if system_name in self.system_states:
                self.system_states[system_name]["status"] = "shutdown"
                self.system_states[system_name]["shutdown_at"] = datetime.datetime.now().isoformat()
            
            # Emit system shutdown event
            self._emit_system_event("system_shutdown", {
                "system_name": system_name,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            self.logger.info(f"System {system_name} shutdown successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error shutting down system {system_name}: {e}")
            return False
    
    def shutdown_all_systems(self) -> bool:
        """
        Shutdown all initialized systems
        
        Returns:
            True if all systems shutdown successfully, False otherwise
        """
        try:
            # Get list of systems to shutdown (in reverse dependency order)
            shutdown_order = self._get_shutdown_order()
            
            # Shutdown each system
            success = True
            for system_name in shutdown_order:
                if not self.shutdown_system(system_name):
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error shutting down all systems: {e}")
            return False
    
    def restart_system(self, system_name: str) -> bool:
        """
        Restart a specific system
        
        Args:
            system_name: Name of system to restart
            
        Returns:
            True if system restarted successfully, False otherwise
        """
        try:
            # Shutdown system
            if not self.shutdown_system(system_name):
                return False
                
            # Initialize system
            if not self.initialize_system(system_name):
                return False
                
            # Emit system restart event
            self._emit_system_event("system_restarted", {
                "system_name": system_name,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            self.logger.info(f"System {system_name} restarted successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error restarting system {system_name}: {e}")
            return False
    
    def get_system(self, system_name: str) -> Any:
        """
        Get a system instance
        
        Args:
            system_name: Name of system to get
            
        Returns:
            System instance or None if not found
        """
        return self.registry.get(system_name)
    
    def get_registry_reference(self) -> Dict[str, Any]:
        """
        Get a reference to the registry
        
        Returns:
            Registry reference
        """
        return self.registry
    
    def get_system_status(self, system_name: str) -> Dict[str, Any]:
        """
        Get status of a specific system
        
        Args:
            system_name: Name of system to check
            
        Returns:
            System status dictionary
        """
        if system_name not in self.system_states:
            return {"status": "unknown"}
            
        return self.system_states[system_name]
    
    def get_all_system_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all systems
        
        Returns:
            Dictionary mapping system names to status dictionaries
        """
        return self.system_states
    
    def _get_dependent_systems(self, system_name: str) -> List[str]:
        """
        Get systems that depend on a specific system
        
        Args:
            system_name: Name of system to check
            
        Returns:
            List of system names that depend on the specified system
        """
        dependents = []
        
        for name, deps in self.dependencies.items():
            if system_name in deps:
                dependents.append(name)
                
        return dependents
    
    def _get_shutdown_order(self) -> List[str]:
        """
        Get order in which systems should be shutdown
        
        Returns:
            List of system names in shutdown order
        """
        # Start with systems that have no dependents
        result = []
        remaining = set(self.registry.keys())
        
        while remaining:
            # Find systems with no remaining dependents
            to_remove = []
            
            for system_name in remaining:
                dependents = [s for s in self._get_dependent_systems(system_name) if s in remaining]
                if not dependents:
                    to_remove.append(system_name)
            
            # If no systems can be removed, we have a circular dependency
            if not to_remove:
                self.logger.warning("Circular dependency detected, remaining systems: {}".format(remaining))
                result.extend(list(remaining))
                break
                
            # Add systems to result and remove from remaining
            result.extend(to_remove)
            remaining -= set(to_remove)
            
        # Special case: event_system should be shutdown last
        if "event_system" in result:
            result.remove("event_system")
            result.append("event_system")
            
        return result
    
    def _emit_system_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """
        Emit a system event
        
        Args:
            event_name: Name of event to emit
            data: Event data
        """
        try:
            # Get event system
            event_system = self.registry.get("event_system")
            if not event_system:
                return
                
            # Emit event
            if hasattr(event_system, "emit"):
                event_system.emit(event_name, data)
                
        except Exception as e:
            self.logger.error(f"Error emitting system event {event_name}: {e}")
    
    def create_backup(self, reason: str = "manual") -> str:
        """
        Create a backup of system states
        
        Args:
            reason: Reason for backup
            
        Returns:
            Backup directory path
        """
        try:
            # Create backup directory
            backup_dir = self.config.get("paths.backups_dir", "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"{reason}_{timestamp}")
            os.makedirs(backup_path, exist_ok=True)
            
            # Save configuration
            config_file = os.path.join(backup_path, "config.json")
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            # Save system states
            states_file = os.path.join(backup_path, "system_states.json")
            with open(states_file, 'w') as f:
                json.dump(self.system_states, f, indent=2)
            
            # Save system data
            for system_name, system in self.registry.items():
                # Skip event system
                if system_name == "event_system":
                    continue
                    
                # Export state if supported
                if hasattr(system, "export_state"):
                    try:
                        state = system.export_state()
                        state_file = os.path.join(backup_path, f"{system_name}_state.json")
                        with open(state_file, 'w') as f:
                            json.dump(state, f, indent=2)
                    except Exception as e:
                        self.logger.warning(f"Error exporting state for system {system_name}: {e}")
            
            # Emit backup created event
            self._emit_system_event("backup_created", {
                "backup_path": backup_path,
                "reason": reason,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            self.logger.info(f"Backup created at {backup_path}")
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return ""
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore a backup
        
        Args:
            backup_path: Path to backup directory
            
        Returns:
            True if backup restored successfully, False otherwise
        """
        try:
            # Check if backup exists
            if not os.path.isdir(backup_path):
                self.logger.error(f"Backup directory not found: {backup_path}")
                return False
                
            # Shutdown all systems
            self.shutdown_all_systems()
            
            # Load configuration from backup
            config_file = os.path.join(backup_path, "config.json")
            if os.path.isfile(config_file):
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
            
            # Load system states from backup
            states_file = os.path.join(backup_path, "system_states.json")
            if os.path.isfile(states_file):
                with open(states_file, 'r') as f:
                    self.system_states = json.load(f)
            
            # Initialize all systems
            if not self.initialize_all_systems():
                self.logger.error("Error initializing systems after restore")
                return False
                
            # Restore system states
            for system_name, system in self.registry.items():
                # Skip event system
                if system_name == "event_system":
                    continue
                    
                # Import state if supported
                if hasattr(system, "import_state"):
                    state_file = os.path.join(backup_path, f"{system_name}_state.json")
                    if os.path.isfile(state_file):
                        try:
                            with open(state_file, 'r') as f:
                                state = json.load(f)
                            system.import_state(state)
                        except Exception as e:
                            self.logger.warning(f"Error importing state for system {system_name}: {e}")
            
            # Emit backup restored event
            self._emit_system_event("backup_restored", {
                "backup_path": backup_path,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            self.logger.info(f"Backup restored from {backup_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False
    
    def run(self) -> bool:
        """
        Run the simulator
        
        Returns:
            True if run successfully, False otherwise
        """
        try:
            # Initialize all systems
            if not self.initialize_all_systems():
                self.logger.error("Error initializing systems")
                return False
                
            # Get day simulator
            day_simulator = self.get_system("day_simulation_system")
            if not day_simulator:
                self.logger.error("Day simulation system not found")
                return False
                
            # Get range of days to simulate
            start_day = self.config.get("simulation.start_day", 1)
            end_day = self.config.get("simulation.end_day", start_day)
            
            # Emit simulation_start event
            self._emit_system_event("simulation_start", {
                "start_day": start_day,
                "end_day": end_day,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Create backup before starting
            self.create_backup("pre_simulation")
            
            # Simulate each day
            for day in range(start_day, end_day + 1):
                try:
                    # Emit day_start event
                    self._emit_system_event("day_start", {
                        "day": day,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    
                    # Simulate day
                    day_result = day_simulator.simulate_day(day)
                    
                    # Emit day_complete event
                    self._emit_system_event("day_complete", {
                        "day": day,
                        "result": day_result,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    
                    # Create backup if configured
                    if day % self.config.get("advanced.auto_backup_frequency", 5) == 0:
                        self.create_backup(f"day{day}")
                        
                except Exception as e:
                    self.logger.error(f"Error simulating day {day}: {e}")
                    self._emit_system_event("day_error", {
                        "day": day,
                        "error": str(e),
                        "timestamp": datetime.datetime.now().isoformat()
                    })
            
            # Create backup after simulation
            self.create_backup("post_simulation")
            
            # Emit simulation_complete event
            self._emit_system_event("simulation_complete", {
                "start_day": start_day,
                "end_day": end_day,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Shutdown all systems
            self.shutdown_all_systems()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error running simulator: {e}")
            return False
