import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
HISTORY_PATH = BASE_DIR / "energy_scenarios.csv"

with CONFIG_PATH.open(encoding="utf-8") as f:
    CONFIG = json.load(f)

st.set_page_config(page_title="Smart Building Energy Optimizer", page_icon="⚡", layout="wide")

def analyze_room(temperature_c, people, active_appliances, energy_demand_kw=None, room_type="Classroom"):
    # Transparent illustrative estimate: appliance count is a proxy because exact appliance types are not provided.
    estimated_kw = (
        active_appliances * CONFIG["assumed_average_appliance_kw"]
        + max(0, temperature_c - CONFIG["cooling_reference_c"]) * CONFIG["cooling_kw_per_degree"]
        + people * CONFIG["occupancy_kw_per_person"]
    )
    if energy_demand_kw is not None:
        estimated_kw = max(estimated_kw, float(energy_demand_kw))
    estimated_kw = round(estimated_kw, 2)

    if estimated_kw < CONFIG["low_energy_max_kw"]:
        level = "Low"
    elif estimated_kw < CONFIG["medium_energy_max_kw"]:
        level = "Medium"
    else:
        level = "High"

    recommendations = []
    if temperature_c >= 30 and people > 0:
        recommendations.append("Maintain adequate AC cooling for the hot, occupied room. Do not switch off cooling needed for comfort.")
    elif temperature_c <= 22:
        recommendations.append("The room is relatively cool. Check whether AC can be reduced while keeping the room comfortable.")
    else:
        recommendations.append("Maintain comfortable conditions and use cooling only when needed.")

    if people == 0:
        recommendations.append("The room is unoccupied: switch off nonessential lights, fans, and other appliances.")
    elif people <= 3:
        recommendations.append("Check whether lighting or fans in unused areas can be reduced.")
    if active_appliances >= 5:
        recommendations.append("Review the active appliances and switch off only equipment that is not required.")
    if level == "High":
        recommendations.append("Compare this scenario with a lower-appliance-use scenario and inspect the largest loads.")
    elif level == "Low":
        recommendations.append("Estimated demand is low; continue sensible energy use.")

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "room_type": room_type,
        "temperature_c": float(temperature_c),
        "people": int(people),
        "active_appliances": int(active_appliances),
        "energy_demand_kw": None if energy_demand_kw is None else float(energy_demand_kw),
        "estimated_energy_kw": estimated_kw,
        "energy_level": level,
        "recommendation": " ".join(recommendations),
    }

def save_scenario(result):
    row = pd.DataFrame([result])
    if HISTORY_PATH.exists():
        try:
            old = pd.read_csv(HISTORY_PATH)
            row = pd.concat([old, row], ignore_index=True)
        except Exception:
            pass
    row.to_csv(HISTORY_PATH, index=False)

st.markdown("""
<style>
.block-container {padding-top: 1.8rem; padding-bottom: 2rem; max-width: 1400px;}
.hero {padding: 1.3rem 1.5rem; border-radius: 16px; background: linear-gradient(120deg,#102a43,#176b87); color:white; margin-bottom: 1rem;}
.hero h1 {color:white; margin-bottom:.25rem;}
.hero p {color:#e3f4fa; margin-bottom:0;}
.metric-card {padding: 1rem 1.1rem; border:1px solid #dce4ec; border-radius:14px; background:rgba(128,128,128,.04); min-height:115px;}
.metric-label {font-size:.9rem; opacity:.75; margin-bottom:.35rem;}
.metric-value {font-size:1.8rem; font-weight:700;}
.rec-card {padding:1.1rem 1.2rem; border-radius:14px; border:1px solid #c9d8e5; background:rgba(33,150,243,.07);}
.small-note {font-size:.85rem; opacity:.75;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>⚡ Smart Building Energy Optimizer</h1>
<p>Analyze room conditions, estimate energy demand, and get practical energy-saving recommendations.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🏢 Classroom inputs")
    room_type = st.selectbox("Room type", ["Classroom", "Computer lab", "Office", "Laboratory", "Corridor"])
    temperature = st.number_input("Temperature (°C)", min_value=-10.0, max_value=60.0, value=34.0, step=1.0)
    people = st.number_input("Number of people", min_value=0, max_value=500, value=18, step=1)
    appliances = st.number_input("Active appliances (count)", min_value=0, max_value=200, value=7, step=1)
    include_demand = st.checkbox("I know the current energy demand (kW)", value=False)
    demand = None
    if include_demand:
        demand = st.number_input("Current energy demand (kW)", min_value=0.0, max_value=10000.0, value=1.5, step=0.1)
    analyze = st.button("Analyze room", type="primary", use_container_width=True)
    st.caption("Inputs are used only for this local demonstration.")

if "last_result" not in st.session_state:
    st.session_state.last_result = analyze_room(temperature, people, appliances, demand, room_type)
if analyze:
    st.session_state.last_result = analyze_room(temperature, people, appliances, demand, room_type)
    save_scenario(st.session_state.last_result)

result = st.session_state.last_result
level = result["energy_level"]
if level == "High":
    st.warning("Energy status: HIGH — review usage while maintaining room comfort.")
elif level == "Medium":
    st.info("Energy status: MEDIUM — review optional loads and keep conditions comfortable.")
else:
    st.success("Energy status: LOW — estimated demand is relatively low.")

st.subheader("Current room summary")
cols = st.columns(4)
cards = [
    ("Temperature", f'{result["temperature_c"]:g} °C'),
    ("People in room", str(result["people"])),
    ("Active appliances", str(result["active_appliances"])),
    ("Estimated energy", f'{result["estimated_energy_kw"]:.2f} kW'),
]
for col, (label, value) in zip(cols, cards):
    with col:
        st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

st.markdown("")
left, right = st.columns([1.35, 1])
with left:
    st.subheader("📊 Scenario comparison")
    demo = pd.DataFrame([
        analyze_room(22, 5, 3, room_type=room_type),
        analyze_room(27, 12, 5, room_type=room_type),
        result,
    ])
    demo["Scenario"] = ["Cool / low use", "Moderate use", "Current input"]
    fig = px.bar(demo, x="Scenario", y="estimated_energy_kw", color="energy_level",
                 color_discrete_map={"Low":"#2e9d68","Medium":"#e6a23c","High":"#df4b4b"},
                 hover_data={"temperature_c":True,"people":True,"active_appliances":True,"estimated_energy_kw":":.2f","energy_level":True},
                 labels={"estimated_energy_kw":"Estimated energy (kW)", "energy_level":"Energy level"},
                 title="Estimated energy for example scenarios")
    fig.update_layout(height=400, margin=dict(l=15,r=15,t=55,b=15), legend_title_text="Energy level")
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("💡 Recommendations")
    st.markdown(f'<div class="rec-card"><b>{result["room_type"]} guidance</b><br><br>{result["recommendation"]}</div>', unsafe_allow_html=True)
    st.caption("These are suggestions only; the app does not control physical appliances.")

st.subheader("🧠 AI methods represented")
st.write("Rule-based reasoning • BFS/DFS and A* search demonstrations • fuzzy-style control • Perceptron classification • small bigram language-model demo in the companion notebook.")
st.caption("Model limitation: estimated energy uses assumed average appliance loads and temperature/occupancy factors. It is not a real meter reading and should not be used for operational decisions without calibration.")

if HISTORY_PATH.exists():
    st.subheader("Saved analyses")
    try:
        history = pd.read_csv(HISTORY_PATH)
        st.dataframe(history.tail(10), use_container_width=True, hide_index=True)
    except Exception:
        st.caption("No saved history yet.")
