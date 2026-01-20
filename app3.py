import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from itertools import combinations

# HydroStar Brand Colors
PRIMARY_GREEN = "#a7d730"
SECONDARY_GREEN = "#499823"
DARK_GREY = "#30343c"
LIGHT_GREY = "#8c919a"
PLOT_BG = "#f2f4f7"
TEXT_BLACK = "#000000"

# Status colors
STATUS_GREEN = "#4CAF50"
STATUS_RED = "#F44336"
STATUS_ORANGE = "#FF9800"

# B9 Electrolyte dilution factor (30% B9 means 70% wastewater)
B9_DILUTION_FACTOR = 0.7

# Total electrolyte volume per 1 kg of H2 (includes B9 portion, 40% efficiency assumption)
ELECTROLYTE_PER_KG_H2 = 12.6

# Maximum water sources to combine
MAX_COMBINATION_SIZE = 5

# Page configuration
st.set_page_config(
    page_title="HydroStar Water Blend Optimizer",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for HydroStar branding
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Hind', sans-serif;
    }}
    
    .main {{
        background-color: #0e1117;
    }}
    
    .stApp {{
        background-color: #0e1117;
    }}
    
    h1, h2, h3 {{
        font-family: 'Hind', sans-serif;
        color: {DARK_GREY};
    }}
    
    .status-card {{
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-family: 'Hind', sans-serif;
        color: #000000;
    }}
    
    .status-safe {{
        background-color: #e8f5e9;
        border-left: 5px solid {STATUS_GREEN};
    }}
    
    .status-escalation {{
        background-color: #ffebee;
        border-left: 5px solid {STATUS_RED};
    }}
    
    div[data-testid="stSidebar"] {{
        background-color: {DARK_GREY};
    }}
    
    div[data-testid="stSidebar"] .stMarkdown {{
        color: white;
    }}
    
    div[data-testid="stSidebar"] label {{
        color: white !important;
    }}
    
    .stButton > button {{
        background-color: {PRIMARY_GREEN};
        color: {DARK_GREY};
        font-weight: 600;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-family: 'Hind', sans-serif;
    }}
    
    .stButton > button:hover {{
        background-color: {SECONDARY_GREEN};
        color: white;
    }}
    
    .info-box {{
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #2196F3;
        margin: 10px 0;
    }}
    
    .warning-box {{
        background-color: #fff3e0;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #FF9800;
        margin: 10px 0;
    }}
    
    .success-box {{
        background-color: #e8f5e9;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid {STATUS_GREEN};
        margin: 15px 0;
    }}
    
    .error-box {{
        background-color: #ffebee;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid {STATUS_RED};
        margin: 15px 0;
    }}
    
    .h2-production-box {{
        position: relative;
        background: #1b222b;
        display: inline-block;
        width: fit-content;
        min-width: 220px;
        max-width: 320px;
        padding: 16px 18px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        text-align: left;
        overflow: hidden;
    }}

    .h2-production-box::before {{
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        width: 6px;
        height: 100%;
        background: linear-gradient(180deg, {PRIMARY_GREEN} 0%, {SECONDARY_GREEN} 100%);
    }}

    .h2-required-label {{
        font-size: 11px;
        letter-spacing: 1.4px;
        text-transform: uppercase;
        color: #ffffff;
        margin-bottom: 8px;
    }}

    .h2-required-value {{
        font-size: 28px;
        font-weight: 700;
        color: {PLOT_BG};
        line-height: 1.1;
    }}

    .h2-required-unit {{
        font-size: 14px;
        font-weight: 600;
        color: #ffffff;
        margin-left: 8px;
    }}

    .h2-required-breakdown {{
        font-size: 12px;
        color: #ffffff;
        margin-top: 6px;
    }}
    
    .recipe-card {{
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 20px 0;
        border: 2px solid {PRIMARY_GREEN};
    }}
    
    .recipe-title {{
        color: {SECONDARY_GREEN};
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 20px;
        font-family: 'Hind', sans-serif;
    }}
    
    .ingredient-item {{
        background-color: white;
        padding: 12px 15px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid {PRIMARY_GREEN};
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    
    .ingredient-volume {{
        font-size: 20px;
        font-weight: 700;
        color: {DARK_GREY};
    }}
    
    .ingredient-type {{
        font-size: 14px;
        color: {LIGHT_GREY};
    }}

    .recipe-step {{
        background-color: #f1f3f5;
        padding: 12px 15px;
        border-radius: 10px;
        margin: 12px 0;
        border-left: 4px solid {SECONDARY_GREEN};
    }}

    .step-title {{
        font-size: 16px;
        font-weight: 700;
        color: {DARK_GREY};
        margin-bottom: 6px;
    }}

    .step-detail {{
        font-size: 14px;
        color: {DARK_GREY};
    }}
    
    .dilution-warning {{
        background-color: #fff8e1;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid {STATUS_ORANGE};
        margin: 15px 0;
    }}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# WATER TYPE CONCENTRATION DATA (Median values from EA Statistics 2000-2025)
# Only the 8 analytes relevant for Alkaline pH assessment
# All concentrations in mg/L
# None values treated as 0 (no contribution to blend)
# =============================================================================

WATER_TYPE_CONCENTRATIONS = {
    "DISTILLED WATER": {
        "Chloride": 0.0, "Bromide": 0.0, "Iodide": 0.0, "Sulphide": 0.0,
        "Cyanide": 0.0, "Nitrate": 0.0, "Nitrite": 0.0, "Ammonium": 0.0
    },
    "RAIN WATER": {
        "Chloride": 3.47, "Bromide": 0.0, "Iodide": 0.0, "Sulphide": 0.0,
        "Cyanide": 0.0, "Nitrate": 0.27, "Nitrite": 0.0, "Ammonium": 0.41
    },
    "TAP WATER (CARDIFF)": {
        "Chloride": 0.0, "Bromide": 0.0, "Iodide": 0.0, "Sulphide": 0.0,
        "Cyanide": 0.0, "Nitrate": 0.0, "Nitrite": 0.0, "Ammonium": 0.0
    },
    "FINAL SEWAGE EFFLUENT": {
        "Chloride": 94.3, "Bromide": 0.119, "Iodide": 0.003, "Sulphide": 0.017,
        "Cyanide": 0.005, "Nitrate": 14.0, "Nitrite": 0.2, "Ammonium": 0.82
    },
    "Yeo Valley (Final Effluent)": {
        "Chloride": 36.1, "Bromide": 0.0, "Iodide": 0.0, "Sulphide": 0.0,
        "Cyanide": 0.0, "Nitrate": 0.0, "Nitrite": 0.0, "Ammonium": 1.05
    },
    "CRUDE SEWAGE": {
        "Chloride": 180.0, "Bromide": 0.0, "Iodide": 0.0, "Sulphide": 0.016,
        "Cyanide": 0.007, "Nitrate": 0.6, "Nitrite": 0.038, "Ammonium": 28.0
    },
    "ANY SEWAGE": {
        "Chloride": 99.0, "Bromide": 0.0, "Iodide": 0.0, "Sulphide": 0.022,
        "Cyanide": 0.005, "Nitrate": 9.72, "Nitrite": 0.12, "Ammonium": 3.39
    },
    "ANY TRADE EFFLUENT": {
        "Chloride": 77.0, "Bromide": 0.317, "Iodide": 0.013, "Sulphide": 0.024,
        "Cyanide": 0.012, "Nitrate": 3.415, "Nitrite": 0.044, "Ammonium": 0.5
    },
    "TRADE EFFLUENT - FRESHWATER RETURNED ABSTRACTED": {
        "Chloride": 39.6, "Bromide": 0.145, "Iodide": 0.0, "Sulphide": 0.01,
        "Cyanide": 0.0, "Nitrate": 6.225, "Nitrite": 0.024, "Ammonium": 0.087
    },
    "STORM SEWER OVERFLOW DISCHARGE": {
        "Chloride": 58.4, "Bromide": 0.0, "Iodide": 0.0, "Sulphide": 0.073,
        "Cyanide": 0.382, "Nitrate": 0.9, "Nitrite": 0.1, "Ammonium": 6.43
    },
    "SURFACE DRAINAGE": {
        "Chloride": 69.6, "Bromide": 0.076, "Iodide": 0.02, "Sulphide": 0.015,
        "Cyanide": 0.005, "Nitrate": 1.68, "Nitrite": 0.05, "Ammonium": 0.5
    },
    "ANY LEACHATE": {
        "Chloride": 778.0, "Bromide": 7.6, "Iodide": 0.02, "Sulphide": 0.07,
        "Cyanide": 0.05, "Nitrate": 0.9, "Nitrite": 0.1, "Ammonium": 120.5
    },
    "GROUNDWATER - PURGED/PUMPED/REFILLED": {
        "Chloride": 43.8, "Bromide": 0.082, "Iodide": 0.003, "Sulphide": 0.01,
        "Cyanide": 0.005, "Nitrate": 6.0, "Nitrite": 0.004, "Ammonium": 0.089
    },
    "MINEWATER": {
        "Chloride": 19.0, "Bromide": 0.101, "Iodide": 0.003, "Sulphide": 0.01,
        "Cyanide": 0.005, "Nitrate": 0.312, "Nitrite": 0.004, "Ammonium": 0.03
    },
    "CANAL WATER": {
        "Chloride": 58.0, "Bromide": 0.067, "Iodide": 0.0, "Sulphide": 0.011,
        "Cyanide": 0.008, "Nitrate": 2.04, "Nitrite": 0.019, "Ammonium": 0.056
    }
}

# Sludge production rates (kg per m3 of water). Provided values are exact, others are rough estimates.
SLUDGE_PRODUCTION_KG_PER_M3 = {
    "Yeo Valley (Final Effluent)": 0.3,
    "RAIN WATER": 0.0015,
    "TAP WATER (CARDIFF)": 0.023,
    "FINAL SEWAGE EFFLUENT": 0.26,
    "DISTILLED WATER": 0.0,
    "CRUDE SEWAGE": 0.6,
    "ANY SEWAGE": 0.35,
    "ANY TRADE EFFLUENT": 0.4,
    "TRADE EFFLUENT - FRESHWATER RETURNED ABSTRACTED": 0.22,
    "STORM SEWER OVERFLOW DISCHARGE": 0.18,
    "SURFACE DRAINAGE": 0.05,
    "ANY LEACHATE": 0.9,
    "GROUNDWATER - PURGED/PUMPED/REFILLED": 0.01,
    "MINEWATER": 0.08,
    "CANAL WATER": 0.03
}

# =============================================================================
# ESCALATION LEVELS (8 analytes only)
# =============================================================================

ALKALINE_ESCALATION_LEVELS = {
    "Chloride": 3500.0,
    "Bromide": 8.0,
    "Iodide": 1.3,
    "Sulphide": 1.0,
    "Cyanide": 0.02,
    "Nitrate": 50.0,
    "Nitrite": 50.0,
    "Ammonium": 10.0
}

NEUTRAL_ESCALATION_LEVELS = {
    "Chloride": 20.0,
    "Bromide": 0.5,
    "Iodide": 0.1,
    "Sulphide": 0.2,
    "Cyanide": 0.02,
    "Nitrate": 10.0,
    "Nitrite": 1.0,
    "Ammonium": 2.0
}

ACIDIC_ESCALATION_LEVELS = {
    "Chloride": 350.0,
    "Bromide": 1.0,
    "Iodide": 0.1,
    "Sulphide": 0.1,
    "Cyanide": 0.005,
    "Nitrate": 10.0,
    "Nitrite": 10.0,
    "Ammonium": 1.0
}


def calculate_blend_concentration(water_sources, analyte):
    """
    Calculate weighted average concentration for an analyte across water sources.
    Formula: C_blend = (C1 x V1 + C2 x V2 + ...) / (V1 + V2 + ...)
    """
    total_mass = 0.0
    total_volume = 0.0
    
    for water_type, volume in water_sources:
        conc = WATER_TYPE_CONCENTRATIONS[water_type].get(analyte, 0.0)
        if conc is None:
            conc = 0.0
        total_mass += conc * volume
        total_volume += volume
    
    if total_volume == 0:
        return 0.0
    
    return total_mass / total_volume


def apply_b9_dilution(concentration):
    """Apply 30% B9 electrolyte dilution. Final = Blend x 0.7"""
    return concentration * B9_DILUTION_FACTOR


def get_status(final_concentration, escalation_level):
    """Determine status: SAFE if below escalation level, otherwise ESCALATION."""
    if final_concentration >= escalation_level:
        return "escalation"
    return "safe"


def analyze_combination(water_sources, escalation_levels):
    """
    Analyze a water source combination against escalation levels.
    Returns dict with overall status, analyte results, and safety metrics.
    """
    results = {
        "overall_status": "safe",
        "analyte_results": {},
        "total_volume": sum(v for _, v in water_sources),
        "limiting_analytes": [],
        "safe_count": 0,
        "escalation_count": 0
    }
    
    worst_ratio = float('inf')
    worst_analyte = None
    max_dilution_needed = 1.0
    dilution_limiting_analyte = None
    ratio_cap = 100.0
    
    for analyte, limit in escalation_levels.items():
        blend_conc = calculate_blend_concentration(water_sources, analyte)
        final_conc = apply_b9_dilution(blend_conc)
        status = get_status(final_conc, limit)
        
        results["analyte_results"][analyte] = {
            "blend_concentration": blend_conc,
            "final_concentration": final_conc,
            "escalation_level": limit,
            "status": status
        }
        
        if status == "safe":
            results["safe_count"] += 1
        else:
            results["escalation_count"] += 1
            results["limiting_analytes"].append((analyte, final_conc, limit))
            results["overall_status"] = "escalation"
        
        if final_conc > 0:
            ratio = limit / final_conc
            if ratio < worst_ratio:
                worst_ratio = ratio
                worst_analyte = analyte
            
            if final_conc > limit:
                dilution = final_conc / limit
                if dilution > max_dilution_needed:
                    max_dilution_needed = dilution
                    dilution_limiting_analyte = analyte
    
    results["safety_score"] = ratio_cap if worst_ratio == float('inf') else min(worst_ratio, ratio_cap)
    results["worst_analyte"] = worst_analyte
    results["worst_ratio"] = ratio_cap if worst_ratio == float('inf') else worst_ratio
    results["required_dilution"] = max_dilution_needed
    results["dilution_limiting_analyte"] = dilution_limiting_analyte
    
    return results


def get_all_combinations(water_entries, max_size):
    """Generate all combinations from 1 source up to max_size sources."""
    all_combos = []
    n = len(water_entries)
    
    for r in range(1, min(n + 1, max_size + 1)):
        for combo in combinations(range(n), r):
            sources = [(water_entries[i]["type"], water_entries[i]["volume"]) for i in combo]
            all_combos.append(sources)
    
    return all_combos


def sort_results(results):
    """Sort results by: 1. Status (SAFE first), 2. Safety score (higher is better)"""
    def sort_key(r):
        status_priority = 0 if r["overall_status"] == "safe" else 1
        return (status_priority, -r["safety_score"])
    
    return sorted(results, key=sort_key)


def get_status_color(status):
    """Return color based on status."""
    if status == "safe":
        return STATUS_GREEN
    return STATUS_RED


def calculate_sludge_kg(water_sources):
    """Calculate sludge production in kg for the given water sources."""
    total_sludge = 0.0
    breakdown = []
    for water_type, volume in water_sources:
        rate = SLUDGE_PRODUCTION_KG_PER_M3.get(water_type)
        if rate is None:
            breakdown.append({
                "water_type": water_type,
                "volume_l": volume,
                "rate_kg_m3": None,
                "sludge_kg": None
            })
            continue
        sludge_kg = (volume / 1000.0) * rate
        total_sludge += sludge_kg
        breakdown.append({
            "water_type": water_type,
            "volume_l": volume,
            "rate_kg_m3": rate,
            "sludge_kg": sludge_kg
        })
    return total_sludge, breakdown


def rank_water_sources(water_entries, escalation_levels):
    """Rank sources by safety (safe first, higher safety score first)."""
    ranked = []
    for entry in water_entries:
        analysis = analyze_combination([(entry["type"], 1.0)], escalation_levels)
        ranked.append({
            "type": entry["type"],
            "available_volume": entry["volume"],
            "overall_status": analysis["overall_status"],
            "safety_score": analysis["safety_score"]
        })
    ranked.sort(key=lambda item: (0 if item["overall_status"] == "safe" else 1, -item["safety_score"]))
    return ranked


def build_blend_from_ranking(ranked_sources, required_volume):
    """Fill the required volume using the safest sources first."""
    selected = []
    remaining = required_volume
    for source in ranked_sources:
        if remaining <= 0:
            break
        use_volume = min(source["available_volume"], remaining)
        if use_volume > 0:
            selected.append((source["type"], use_volume))
            remaining -= use_volume
    return selected, remaining


# =============================================================================
# MAIN APP
# =============================================================================

# Initialize session state
if "water_entries" not in st.session_state:
    st.session_state.water_entries = [{"type": None, "volume": None}]

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

if "h2_target" not in st.session_state:
    st.session_state.h2_target = 1.0

# Header with logo
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try:
        st.image("logo.png", width=200)
    except:
        st.markdown(f"<div style='background-color:{PRIMARY_GREEN}; padding:20px; border-radius:10px; text-align:center;'><span style='font-size:24px; font-weight:bold; color:{DARK_GREY};'>H2</span></div>", unsafe_allow_html=True)

with col_title:
    st.markdown(f"""
    <div>
        <h1 style='color:{PRIMARY_GREEN}; margin-bottom:0; font-family:Hind;'>Water Blend Optimizer</h1>
        <p style='color:{LIGHT_GREY}; font-family:Hind;'>Find the optimal water blend for green hydrogen production</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown(f"<h2 style='color:{PRIMARY_GREEN}; font-family:Hind;'>Configuration</h2>", unsafe_allow_html=True)
    
    ph_type = st.selectbox(
        "Select Wastewater pH Type",
        options=[
            "Alkaline pH (over 8)",
            "Neutral pH (5.5 to 7.5)",
            "Acidic pH (less than 5)"
        ],
        index=0,
        help="Select the wastewater pH range"
    )
    
    if ph_type == "Neutral pH (5.5 to 7.5)":
        escalation_levels = NEUTRAL_ESCALATION_LEVELS
    elif ph_type == "Acidic pH (less than 5)":
        escalation_levels = ACIDIC_ESCALATION_LEVELS
    else:
        escalation_levels = ALKALINE_ESCALATION_LEVELS
    
    st.markdown("---")
    
    # B9 Info
    st.markdown(f"<h3 style='color:{PRIMARY_GREEN}; font-family:Hind;'>B9 Electrolyte</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='color:white; font-family:Hind; font-size:14px;'>
        <p>All blends include <strong>30% B9 Electrolyte</strong>, 
        reducing contaminant concentrations by 30%.</p>
        <p style='font-style:italic; color:{LIGHT_GREY};'>Final = Blend x 0.7</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Legend
    st.markdown(f"<h3 style='color:{PRIMARY_GREEN}; font-family:Hind;'>Status Legend</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='color:white; font-family:Hind;'>
        <div style='display:flex; align-items:center; margin:10px 0;'>
            <div style='width:20px; height:20px; background-color:{STATUS_GREEN}; border-radius:4px; margin-right:10px;'></div>
            <span>Safe - Below escalation level</span>
        </div>
        <div style='display:flex; align-items:center; margin:10px 0;'>
            <div style='width:20px; height:20px; background-color:{STATUS_RED}; border-radius:4px; margin-right:10px;'></div>
            <span>Escalation - Above safe limit</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"<h3 style='color:{PRIMARY_GREEN}; font-family:Hind;'>Sludge Rates</h3>", unsafe_allow_html=True)
    sludge_rate_lines = [
        "<div style='color:white; font-family:Hind; font-size:14px;'>",
        "<p>Rates shown are g per 1000 L of water</p>",
        "<ul style='margin:0; padding-left:18px;'>"
    ]
    for water_type in WATER_TYPE_CONCENTRATIONS.keys():
        rate = SLUDGE_PRODUCTION_KG_PER_M3.get(water_type)
        rate_g_per_1000l = rate * 1000.0 if rate is not None else None
        rate_text = f"{rate_g_per_1000l:.1f}" if rate_g_per_1000l is not None else "N/A"
        sludge_rate_lines.append(f"<li>{water_type}: {rate_text}</li>")
    sludge_rate_lines += ["</ul>", "</div>"]
    st.markdown("\n".join(sludge_rate_lines), unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"<p style='color:{LIGHT_GREY}; font-size:12px; font-family:Hind;'>HydroStar Europe Ltd.</p>", unsafe_allow_html=True)

# Main content - H2 Production Target
st.markdown(f"<h2 style='color:{SECONDARY_GREEN}; font-family:Hind;'>Hydrogen Production Target</h2>", unsafe_allow_html=True)

col_h2_input, col_h2_info = st.columns([1, 2])

with col_h2_input:
    h2_target = st.number_input(
        "Target H2 Production (kg)",
        min_value=1.0,
        max_value=120.0,
        value=st.session_state.h2_target,
        step=1.0,
        help="250kW electrolyser produces up to 120 kg H2 per day"
    )
    st.session_state.h2_target = h2_target

total_electrolyte_required = round(h2_target * ELECTROLYTE_PER_KG_H2, 1)
water_required_raw = total_electrolyte_required * B9_DILUTION_FACTOR
water_required = round(water_required_raw, 1)
b9_required = round(total_electrolyte_required - water_required, 1)

with col_h2_info:
    st.markdown(f"""
    <div style='display:flex; align-items:flex-start; justify-content:flex-start;'>
        <div class='h2-production-box'>
            <div class='h2-required-label'>Total Electrolyte Required</div>
            <div class='h2-required-value'>
                {total_electrolyte_required:.1f}<span class='h2-required-unit'>Liters</span>
            </div>
            <div class='h2-required-breakdown'>
                Water portion: {water_required:.1f} L | B9 portion: {b9_required:.1f} L
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Water Sources Section
st.markdown(f"<h2 style='color:{SECONDARY_GREEN}; font-family:Hind;'>Enter Your Available Water Sources</h2>", unsafe_allow_html=True)

# Instructions
st.markdown(f"""
<div class='info-box'>
    <p style='margin:0; font-family:Hind; color:{DARK_GREY};'>
        <strong>How it works:</strong> Add your available water sources and volumes in Liters. 
        The system ranks your sources by safety, fills the required water volume from the safest sources,
        and then tells you exactly how much B9 (and any extra distilled water) to add.
    </p>
</div>
""", unsafe_allow_html=True)

# Water type options
priority_types = ["RAIN WATER", "TAP WATER (CARDIFF)", "Yeo Valley (Final Effluent)", "DISTILLED WATER"]
water_type_options = [t for t in priority_types if t in WATER_TYPE_CONCENTRATIONS]
water_type_options += [k for k in WATER_TYPE_CONCENTRATIONS.keys() if k not in water_type_options]

# Water entry form
for i, entry in enumerate(st.session_state.water_entries):
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        selected_types = [e["type"] for j, e in enumerate(st.session_state.water_entries) if j != i and e["type"]]
        available_options = ["-- Select Water Type --"] + [t for t in water_type_options if t not in selected_types]
        
        current_selection = entry["type"] if entry["type"] in available_options else "-- Select Water Type --"
        
        selected = st.selectbox(
            f"Water Type {i+1}",
            options=available_options,
            index=available_options.index(current_selection) if current_selection in available_options else 0,
            key=f"water_type_{i}",
            label_visibility="collapsed"
        )
        
        if selected != "-- Select Water Type --":
            st.session_state.water_entries[i]["type"] = selected
        else:
            st.session_state.water_entries[i]["type"] = None
    
    with col2:
        volume_value = entry["volume"] if entry["volume"] not in (None, 0.0) else None
        volume = st.number_input(
            f"Volume (Liters)",
            min_value=0.0,
            value=volume_value,
            format="%.2f",
            key=f"volume_{i}",
            label_visibility="collapsed",
            placeholder="Enter volume (L)"
        )
        st.session_state.water_entries[i]["volume"] = volume
    
    with col3:
        if len(st.session_state.water_entries) > 1:
            if st.button("X", key=f"remove_{i}", help="Remove"):
                st.session_state.water_entries.pop(i)
                st.rerun()

# Buttons
col_add, col_analyze, col_clear = st.columns([1, 1, 1])

with col_add:
    if st.button("+ Add Water Source", use_container_width=True):
        st.session_state.water_entries.append({"type": None, "volume": None})
        st.rerun()

with col_analyze:
    analyze_clicked = st.button("Find Optimal Blend", type="primary", use_container_width=True)

with col_clear:
    if st.button("Clear All", use_container_width=True):
        st.session_state.water_entries = [{"type": None, "volume": None}]
        st.session_state.analysis_results = None
        st.rerun()

# Analysis
if analyze_clicked:
    valid_entries = [
        e for e in st.session_state.water_entries
        if e["type"] is not None and (e["volume"] or 0) > 0
    ]
    
    if len(valid_entries) == 0:
        st.warning("Please add at least one water source with a volume greater than 0.")
    else:
        total_available = sum(e["volume"] or 0 for e in valid_entries)

        ranked_sources = rank_water_sources(valid_entries, escalation_levels)
        selected_sources, remaining_volume = build_blend_from_ranking(ranked_sources, water_required)

        results = []
        if remaining_volume <= 1e-6:
            analysis = analyze_combination(selected_sources, escalation_levels)
            analysis["water_sources"] = selected_sources
            results.append(analysis)

        st.session_state.analysis_results = {
            "results": results,
            "total_available": total_available,
            "water_required": water_required,
            "electrolyte_required": total_electrolyte_required,
            "b9_required": b9_required,
            "h2_target": h2_target,
        }

# Display results
if st.session_state.analysis_results:
    data = st.session_state.analysis_results
    results = data["results"]
    total_available = data["total_available"]
    water_required = data["water_required"]
    total_electrolyte_required = data["electrolyte_required"]
    b9_required = data["b9_required"]
    h2_target_display = data["h2_target"]
    
    st.markdown("---")
    st.markdown(f"<h2 style='color:{SECONDARY_GREEN}; font-family:Hind;'>Your Optimal Blend Recipe</h2>", unsafe_allow_html=True)
    
    # Check if we have insufficient water
    epsilon = 1e-6
    if total_available + epsilon < water_required:
        st.markdown(f"""
        <div class='error-box'>
            <h3 style='color:{STATUS_RED}; margin-top:0;'>Insufficient Water Available</h3>
            <p style='margin:0; font-family:Hind; color:{DARK_GREY};'>
                You have <strong>{total_available:.1f}L</strong> available but need <strong>{water_required:.1f}L</strong> 
                of water (70% of the <strong>{total_electrolyte_required:.1f}L</strong> total electrolyte)
                to produce <strong>{h2_target_display:.0f} kg H2</strong>.
                <br><br>
                <strong>Shortfall:</strong> {max(0.0, water_required - total_available):.1f}L
                <br><br>
                Please add more water sources or reduce your hydrogen production target.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Check if a blend could be built
    elif len(results) == 0:
        st.markdown(f"""
        <div class='error-box'>
            <h3 style='color:{STATUS_RED}; margin-top:0;'>No Valid Blend Found</h3>
            <p style='margin:0; font-family:Hind; color:{DARK_GREY};'>
                We could not build a full blend with the volumes provided.
                The target water volume is <strong>{water_required:.1f}L</strong>.
                <br><br>
                Please add more water sources or increase the volumes available.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Get the best (safest) result - it's already sorted, so take the first one
        best_result = results[0]
        is_safe = best_result["overall_status"] == "safe"

        water_blend_volume = best_result["total_volume"]
        b9_volume = b9_required
        total_after_b9 = total_electrolyte_required
        needs_dilution = best_result["required_dilution"] > 1
        distilled_water_needed = total_after_b9 * (best_result["required_dilution"] - 1) if needs_dilution else 0.0
        total_after_dilution = total_after_b9 + distilled_water_needed
        
        # Status Banner
        if is_safe:
            st.markdown(f"""
            <div class='success-box'>
                <h3 style='color:{STATUS_GREEN}; margin-top:0;'>Safe Blend Found</h3>
                <p style='margin:0; font-family:Hind; color:{DARK_GREY};'>
                    This is the <strong>safest blend</strong> for your inputs. Follow the steps below to prepare it.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='error-box'>
                <h3 style='color:{STATUS_RED}; margin-top:0;'>Dilution Required</h3>
                <p style='margin:0; font-family:Hind; color:{DARK_GREY};'>
                    This is the <strong>safest available blend</strong>, but it needs additional distilled water to meet safety limits.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        recipe_lines = [
            "<div class='recipe-card'>",
            "<div class='recipe-title'>Optimal Blend Recipe</div>",
            "<div class='recipe-step'>",
            "<div class='step-title'>Step 1 - Measure your water sources</div>",
            "<div class='step-detail'>",
            (
                "Use these volumes to make "
                f"{water_blend_volume:.1f} L of water for your {h2_target_display:.0f} kg H2 target "
                f"(70% of the {total_electrolyte_required:.1f} L total electrolyte):"
            ),
            "</div>",
        ]
        for water_type, volume in best_result["water_sources"]:
            recipe_lines.append(
                "<div class='ingredient-item'>"
                f"<span class='ingredient-volume'>{volume:.1f} L</span>"
                f"<span class='ingredient-type'> - {water_type}</span>"
                "</div>"
            )
        recipe_lines += [
            "</div>",
            "<div class='recipe-step'>",
            "<div class='step-title'>Step 2 - Add B9 electrolyte</div>",
            "<div class='step-detail'>",
            f"Add <strong>{b9_volume:.1f} L</strong> of B9 (30% of total electrolyte).",
            f"<br>Total electrolyte after B9: <strong>{total_after_b9:.1f} L</strong>",
            "</div>",
            "</div>",
        ]
        if needs_dilution:
            recipe_lines += [
                "<div class='recipe-step'>",
                "<div class='step-title'>Step 3 - Dilute to safe limits</div>",
                "<div class='step-detail'>",
                f"Add <strong>{distilled_water_needed:.1f} L</strong> additional distilled water to make the blend safe.",
                f"<br>Final electrolyte volume: <strong>{total_after_dilution:.1f} L</strong>",
                f"<br><em>Limiting analyte: {best_result.get('dilution_limiting_analyte', 'N/A')}</em>",
                "</div>",
                "</div>",
            ]
        else:
            recipe_lines += [
                "<div class='recipe-step'>",
                "<div class='step-title'>Step 3 - No dilution needed</div>",
                "<div class='step-detail'>",
                "This blend is already within safe limits after B9.",
                f"<br>Final electrolyte volume: <strong>{total_after_b9:.1f} L</strong>",
                "</div>",
                "</div>",
            ]
        recipe_lines.append("</div>")
        st.markdown("\n".join(recipe_lines), unsafe_allow_html=True)
        
        # Summary Metrics
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_color = STATUS_GREEN if is_safe else STATUS_RED
            status_text = "SAFE" if is_safe else "NEEDS DILUTION"
            st.markdown(f"""
            <div style='background-color:white; padding:15px; border-radius:10px; text-align:center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <p style='color:{LIGHT_GREY}; margin:0; font-family:Hind; font-size:12px;'>STATUS</p>
                <p style='font-size:18px; font-weight:bold; color:{status_color}; margin:5px 0 0 0; font-family:Hind;'>{status_text}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background-color:white; padding:15px; border-radius:10px; text-align:center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <p style='color:{LIGHT_GREY}; margin:0; font-family:Hind; font-size:12px;'>WATER PORTION</p>
                <p style='font-size:18px; font-weight:bold; color:{DARK_GREY}; margin:5px 0 0 0; font-family:Hind;'>{water_blend_volume:.1f} L</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='background-color:white; padding:15px; border-radius:10px; text-align:center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <p style='color:{LIGHT_GREY}; margin:0; font-family:Hind; font-size:12px;'>B9 ELECTROLYTE</p>
                <p style='font-size:18px; font-weight:bold; color:{SECONDARY_GREEN}; margin:5px 0 0 0; font-family:Hind;'>{b9_volume:.1f} L</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            distilled_display = f"{distilled_water_needed:.1f} L" if needs_dilution else "0.0 L"
            st.markdown(f"""
            <div style='background-color:white; padding:15px; border-radius:10px; text-align:center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <p style='color:{LIGHT_GREY}; margin:0; font-family:Hind; font-size:12px;'>DISTILLED WATER</p>
                <p style='font-size:18px; font-weight:bold; color:{DARK_GREY}; margin:5px 0 0 0; font-family:Hind;'>{distilled_display}</p>
            </div>
            """, unsafe_allow_html=True)

        total_sludge_kg, sludge_breakdown = calculate_sludge_kg(best_result["water_sources"])
        total_sludge_g = total_sludge_kg * 1000.0
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:{SECONDARY_GREEN}; font-family:Hind;'>Sludge Estimate</h3>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='info-box'>
            <p style='margin:0; font-family:Hind; color:{DARK_GREY};'>
                Estimated sludge from the water portion: <strong>{total_sludge_g:.3f} g</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        sludge_rows = []
        for item in sludge_breakdown:
            rate_g_per_1000l = item["rate_kg_m3"] * 1000.0 if item["rate_kg_m3"] is not None else None
            sludge_g = item["sludge_kg"] * 1000.0 if item["sludge_kg"] is not None else None
            rate_display = f"{rate_g_per_1000l:.1f}" if rate_g_per_1000l is not None else "N/A"
            sludge_display = f"{sludge_g:.3f}" if sludge_g is not None else "N/A"
            sludge_rows.append({
                "Water Type": item["water_type"],
                "Volume (L)": f"{item['volume_l']:.1f}",
                "Sludge Rate (g per 1000 L)": rate_display,
                "Sludge (g)": sludge_display
            })
        st.dataframe(pd.DataFrame(sludge_rows), use_container_width=True, hide_index=True)
        
        with st.expander("Show safety details (optional)"):
            analyte_data = []
            for analyte, data in best_result["analyte_results"].items():
                status = "SAFE" if data["status"] == "safe" else "EXCEEDS LIMIT"
                margin = ((data['escalation_level'] - data['final_concentration']) / data['escalation_level']) * 100 if data['escalation_level'] > 0 else 0
                analyte_data.append({
                    "Analyte": analyte,
                    "Final Concentration (mg/L)": f"{data['final_concentration']:.4f}",
                    "Escalation Limit (mg/L)": f"{data['escalation_level']:.4f}",
                    "Safety Margin": f"{margin:.1f}%" if margin > 0 else "EXCEEDED",
                    "Status": status
                })
            
            df = pd.DataFrame(analyte_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            if best_result.get('worst_analyte'):
                st.markdown(f"""
                <div class='info-box'>
                    <p style='margin:0; font-family:Hind; color:{DARK_GREY};'>
                        <strong>Limiting Analyte:</strong> {best_result['worst_analyte']} - This analyte has the smallest safety margin.
                    </p>
                </div>
                """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align:center; color:{LIGHT_GREY}; font-family:Hind; padding:20px;'>
    <p style='margin:0;'>HydroStar Europe Ltd.</p>
    <p style='margin:5px 0 0 0; font-size:12px;'>For inquiries: domanique@hydrostar-eu.com | www.hydrostar-eu.com</p>
</div>
""", unsafe_allow_html=True)
