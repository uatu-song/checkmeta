# systems/chess_engine.py
import chess
import random

def apply_opening_moves(board: chess.Board, opening_moves):
    for move_san in opening_moves:
        try:
            move = board.parse_san(move_san)
            board.push(move)
        except Exception:
            continue

def select_move(board: chess.Board, unit: dict, stockfish_path=None) -> chess.Move:
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None
    return random.choice(legal_moves)
