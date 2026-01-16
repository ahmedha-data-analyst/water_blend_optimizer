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

# B9 Electrolyte dilution factor (30% B9 means 70% wastewater)
B9_DILUTION_FACTOR = 0.7

# Water to Hydrogen conversion: 12.6 liters of water per 1 kg of H2 (40% efficiency assumption)
WATER_PER_KG_H2 = 12.6

# Maximum water sources to combine
MAX_COMBINATION_SIZE = 4

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
    
    .h2-production-box {{
        position: relative;
        background: #ffffff;
        display: inline-block;
        width: fit-content;
        min-width: 220px;
        max-width: 320px;
        padding: 16px 18px;
        border-radius: 12px;
        border: 1px solid #e6e9ef;
        margin: 15px 0;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
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
        color: {LIGHT_GREY};
        margin-bottom: 8px;
    }}

    .h2-required-value {{
        font-size: 28px;
        font-weight: 700;
        color: {DARK_GREY};
        line-height: 1.1;
    }}

    .h2-required-unit {{
        font-size: 14px;
        font-weight: 600;
        color: {LIGHT_GREY};
        margin-left: 8px;
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
    "PURIFIED WATER": {
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


def calculate_blend_concentration(water_sources, analyte):
    """
    Calculate weighted average concentration for an analyte across water sources.
    
    Formula: C_blend = (C1 x V1 + C2 x V2 + ...) / (V1 + V2 + ...)
    
    None values are treated as 0.
    """
    total_mass = 0.0
    total_volume = 0.0
    
    for water_type, volume in water_sources:
        conc = WATER_TYPE_CONCENTRATIONS[water_type].get(analyte, 0.0)
        if conc is None:
            conc = 0.0  # Treat missing data as 0
        total_mass += conc * volume
        total_volume += volume
    
    if total_volume == 0:
        return 0.0
    
    return total_mass / total_volume


def apply_b9_dilution(concentration):
    """
    Apply 30% B9 electrolyte dilution.
    Final = Blend x 0.7
    """
    return concentration * B9_DILUTION_FACTOR


def get_status(final_concentration, escalation_level):
    """
    Determine status: SAFE if below escalation level, otherwise ESCALATION.
    """
    if final_concentration >= escalation_level:
        return "escalation"
    return "safe"


def analyze_combination(water_sources, escalation_levels):
    """
    Analyze a water source combination against escalation levels.
    
    Returns dict with:
    - overall_status: "safe" or "escalation"
    - analyte_results: breakdown per analyte
    - safety_score: higher = safer (worst-case safety factor, capped)
    - worst_analyte: the analyte closest to or exceeding limit
    - required_dilution: how much purified water needed if not safe
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
    ratio_cap = 100.0  # Keep scores readable and comparable
    
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
        
        # Calculate safety factor (limit / concentration); lower is worse
        if final_conc > 0:
            ratio = limit / final_conc
            
            if ratio < worst_ratio:
                worst_ratio = ratio
                worst_analyte = analyte
            
            # Check if dilution needed
            if final_conc > limit:
                dilution = final_conc / limit
                if dilution > max_dilution_needed:
                    max_dilution_needed = dilution
                    dilution_limiting_analyte = analyte
        else:
            pass  # Zero concentration does not penalize the worst-case score
    
    # Safety score is the worst-case safety factor, capped for display stability
    results["safety_score"] = ratio_cap if worst_ratio == float('inf') else min(worst_ratio, ratio_cap)
    results["worst_analyte"] = worst_analyte
    results["worst_ratio"] = ratio_cap if worst_ratio == float('inf') else worst_ratio
    results["required_dilution"] = max_dilution_needed
    results["dilution_limiting_analyte"] = dilution_limiting_analyte
    
    return results


def get_all_combinations(water_entries, max_size):
    """
    Generate all combinations from 1 source up to max_size sources.
    """
    all_combos = []
    n = len(water_entries)
    
    for r in range(1, min(n + 1, max_size + 1)):
        for combo in combinations(range(n), r):
            sources = [(water_entries[i]["type"], water_entries[i]["volume"]) for i in combo]
            all_combos.append(sources)
    
    return all_combos


def sort_results(results):
    """
    Sort results by:
    1. Status (SAFE first, then ESCALATION)
    2. Safety score (higher is better)
    """
    def sort_key(r):
        # SAFE = 0, ESCALATION = 1 (lower is better)
        status_priority = 0 if r["overall_status"] == "safe" else 1
        # Negate safety score so higher scores come first
        return (status_priority, -r["safety_score"])
    
    return sorted(results, key=sort_key)


def get_status_color(status):
    """Return color based on status."""
    if status == "safe":
        return STATUS_GREEN
    return STATUS_RED


# =============================================================================
# MAIN APP
# =============================================================================

# Initialize session state
if "water_entries" not in st.session_state:
    st.session_state.water_entries = [{"type": None, "volume": 0.0}]

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
        <p style='color:{LIGHT_GREY}; font-family:Hind;'>Find optimal water combinations for green hydrogen production</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown(f"<h2 style='color:{PRIMARY_GREEN}; font-family:Hind;'>Configuration</h2>", unsafe_allow_html=True)
    
    ph_type = st.selectbox(
        "Select Wastewater pH Type",
        options=["Alkaline pH", "Neutral pH"],
        index=0,
        help="Select the wastewater pH type"
    )
    
    escalation_levels = ALKALINE_ESCALATION_LEVELS if ph_type == "Alkaline pH" else NEUTRAL_ESCALATION_LEVELS
    
    st.markdown("---")
    
    max_combo_size = st.slider(
        "Max water sources per blend",
        min_value=1,
        max_value=5,
        value=4,
        help="Maximum number of water sources to combine"
    )
    
    top_n_results = st.slider(
        "Show top N results",
        min_value=5,
        max_value=50,
        value=20,
        help="Number of best combinations to display"
    )
    
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

water_required = h2_target * WATER_PER_KG_H2

with col_h2_info:
    st.markdown(f"""
    <div style='display:flex; align-items:flex-start; justify-content:flex-start;'>
        <div class='h2-production-box'>
            <div class='h2-required-label'>Total electrolyte Required</div>
            <div class='h2-required-value'>
                {water_required:.1f}<span class='h2-required-unit'>Liters</span>
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
        The system ranks all combinations by safety and shows if you have enough water for your H2 target.
        <br><br>
        <strong>Tip:</strong> Add "PURIFIED WATER" as a source to see how dilution improves your blends.
    </p>
</div>
""", unsafe_allow_html=True)

# Water type options
priority_types = ["RAIN WATER", "TAP WATER (CARDIFF)", "PURIFIED WATER"]
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
        volume = st.number_input(
            f"Volume (Liters)",
            min_value=0.0,
            value=entry["volume"],
            format="%.2f",
            key=f"volume_{i}",
            label_visibility="collapsed",
            placeholder="Volume in Liters"
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
    if st.button("Add Water Source", use_container_width=True):
        st.session_state.water_entries.append({"type": None, "volume": 0.0})
        st.rerun()

with col_analyze:
    analyze_clicked = st.button("Analyze Combinations", type="primary", use_container_width=True)

with col_clear:
    if st.button("Clear All", use_container_width=True):
        st.session_state.water_entries = [{"type": None, "volume": 0.0}]
        st.session_state.analysis_results = None
        st.rerun()

# Analysis
if analyze_clicked:
    valid_entries = [
        e for e in st.session_state.water_entries
        if e["type"] is not None and e["volume"] > 0
    ]
    
    if len(valid_entries) == 0:
        st.warning("Please add at least one water source with a volume greater than 0.")
    else:
        total_available = sum(e["volume"] for e in valid_entries)
        
        # Get all combinations
        all_combinations = get_all_combinations(valid_entries, max_combo_size)
        
        # Analyze each combination - ONLY keep those that meet the H2 target
        results = []
        for combo in all_combinations:
            analysis = analyze_combination(combo, escalation_levels)
            analysis["water_sources"] = combo
            
            # Only include combinations that meet the required volume
            if analysis["total_volume"] >= water_required:
                analysis["meets_h2_target"] = True
                results.append(analysis)
        
        # Sort: SAFE first, then by safety score (descending)
        results = sort_results(results)
        
        st.session_state.analysis_results = {
            "results": results,
            "total_available": total_available,
            "water_required": water_required,
            "h2_target": h2_target,
            "total_combinations_checked": len(all_combinations)
        }

# Display results
if st.session_state.analysis_results:
    data = st.session_state.analysis_results
    results = data["results"]
    total_available = data["total_available"]
    water_required = data["water_required"]
    h2_target_display = data["h2_target"]
    total_checked = data.get("total_combinations_checked", 0)
    
    st.markdown("---")
    st.markdown(f"<h2 style='color:{SECONDARY_GREEN}; font-family:Hind;'>Analysis Results</h2>", unsafe_allow_html=True)
    
    # Water availability check
    if total_available < water_required:
        st.markdown(f"""
        <div class='warning-box'>
            <p style='margin:0; font-family:Hind; color:{DARK_GREY};'>
                <strong>Insufficient Water:</strong> You have {total_available:.1f}L available but need {water_required:.1f}L 
                to produce {h2_target_display:.0f} kg H2.
                <br>Shortfall: {water_required - total_available:.1f}L
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='info-box'>
            <p style='margin:0; font-family:Hind; color:{DARK_GREY};'>
                <strong>Sufficient Water:</strong> You have {total_available:.1f}L available. 
                Need {water_required:.1f}L to produce {h2_target_display:.0f} kg H2.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Check if any combinations meet the target
    if len(results) == 0:
        st.markdown(f"""
        <div class='warning-box'>
            <p style='margin:0; font-family:Hind; color:{DARK_GREY};'>
                <strong>No Valid Combinations:</strong> None of the {total_checked} possible combinations 
                provide enough volume ({water_required:.1f}L) to meet your H2 target.
                <br><br>
                Try adding more water sources or increasing the "Max water sources per blend" in the sidebar.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Summary counts
        safe_combos = [r for r in results if r["overall_status"] == "safe"]
        escalation_combos = [r for r in results if r["overall_status"] == "escalation"]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style='background-color:white; padding:20px; border-radius:10px; text-align:center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <p style='color:{TEXT_BLACK}; margin:0; font-family:Hind;'>Valid Combinations</p>
                <p style='font-size:36px; font-weight:bold; color:{DARK_GREY}; margin:0; font-family:Hind;'>{len(results)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background-color:white; padding:20px; border-radius:10px; text-align:center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <p style='color:{TEXT_BLACK}; margin:0; font-family:Hind;'>Safe</p>
                <p style='font-size:36px; font-weight:bold; color:{STATUS_GREEN}; margin:0; font-family:Hind;'>{len(safe_combos)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='background-color:white; padding:20px; border-radius:10px; text-align:center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <p style='color:{TEXT_BLACK}; margin:0; font-family:Hind;'>Escalation</p>
                <p style='font-size:36px; font-weight:bold; color:{STATUS_RED}; margin:0; font-family:Hind;'>{len(escalation_combos)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Results table
        st.markdown(f"<h3 style='color:{SECONDARY_GREEN}; font-family:Hind;'>Combinations That Meet Your {h2_target_display:.0f} kg H2 Target ({water_required:.0f}L Required)</h3>", unsafe_allow_html=True)
        
        table_data = []
        for idx, result in enumerate(results[:top_n_results]):
            sources_str = " + ".join([f"{v:.0f}L {t.split()[0]}" for t, v in result["water_sources"]])
            if len(sources_str) > 50:
                sources_str = sources_str[:47] + "..."
            
            status_text = "SAFE" if result["overall_status"] == "safe" else "ESCALATION"
            dilution_str = f"{result['required_dilution']:.1f}x" if result['required_dilution'] > 1 else "None"
            h2_producible = result['total_volume'] / WATER_PER_KG_H2
            
            table_data.append({
                "Rank": idx + 1,
                "Status": status_text,
                "Combination": sources_str,
                "Volume (L)": f"{result['total_volume']:.1f}",
                "H2 Output (kg)": f"{h2_producible:.1f}",
                "Safety Score": f"{result['safety_score']:.1f}",
                "Limiting Analyte": result.get("worst_analyte", "N/A") or "N/A",
                "Dilution Needed": dilution_str
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Detailed analysis
        st.markdown(f"<h3 style='color:{SECONDARY_GREEN}; font-family:Hind;'>Detailed Analysis</h3>", unsafe_allow_html=True)
        
        for idx, result in enumerate(results[:min(10, top_n_results)]):
            sources_str = " + ".join([f"{v:.1f}L {t}" for t, v in result["water_sources"]])
            status_text = result["overall_status"].upper()
            h2_producible = result['total_volume'] / WATER_PER_KG_H2
            
            with st.expander(f"#{idx+1} | {status_text} | {h2_producible:.1f} kg H2 | {sources_str}", expanded=(idx == 0)):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown(f"**Water Sources:**")
                    for water_type, volume in result["water_sources"]:
                        st.markdown(f"- {water_type}: {volume:.2f} L")
                    st.markdown(f"**Total Volume:** {result['total_volume']:.2f} L")
                    st.markdown(f"**H2 Producible:** {h2_producible:.1f} kg")
                
                with col_b:
                    st.markdown(f"**Safety Score:** {result['safety_score']:.2f}")
                    st.markdown(f"**Limiting Analyte:** {result.get('worst_analyte', 'N/A')}")
                    
                    if result['required_dilution'] > 1:
                        st.markdown(f"**Dilution Required:** {result['required_dilution']:.1f}x")
                        pure_water_needed = result['total_volume'] * (result['required_dilution'] - 1)
                        st.markdown(f"Add **{pure_water_needed:.1f}L purified water** to make safe")
                    else:
                        st.markdown(f"**No dilution needed**")
                
                # Analyte breakdown table
                st.markdown("**Analyte Breakdown:**")
                analyte_data = []
                for analyte, data in result["analyte_results"].items():
                    status = "SAFE" if data["status"] == "safe" else "ESCALATION"
                    analyte_data.append({
                        "Analyte": analyte,
                        "Final (mg/L)": f"{data['final_concentration']:.4f}",
                        "Limit (mg/L)": f"{data['escalation_level']:.4f}",
                        "Status": status
                    })
                st.dataframe(pd.DataFrame(analyte_data), use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align:center; color:{LIGHT_GREY}; font-family:Hind; padding:20px;'>
    <p style='margin:0;'>HydroStar Europe Ltd.</p>
    <p style='margin:5px 0 0 0; font-size:12px;'>For inquiries: domanique@hydrostar-eu.com | www.hydrostar-eu.com</p>
</div>
""", unsafe_allow_html=True)
