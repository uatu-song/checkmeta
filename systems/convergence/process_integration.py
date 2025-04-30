"""
process_convergences.py

Handles convergence logic, cross-board interactions, and multi-player effects.
Patched for rStats compliance: emits convergence_triggered and assist_given events.
"""

from event_emitter import EventEmitter
import logging

class ConvergenceProcessor:
    def __init__(self, registry, config):
        self.registry = registry
        self.config = config
        self.logger = logging.getLogger("ConvergenceProcessor")
        self.emitter = EventEmitter("convergence_events.jsonl")

    def apply_convergence(self, assister_id, recipient_id, board_id, turn, convergence_type):
        # Log internally
        self.logger.info(f"{assister_id} assists {recipient_id} via {convergence_type} on {board_id} (turn {turn})")

        # Emit assist_given
        self.emitter.emit("assist_given", {
            "assister_id": assister_id,
            "recipient_id": recipient_id,
            "convergence_type": convergence_type,
            "board_id": board_id,
            "turn": turn
        })

        # Emit convergence_triggered
        self.emitter.emit("convergence_triggered", {
            "board_id": board_id,
            "participants": [assister_id, recipient_id],
            "convergence_type": convergence_type,
            "turn": turn
        })
