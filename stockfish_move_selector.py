# stockfish_move_selector.py
# Scores and selects moves using Stockfish with trait-based biases

import chess
import chess.engine
from typing import List

STOCKFISH_PATH = "/usr/bin/stockfish"  # Modify if needed

# Default trait modifiers (example schema)
TRAIT_BIAS = {
    "aggressive": {"favor_attacks": 1.5},
    "defensive": {"favor_safety": 1.3},
    "flanker": {"favor_edges": 1.2},
    "ambusher": {"surprise": 1.4}
}


def score_moves_with_traits(board: chess.Board, legal_moves: List[chess.Move], traits: List[str], time_limit=0.05) -> chess.Move:
    """
    Uses Stockfish to evaluate all legal moves and applies bias modifiers based on traits.
    Returns the best move after weighting.
    """
    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            move_scores = []
            for move in legal_moves:
                board.push(move)
                info = engine.analyse(board, chess.engine.Limit(time=time_limit))
                board.pop()

                score_cp = info["score"].relative.score(mate_score=10000) or 0
                score = apply_trait_bias(board, move, score_cp, traits)
                move_scores.append((move, score))

            # Select move with best adjusted score
            best_move = max(move_scores, key=lambda x: x[1])[0]
            return best_move
    except FileNotFoundError:
        raise RuntimeError("Stockfish binary not found. Update STOCKFISH_PATH.")


def apply_trait_bias(board, move, base_score, traits):
    """
    Modifies Stockfish score based on trait preferences (placeholder logic).
    """
    bias = 1.0
    for trait in traits:
        modifiers = TRAIT_BIAS.get(trait, {})
        if "favor_attacks" in modifiers:
            if board.is_capture(move):
                bias *= modifiers["favor_attacks"]
        if "favor_edges" in modifiers:
            if move.to_square % 8 in [0, 7]:  # A or H file
                bias *= modifiers["favor_edges"]
    return base_score * bias


# Note: This file assumes Stockfish is locally installed.
# It will fail silently if Stockfish is missing or inaccessible.