import requests
import streamlit as st


@st.cache_data
def fetch_pokemon_list():
    try:
        r = requests.get("https://pokeapi.co/api/v2/pokemon?limit=151", timeout=10)
        r.raise_for_status()
        return [p["name"] for p in r.json()["results"]]
    except requests.RequestException:
        st.error("Failed to load Pokemon list.")
        return []


@st.cache_data
def fetch_pokemon(name):
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower().strip()}", timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "name": data["name"],
            "sprite": data["sprites"]["front_default"],
            "types": [t["type"]["name"] for t in data["types"]],
            "stats": {s["stat"]["name"]: s["base_stat"] for s in data["stats"]},
            "moves": [m["move"]["name"] for m in data["moves"]],
        }
    except requests.RequestException:
        st.error(f"Could not fetch '{name}'.")
        return None


@st.cache_data
def fetch_move(move_name):
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/move/{move_name}", timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "name": data["name"],
            "power": data["power"],
            "accuracy": data["accuracy"],
            "type": data["type"]["name"],
            "damage_class": data["damage_class"]["name"],
        }
    except requests.RequestException:
        return None


@st.cache_data
def fetch_type_effectiveness(move_type):
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/type/{move_type}", timeout=10)
        r.raise_for_status()
        dr = r.json()["damage_relations"]
        return {
            "double_damage_to": [t["name"] for t in dr["double_damage_to"]],
            "half_damage_to":   [t["name"] for t in dr["half_damage_to"]],
            "no_damage_to":     [t["name"] for t in dr["no_damage_to"]],
        }
    except requests.RequestException:
        return {"double_damage_to": [], "half_damage_to": [], "no_damage_to": []}


@st.cache_data
def get_damaging_moves(move_names, max_checked=60):
    damaging = []
    for name in move_names[:max_checked]:
        move = fetch_move(name)
        if move and move["power"] and move["power"] > 0:
            damaging.append(move)
        if len(damaging) >= 20:
            break
    return damaging

