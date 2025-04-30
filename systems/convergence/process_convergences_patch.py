def process_convergences(self, team_a: List[Dict[str, Any]], team_a_boards: List[chess.Board],
                      team_b: List[Dict[str, Any]], team_b_boards: List[chess.Board],
                      match_context: Dict[str, Any], max_per_char: int = 3) -> List[Dict[str, Any]]:
    """
    Process convergences between boards
    
    Enhanced in v4.2 to emit convergence events for rStats tracking
    - convergence_triggered: When a character initiates a convergence
    - assist_given: When a character assists another character
    """
    self.logger.info(f"Processing convergences for round {match_context.get('round')}")
    
    event_system = self.registry.get("event_system")
    if not event_system:
        self.logger.warning("Event system not available, convergence events will not be emitted")
    
    # Track convergences by character to enforce max_per_char
    convergence_counts = defaultdict(int)
    
    # Track all convergences for reporting
    all_convergences = []
    
    # Process team A convergences
    for i, (char_a, board_a) in enumerate(zip(team_a, team_a_boards)):
        # Skip knocked out or inactive characters
        if char_a.get("is_ko", False) or not char_a.get("is_active", True):
            continue
            
        # Skip if already at max convergences
        if convergence_counts.get(char_a.get("id")) >= max_per_char:
            continue
            
        # Check for pre-convergence traits
        if self.trait_system:
            self.trait_system.check_pre_convergence_traits(char_a, board_a, match_context)
        
        # Calculate convergence chance
        base_chance = self.config.get("simulation.convergence_base_chance", 0.15)
        ldr_bonus = char_a.get("aLDR", 0) * self.config.get("simulation.convergence_ldr_factor", 0.005)
        esp_bonus = char_a.get("aESP", 0) * self.config.get("simulation.convergence_esp_factor", 0.01)
        
        convergence_chance = base_chance + ldr_bonus + esp_bonus
        
        # Apply convergence traits if any
        if self.trait_system:
            convergence_chance = self.trait_system.apply_convergence_chance_traits(char_a, convergence_chance)
        
        # Roll for convergence
        if random.random() <= convergence_chance:
            # Select a valid target for convergence
            valid_targets = []
            
            for j, (target, board_b) in enumerate(zip(team_a, team_a_boards)):
                # Cannot converge with self
                if i == j:
                    continue
                    
                # Cannot converge with KO'd or inactive characters
                if target.get("is_ko", False) or not target.get("is_active", True):
                    continue
                    
                # Cannot converge with characters already at max
                if convergence_counts.get(target.get("id")) >= max_per_char:
                    continue
                    
                # Check for compatibility
                if self._check_convergence_compatibility(char_a, target):
                    valid_targets.append((j, target, board_b))
            
            # If valid targets found, select one randomly
            if valid_targets:
                target_idx, target_char, target_board = random.choice(valid_targets)
                
                # Apply convergence effect
                convergence_effect = self._calculate_convergence_effect(char_a, target_char)
                self._apply_convergence(char_a, target_char, convergence_effect, match_context)
                
                # Increment convergence counts
                convergence_counts[char_a.get("id")] = convergence_counts.get(char_a.get("id"), 0) + 1
                convergence_counts[target_char.get("id")] = convergence_counts.get(target_char.get("id"), 0) + 1
                
                # Create convergence record
                convergence_record = {
                    "round": match_context.get("round"),
                    "initiator_id": char_a.get("id"),
                    "initiator_name": char_a.get("name"),
                    "target_id": target_char.get("id"),
                    "target_name": target_char.get("name"), 
                    "team": "A",
                    "effect": convergence_effect,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Log the convergence
                all_convergences.append(convergence_record)
                if "convergence_logs" in match_context:
                    match_context["convergence_logs"].append(convergence_record)
                    
                self.logger.info(f"Convergence: {char_a['name']} -> {target_char['name']}, effect: {convergence_effect}")
                
                # Emit events for rStats tracking
                if event_system:
                    # Emit convergence_triggered event for the initiator
                    event_system.emit("convergence_triggered", {
                        "character": char_a,
                        "target": target_char,
                        "match_context": match_context,
                        "effect": convergence_effect,
                        "result": "success"
                    })
                    
                    # Emit assist_given event for the initiator
                    event_system.emit("assist_given", {
                        "character": char_a,
                        "target": target_char,
                        "match_context": match_context,
                        "effect": convergence_effect,
                        "type": "convergence"
                    })
                
                # Check for post-convergence traits
                if self.trait_system:
                    self.trait_system.check_post_convergence_traits(char_a, target_char, match_context)
    
    # Process team B convergences (similar to Team A)
    for i, (char_b, board_b) in enumerate(zip(team_b, team_b_boards)):
        # Skip knocked out or inactive characters
        if char_b.get("is_ko", False) or not char_b.get("is_active", True):
            continue
            
        # Skip if already at max convergences
        if convergence_counts.get(char_b.get("id")) >= max_per_char:
            continue
            
        # Check for pre-convergence traits
        if self.trait_system:
            self.trait_system.check_pre_convergence_traits(char_b, board_b, match_context)
        
        # Calculate convergence chance
        base_chance = self.config.get("simulation.convergence_base_chance", 0.15)
        ldr_bonus = char_b.get("aLDR", 0) * self.config.get("simulation.convergence_ldr_factor", 0.005)
        esp_bonus = char_b.get("aESP", 0) * self.config.get("simulation.convergence_esp_factor", 0.01)
        
        convergence_chance = base_chance + ldr_bonus + esp_bonus
        
        # Apply convergence traits if any
        if self.trait_system:
            convergence_chance = self.trait_system.apply_convergence_chance_traits(char_b, convergence_chance)
        
        # Roll for convergence
        if random.random() <= convergence_chance:
            # Select a valid target for convergence
            valid_targets = []
            
            for j, (target, target_board) in enumerate(zip(team_b, team_b_boards)):
                # Cannot converge with self
                if i == j:
                    continue
                    
                # Cannot converge with KO'd or inactive characters
                if target.get("is_ko", False) or not target.get("is_active", True):
                    continue
                    
                # Cannot converge with characters already at max
                if convergence_counts.get(target.get("id")) >= max_per_char:
                    continue
                    
                # Check for compatibility
                if self._check_convergence_compatibility(char_b, target):
                    valid_targets.append((j, target, target_board))
            
            # If valid targets found, select one randomly
            if valid_targets:
                target_idx, target_char, target_board = random.choice(valid_targets)
                
                # Apply convergence effect
                convergence_effect = self._calculate_convergence_effect(char_b, target_char)
                self._apply_convergence(char_b, target_char, convergence_effect, match_context)
                
                # Increment convergence counts
                convergence_counts[char_b.get("id")] = convergence_counts.get(char_b.get("id"), 0) + 1
                convergence_counts[target_char.get("id")] = convergence_counts.get(target_char.get("id"), 0) + 1
                
                # Create convergence record
                convergence_record = {
                    "round": match_context.get("round"),
                    "initiator_id": char_b.get("id"),
                    "initiator_name": char_b.get("name"),
                    "target_id": target_char.get("id"),
                    "target_name": target_char.get("name"), 
                    "team": "B",
                    "effect": convergence_effect,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Log the convergence
                all_convergences.append(convergence_record)
                if "convergence_logs" in match_context:
                    match_context["convergence_logs"].append(convergence_record)
                    
                self.logger.info(f"Convergence: {char_b['name']} -> {target_char['name']}, effect: {convergence_effect}")
                
                # Emit events for rStats tracking
                if event_system:
                    # Emit convergence_triggered event for the initiator
                    event_system.emit("convergence_triggered", {
                        "character": char_b,
                        "target": target_char,
                        "match_context": match_context,
                        "effect": convergence_effect,
                        "result": "success"
                    })
                    
                    # Emit assist_given event for the initiator
                    event_system.emit("assist_given", {
                        "character": char_b,
                        "target": target_char,
                        "match_context": match_context,
                        "effect": convergence_effect,
                        "type": "convergence"
                    })
                
                # Check for post-convergence traits
                if self.trait_system:
                    self.trait_system.check_post_convergence_traits(char_b, target_char, match_context)
    
    # Return all convergences processed
    return all_convergences