# META Fantasy League Parity Testing Demonstration

This demonstration shows how to use the new parity modules to test and improve fairness in your META Fantasy League simulation.

## Basic Usage Example

```python
# Import necessary modules
from meta_simulator import MetaLeagueSimulator
from systems.initiative_randomizer import randomize_team_order
from systems.buffered_damage import BufferedDamageSystem
from systems.enhanced_field_leader import FieldLeaderEnhancer
from systems.loss_conditions import LossConditionSystem
from systems.convergence_balancer import ConvergenceBalancer
from systems.momentum_system import MomentumSystem
from utils.parity_tester import ParityTester
from utils.loaders import load_lineups_from_excel

# Initialize the simulator
simulator = MetaLeagueSimulator()

# Load teams
teams = load_lineups_from_excel("data/lineups/All Lineups 1.xlsx")
team_a = teams.get("t001", [])
team_b = teams.get("t002", [])

# Quick demonstration of each module

# 1. Initiative Randomizer
first_team, first_boards, first_id, second_team, second_boards, second_id = randomize_team_order(
    team_a, [], team_b, []
)
print(f"First team to process: Team {first_id}")

# 2. Enhanced Field Leader
fl_enhancer = FieldLeaderEnhancer()
enhanced_a, enhanced_b = fl_enhancer.enhance_field_leaders(
    [char.copy() for char in team_a],
    [char.copy() for char in team_b]
)

# Find the Field Leaders
fl_a = next((char for char in enhanced_a if char.get("role") == "FL"), None)
fl_b = next((char for char in enhanced_b if char.get("role") == "FL"), None)

print(f"Team A FL: {fl_a['name']} - HP: {fl_a['HP']}, Traits: {fl_a['traits']}")
print(f"Team B FL: {fl_b['name']} - HP: {fl_b['HP']}, Traits: {fl_b['traits']}")

# 3. Loss Conditions
loss_system = LossConditionSystem()
is_loss, reason = loss_system.check_team_loss(team_a)
print(f"Team A loss status: {is_loss}, Reason: {reason}")

# 4. Run comprehensive parity tests
tester = ParityTester(simulator)

# Set up a small test to demonstrate
mini_test_results = tester.run_mirrored_tests(team_a, team_b, iterations=2, save_results=False)
print(f"Team A win rate: {mini_test_results['team_a_win_rate']:.1f}%")
print(f"Team B win rate: {mini_test_results['team_b_win_rate']:.1f}%")
```

## Testing Before and After Improvements

To properly assess the impact of the parity improvements, you should run tests both before and after implementing the changes:

```python
import copy
import json

# 1. Test with original simulator
original_simulator = MetaLeagueSimulator()
original_tester = ParityTester(original_simulator)

print("Running tests with original simulator...")
original_results = original_tester.run_mirrored_tests(
    copy.deepcopy(team_a), 
    copy.deepcopy(team_b), 
    iterations=5
)

# 2. Apply enhancements to a new simulator instance
enhanced_simulator = MetaLeagueSimulator()

# Apply the modules manually for testing
def apply_enhancements(simulator):
    # Add the enhanced systems
    simulator.buffered_damage = BufferedDamageSystem()
    simulator.field_leader_enhancer = FieldLeaderEnhancer()
    simulator.loss_condition_system = LossConditionSystem()
    simulator.convergence_balancer = ConvergenceBalancer()
    simulator.momentum_system = MomentumSystem()
    
    # Override the method that checks team loss
    original_check = simulator._check_team_loss_conditions
    simulator._check_team_loss_conditions = lambda team: simulator.loss_condition_system.check_team_loss(team)[0]
    
    # Override convergence processing
    original_process = simulator._process_convergences
    
    def enhanced_process(team_a, team_a_boards, team_b, team_b_boards, match_context, show_details=True):
        # Use initiative randomizer
        first_team, first_boards, first_id, second_team, second_boards, second_id = randomize_team_order(
            team_a, team_a_boards, team_b, team_b_boards
        )
        
        # Call original method with randomized order
        return original_process(first_team, first_boards, second_team, second_boards, match_context, show_details)
    
    simulator._process_convergences = enhanced_process
    
    return simulator

# Apply enhancements and run tests
enhanced_simulator = apply_enhancements(enhanced_simulator)
enhanced_tester = ParityTester(enhanced_simulator)

print("\nRunning tests with enhanced simulator...")
enhanced_results = enhanced_tester.run_mirrored_tests(
    copy.deepcopy(team_a), 
    copy.deepcopy(team_b), 
    iterations=5
)

# 3. Compare results
print("\n=== COMPARISON OF RESULTS ===")
print(f"Original Team A win rate: {original_results['team_a_win_rate']:.1f}%")
print(f"Original Team B win rate: {original_results['team_b_win_rate']:.1f}%")
print(f"Original Position advantage: {original_results['position_advantage_pct']:.1f}%")

print(f"\nEnhanced Team A win rate: {enhanced_results['team_a_win_rate']:.1f}%")
print(f"Enhanced Team B win rate: {enhanced_results['team_b_win_rate']:.1f}%")
print(f"Enhanced Position advantage: {enhanced_results['position_advantage_pct']:.1f}%")

improvement = abs(50 - original_results['team_a_win_rate']) - abs(50 - enhanced_results['team_a_win_rate'])
print(f"\nImprovement in team balance: {improvement:.1f}%")
```

## Visualizing Improvements

To better visualize the improvements in parity, you can create a simple bar chart:

```python
import matplotlib.pyplot as plt
import numpy as np

# Create bar chart comparing original vs enhanced
labels = ['Team A Win %', 'Team B Win %', 'Position A Win %', 'Position B Win %']
original_values = [
    original_results['team_a_win_rate'],
    original_results['team_b_win_rate'],
    original_results['position_a_win_rate'],
    original_results['position_b_win_rate']
]
enhanced_values = [
    enhanced_results['team_a_win_rate'],
    enhanced_results['team_b_win_rate'],
    enhanced_results['position_a_win_rate'],
    enhanced_results['position_b_win_rate']
]

x = np.arange(len(labels))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x - width/2, original_values, width, label='Original')
ax.bar(x + width/2, enhanced_values, width, label='Enhanced')

ax.set_ylabel('Win Rate (%)')
ax.set_title('Comparison of Team and Position Win Rates')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()

# Add a horizontal line at 50% for perfect parity reference
ax.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='Perfect Parity')

# Add values on top of bars
for i, v in enumerate(original_values):
    ax.text(i - width/2, v + 1, f"{v:.1f}%", ha='center')
for i, v in enumerate(enhanced_values):
    ax.text(i + width/2, v + 1, f"{v:.1f}%", ha='center')

plt.tight_layout()
plt.savefig("parity_improvement_results.png")
plt.show()