#!/usr/bin/env python3
"""
META Simulator v4.2.1 Improved Patcher

This script analyzes your codebase structure and applies appropriate patches
to integrate the enhanced PGN tracker and stamina system.
"""

import os
import re
import sys
import shutil
import datetime

def backup_file(filepath):
    """Create a backup of a file with timestamp"""
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        return False
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.{timestamp}.bak"
    
    try:
        shutil.copy2(filepath, backup_path)
        print(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def find_latest_simulator():
    """Find the latest simulator file based on naming and modification time"""
    candidates = [
        "meta_simulator_v4_fixed_stats.py",
        "meta_simulator_v4_fixed.py",
        "meta_simulator_v4.py"
    ]
    
    existing_files = [f for f in candidates if os.path.exists(f)]
    
    if not existing_files:
        print("Error: Could not find any simulator file.")
        return None
    
    # Sort by modification time (newest first)
    latest_file = sorted(existing_files, key=lambda f: os.path.getmtime(f), reverse=True)[0]
    
    print(f"Found latest simulator: {latest_file}")
    return latest_file

def analyze_simulator_structure(filepath):
    """Analyze the simulator file structure to identify key components"""
    print("Analyzing simulator structure...")
    
    structure = {
        "imports_section": False,
        "class_name": None,
        "init_method": False,
        "registry_pattern": None,
        "pgn_tracker_init": False,
        "subsystems_init": False,
        "match_simulation": False,
        "day_simulation": False,
        "persistent_data": False,
        "combat_system": False
    }
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find class definition
    class_match = re.search(r'class\s+(\w+)', content)
    if class_match:
        structure["class_name"] = class_match.group(1)
        print(f"Found simulator class: {structure['class_name']}")
    
    # Check for imports section
    if re.search(r'^import\s+|^from\s+\w+\s+import', content, re.MULTILINE):
        structure["imports_section"] = True
    
    # Check for __init__ method
    if re.search(r'def\s+__init__\s*\(', content):
        structure["init_method"] = True
    
    # Check registry pattern
    registry_match = re.search(r'self\.registry\.register\s*\(\s*["\'](\w+)["\']', content)
    if registry_match:
        structure["registry_pattern"] = registry_match.group(0)
    elif re.search(r'registry\.register\s*\(\s*["\'](\w+)["\']', content):
        structure["registry_pattern"] = "registry.register"
    
    # Check for PGN tracker initialization
    if re.search(r'pgn_tracker\s*=|PGNTracker\(', content):
        structure["pgn_tracker_init"] = True
    
    # Check for subsystems initialization method
    if re.search(r'def\s+_initialize_subsystems|initialize_subsystems', content):
        structure["subsystems_init"] = True
    
    # Check for match simulation
    if re.search(r'def\s+simulate_match', content):
        structure["match_simulation"] = True
    
    # Check for day simulation
    if re.search(r'def\s+simulate_day', content):
        structure["day_simulation"] = True
    
    # Check for persistent data saving
    if re.search(r'def\s+_save_persistent_data|save_persistent_data', content):
        structure["persistent_data"] = True
    
    # Check for combat system
    if re.search(r'def\s+calculate_damage|apply_damage|apply_combat', content):
        structure["combat_system"] = True
    
    print("Analysis complete.")
    return structure, content

def patch_imports(content, structure):
    """Patch the import section to include new modules"""
    import_section = """
# Import enhanced modules
from enhanced_pgn_tracker import EnhancedPGNTracker
from stamina_system import StaminaSystem
"""
    
    # Look for the last import statement
    import_pattern = re.compile(r'^import.*$|^from.*import.*$', re.MULTILINE)
    matches = list(re.finditer(import_pattern, content))
    
    if not matches:
        print("Warning: Could not find import section. Adding imports at the beginning.")
        return import_section + content
    
    last_import = matches[-1]
    position = last_import.end()
    
    # Insert our imports after the last import
    patched = content[:position] + import_section + content[position:]
    print("✓ Added enhanced module imports")
    return patched

def patch_pgn_tracker(content, structure):
    """Patch PGN tracker based on the identified structure"""
    result = content
    
    # Try multiple patterns to find PGN tracker initialization
    patterns = [
        # Pattern 1: Direct initialization with assignment
        (r'(pgn_tracker\s*=\s*)(?:PGNTracker)\s*\(\s*(?:self\.)?config\s*\)', 
         r'\1EnhancedPGNTracker(self.config)'),
        
        # Pattern 2: Registry-based initialization
        (r'((?:self\.)?registry\.register\s*\(\s*["\']pgn_tracker["\']\s*,\s*)(?:PGNTracker)\s*\(\s*(?:self\.)?config\s*\)\s*\)', 
         r'\1EnhancedPGNTracker(self.config))'),
        
        # Pattern 3: Conditional initialization
        (r'(if\s+.*?:\s*\n\s+pgn_tracker\s*=\s*)(?:PGNTracker)\s*\(\s*(?:self\.)?config\s*\)', 
         r'\1EnhancedPGNTracker(self.config)'),

        # Pattern 4: Function or method call
        (r'((?:initialize|create)_pgn_tracker\s*\([^)]*\)\s*)', 
         r'\1\n        # PGN tracker updated to enhanced version\n        pgn_tracker = EnhancedPGNTracker(self.config)\n        self.registry.register("pgn_tracker", pgn_tracker)')
    ]
    
    patched = False
    for pattern, replacement in patterns:
        if re.search(pattern, result):
            result = re.sub(pattern, replacement, result)
            print("✓ Patched PGN tracker initialization")
            patched = True
            break
    
    if not patched:
        print("! Could not patch PGN tracker initialization automatically")
        print("  Please manually update PGN tracker initialization to use EnhancedPGNTracker")
    
    return result

def add_stamina_initialization(content, structure):
    """Add stamina system initialization based on the structure"""
    result = content
    
    # Find where to insert stamina system initialization
    if structure["subsystems_init"]:
        # Try to find subsystems initialization method
        subsystems_patterns = [
            # Pattern 1: Standard initialization method
            (r'(def\s+_initialize_subsystems\s*\([^)]*\)\s*:.*?)(\s+return|\s+self\.logger\.info\([^)]*\)|\s+$)', 
             r'\1\n        # Initialize stamina system if enabled\n        if self.config.get("features.stamina_enabled", True):\n            stamina_system = StaminaSystem(self.config)\n            self.registry.register("stamina_system", stamina_system)\n\2'),
            
            # Pattern 2: Alternative method name
            (r'(def\s+initialize_subsystems\s*\([^)]*\)\s*:.*?)(\s+return|\s+self\.logger\.info\([^)]*\)|\s+$)', 
             r'\1\n        # Initialize stamina system if enabled\n        if self.config.get("features.stamina_enabled", True):\n            stamina_system = StaminaSystem(self.config)\n            self.registry.register("stamina_system", stamina_system)\n\2')
        ]
        
        patched = False
        for pattern, replacement in subsystems_patterns:
            if re.search(pattern, result, re.DOTALL):
                result = re.sub(pattern, replacement, result, flags=re.DOTALL)
                print("✓ Added stamina system initialization")
                patched = True
                break
        
        if not patched:
            # Try adding after a registry registration
            registry_pattern = r'(self\.registry\.register\s*\([^)]*\))'
            matches = list(re.finditer(registry_pattern, result))
            if matches:
                last_match = matches[-1]
                position = last_match.end()
                stamina_init = '\n        # Initialize stamina system if enabled\n        if self.config.get("features.stamina_enabled", True):\n            stamina_system = StaminaSystem(self.config)\n            self.registry.register("stamina_system", stamina_system)'
                
                result = result[:position] + stamina_init + result[position:]
                print("✓ Added stamina system initialization after last registry registration")
                patched = True
        
        if not patched:
            print("! Could not add stamina system initialization automatically")
            print("  Please manually add stamina system initialization")
    else:
        print("! Could not find subsystems initialization method")
        print("  Please manually add stamina system initialization")
    
    return result

def add_stamina_to_match(content, structure):
    """Add stamina system integration to match simulation"""
    result = content
    
    if structure["match_simulation"]:
        # Try to find where to insert stamina initialization in match simulation
        match_patterns = [
            # Pattern 1: After team setup
            (r'(def\s+simulate_match\s*\([^)]*\)\s*:.*?team_a_name\s*=.*?team_b_name\s*=.*?)(\s+# Create match context|\s+match_context\s*=)', 
             r'\1\n        # Initialize character stamina if enabled\n        if self.config.get("features.stamina_enabled", True):\n            stamina_system = self.registry.get("stamina_system")\n            if stamina_system:\n                for char in team_a_active + team_b_active:\n                    stamina_system.initialize_character_stamina(char)\n\2'),
            
            # Pattern 2: After match context creation
            (r'(match_context\s*=\s*\{[^}]*\})(\s+# Apply injuries|\s+if\s+self\.config\.get)', 
             r'\1\n\n        # Initialize character stamina if enabled\n        if self.config.get("features.stamina_enabled", True):\n            stamina_system = self.registry.get("stamina_system")\n            if stamina_system:\n                for char in team_a_active + team_b_active:\n                    stamina_system.initialize_character_stamina(char)\2')
        ]
        
        patched_init = False
        for pattern, replacement in match_patterns:
            if re.search(pattern, result, re.DOTALL):
                result = re.sub(pattern, replacement, result, flags=re.DOTALL)
                print("✓ Added stamina initialization to match simulation")
                patched_init = True
                break
        
        if not patched_init:
            print("! Could not add stamina initialization to match simulation automatically")
            print("  Please manually add stamina initialization to match simulation")
        
        # Add end of round stamina effects
        round_patterns = [
            # Pattern 1: After end of round effects
            (r'(_apply_end_of_round_effects\s*\([^)]*\))', 
             r'\1\n\n            # Apply stamina effects if enabled\n            if self.config.get("features.stamina_enabled", True):\n                stamina_system = self.registry.get("stamina_system")\n                if stamina_system:\n                    stamina_system.apply_end_of_round_recovery(\n                        team_a_active + team_b_active,\n                        match_context\n                    )'),
            
            # Pattern 2: Inside round loop
            (r'(round_number\s*\+=\s*1)', 
             r'            # Apply stamina effects if enabled\n            if self.config.get("features.stamina_enabled", True):\n                stamina_system = self.registry.get("stamina_system")\n                if stamina_system:\n                    stamina_system.apply_end_of_round_recovery(\n                        team_a_active + team_b_active,\n                        match_context\n                    )\n\n            \1')
        ]
        
        patched_round = False
        for pattern, replacement in round_patterns:
            if re.search(pattern, result):
                result = re.sub(pattern, replacement, result)
                print("✓ Added stamina effects to end of round processing")
                patched_round = True
                break
        
        if not patched_round:
            print("! Could not add stamina effects to end of round processing automatically")
            print("  Please manually add stamina effects to end of round processing")
    else:
        print("! Could not find match simulation method")
        print("  Please manually add stamina integration to match simulation")
    
    return result

def add_stamina_to_day(content, structure):
    """Add stamina system integration to day simulation"""
    result = content
    
    if structure["day_simulation"]:
        # Try to find where to insert stamina processing in day simulation
        day_patterns = [
            # Pattern 1: After injury processing
            (r'(injury_system\s*=\s*(?:self\.)?registry\.get\s*\(\s*["\']injury_system["\']\s*\).*?self\.logger\.info\s*\([^)]*\))', 
             r'\1\n\n        # Process stamina recovery if enabled\n        if self.config.get("features.stamina_enabled", True):\n            stamina_system = self.registry.get("stamina_system")\n            if stamina_system:\n                stamina_report = stamina_system.process_day_change(day_number)\n                self.logger.info(f"Processed stamina recovery: {len(stamina_report[\'full_recovery\'])} full, {len(stamina_report[\'partial_recovery\'])} partial")'),
            
            # Pattern 2: Before match simulation loop
            (r'(# Simulate each match[\s\n]*match_results\s*=\s*\[\])', 
             r'        # Process stamina recovery if enabled\n        if self.config.get("features.stamina_enabled", True):\n            stamina_system = self.registry.get("stamina_system")\n            if stamina_system:\n                stamina_report = stamina_system.process_day_change(day_number)\n                self.logger.info(f"Processed stamina recovery: {len(stamina_report[\'full_recovery\'])} full, {len(stamina_report[\'partial_recovery\'])} partial")\n\n        \1')
        ]
        
        patched = False
        for pattern, replacement in day_patterns:
            if re.search(pattern, result, re.DOTALL):
                result = re.sub(pattern, replacement, result, flags=re.DOTALL)
                print("✓ Added stamina recovery to day simulation")
                patched = True
                break
        
        if not patched:
            print("! Could not add stamina recovery to day simulation automatically")
            print("  Please manually add stamina recovery to day simulation")
    else:
        print("! Could not find day simulation method")
        print("  Please manually add stamina recovery to day simulation")
    
    return result

def add_stamina_to_persistent_data(content, structure):
    """Add stamina system to persistent data saving"""
    result = content
    
    if structure["persistent_data"]:
        # Try to find where to insert stamina data saving
        patterns = [
            # Pattern 1: Inside _save_persistent_data method
            (r'(def\s+_save_persistent_data\s*\([^)]*\)\s*:.*?(?:save|store)_[a-z_]+_data\s*\([^)]*\))', 
             r'\1\n\n        # Save stamina system data\n        stamina_system = self.registry.get("stamina_system")\n        if stamina_system and hasattr(stamina_system, "save_stamina_data"):\n            stamina_system.save_stamina_data()'),
            
            # Pattern 2: Inside save_persistent_data method
            (r'(def\s+save_persistent_data\s*\([^)]*\)\s*:.*?(?:save|store)_[a-z_]+_data\s*\([^)]*\))', 
             r'\1\n\n        # Save stamina system data\n        stamina_system = self.registry.get("stamina_system")\n        if stamina_system and hasattr(stamina_system, "save_stamina_data"):\n            stamina_system.save_stamina_data()')
        ]
        
        patched = False
        for pattern, replacement in patterns:
            if re.search(pattern, result, re.DOTALL):
                result = re.sub(pattern, replacement, result, flags=re.DOTALL)
                print("✓ Added stamina data saving to persistent data method")
                patched = True
                break
        
        if not patched:
            print("! Could not add stamina data saving automatically")
            print("  Please manually add stamina data saving")
    else:
        print("! Could not find persistent data saving method")
        print("  Please manually add stamina data saving")
    
    return result

def add_stamina_to_combat(content, structure):
    """Add stamina system effects to combat calculations"""
    result = content
    
    if structure["combat_system"]:
        # Try to find where to insert stamina effects in combat
        patterns = [
            # Pattern 1: Inside damage calculation method
            (r'(def\s+calculate_damage\s*\([^)]*\)\s*:.*?damage\s*=.*?)[;\n]', 
             r'\1\n\n        # Apply stamina modifier if enabled\n        if self.config.get("features.stamina_enabled", True):\n            stamina_system = self.registry.get("stamina_system")\n            if stamina_system and "defender" in locals():\n                # Apply stamina modifier to defender (takes more damage when tired)\n                stamina_modifier = stamina_system.calculate_stamina_damage_modifier(defender)\n                damage *= stamina_modifier;'),
            
            # Pattern 2: Inside apply_damage method
            (r'(def\s+apply_damage\s*\([^)]*\)\s*:.*?damage\s*=.*?)[;\n]', 
             r'\1\n\n        # Apply stamina modifier if enabled\n        if self.config.get("features.stamina_enabled", True):\n            stamina_system = self.registry.get("stamina_system")\n            if stamina_system and "defender" in locals():\n                # Apply stamina modifier to defender (takes more damage when tired)\n                stamina_modifier = stamina_system.calculate_stamina_damage_modifier(defender)\n                damage *= stamina_modifier;')
        ]
        
        patched = False
        for pattern, replacement in patterns:
            if re.search(pattern, result, re.DOTALL):
                result = re.sub(pattern, replacement, result, flags=re.DOTALL)
                print("✓ Added stamina effects to combat calculations")
                patched = True
                break
        
        if not patched:
            print("! Could not add stamina effects to combat calculations automatically")
            print("  Please manually add stamina effects to combat calculations")
    else:
        print("! Could not find combat calculation method")
        print("  Please manually add stamina effects to combat calculations")
    
    return result

def create_config_update_instructions(structure):
    """Create instructions for updating configuration based on structure"""
    instructions = """
# Configuration Update Instructions
# --------------------------------
#
# Add these settings to your meta_simulator_config_v4_2.py file:

"features": {
    "per_board_pgn": True,      # Generate individual PGN files per board
    "aggregate_match_pgn": True, # Generate aggregated match PGN file
    "stamina_enabled": True      # Enable stamina system
},
"stamina_settings": {
    "stamina_decay_per_round_multiplier": 1.15,
    "low_stamina_extra_damage_taken_percent": 20,
    "base_stamina_value": 100,
    "base_stamina_decay_per_round": 5,
    "base_stamina_recovery_per_day": 15,
    "low_stamina_threshold": 35
}
"""
    
    # Save to file
    with open("config_update_instructions.txt", "w") as f:
        f.write(instructions)
    
    print("✓ Created configuration update instructions (config_update_instructions.txt)")
    return instructions

def main():
    print("META Simulator v4.2.1 Improved Patcher")
    print("------------------------------------")
    
    # Find latest simulator
    simulator_file = find_latest_simulator()
    if not simulator_file:
        sys.exit(1)
    
    # Create backup
    if not backup_file(simulator_file):
        sys.exit(1)
    
    # Analyze simulator structure
    structure, content = analyze_simulator_structure(simulator_file)
    
    print("\nApplying patches based on analysis...")
    
    # Apply patches
    content = patch_imports(content, structure)
    content = patch_pgn_tracker(content, structure)
    content = add_stamina_initialization(content, structure)
    content = add_stamina_to_match(content, structure)
    content = add_stamina_to_day(content, structure)
    content = add_stamina_to_persistent_data(content, structure)
    content = add_stamina_to_combat(content, structure)
    
    # Create config update instructions
    config_instructions = create_config_update_instructions(structure)
    
    # Write patched file
    with open(simulator_file, "w") as f:
        f.write(content)
    
    print(f"\nSuccessfully patched {simulator_file}")
    print("\nManual steps required:")
    
    # Check if we have manual steps required
    manual_steps = []
    
    if not structure["pgn_tracker_init"]:
        manual_steps.append("- Add PGN tracker initialization and registration")
    
    if not structure["subsystems_init"]:
        manual_steps.append("- Add stamina system initialization and registration")
    
    if not structure["match_simulation"]:
        manual_steps.append("- Add stamina initialization to match simulation")
        manual_steps.append("- Add stamina effects to end of round processing")
    
    if not structure["day_simulation"]:
        manual_steps.append("- Add stamina recovery to day simulation")
    
    if not structure["persistent_data"]:
        manual_steps.append("- Add stamina data saving to persistent data method")
    
    if not structure["combat_system"]:
        manual_steps.append("- Add stamina effects to combat calculations")
    
    # Always add these steps
    manual_steps.append("- Update configuration with new PGN and stamina settings (see config_update_instructions.txt)")
    manual_steps.append("- Test the simulator with these changes")
    
    # Print manual steps
    for step in manual_steps:
        print(step)
    
    print("\nRefer to the implementation guide for more details on these integration points.")

if __name__ == "__main__":
    main()