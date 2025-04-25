# chess_match_simulator.py
# Simulates a full legal chess game with White = unit, Black = AI opponent

import chess
import chess.pgn
import random
from io import StringIO


def simulate_chess_match_white(unit_traits: list = None, max_moves: int = 40) -> str:
    """
    Simulates a chess game using legal moves only.
    White = player (unit); Black = AI
    Returns PGN as string.
    """
    board = chess.Board()
    game = chess.pgn.Game()
    game.headers["Event"] = "checkMeta Simulation"
    game.headers["White"] = "Unit"
    game.headers["Black"] = "AI"
    node = game

    unit_traits = unit_traits or []

    for _ in range(max_moves):
        if board.is_game_over():
            break

        legal_moves = list(board.legal_moves)
        move = select_legal_move(board, legal_moves, unit_traits, board.turn)
        board.push(move)
        node = node.add_variation(move)

    return str(game)


def select_legal_move(board: chess.Board, legal_moves, traits, is_white_turn: bool):
    """
    Placeholder: selects a move at random.
    Trait logic will be applied later here.
    """
    return random.choice(legal_moves)


# Example run
if __name__ == "__main__":
    pgn_output = simulate_chess_match_white(["aggressive"], max_moves=20)
    print("Generated PGN:\n", pgn_output)
