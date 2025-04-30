def _create_backup(self, snapshot_name: str) -> str:
    """Create a backup of the current state"""
    backup_dir = self.config.get("paths.backups_dir", "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"{snapshot_name}_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)
    
    # Save configuration
    config_file = os.path.join(backup_path, "config.json")
    with open(config_file, 'w') as f:
        json.dump(self.config.to_dict(), f, indent=2)
    
    # Save system states
    systems_to_backup = [
        "trait_system", 
        "injury_system", 
        "stat_tracker", 
        "xp_system", 
        "morale_system", 
        "stamina_system"
    ]
    
    for system_name in systems_to_backup:
        system = self.registry.get(system_name)
        if system and hasattr(system, "export_state"):
            try:
                state_file = os.path.join(backup_path, f"{system_name}_state.json")
                state = system.export_state()
                with open(state_file, 'w') as f:
                    json.dump(state, f, indent=2)
            except Exception as e:
                self.logger.error(f"Error backing up {system_name}: {e}")
    
    self.logger.info(f"Backup created at {backup_path}")
    return backup_path