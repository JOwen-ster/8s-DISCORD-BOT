# first select the game_id corresponding to the host's id
# then select all players ids who belong to that game_reference
# Ensure teams are not the same as last round (store each role for both teams and the game_id)
# Ensure roles are still valid before shuffling and store the players id : their current role
# check isAlpha column for each player using their id, build 2 current teams then shuffle

import random

async def shuffle_teams(player_map: dict[int, str]) -> tuple[dict[str, str | list[str]]]:
    """
    Shuffle 8 players into alpha and bravo teams based on role rules.

    Parameters:
    - player_map: Dict[player_id, role] where role is one of
    "8s-backline", "8s-support", "8s-slayer"

    Returns:
    - Tuple of two dicts: (alpha_team, bravo_team)
    Each dict has keys: "backline", "support", "slayers"
    """

    # Separate players by role
    backlines = [pid for pid, role in player_map.items() if role == "8s-backline"]
    supports = [pid for pid, role in player_map.items() if role == "8s-support"]
    slayers = [pid for pid, role in player_map.items() if role == "8s-slayer"]

    assert len(backlines) == 2 and len(supports) == 2 and len(slayers) == 4, "Invalid role counts"

    # Backlines: one on each team
    alpha_backline, bravo_backline = backlines

    # Supports: swap every time
    alpha_support, bravo_support = supports[::-1]

    # Slayers: shuffle using fisher yates algorithm
    random.shuffle(slayers)
    alpha_slayers = slayers[:2]
    bravo_slayers = slayers[2:]

    # Construct team dicts
    alpha_team = {
        "backline": alpha_backline,
        "support": alpha_support,
        "slayers": alpha_slayers
    }

    bravo_team = {
        "backline": bravo_backline,
        "support": bravo_support,
        "slayers": bravo_slayers
    }

    return alpha_team, bravo_team
