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
