###############################
# config/openings.py
###############################
"""
Role-based chess openings for META League characters
"""

# Role-based opening moves
ROLE_OPENINGS = {
    "FL": ["d4 Nf6 c4", "Nf3 d5 c4", "e4 e6"],  # Field Leader - more strategic/solid openings
    "RG": ["Nf3", "g3", "b3"],                  # Ranger
    "VG": ["e4 e5 Nf3", "d4 d5 c4"],            # Vanguard
    "EN": ["e4 e5", "e4 c5", "d4 d5 c4 e6"],    # Enforcer - aggressive openings
    "GO": ["g3", "b3", "c4"],                   # Ghost Operative
    "PO": ["d4 Nf6", "e4 e6", "c4 c5"],         # Psi Operative
    "SV": ["e4 e5 Nf3 Nc6", "d4 d5 c4 e6"]      # Sovereign
}