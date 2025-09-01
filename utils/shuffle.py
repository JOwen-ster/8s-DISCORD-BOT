# first select the game_id corresponding to the host's id
# then select all players ids who belong to that game_reference
# Ensure teams are not the same as last round (store each role for both teams and the game_id)
# Ensure roles are still valid before shuffling and store the players id : their current role
# check isAlpha column for each player using their id, build 2 current teams then shuffle

import random


def split_into_teams(players_map: dict[int, str]):
    if len(players_map) != 8: 
        return

    backlines, supports, slayers = [], [], []

    for id, role_name in players_map.items():
        match role_name:
            case "8s-backline":
                backlines.append(id)
            case "8s-support":
                supports.append(id)
            case _:
                slayers.append(id)

    alpha = {
        "backline": backlines[0],
        "support": supports[0],
        "slayers": [slayers[0], slayers[1]],
    }

    bravo = {
        "backline": backlines[1],
        "support": supports[1],
        "slayers": [slayers[2], slayers[3]],
    }

    return alpha, bravo


# takes in a dict of user_id : role_name
async def shuffle_teams(player_map: dict[int, str], prev_alpha, prev_bravo) -> tuple[dict[str, str | list[str]]]:
    """
    - Shuffle 8 players into alpha and bravo teams based on role rules.

    - Returns a Tuple of two dicts representing teams. Each dict has keys: "backline", "support", "slayers"
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