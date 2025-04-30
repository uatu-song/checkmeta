"""
Stamina System Integration Test

This script provides a simplified test harness for the stamina system integration
with the trait, convergence, and combat systems in the META Fantasy League Simulator.
"""

import json
import logging
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("INTEGRATION_TEST")

# Mock system_base and registry classes for testing
class SystemBase:
    def __init__(self, name, registry, config=None):
        self.name = name
        self.registry = registry
        self.config = config
        self.active = False
        
    def activate(self):
        self._activate_implementation()
        self.active = True
        
    def _activate_implementation(self):
        pass

class SystemRegistry:
    def __init__(self):
        self._systems = {}
        self._activation_status = {}
        
    def register(self, name, system):
        self._systems[name] = system
        self._activation_status[name] = False
        return system
        
    def activate(self, name):
        if name not in self._systems:
            raise KeyError(f"System '{name}' not registered")
        
        self._systems[name].activate()
        self._activation_status[name] = True
        
    def get(self, name):
        return self._systems.get(name, None)
        
    def is_active(self, name):
        return self._activation_status.get(name, False)
        
    def get_all_systems(self):
        return list(self._systems.keys())


# Mock systems for testing
class MockStaminaSystem(SystemBase):
    def __init__(self, config, registry):
        super().__init__("stamina_system", registry, config)
        self.logger = logging.getLogger("MOCK_STAMINA_SYSTEM")
        
    def initialize_character_stamina(self, character):
        if "stamina" not in character:
            character["stamina"] = 100.0
            character["stamina_log"] = []
        return character["stamina"]
        
    def apply_stamina_cost(self, character, cost, reason, match_context):
        if "stamina" not in character:
            self.initialize_character_stamina(character)
            
        # Apply the cost
        character["stamina"] = max(character["stamina"] - cost, 0)
        
        # Log the stamina change
        log_entry = {
            "round": match_context.get("round", 0),
            "cost": cost,
            "reason": reason,
            "stamina": character["stamina"]
        }
        
        character["stamina_log"].append(log_entry)
        
        # Also add to match context
        if "stamina_logs" not in match_context:
            match_context["stamina_logs"] = []
            
        match_log_entry = {
            "character_id": character.get("id", "unknown"),
            "character_name": character.get("name", "Unknown"),
            "round": match_context.get("round", 0),
            "cost": cost,
            "reason": reason,
            "stamina": character["stamina"]
        }
        
        match_context["stamina_logs"].append(match_log_entry)
        
        return character["stamina"]
        
    def apply_end_of_round_effects(self, characters, match_context):
        # Apply round-end recovery
        for character in characters:
            if "stamina" not in character:
                self.initialize_character_stamina(character)
                
            # Apply recovery (base 5 points)
            recovery = 5.0
            if "aDUR" in character:
                # Higher durability improves recovery
                recovery *= (1.0 + (character["aDUR"] - 50) / 100.0)
                
            old_stamina = character["stamina"]
            new_stamina = min(old_stamina + recovery, 100.0)
            character["stamina"] = new_stamina
            
            # Log the recovery
            if new_stamina > old_stamina:
                log_entry = {
                    "round": match_context.get("round", 0),
                    "recovery": new_stamina - old_stamina,
                    "reason": "end_of_round_recovery",
                    "stamina": new_stamina
                }
                
                character["stamina_log"].append(log_entry)
                
                # Also add to match context
                if "stamina_logs" not in match_context:
                    match_context["stamina_logs"] = []
                    
                match_log_entry = {
                    "character_id": character.get("id", "unknown"),
                    "character_name": character.get("name", "Unknown"),
                    "round": match_context.get("round", 0),
                    "recovery": new_stamina - old_stamina,
                    "reason": "end_of_round_recovery",
                    "stamina": new_stamina
                }
                
                match_context["stamina_logs"].append(match_log_entry)
                
    def process_overnight_recovery(self, character):
        """Process overnight stamina recovery between matches"""
        if "stamina" not in character:
            return self.initialize_character_stamina(character)
            
        # Get current stamina
        current_stamina = character["stamina"]
        
        # If already at max, nothing to do
        if current_stamina >= 100.0:
            return current_stamina
            
        # Calculate recovery (default: recover 70% of missing stamina)
        recovery_percent = 0.7  # 70%
        missing_stamina = 100.0 - current_stamina
        recovery_amount = missing_stamina * recovery_percent
        
        # Apply durability bonus if available
        if "aDUR" in character:
            durability_bonus = (character["aDUR"] - 50) / 100.0  # -0.5 to +0.5
            recovery_amount *= (1.0 + durability_bonus)
            
        # Apply the recovery
        new_stamina = min(current_stamina + recovery_amount, 100.0)
        character["stamina"] = new_stamina
        
        return new_stamina


class MockTraitSystem(SystemBase):
    def __init__(self, config, registry):
        super().__init__("trait_system", registry, config)
        self.logger = logging.getLogger("MOCK_TRAIT_SYSTEM")
        self.activation_checks = []
        self.post_activation_hooks = []
        self.trait_catalog = []
        
        # Load trait catalog
        self._load_trait_catalog()
        
    def _load_trait_catalog(self):
        """Load mock trait catalog"""
        self.trait_catalog = [
            {
                "trait_id": "power_strike",
                "name": "Power Strike",
                "stamina_cost": "high",
                "description": "A powerful attack that deals extra damage"
            },
            {
                "trait_id": "defensive_stance",
                "name": "Defensive Stance",
                "stamina_cost": "medium",
                "description": "Increases defense but reduces mobility"
            },
            {
                "trait_id": "rapid_assault",
                "name": "Rapid Assault",
                "stamina_cost": "medium",
                "description": "Multiple quick attacks with reduced damage"
            },
            {
                "trait_id": "berserker_rage",
                "name": "Berserker Rage",
                "stamina_cost": "extreme",
                "description": "Massively increases damage but reduces defense"
            },
            {
                "trait_id": "quick_recovery",
                "name": "Quick Recovery",
                "stamina_cost": "low",
                "description": "Improves stamina recovery rate"
            }
        ]
        
    def register_activation_check(self, check_function):
        """Register a function to check if traits can be activated"""
        self.activation_checks.append(check_function)
        
    def register_post_activation_hook(self, hook_function):
        """Register a function to be called after trait activation"""
        self.post_activation_hooks.append(hook_function)
        
    def get_trait(self, trait_id):
        """Get trait data from catalog"""
        for trait in self.trait_catalog:
            if trait["trait_id"] == trait_id:
                return trait
        return None
        
    def get_trait_catalog(self):
        """Get the full trait catalog"""
        return self.trait_catalog
        
    def activate_trait(self, character, trait_id, match_context):
        """Attempt to activate a trait"""
        # Get trait data
        trait_data = self.get_trait(trait_id)
        if not trait_data:
            return {
                "success": False,
                "reason": "Trait not found"
            }
            
        # Run activation checks
        for check in self.activation_checks:
            can_activate, reason = check(character, trait_id, match_context)
            if not can_activate:
                return {
                    "success": False,
                    "reason": reason
                }
                
        # Trait can be activated
        result = {
            "success": True,
            "trait_id": trait_id,
            "trait_name": trait_data["name"],
            "character_id": character.get("id", "unknown"),
            "character_name": character.get("name", "Unknown"),
            "round": match_context.get("round", 0)
        }
        
        # Run post-activation hooks
        for hook in self.post_activation_hooks:
            hook(character, trait_id, result, match_context)
            
        return result


class MockConvergenceSystem(SystemBase):
    def __init__(self, config, registry):
        super().__init__("convergence_system", registry, config)
        self.logger = logging.getLogger("MOCK_CONVERGENCE_SYSTEM")
        self.pre_convergence_hooks = []
        self.post_convergence_hooks = []
        self.chance_modifiers = []
        self.damage_modifiers = []
        
    def register_pre_convergence_hook(self, hook_function):
        """Register a function to be called before convergence processing"""
        self.pre_convergence_hooks.append(hook_function)
        
    def register_post_convergence_hook(self, hook_function):
        """Register a function to be called after convergence processing"""
        self.post_convergence_hooks.append(hook_function)
        
    def register_chance_modifier(self, modifier_function):
        """Register a function to modify convergence chance"""
        self.chance_modifiers.append(modifier_function)
        
    def register_damage_modifier(self, modifier_function):
        """Register a function to modify convergence damage"""
        self.damage_modifiers.append(modifier_function)
        
    def process_convergence(self, initiator, target, assists, match_context):
        """Process a convergence attempt"""
        # Run pre-convergence hooks
        for hook in self.pre_convergence_hooks:
            if not hook(initiator, target, assists, match_context):
                return {
                    "success": False,
                    "reason": "Pre-convergence check failed"
                }
                
        # Calculate base convergence chance (based on leadership)
        base_chance = 0.3  # 30% base chance
        if "aLDR" in initiator:
            base_chance += (initiator["aLDR"] - 50) / 100.0  # -0.5 to +0.5 modifier
            
        # Apply chance modifiers
        for modifier in self.chance_modifiers:
            base_chance = modifier(initiator, target, base_chance, match_context)
            
        # Check if convergence succeeds
        import random
        success = random.random() < base_chance
        
        # If successful, calculate damage
        if success:
            base_damage = 10.0  # Base convergence damage
            
            # Apply damage modifiers
            for modifier in self.damage_modifiers:
                base_damage = modifier(initiator, target, base_damage, match_context)
                
            # Apply the damage (simplified)
            if "HP" in target:
                target["HP"] = max(target["HP"] - base_damage, 0)
                
        # Create result
        result = {
            "success": success,
            "id": f"conv_{match_context.get('round', 0)}_{initiator.get('id', 'unknown')}",
            "initiator": initiator,
            "target": target,
            "assists": assists,
            "chance": base_chance,
            "damage": base_damage if success else 0.0,
            "round": match_context.get("round", 0)
        }
        
        # Run post-convergence hooks
        for hook in self.post_convergence_hooks:
            hook(result, match_context)
            
        return result


class MockCombatSystem(SystemBase):
    def __init__(self, config, registry):
        super().__init__("combat_system", registry, config)
        self.logger = logging.getLogger("MOCK_COMBAT_SYSTEM")
        self.damage_modifiers = []
        self.attack_modifiers = []
        self.critical_modifiers = []
        self.post_damage_hooks = []
        
    def register_damage_modifier(self, modifier_function):
        """Register a function to modify damage taken"""
        self.damage_modifiers.append(modifier_function)
        
    def register_attack_modifier(self, modifier_function):
        """Register a function to modify attack effectiveness"""
        self.attack_modifiers.append(modifier_function)
        
    def register_critical_modifier(self, modifier_function):
        """Register a function to modify critical hit chance"""
        self.critical_modifiers.append(modifier_function)
        
    def register_post_damage_hook(self, hook_function):
        """Register a function to be called after damage is applied"""
        self.post_damage_hooks.append(hook_function)
        
    def apply_damage(self, attacker, target, base_damage, attack_type, match_context):
        """Apply damage from attacker to target"""
        # Calculate attack effectiveness
        effectiveness = 1.0
        for modifier in self.attack_modifiers:
            effectiveness = modifier(attacker, target, effectiveness, match_context)
            
        # Calculate critical hit chance
        crit_chance = 0.1  # 10% base critical chance
        if "aFS" in attacker:
            crit_chance += (attacker["aFS"] - 50) / 200.0  # -0.25 to +0.25 modifier
            
        # Apply critical modifiers
        for modifier in self.critical_modifiers:
            crit_chance = modifier(attacker, crit_chance, attack_type, match_context)
            
        # Check for critical hit
        import random
        is_critical = random.random() < crit_chance
        
        # Calculate damage
        damage = base_damage * effectiveness
        if is_critical:
            damage *= 1.5  # 50% more damage on critical hit
            
        # Apply damage modifiers to target
        for modifier in self.damage_modifiers:
            damage = modifier(target, damage, attack_type, match_context)
            
        # Apply damage to target
        if "HP" not in target:
            target["HP"] = 100.0
            
        old_hp = target["HP"]
        new_hp = max(old_hp - damage, 0)
        target["HP"] = new_hp
        
        # Check for KO
        if new_hp <= 0 and old_hp > 0:
            target["is_ko"] = True
            target["ko_reason"] = "combat_damage"
            
        # Create attack data
        attack_data = {
            "type": attack_type,
            "base_damage": base_damage,
            "effectiveness": effectiveness,
            "is_critical": is_critical,
            "crit_chance": crit_chance,
            "final_damage": damage,
            "old_hp": old_hp,
            "new_hp": new_hp,
            "is_ko": new_hp <= 0,
            "defense_type": "normal"
        }
        
        # Run post-damage hooks
        for hook in self.post_damage_hooks:
            hook(attacker, target, damage, attack_data, match_context)
            
        return attack_data


class MockEventSystem(SystemBase):
    def __init__(self, config, registry):
        super().__init__("event_system", registry, config)
        self.logger = logging.getLogger("MOCK_EVENT_SYSTEM")
        self.events = []
        self.subscribers = {}
        
    def emit(self, event):
        """Emit an event"""
        # Add timestamp
        import datetime
        event["timestamp"] = datetime.datetime.now().isoformat()
        
        # Store the event
        self.events.append(event)
        
        # Notify subscribers
        event_type = event.get("type", "unknown")
        if event_type in self.subscribers:
            for subscriber in self.subscribers[event_type]:
                try:
                    subscriber(event)
                except Exception as e:
                    self.logger.error(f"Error in event subscriber: {e}")
                    
        return True
        
    def subscribe(self, event_type, subscriber_function):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
            
        self.subscribers[event_type].append(subscriber_function)
        
    def get_events(self, event_type=None):
        """Get all events of a specific type, or all events if type is None"""
        if event_type is None:
            return self.events
            
        return [e for e in self.events if e.get("type") == event_type]


# Function to create test characters
def create_test_characters():
    """Create a set of test characters"""
    return [
        {
            "id": "char_001",
            "name": "Alice",
            "team_id": "team_a",
            "HP": 100.0,
            "aSTR": 60,  # High strength
            "aSPD": 55,
            "aFS": 50,
            "aLDR": 70,  # High leadership
            "aDUR": 40,  # Low durability
            "aRES": 45,
            "aWIL": 50
        },
        {
            "id": "char_002",
            "name": "Bob",
            "team_id": "team_a",
            "HP": 100.0,
            "aSTR": 45,
            "aSPD": 65,  # High speed
            "aFS": 60,  # High finesse
            "aLDR": 50,
            "aDUR": 50,
            "aRES": 40,  # Low resilience
            "aWIL": 60  # High willpower
        },
        {
            "id": "char_003",
            "name": "Charlie",
            "team_id": "team_b",
            "HP": 100.0,
            "aSTR": 50,
            "aSPD": 40,  # Low speed
            "aFS": 45,
            "aLDR": 65,  # High leadership
            "aDUR": 70,  # High durability
            "aRES": 60,  # High resilience
            "aWIL": 40  # Low willpower
        },
        {
            "id": "char_004",
            "name": "Diana",
            "team_id": "team_b",
            "HP": 100.0,
            "aSTR": 65,  # High strength
            "aSPD": 60,  # High speed
            "aFS": 55,
            "aLDR": 45,
            "aDUR": 40,  # Low durability
            "aRES": 50,
            "aWIL": 55
        }
    ]


# Test function for trait-stamina integration
def test_trait_stamina_integration(integrator, characters, match_context):
    """Test the trait-stamina integration"""
    logger.info("Testing trait-stamina integration...")
    
    trait_system = integrator.registry.get("trait_system")
    
    # Test trait activation with different stamina levels
    results = []
    
    # Test high-cost trait at full stamina
    alice = characters[0]  # Alice has high leadership but low durability
    result = trait_system.activate_trait(alice, "berserker_rage", match_context)
    results.append({
        "character": alice["name"],
        "trait": "berserker_rage",
        "success": result["success"],
        "stamina_before": alice.get("stamina", 100),
        "stamina_after": alice.get("stamina", 100)
    })
    
    # Test medium-cost trait at moderate stamina
    # First, reduce stamina
    alice["stamina"] = 50.0
    result = trait_system.activate_trait(alice, "defensive_stance", match_context)
    results.append({
        "character": alice["name"],
        "trait": "defensive_stance",
        "success": result["success"],
        "stamina_before": 50.0,
        "stamina_after": alice.get("stamina", 50.0)
    })
    
    # Test low-cost trait at very low stamina
    alice["stamina"] = 15.0
    result = trait_system.activate_trait(alice, "quick_recovery", match_context)
    results.append({
        "character": alice["name"],
        "trait": "quick_recovery", 
        "success": result["success"],
        "stamina_before": 15.0,
        "stamina_after": alice.get("stamina", 15.0)
    })
    
    # Test high-cost trait at very low stamina (should fail)
    result = trait_system.activate_trait(alice, "berserker_rage", match_context)
    results.append({
        "character": alice["name"],
        "trait": "berserker_rage",
        "success": result["success"],
        "stamina_before": alice.get("stamina", 15.0),
        "stamina_after": alice.get("stamina", 15.0),
        "reason": result.get("reason", "Unknown")
    })
    
    # Print results
    logger.info("Trait activation results:")
    for r in results:
        if r["success"]:
            logger.info(f"✓ {r['character']} activated {r['trait']} - Stamina: {r['stamina_before']:.1f} → {r['stamina_after']:.1f}")
        else:
            logger.info(f"✗ {r['character']} failed to activate {r['trait']} - Stamina: {r['stamina_before']:.1f} | Reason: {r.get('reason', 'Unknown')}")
            
    return results


# Test function for convergence-stamina integration
def test_convergence_stamina_integration(integrator, characters, match_context):
    """Test the convergence-stamina integration"""
    logger.info("Testing convergence-stamina integration...")
    
    convergence_system = integrator.registry.get("convergence_system")
    
    # Test convergence with different stamina levels
    results = []
    
    # Test convergence at full stamina
    alice = characters[0]  # Alice has high leadership
    bob = characters[1]
    charlie = characters[2]  # Charlie has high durability
    
    # Reset stamina
    alice["stamina"] = 100.0
    charlie["stamina"] = 100.0
    
    # Alice initiates convergence against Charlie
    result = convergence_system.process_convergence(alice, charlie, [bob], match_context)
    results.append({
        "initiator": alice["name"],
        "target": charlie["name"],
        "success": result["success"],
        "initiator_stamina_before": 100.0,
        "initiator_stamina_after": alice.get("stamina"),
        "target_stamina_before": 100.0,
        "target_stamina_after": charlie.get("stamina")
    })
    
    # Test convergence at low stamina
    alice["stamina"] = 30.0
    charlie["stamina"] = 30.0
    
    # Alice initiates convergence against Charlie again
    result = convergence_system.process_convergence(alice, charlie, [bob], match_context)
    results.append({
        "initiator": alice["name"],
        "target": charlie["name"],
        "success": result["success"],
        "initiator_stamina_before": 30.0,
        "initiator_stamina_after": alice.get("stamina"),
        "target_stamina_before": 30.0,
        "target_stamina_after": charlie.get("stamina")
    })
    
    # Print results
    logger.info("Convergence results:")
    for r in results:
        success_str = "successful" if r["success"] else "failed"
        logger.info(f"{r['initiator']} {success_str} convergence against {r['target']}")
        logger.info(f"  Initiator stamina: {r['initiator_stamina_before']:.1f} → {r['initiator_stamina_after']:.1f}")
        logger.info(f"  Target stamina: {r['target_stamina_before']:.1f} → {r['target_stamina_after']:.1f}")
            
    return results


# Test function for combat-stamina integration
def test_combat_stamina_integration(integrator, characters, match_context):
    """Test the combat-stamina integration"""
    logger.info("Testing combat-stamina integration...")
    
    combat_system = integrator.registry.get("combat_system")
    
    # Test combat with different stamina levels
    results = []
    
    # Test combat at full stamina
    alice = characters[0]  # High strength
    charlie = characters[2]  # High durability
    
    # Reset stamina and HP
    alice["stamina"] = 100.0
    alice["HP"] = 100.0
    charlie["stamina"] = 100.0
    charlie["HP"] = 100.0
    
    # Alice attacks Charlie
    result = combat_system.apply_damage(alice, charlie, 10.0, "standard_attack", match_context)
    results.append({
        "attacker": alice["name"],
        "target": charlie["name"],
        "damage_done": result["final_damage"],
        "is_critical": result["is_critical"],
        "attacker_stamina_before": 100.0,
        "attacker_stamina_after": alice.get("stamina"),
        "target_stamina_before": 100.0,
        "target_stamina_after": charlie.get("stamina")
    })
    
    # Test combat at low stamina
    alice["stamina"] = 30.0
    charlie["stamina"] = 30.0
    
    # Alice attacks Charlie again
    result = combat_system.apply_damage(alice, charlie, 10.0, "standard_attack", match_context)
    results.append({
        "attacker": alice["name"],
        "target": charlie["name"],
        "damage_done": result["final_damage"],
        "is_critical": result["is_critical"],
        "attacker_stamina_before": 30.0,
        "attacker_stamina_after": alice.get("stamina"),
        "target_stamina_before": 30.0,
        "target_stamina_after": charlie.get("stamina")
    })
    
    # Print results
    logger.info("Combat results:")
    for r in results:
        crit_str = "(CRITICAL)" if r["is_critical"] else ""
        logger.info(f"{r['attacker']} attacked {r['target']} for {r['damage_done']:.1f} damage {crit_str}")
        logger.info(f"  Attacker stamina: {r['attacker_stamina_before']:.1f} → {r['attacker_stamina_after']:.1f}")
        logger.info(f"  Target stamina: {r['target_stamina_before']:.1f} → {r['target_stamina_after']:.1f}")
            
    return results


# Main test function
def main():
    """Main test function"""
    logger.info("Starting stamina system integration test...")
    
    # Create registry and config
    registry = SystemRegistry()
    config = {
        "paths": {
            "stamina_integration_config": "stamina_integration_config.json"
        }
    }
    
    # Create mock systems
    stamina_system = MockStaminaSystem(config, registry)
    trait_system = MockTraitSystem(config, registry)
    convergence_system = MockConvergenceSystem(config, registry)
    combat_system = MockCombatSystem(config, registry)
    event_system = MockEventSystem(config, registry)
    
    # Register systems
    registry.register("stamina_system", stamina_system)
    registry.register("trait_system", trait_system)
    registry.register("convergence_system", convergence_system)
    registry.register("combat_system", combat_system)
    registry.register("event_system", event_system)
    
    # Import integrators
    # For a real test, you would import these from the modules
    # Here we'll assume they're already imported
    from trait_stamina_integrator import TraitStaminaIntegrator
    from convergence_stamina_integrator import ConvergenceStaminaIntegrator
    from combat_stamina_integrator import CombatStaminaIntegrator
    from stamina_system_integrator import StaminaSystemIntegrator
    
    # Create integrators
    trait_integrator = TraitStaminaIntegrator(config, registry)
    convergence_integrator = ConvergenceStaminaIntegrator(config, registry)
    combat_integrator = CombatStaminaIntegrator(config, registry)
    
    # Register integrators
    registry.register("trait_stamina_integrator", trait_integrator)
    registry.register("convergence_stamina_integrator", convergence_integrator)
    registry.register("combat_stamina_integrator", combat_integrator)
    
    # Create main integrator
    system_integrator = StaminaSystemIntegrator(config, registry)
    registry.register("stamina_system_integrator", system_integrator)
    
    # Activate all systems
    for system_name in registry.get_all_systems():
        registry.activate(system_name)
        
    # Create test characters
    characters = create_test_characters()
    
    # Create match context
    match_context = {
        "match_id": "test_match_001",
        "round": 1,
        "day": 1,
        "stamina_logs": []
    }
    
    # Initialize stamina for all characters
    for character in characters:
        stamina_system.initialize_character_stamina(character)
        
    # Test trait-stamina integration
    trait_results = test_trait_stamina_integration(system_integrator, characters, match_context)
    
    # Test convergence-stamina integration
    convergence_results = test_convergence_stamina_integration(system_integrator, characters, match_context)
    
    # Test combat-stamina integration
    combat_results = test_combat_stamina_integration(system_integrator, characters, match_context)
    
    # Test end of round effects
    logger.info("Testing end of round effects...")
    for character in characters:
        character["stamina"] = 50.0  # Set all to 50% stamina
        
    stamina_system.apply_end_of_round_effects(characters, match_context)
    
    logger.info("Stamina after end of round recovery:")
    for character in characters:
        logger.info(f"{character['name']}: {character['stamina']:.1f}")
        
    # Test overnight recovery
    logger.info("Testing overnight recovery...")
    for character in characters:
        character["stamina"] = 40.0  # Set all to 40% stamina
        
    for character in characters:
        new_stamina = stamina_system.process_overnight_recovery(character)
        logger.info(f"{character['name']}: 40.0 → {new_stamina:.1f}")
        
    # Generate analytics
    logger.info("Generating stamina analytics...")
    match_results = {
        "match_id": match_context["match_id"],
        "day": match_context["day"],
        "character_results": [
            {
                "character_id": char["id"],
                "character_name": char["name"],
                "team_id": char["team_id"],
                "stamina_log": char.get("stamina_log", [])
            }
            for char in characters
        ],
        "stamina_logs": match_context.get("stamina_logs", [])
    }
    
    analytics = system_integrator.integrators.get("stamina_system").generate_stamina_analytics(match_results)
    
    logger.info("Test completed successfully!")
    return {
        "trait_results": trait_results,
        "convergence_results": convergence_results,
        "combat_results": combat_results,
        "analytics": analytics
    }


# Run the test when script is executed directly
if __name__ == "__main__":
    main()

