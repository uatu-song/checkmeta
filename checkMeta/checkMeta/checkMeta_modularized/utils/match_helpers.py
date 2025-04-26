# utils/match_helpers.py
import chess

def calculate_material(board: chess.Board) -> int:
    material = 0
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9
    }
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == chess.WHITE:
            material += piece_values.get(piece.piece_type, 0)
    return material
