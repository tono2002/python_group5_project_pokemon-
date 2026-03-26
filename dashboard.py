import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from api import fetch_pokemon_list, fetch_pokemon, get_damaging_moves
from battle import run_battle

st.set_page_config(page_title="Pokemon Combat Simulator", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap');
html,body,[class*="css"],.stApp{font-family:'DM Sans',sans-serif;}
h1{font-weight:300;letter-spacing:-1.5px;font-size:2.8rem;} h2{font-weight:300;letter-spacing:-.5px;margin-top:1.4rem;} h3{font-weight:400;margin:.2rem 0;}
footer{visibility:hidden;} [data-testid="stHeader"]{background:transparent;} [data-testid="stTabs"] button{font-family:'DM Sans',sans-serif;font-weight:400;}
.stButton>button{background:#111;color:#fff;border:none;border-radius:6px;padding:.55rem 2.4rem;font-family:'DM Sans',sans-serif;font-weight:400;letter-spacing:.3px;transition:background .2s,transform .1s;}
.stButton>button:hover{background:#333;color:#fff;transform:translateY(-1px);} .stButton>button:active{transform:translateY(0);}
.stButton>button[kind="primary"]{background:#e63946;font-size:1.1rem;padding:.75rem 3rem;letter-spacing:1px;} .stButton>button[kind="primary"]:hover{background:#c1121f;color:#fff;}
[data-testid="stDialog"] .stButton>button{padding:.2rem .1rem;font-size:.58rem;letter-spacing:.3px;border-radius:4px;}
@keyframes pop{0%{transform:scale(.92);opacity:0;}100%{transform:scale(1);opacity:1;}}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
@keyframes countdown{0%{transform:scale(1.4);opacity:0;}20%,80%{transform:scale(1);opacity:1;}100%{transform:scale(.8);opacity:0;}}
</style>""", unsafe_allow_html=True)

COLORS = ["#111111", "#e63946"]; CHART_TEMPLATE = "plotly_white"
SPRITE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{}.png"
TYPE_COLORS = {
    "fire":("#FF6B35","#fff"),"water":("#29B6F6","#fff"),"grass":("#66BB6A","#fff"),"electric":("#FFD600","#000"),
    "psychic":("#EC407A","#fff"),"ice":("#26C6DA","#000"),"dragon":("#5C6BC0","#fff"),"dark":("#37474F","#fff"),
    "fairy":("#F48FB1","#000"),"normal":("#9E9E9E","#fff"),"fighting":("#EF5350","#fff"),"flying":("#7986CB","#fff"),
    "poison":("#AB47BC","#fff"),"ground":("#FFCA28","#000"),"rock":("#8D6E63","#fff"),"bug":("#9CCC65","#000"),
    "ghost":("#7E57C2","#fff"),"steel":("#78909C","#fff"),}

def type_badges(types):
    return "".join(f'<span style="background:{TYPE_COLORS.get(t,("#aaa","#fff"))[0]};color:{TYPE_COLORS.get(t,("#aaa","#fff"))[1]};padding:3px 12px;border-radius:20px;font-size:.72rem;font-weight:500;letter-spacing:.8px;margin-right:5px;">{t.upper()}</span>' for t in types)

def stat_bar(label, value, max_val=255):
    p = int(value/max_val*100); c = "#4CAF50" if p>55 else "#FF9800" if p>28 else "#EF5350"
    return f'<div style="margin-bottom:7px;"><div style="display:flex;justify-content:space-between;font-size:.78rem;margin-bottom:3px;color:#444;"><span>{label}</span><span style="font-weight:500;">{value}</span></div><div style="background:#f0f0f0;border-radius:4px;height:5px;"><div style="background:{c};width:{p}%;height:5px;border-radius:4px;"></div></div></div>'

def move_card(move):
    b, f = TYPE_COLORS.get(move["type"], ("#aaa","#fff"))
    return (f'<div style="border-left:4px solid {b};background:#fafafa;border-radius:0 8px 8px 0;padding:.7rem 1rem;margin-top:.5rem;animation:fadeIn .3s ease;">'
            f'<span style="background:{b};color:{f};padding:2px 10px;border-radius:20px;font-size:.7rem;font-weight:500;letter-spacing:.8px;">{move["type"].upper()}</span>'
            f' &nbsp;PWR <b>{move["power"]}</b> · ACC <b>{move["accuracy"]}</b> · {move["damage_class"].title()}</div>')

winner_banner = lambda t: f'<div style="background:#111;color:#fff;padding:1.3rem 2rem;border-radius:8px;text-align:center;font-size:1.7rem;font-weight:300;letter-spacing:-.5px;animation:pop .35s ease;margin:1rem 0;">{t}</div>'

def radar_chart(p1, p2):
    labels = ["hp","attack","defense","special-attack","special-defense","speed"]
    fig = go.Figure()
    for poke, color in [(p1,COLORS[0]),(p2,COLORS[1])]:
        vals = [poke["stats"][s] for s in labels]
        fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=[s.upper() for s in labels]+[labels[0].upper()],
            name=poke["name"].title(), line=dict(color=color,width=2), fill="toself", fillcolor=color, opacity=0.12))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,255])), template=CHART_TEMPLATE,
        font_family="DM Sans", title="Stat Radar", title_font_weight=300, height=240, margin=dict(t=40,b=20))
    return fig

for k, v in [("p1_idx",24),("p2_idx",5),("battle_results",None)]:
    if k not in st.session_state: st.session_state[k] = v
pokemon_list = fetch_pokemon_list()
if not pokemon_list: st.stop()

@st.dialog("Choose a Pokemon", width="large")
def pokemon_album(slot):
    search = st.text_input("", placeholder="Search...", label_visibility="collapsed")
    filtered = [(i,n) for i,n in enumerate(pokemon_list) if search.lower() in n.lower()]
    for row_start in range(0, len(filtered), 9):
        for col,(idx,name) in zip(st.columns(9), filtered[row_start:row_start+9]):
            with col:
                st.image(SPRITE_URL.format(idx+1), use_container_width=True)
                if st.button(name.upper(), key=f"pick_{name}", use_container_width=True):
                    st.session_state[slot] = idx; st.rerun()

st.markdown("""<div style="text-align:center;padding:2rem 0 .5rem;">
<h1 style="font-weight:300;letter-spacing:-2px;font-size:3rem;margin-bottom:.4rem;">Pokemon Combat Simulator</h1>
<p style="font-size:.78rem;letter-spacing:1.5px;color:#aaa;margin:0 0 1.2rem;"><span style="color:#e63946;">ANTONIO ABAD BALLBÉ</span> &nbsp;·&nbsp; <span style="color:#111;">DIEGO ALFARO GÓMEZ</span> &nbsp;·&nbsp; <span style="color:#e63946;">ANDREA ALARCÓN VALLES</span> &nbsp;·&nbsp; <span style="color:#111;">JO AL AHMAR</span> &nbsp;·&nbsp; <span style="color:#e63946;">VLAD-MATEI MARINESCU</span></p>
<p style="font-size:.9rem;color:#555;max-width:560px;margin:0 auto;font-weight:300;line-height:1.6;">Pick two Pokemon from the original 151, equip them with moves, and simulate a turn-based battle. Speed decides who strikes first — type matchups, accuracy, and stats shape every round.</p>
</div>""", unsafe_allow_html=True)
st.divider()

st.header("Choose your Pokemon")
col1, mid, col2 = st.columns([5,1,5])
with col1:
    idx1 = st.session_state.p1_idx
    img_col, info_col = st.columns([1,2])
    with img_col:
        st.image(SPRITE_URL.format(idx1+1), use_container_width=True)
        if st.button("Change", key="open_p1", use_container_width=True): pokemon_album("p1_idx")
    with info_col:
        poke1_name = pokemon_list[idx1]
        st.markdown(f"<h3 style='margin-bottom:4px;'>{poke1_name.upper()}</h3>", unsafe_allow_html=True)
with mid:
    st.markdown("<div style='text-align:center;font-size:2rem;font-weight:300;padding-top:3rem;letter-spacing:2px;color:#ccc;'>VS</div>", unsafe_allow_html=True)
with col2:
    idx2 = st.session_state.p2_idx
    img_col2, info_col2 = st.columns([1,2])
    with img_col2:
        st.image(SPRITE_URL.format(idx2+1), use_container_width=True)
        if st.button("Change", key="open_p2", use_container_width=True): pokemon_album("p2_idx")
    with info_col2:
        poke2_name = pokemon_list[idx2]
        st.markdown(f"<h3 style='margin-bottom:4px;'>{poke2_name.upper()}</h3>", unsafe_allow_html=True)

if poke1_name == poke2_name: st.warning("Both players selected the same Pokemon.")
poke1 = fetch_pokemon(poke1_name); poke2 = fetch_pokemon(poke2_name)
if not poke1 or not poke2: st.stop()

with col1:
    with info_col:
        st.markdown(type_badges(poke1["types"]) + "<br>" + "".join(stat_bar(k,v) for k,v in poke1["stats"].items()), unsafe_allow_html=True)
with col2:
    with info_col2:
        st.markdown(type_badges(poke2["types"]) + "<br>" + "".join(stat_bar(k,v) for k,v in poke2["stats"].items()), unsafe_allow_html=True)

st.divider(); st.header("Select Moves")
damaging1 = get_damaging_moves(tuple(poke1["moves"])); damaging2 = get_damaging_moves(tuple(poke2["moves"]))
if not damaging1 or not damaging2: st.error("Could not load moves."); st.stop()
col1, col2 = st.columns(2)
with col1:
    move1_name = st.selectbox(f"Move for {poke1['name'].title()}", [m["name"] for m in damaging1], format_func=lambda x: x.upper())
    move1 = next(m for m in damaging1 if m["name"] == move1_name); st.markdown(move_card(move1), unsafe_allow_html=True)
with col2:
    move2_name = st.selectbox(f"Move for {poke2['name'].title()}", [m["name"] for m in damaging2], format_func=lambda x: x.upper())
    move2 = next(m for m in damaging2 if m["name"] == move2_name); st.markdown(move_card(move2), unsafe_allow_html=True)

st.divider(); st.header("Stat Comparison")
stat_df = pd.DataFrame([{"pokemon":poke1["name"],**poke1["stats"]},{"pokemon":poke2["name"],**poke2["stats"]}])
melted = stat_df.melt(id_vars="pokemon", var_name="stat", value_name="value")
fig_stats = px.bar(melted, x="stat", y="value", color="pokemon", barmode="group",
                   color_discrete_sequence=COLORS, template=CHART_TEMPLATE, title="Base Stats")
fig_stats.update_layout(font_family="DM Sans", title_font_weight=300, height=240, margin=dict(t=40,b=20,l=10,r=10))
tab1, tab2 = st.tabs(["Bar Chart","Radar"])
with tab1: st.plotly_chart(fig_stats, use_container_width=True)
with tab2: st.plotly_chart(radar_chart(poke1,poke2), use_container_width=True)

st.divider(); st.header("Battle")
left, center, right = st.columns([2,1,2])
with left:
    st.markdown(f"<div style='text-align:center;'><img src='{poke1['sprite']}' width='90'><p style='font-size:.8rem;font-weight:500;letter-spacing:.5px;margin-top:-4px;'>{poke1['name'].upper()}</p></div>", unsafe_allow_html=True)
with center:
    st.markdown("<div style='padding-top:2rem;'>", unsafe_allow_html=True)
    battle_clicked = st.button("Battle!", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with right:
    st.markdown(f"<div style='text-align:center;'><img src='{poke2['sprite']}' width='90'><p style='font-size:.8rem;font-weight:500;letter-spacing:.5px;margin-top:-4px;'>{poke2['name'].upper()}</p></div>", unsafe_allow_html=True)

if battle_clicked:
    slot = st.empty()
    for n in ["3","2","1","⚔"]:
        slot.markdown(f'<div style="text-align:center;font-size:5rem;font-weight:300;animation:countdown .8s ease;letter-spacing:-2px;">{n}</div>', unsafe_allow_html=True)
        time.sleep(0.8)
    slot.empty(); st.session_state.battle_results = run_battle(poke1, poke2, move1, move2)

if st.session_state.battle_results:
    battle_log, hp_history, winner = st.session_state.battle_results
    st.markdown(winner_banner(winner), unsafe_allow_html=True)
    EFF = {"Super effective!":"background-color:#d4edda;color:#155724;","Not very effective":"background-color:#fff3cd;color:#856404;",
           "No effect":"background-color:#e2e3e5;color:#383d41;","Missed!":"background-color:#f8d7da;color:#721c24;"}
    log_df = pd.DataFrame(battle_log)
    st.dataframe(log_df.style.applymap(lambda v: EFF.get(v,""), subset=["effectiveness"]), use_container_width=True, height=220)
    _, center2, _ = st.columns([2,1,2])
    with center2:
        if st.button("Rematch!", use_container_width=True):
            slot2 = st.empty()
            for n in ["3","2","1","⚔"]:
                slot2.markdown(f'<div style="text-align:center;font-size:5rem;font-weight:300;animation:countdown .8s ease;letter-spacing:-2px;">{n}</div>', unsafe_allow_html=True)
                time.sleep(0.8)
            slot2.empty(); st.session_state.battle_results = run_battle(poke1, poke2, move1, move2); st.rerun()
    st.header("HP Over Time")
    hp_df = pd.DataFrame(hp_history)
    fig_hp = px.line(hp_df, x="round", y="hp", color="pokemon", markers=True,
                     color_discrete_sequence=COLORS, template=CHART_TEMPLATE, title="HP Over Time")
    fig_hp.update_traces(line=dict(width=3))
    fig_hp.update_layout(font_family="DM Sans", title_font_weight=300, height=280, margin=dict(t=40,b=20))
    st.plotly_chart(fig_hp, use_container_width=True)