def _save_persistent_data(self) -> None:
    """Save persistent data for all systems"""
    systems_to_save = [
        "trait_system", 
        "injury_system", 
        "stat_tracker", 
        "xp_system", 
        "morale_system", 
        "stamina_system"
    ]
    
    for system_name in systems_to_save:
        system = self.registry.get(system_name)
        if system and hasattr(system, "save_persistent_data"):
            try:
                system.save_persistent_data()
            except Exception as e:
                self.logger.error(f"Error saving persistent data for {system_name}: {e}")