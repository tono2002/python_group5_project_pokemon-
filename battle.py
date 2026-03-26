import random
from api import fetch_type_effectiveness


def calculate_effectiveness(move_type, defender_types):
    type_data = fetch_type_effectiveness(move_type)
    mult = 1.0
    for dtype in defender_types:
        if dtype in type_data["double_damage_to"]:   mult *= 2.0
        elif dtype in type_data["half_damage_to"]:   mult *= 0.5
        elif dtype in type_data["no_damage_to"]:     mult *= 0.0
    return mult


def calculate_damage(attacker_stats, defender_stats, defender_types, move):
    if move["damage_class"] == "physical":
        atk, dfs = attacker_stats["attack"], defender_stats["defense"]
    else:
        atk, dfs = attacker_stats["special-attack"], defender_stats["special-defense"]
    eff = calculate_effectiveness(move["type"], defender_types)
    acc = move["accuracy"] if move["accuracy"] else 100
    if random.random() < acc / 100:
        return int(((2 * 50 / 5 + 2) * move["power"] * (atk / dfs) / 50 + 2) * eff), eff, False
    return 0, eff, True


def eff_label(eff, missed):
    if missed:      return "Missed!"
    if eff > 1.0:   return "Super effective!"
    if 0 < eff < 1: return "Not very effective"
    if eff == 0:    return "No effect"
    return ""


def run_battle(p1, p2, move1, move2):
    hp1, hp2 = p1["stats"]["hp"], p2["stats"]["hp"]
    battle_log = []
    hp_history = [{"round": 0, "pokemon": p1["name"], "hp": hp1},
                  {"round": 0, "pokemon": p2["name"], "hp": hp2}]

    for rnd in range(1, 101):
        s1, s2 = p1["stats"]["speed"], p2["stats"]["speed"]
        if s1 != s2:
            first, second = ((p1,p2,move1,move2),(p2,p1,move2,move1)) if s1 > s2 else ((p2,p1,move2,move1),(p1,p2,move1,move2))
        else:
            first, second = ((p1,p2,move1,move2),(p2,p1,move2,move1)) if random.random() < 0.5 else ((p2,p1,move2,move1),(p1,p2,move1,move2))

        hps = {"hp1": hp1, "hp2": hp2}
        for att, dfn, a_mv, _ in [first]:
            k = "hp2" if att is p1 else "hp1"
            dmg, eff, missed = calculate_damage(att["stats"], dfn["stats"], dfn["types"], a_mv)
            hps[k] = max(0, hps[k] - dmg)
            battle_log.append({"round": rnd, "attacker": att["name"], "move": a_mv["name"],
                                "damage": dmg, "effectiveness": eff_label(eff, missed), "defender_hp": hps[k]})

        hp1, hp2 = hps["hp1"], hps["hp2"]
        if hp1 <= 0 or hp2 <= 0:
            hp_history += [{"round": rnd, "pokemon": p1["name"], "hp": hp1},
                           {"round": rnd, "pokemon": p2["name"], "hp": hp2}]
            break

        for att, dfn, a_mv, _ in [second]:
            k = "hp2" if att is p1 else "hp1"
            dmg, eff, missed = calculate_damage(att["stats"], dfn["stats"], dfn["types"], a_mv)
            hps[k] = max(0, hps[k] - dmg)
            battle_log.append({"round": rnd, "attacker": att["name"], "move": a_mv["name"],
                                "damage": dmg, "effectiveness": eff_label(eff, missed), "defender_hp": hps[k]})

        hp1, hp2 = hps["hp1"], hps["hp2"]
        hp_history += [{"round": rnd, "pokemon": p1["name"], "hp": hp1},
                       {"round": rnd, "pokemon": p2["name"], "hp": hp2}]
        if hp1 <= 0 or hp2 <= 0:
            break

    if hp1 <= 0 and hp2 <= 0:   winner = "Draw!"
    elif hp1 <= 0:               winner = f"{p2['name'].title()} wins!"
    elif hp2 <= 0:               winner = f"{p1['name'].title()} wins!"
    else:                        winner = "Draw — 100 round limit"
    return battle_log, hp_history, winner