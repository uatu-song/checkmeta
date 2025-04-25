# simulate_match.py
# Simulates one match between a white and black unit using PGN, material loss, and convergence logic

from life_state_scaffold import inject_life_meter, is_unit_dead
from checkMeta_core_engine import evaluate_post_match
from material_loss_engine import calculate_material_loss
from convergence_trait_engine import evaluate_convergence
from rstat_logger import log_rstats

SAMPLE_PGN = """
[Event "Test"]
[Site "Sim"]
[Date "2025.04.25"]
[Round "1"]
[White "Unit"]
[Black "AI"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Bxc6 dxc6 5. Nxe5 Qd4 6. Nf3 Qxe4+ 7. Qe2 Qxe2+ 8. Kxe2
"""


def simulate_match(match: dict, pgn_text: str = SAMPLE_PGN) -> dict:
    """
    Simulates a match:
    - Injects full life status
    - Calculates material loss
    - Triggers convergence and trait effects
    - Applies post-match consequences
    - Logs result stats (rStats)
    """
    white = inject_life_meter(match["white"])
    black = inject_life_meter(match["black"])

    material_loss = calculate_material_loss(pgn_text)
    white_convergence = evaluate_convergence(white, material_loss["white_loss"])
    black_convergence = evaluate_convergence(black, material_loss["black_loss"])

    white_rstats = log_rstats(white, white_convergence, material_loss["white_loss"])
    black_rstats = log_rstats(black, black_convergence, material_loss["black_loss"])

    white = evaluate_post_match(white)
    black = evaluate_post_match(black)

    return {
        "match_id": match["match_id"],
        "white": white,
        "black": black,
        "material_loss": material_loss,
        "convergence": {
            "white": white_convergence,
            "black": black_convergence
        },
        "rStats": {
            "white": white_rstats,
            "black": black_rstats
        }
    }


# Example
if __name__ == "__main__":
    match_input = {
        "match_id": "match_01",
        "white": {"id": "unit_1", "role": "FL", "traits": [], "aStats": {"aINT": 0.7, "aLCK": 0.3}},
        "black": {"id": "unit_2", "role": "VG", "traits": [], "aStats": {"aINT": 0.2, "aLCK": 0.1}}
    }
    result = simulate_match(match_input)
    print("Simulated Match:", result)