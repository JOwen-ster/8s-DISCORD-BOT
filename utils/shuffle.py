# first select the game_id corresponding to the host's id
# then select all players ids who belong to that game_reference
# Ensure teams are not the same as last round (store each role for both teams and the game_id)
# Ensure roles are still valid before shuffling and store the players id : their current role
# check isAlpha column for each player using their id, build 2 current teams then shuffle

import random
import discord
from utils.logging_setup import log


async def split_into_teams(players_map: dict[int, str]):
    '''
    Split players (id) based on their selected role
    '''
    if len(players_map) != 8: 
        return None, None

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


# takes in a dict of user_id : role_name for player map and the pre are 
#"backline": backlines[0],
#"support": supports[0],
#"slayers": [slayers[0], slayers[1]] for alpha
async def shuffle_teams(
    player_map: dict[int, str], 
    prev_alpha: dict[str, int | list[int]], 
    prev_bravo: dict[str, int | list[int]]
) -> tuple[dict[str, int | list[int]], dict[str, int | list[int]]]:
    """
    Shuffle 8 players into alpha and bravo teams based on role rules.
    Ensures slayers from the previous round are not on the same team again.
    """
    # Separate players by role
    backlines = [pid for pid, role in player_map.items() if role == "8s-backline"]
    supports = [pid for pid, role in player_map.items() if role == "8s-support"]
    slayers = [pid for pid, role in player_map.items() if role == "8s-slayer"]

    assert len(backlines) == 2 and len(supports) == 2 and len(slayers) == 4, "Invalid role counts"

    # Backlines: stay in the same order
    alpha_backline, bravo_backline = backlines

    # Supports: swap every time
    alpha_support, bravo_support = supports[::-1]

    # Previous slayer groups (from maps)
    prev_alpha_set = set(prev_alpha["slayers"])
    prev_bravo_set = set(prev_bravo["slayers"])

    alpha_slayers, bravo_slayers = [], []
    for _ in range(100):
        # fisher yates alg
        random.shuffle(slayers)
        alpha_slayers = slayers[:2]
        bravo_slayers = slayers[2:]

        # Constraint check
        if set(alpha_slayers) != prev_alpha_set and set(bravo_slayers) != prev_bravo_set:
            break

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


async def drag_teams(players, split_alpha_map, split_bravo_map, bot, alpha_channel_id, bravo_channel_id):
    alpha_chnl = bot.get_channel(alpha_channel_id) or await bot.fetch_channel(alpha_channel_id)
    bravo_chnl = bot.get_channel(bravo_channel_id) or await bot.fetch_channel(bravo_channel_id)

    alpha_ids = {i for v in split_alpha_map.values() for i in (v if isinstance(v, list) else [v])}
    bravo_ids = {i for v in split_bravo_map.values() for i in (v if isinstance(v, list) else [v])}

    for player in players:
        if player.id in alpha_ids:
            await player.move_to(alpha_chnl)
        elif player.id in bravo_ids:
            await player.move_to(bravo_chnl)
        else:
            log(f'Player {player.name} - ID:{player.id} not on a team, skipping...')
