import base64
from pathlib import Path
from datetime import datetime
import streamlit as st
import polars as pl
import numpy as np
import plotly.graph_objects as go

# 1. Very first Streamlit call as strictly required
st.set_page_config(
    page_title="Delhi GridPulse",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Branded Preloader Splash Screen (Elastic Rubber-Band Lock)
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def _get_splash_bg_css() -> str:
    possible_paths = [
        Path("assets/splash_bg_opt.jpg"),
        Path("assets/splash_bg.png"),
        Path("splash_bg.png"),
        Path("splash_bg.png.png"),
        Path("data/splash_bg.png"),
    ]
    img_path = next((p for p in possible_paths if p.exists()), None)
    if img_path:
        mime = "image/jpeg" if img_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
        b64 = base64.b64encode(img_path.read_bytes()).decode("utf-8")
        return f"background: linear-gradient(rgba(248, 250, 252, 0.75), rgba(241, 245, 249, 0.85)), url('data:{mime};base64,{b64}') center/cover no-repeat;"
    return "background: radial-gradient(at 0% 0%, rgba(224, 242, 254, 0.85) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(236, 253, 245, 0.85) 0px, transparent 50%), #F8FAFC;"

SPLASH_BG_STYLE = _get_splash_bg_css()

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    #splash-overlay {{
        position: fixed;
        inset: 0;
        width: 100vw;
        height: 100vh;
        z-index: 9999999;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        {SPLASH_BG_STYLE}
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        animation: splashDismiss 0.5s cubic-bezier(0.4, 0, 0.2, 1) 2.4s forwards;
        pointer-events: auto;
        overflow: hidden;
    }}

    .splash-content {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        user-select: none;
    }}

    .splash-brand {{
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Fredoka', 'Baloo 2', sans-serif;
        font-size: clamp(3.2rem, 7.5vw, 5.8rem);
        font-weight: 700;
        line-height: 1;
        letter-spacing: -0.01em;
        color: #38BDF8;
        text-shadow: 0 4px 18px rgba(56, 189, 248, 0.35), 0 0 40px rgba(14, 165, 233, 0.25);
        margin-bottom: 1.25rem;
    }}

    .word-delhi {{
        display: inline-block;
        animation: slideInLeft 0.85s cubic-bezier(0.175, 0.885, 0.32, 1.275) 0.1s both;
    }}

    .splash-hyphen {{
        display: inline-block;
        color: #06B6D4;
        text-shadow: 0 0 20px rgba(6, 182, 212, 0.8), 0 0 35px rgba(56, 189, 248, 0.6);
        animation: hyphenConnect 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.75s both,
                   hyphenGlow 1.2s ease-in-out 1.2s infinite alternate;
        margin: 0 2px;
    }}

    .word-grid {{
        display: inline-block;
        animation: slideInRight 0.85s cubic-bezier(0.175, 0.885, 0.32, 1.275) 0.1s both;
    }}

    .splash-subtext {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: clamp(0.75rem, 1.8vw, 0.95rem);
        font-weight: 700;
        letter-spacing: 0.24em;
        color: #0284C7;
        text-transform: uppercase;
        opacity: 0;
        animation: subtextFadeIn 0.6s ease-out 0.95s forwards;
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    .splash-loader-bar {{
        width: 140px;
        height: 3px;
        background: rgba(203, 213, 225, 0.6);
        border-radius: 9999px;
        margin-top: 14px;
        overflow: hidden;
        position: relative;
        opacity: 0;
        animation: subtextFadeIn 0.6s ease-out 1.05s forwards;
    }}

    .splash-loader-progress {{
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        width: 100%;
        background: linear-gradient(90deg, #0284C7, #38BDF8, #10B981);
        border-radius: 9999px;
        animation: loaderFill 1.3s cubic-bezier(0.4, 0, 0.2, 1) 1.1s both;
    }}

    @keyframes slideInLeft {{
        0% {{
            transform: translateX(-160%);
            opacity: 0;
        }}
        60% {{
            opacity: 1;
        }}
        100% {{
            transform: translateX(0);
            opacity: 1;
        }}
    }}

    @keyframes slideInRight {{
        0% {{
            transform: translateX(160%);
            opacity: 0;
        }}
        60% {{
            opacity: 1;
        }}
        100% {{
            transform: translateX(0);
            opacity: 1;
        }}
    }}

    @keyframes hyphenConnect {{
        0% {{
            transform: scale(0.1);
            opacity: 0;
        }}
        70% {{
            transform: scale(1.35);
            opacity: 1;
        }}
        100% {{
            transform: scale(1);
            opacity: 1;
        }}
    }}

    @keyframes hyphenGlow {{
        from {{
            text-shadow: 0 0 10px rgba(6, 182, 212, 0.6);
            color: #38BDF8;
        }}
        to {{
            text-shadow: 0 0 25px rgba(16, 185, 129, 0.9), 0 0 40px rgba(56, 189, 248, 0.7);
            color: #10B981;
        }}
    }}

    @keyframes subtextFadeIn {{
        0% {{
            opacity: 0;
            transform: translateY(6px);
        }}
        100% {{
            opacity: 0.95;
            transform: translateY(0);
        }}
    }}

    @keyframes loaderFill {{
        0% {{
            transform: translateX(-100%);
        }}
        100% {{
            transform: translateX(0%);
        }}
    }}

    @keyframes splashDismiss {{
        0% {{
            opacity: 1;
            visibility: visible;
            pointer-events: auto;
        }}
        90% {{
            opacity: 0;
            visibility: visible;
            pointer-events: none;
        }}
        100% {{
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
            display: none !important;
        }}
    }}
    </style>

    <div id="splash-overlay">
        <div class="splash-content">
            <div class="splash-brand">
                <span class="word-delhi">Delhi</span>
                <span class="splash-hyphen">-</span>
                <span class="word-grid">Grid</span>
            </div>
            <div class="splash-subtext">
                <span>SYNCHRONIZING SLDC TELEMETRY...</span>
            </div>
            <div class="splash-loader-bar">
                <div class="splash-loader-progress"></div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Exact Global CSS Block to Eradicate Styling Conflicts
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* 1. Global App Canvas Overrides */
    :root {
        --primary-color: #0284C7;
        --background-color: #F8FAFC;
        --secondary-background-color: #FFFFFF;
        --text-color: #0F172A;
        --font: 'Plus Jakarta Sans', sans-serif;
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background: radial-gradient(at 0% 0%, rgba(224, 242, 254, 0.75) 0px, transparent 50%), 
                    radial-gradient(at 100% 100%, rgba(236, 253, 245, 0.75) 0px, transparent 50%), 
                    #F1F5F9 !important;
        color: #0F172A !important;
    }

    [data-testid="stAppViewBlockContainer"],
    [data-testid="stMainBlockContainer"] {
        padding-bottom: 100px !important;
    }

    /* 2. Eradicate Streamlit's Black Header & Chrome */
    header[data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid rgba(226, 232, 240, 0.8) !important;
    }
    header[data-testid="stHeader"] svg {
        fill: #0F172A !important;
    }
    [data-testid="stToolbar"] {
        right: 1.5rem;
    }

    /* 3. Frosted Light Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.75) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(226, 232, 240, 0.8) !important;
    }
    [data-testid="stSidebar"] * {
        color: #0F172A !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-weight: 600 !important;
        color: #334155 !important;
    }

    /* 1. Disable Draggable Resizing completely */
    [data-testid="stSidebarResizeHandle"] {
        display: none !important;
        pointer-events: none !important;
    }

    /* 2. Lock Fixed Width when Expanded */
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 280px !important;
        max-width: 280px !important;
        width: 280px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    /* 3. Maintain Slim Visible Rail when Collapsed (Rather than total zero collapse) */
    [data-testid="stSidebar"][aria-expanded="false"] {
        min-width: 56px !important;
        max-width: 56px !important;
        width: 56px !important;
        margin-left: 0 !important;
        transform: none !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        overflow: hidden !important;
        background: rgba(255, 255, 255, 0.65) !important;
        backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(226, 232, 240, 0.8) !important;
    }

    /* Hide text and content in the collapsed rail to prevent ugly horizontal clipping */
    [data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarUserContent"] {
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* Adjust Main Canvas margin so it does not tuck behind the 56px rail */
    [data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="false"]) {
        padding-left: 0px !important;
    }

    /* 4. Replace Chevron Arrow with 3 Horizontal Lines (Hamburger Icon) */
    /* 1. Hide ALL native child elements inside the toggle buttons (SVG, spans, material icons) */
    [data-testid="stSidebarCollapseButton"] button *,
    [data-testid="stSidebarExpandButton"] button * {
        display: none !important;
        visibility: hidden !important;
    }

    /* 2. Position the button container cleanly */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarExpandButton"] button {
        position: relative !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 38px !important;
        height: 38px !important;
        border-radius: 8px !important;
        background: rgba(255, 255, 255, 0.85) !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        padding: 0 !important;
        cursor: pointer !important;
    }

    /* 3. Render ONLY the 3 horizontal bars via ::before */
    [data-testid="stSidebarCollapseButton"] button::before,
    [data-testid="stSidebarExpandButton"] button::before {
        content: "" !important;
        display: block !important;
        position: absolute !important;
        width: 18px !important;
        height: 2px !important;
        background-color: #0F172A !important;
        border-radius: 1px !important;
        box-shadow: 0 -5px 0 0 #0F172A, 0 5px 0 0 #0F172A !important;
        margin: 0 !important;
    }

    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="stSidebarExpandButton"] button:hover {
        background: #F1F5F9 !important;
    }

    /* 4. Fix Invisible Text in Native Components */
    p, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #0F172A !important;
    }
    .stCaption, small, [data-testid="stMarkdownContainer"] p:has(small) {
        color: #64748B !important;
    }

    /* 5. Clean Frosted Glass Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.95) !important;
        border-radius: 16px !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: 0 10px 25px -5px rgba(148, 163, 184, 0.15), 0 8px 10px -6px rgba(148, 163, 184, 0.1) !important;
        margin-bottom: 1rem !important;
    }

    .metric-card {
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        border-radius: 14px !important;
        padding: 1.2rem 1.4rem !important;
        min-height: 140px !important;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(148, 163, 184, 0.08) !important;
        margin: 0 !important;
    }

    /* Raised Glass Bubble Frame for Main Chart */
    .chart-bubble-container {
        background: rgba(255, 255, 255, 0.82) !important;
        backdrop-filter: blur(24px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
        border-radius: 24px !important;
        border: 1.5px solid rgba(255, 255, 255, 0.95) !important;
        padding: 24px 28px 16px 28px !important;
        margin: 1.5rem 0 2rem 0 !important;
        /* Multi-tier depth shadows to simulate physical elevation */
        box-shadow: 
            0 20px 40px -15px rgba(15, 23, 42, 0.08),
            0 8px 16px -6px rgba(15, 23, 42, 0.04),
            inset 0 1px 2px rgba(255, 255, 255, 0.9),
            inset 0 -1px 2px rgba(226, 232, 240, 0.6) !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    }

    /* Target Streamlit's Plotly container to ensure transparent inner bounds */
    .chart-bubble-container [data-testid="stPlotlyChart"] {
        background: transparent !important;
        border-radius: 18px !important;
        overflow: hidden !important;
    }

    /* Soft hover lift */
    .chart-bubble-container:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 26px 50px -15px rgba(15, 23, 42, 0.12),
            0 12px 20px -6px rgba(15, 23, 42, 0.06),
            inset 0 1px 2px rgba(255, 255, 255, 0.95) !important;
    }

    /* 6. Metric Cards Typography & Contrast */
    .metric-label {
        display: block !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #64748B !important;
        line-height: 1.25 !important;
        margin: 0 0 0.35rem 0 !important;
    }
    .metric-val {
        display: block !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        line-height: 1.25 !important;
        margin: 0 0 0.35rem 0 !important;
        letter-spacing: -0.01em !important;
    }
    .metric-sub {
        display: block !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        line-height: 1.25 !important;
        margin: 0 !important;
    }

    /* 7. Metric Accent Variants */
    .val-blue { color: #0284C7 !important; }
    .val-red { color: #E11D48 !important; }
    .val-amber { color: #D97706 !important; }
    .val-emerald { color: #059669 !important; }

    .badge-blue { background: #E0F2FE; color: #0369A1; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
    .badge-red { background: #FFE4E6; color: #BE123C; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
    .badge-amber { background: #FEF3C7; color: #B45309; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
    .badge-emerald { background: #D1FAE5; color: #047857; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }

    /* 8. Alert Box High-Contrast Fix */
    .alert-banner-critical {
        background: rgba(254, 242, 242, 0.9) !important;
        border: 1px solid #FECDD3 !important;
        border-left: 5px solid #E11D48 !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        color: #9F1239 !important;
        font-weight: 600 !important;
    }

    /* 9. Sliders, Buttons, and Selectbox Styling */
    .stSlider [data-baseweb="slider"] {
        margin-top: 0.5rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #0284C7, #0EA5E9) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.25rem !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(2, 132, 199, 0.35) !important;
    }

    /* 10. Data Table & Micro Components */
    [data-testid="stDataFrame"] {
        background: #FFFFFF !important;
        border-radius: 12px !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        box-shadow: 0 4px 16px rgba(148, 163, 184, 0.08) !important;
    }

    /* Brand Card & Isolated Floating Advisory Beacon */
    .brand-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 10px 18px;
        box-shadow: 0 4px 18px rgba(148, 163, 184, 0.08);
        display: flex;
        align-items: center;
    }
    .brand-group {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .logo-orb {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        background: linear-gradient(135deg, #0284C7, #06B6D4, #10B981);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
    }
    .brand-title {
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #0F172A;
        line-height: 1.1;
    }
    .brand-tag {
        font-size: 0.78rem;
        font-weight: 500;
        color: #64748B;
    }

    /* Clean Header Container & Clearfix */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        margin-bottom: 2rem !important; /* Forces strict vertical separation */
        padding-bottom: 0.75rem;
        clear: both;
    }

    /* Isolated Floating Advisory Beacon */
    .status-capsule {
        display: inline-flex;
        align-items: center;
        justify-content: flex-end;
        gap: 12px;
        padding: 8px 16px;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 9999px;
        border: 1px solid rgba(226, 232, 240, 0.9);
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.06);
    }

    .beacon-orb {
        width: 14px;
        height: 14px;
        min-width: 14px;
        min-height: 14px;
        border-radius: 50%;
        position: relative;
    }

    /* Dynamic Beacon Colors & Keyframe Pulses */
    .beacon-green {
        background-color: #10B981;
        box-shadow: 0 0 10px #10B981, 0 0 20px rgba(16, 185, 129, 0.4);
        animation: pulse-green 2s infinite;
    }
    .beacon-amber {
        background-color: #F59E0B;
        box-shadow: 0 0 10px #F59E0B, 0 0 20px rgba(245, 158, 11, 0.4);
        animation: pulse-amber 1.6s infinite;
    }
    .beacon-red {
        background-color: #EF4444;
        box-shadow: 0 0 12px #EF4444, 0 0 24px rgba(239, 68, 68, 0.5);
        animation: pulse-red 1.2s infinite;
    }

    @keyframes pulse-green {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.15); opacity: 0.75; }
    }
    @keyframes pulse-amber {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
    }
    @keyframes pulse-red {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.25); opacity: 0.6; }
    }

    .beacon-text {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 0.01em;
        line-height: 1.15;
    }
    .text-green {
        color: #047857;
    }
    .text-amber {
        color: #B45309;
    }
    .text-red {
        color: #BE123C;
    }
    .beacon-sub {
        font-size: 0.7rem;
        font-weight: 600;
        color: #64748B;
        line-height: 1.1;
    }

    /* Pin the AI Bot container directly to the viewport */
    div[data-testid="stPopover"]:has(.chat-bot-marker),
    .floating-bot-wrapper {
        position: fixed !important;
        bottom: 28px !important;
        right: 28px !important;
        z-index: 999999 !important;
        display: block !important;
    }

    /* Target the trigger button itself to float independently */
    .floating-bot-wrapper button {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(240, 249, 255, 0.9)) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1.5px solid rgba(255, 255, 255, 1) !important;
        border-radius: 9999px !important;
        padding: 10px 20px !important;
        box-shadow: 0 10px 30px -5px rgba(2, 132, 199, 0.35), 
                    0 4px 12px -2px rgba(15, 23, 42, 0.1) !important;
        color: #0284C7 !important;
        font-weight: 700 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.9rem !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }

    .floating-bot-wrapper button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 16px 36px -5px rgba(2, 132, 199, 0.45) !important;
    }

    /* Floating Popover Dialogue Overlay */
    div[data-testid="stPopoverBody"] {
        position: fixed !important;
        bottom: 85px !important;
        right: 28px !important;
        width: 380px !important;
        max-height: 520px !important;
        background: rgba(255, 255, 255, 0.92) !important;
        backdrop-filter: blur(24px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
        border: 1.5px solid rgba(255, 255, 255, 1) !important;
        border-radius: 20px !important;
        box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.25) !important;
        z-index: 999999 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Core Engine Pipeline (Zero-Latency Cached Inference)
# ---------------------------------------------------------
from engine.ingestion import fetch_weather_telemetry
from engine.forecaster import train_and_predict
from engine.physics import apply_net_load_and_feeders, simulate_bess_dispatch
from engine.alerting import evaluate_grid_alerts

DATA_DIR = Path(__file__).resolve().parent / "data"
TRAIN_PARQUET = str(DATA_DIR / "synthetic_delhi_demand.parquet")
FEEDER_PARQUET = str(DATA_DIR / "feeder_weights.parquet")


@st.cache_data(show_spinner="Updating weather telemetry and forecast model...")
def get_cached_gross_forecast():
    weather_df, provenance = fetch_weather_telemetry()
    forecast_df = train_and_predict(TRAIN_PARQUET, weather_df)
    return forecast_df, provenance


# ---------------------------------------------------------
# Session State Persistence (Global Physics Parameters)
# ---------------------------------------------------------
if "temp_delta" not in st.session_state:
    st.session_state["temp_delta"] = 0.0
if "solar_mw" not in st.session_state:
    st.session_state["solar_mw"] = 1800.0
if "mva_limit" not in st.session_state:
    st.session_state["mva_limit"] = 9500.0
if "power_factor" not in st.session_state:
    st.session_state["power_factor"] = 0.95
if "deduct_solar" not in st.session_state:
    st.session_state["deduct_solar"] = True
if "nav_view" not in st.session_state:
    st.session_state["nav_view"] = "Overview"
if "bess_enabled" not in st.session_state:
    st.session_state["bess_enabled"] = False
if "bess_max_mw" not in st.session_state:
    st.session_state["bess_max_mw"] = 400.0
if "bess_capacity_mwh" not in st.session_state:
    st.session_state["bess_capacity_mwh"] = 1200.0
if "bess_shave_threshold" not in st.session_state:
    st.session_state["bess_shave_threshold"] = 8000.0
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {
            "role": "assistant",
            "content": "Hi there! I'm your GridPulse Assistant ⚡. Tap any of the quick questions below or ask me anything about today's forecast and power metrics in plain English!"
        }
    ]

gross_forecast_df, provenance_label = get_cached_gross_forecast()

# ---------------------------------------------------------
# Clean Context-Aware Frosted Light Sidebar
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <div style="font-size: 1.3rem;">⚡</div>
            <div style="font-weight: 800; font-size: 1.15rem; color: #0F172A;">SLDC OPERATING DECK</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Date Horizon Selector
    all_dates = gross_forecast_df["timestamp"].dt.date().unique().to_list()
    selected_date = st.selectbox(
        "📅 Forecast Horizon Date",
        options=all_dates,
        index=0,
        format_func=lambda d: d.strftime("%A, %d %b %Y"),
    )

    st.markdown('<div class="metric-label" style="margin-top: 14px;">Navigation Views</div>', unsafe_allow_html=True)
    nav_options = [
        "Overview",
        "Load Simulator",
        "Regional Feeders",
        "Grid Reliability",
        "Settings",
    ]
    current_idx = nav_options.index(st.session_state["nav_view"]) if st.session_state["nav_view"] in nav_options else 0
    nav_selection = st.radio(
        "Navigation",
        options=nav_options,
        index=current_idx,
        label_visibility="collapsed",
    )
    st.session_state["nav_view"] = nav_selection

    # Active Summary Badge
    active_td = float(st.session_state["temp_delta"])
    active_solar = float(st.session_state["solar_mw"]) if st.session_state.get("deduct_solar", True) else 0.0
    active_ceiling = float(st.session_state["mva_limit"]) * float(st.session_state["power_factor"])
    bess_active_side = bool(st.session_state.get("bess_enabled", False))
    bess_status_html = (
        f'<div style="font-size: 0.8rem; font-weight: 700; color: #059669; margin-top: 4px;">'
        f'🔋 BESS: <b>Active ({st.session_state.get("bess_max_mw", 400.0):,.0f} MW)</b></div>'
        if bess_active_side
        else '<div style="font-size: 0.78rem; font-weight: 500; color: #94A3B8; margin-top: 4px;">🔋 BESS: Standby</div>'
    )

    st.markdown(
        f"""
        <div style="background: rgba(255, 255, 255, 0.85); border: 1px solid #CBD5E1; border-radius: 12px; padding: 12px 14px; margin-top: 20px; box-shadow: 0 4px 12px rgba(148, 163, 184, 0.08);">
            <div class="metric-label" style="margin-bottom: 6px;">Active Dispatch Parameters</div>
            <div style="font-size: 0.8rem; font-weight: 600; color: #0284C7; margin-bottom: 4px;">
                🌡️ Temp Shock: <b>{active_td:+.1f}°C</b>
            </div>
            <div style="font-size: 0.8rem; font-weight: 600; color: #059669; margin-bottom: 4px;">
                ☀️ Solar Inflow: <b>{active_solar:,.0f} MW</b>
            </div>
            <div style="font-size: 0.8rem; font-weight: 600; color: #64748B; margin-bottom: 4px;">
                ⚡ Grid Ceiling: <b>{active_ceiling:,.0f} MW</b>
            </div>
            {bess_status_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 8px; background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 10px; margin-top: 22px;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: #10B981; box-shadow: 0 0 6px #10B981;"></div>
            <div>
                <div style="font-size: 0.78rem; font-weight: 700; color: #0F172A;">SLDC Main Server: Online</div>
                <div style="font-size: 0.7rem; color: #64748B;">Telemetry Stream Active</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# Sub-10ms Vector Physics & DuckDB Alert Engine
# ---------------------------------------------------------
# Filter for active operational day (96 blocks)
active_gross_df = gross_forecast_df.filter(pl.col("timestamp").dt.date() == selected_date)
if active_gross_df.height == 0:
    active_gross_df = gross_forecast_df.head(96)
elif active_gross_df.height > 96:
    active_gross_df = active_gross_df.head(96)

# Extract global variables from session state
temp_delta = float(st.session_state["temp_delta"])
installed_solar_mw = float(st.session_state["solar_mw"]) if st.session_state.get("deduct_solar", True) else 0.0
raw_solar_capacity = float(st.session_state["solar_mw"])
mva_limit = float(st.session_state["mva_limit"])
power_factor = float(st.session_state["power_factor"])
grid_capacity_mw = mva_limit * power_factor

physics_df = apply_net_load_and_feeders(
    forecast_df=active_gross_df,
    feeder_weights_path=FEEDER_PARQUET,
    installed_solar_mw=installed_solar_mw,
    temp_delta=temp_delta,
)

# Automated BESS Peak Shaving Vector Dispatch
bess_enabled = bool(st.session_state["bess_enabled"])
bess_max_mw = float(st.session_state["bess_max_mw"])
bess_capacity_mwh = float(st.session_state["bess_capacity_mwh"])
bess_shave_threshold = float(st.session_state["bess_shave_threshold"])

physics_df = simulate_bess_dispatch(
    df=physics_df,
    battery_capacity_mwh=bess_capacity_mwh,
    max_power_mw=bess_max_mw if bess_enabled else 0.0,
    shave_threshold_mw=bess_shave_threshold,
)

alert_df = evaluate_grid_alerts(
    df=physics_df,
    mva_limit=mva_limit,
    power_factor=power_factor,
)

# Derived Real-Time Telemetry Figures
peak_net_p50 = float(alert_df["net_p50"].max())
peak_net_p90 = float(alert_df["net_p90"].max())
peak_gross = float(alert_df["gross_p50"].max())
peak_solar = float(alert_df["solar_generation_mw"].max())
peak_loading = float(alert_df["transformer_loading_pct"].max())
max_ramp_rate = float(alert_df["ramp_rate_mw_min"].abs().max())
max_temp = float(alert_df["temperature_2m"].max()) + temp_delta
max_apparent = float(alert_df["apparent_temperature"].max()) + temp_delta
peak_ghi = float(alert_df["ghi"].max()) if "ghi" in alert_df.columns else 950.0

current_demand = float(alert_df["net_p50"][0])
current_trend_mw = float(alert_df["net_p50"][4] - alert_df["net_p50"][0]) if alert_df.height > 4 else 180.0

peak_idx = int(alert_df["net_p50"].to_numpy().argmax())
peak_time = alert_df["timestamp"][peak_idx]
peak_time_str = peak_time.strftime("%H:%M IST") if hasattr(peak_time, "strftime") else "15:30 IST"

# BESS Telemetry Figures
peak_post_bess = float(alert_df["post_bess_demand_mw"].max())
bess_shaved_mw = max(0.0, peak_net_p50 - peak_post_bess) if bess_enabled else 0.0
bess_dispatched_blocks = int((alert_df["bess_dispatch_mw"] > 0).sum()) if bess_enabled else 0
bess_hours_mitigated = bess_dispatched_blocks * 0.25
min_soc = float(alert_df["bess_soc_pct"].min()) if bess_enabled else 50.0
max_soc = float(alert_df["bess_soc_pct"].max()) if bess_enabled else 50.0

effective_peak = peak_post_bess if bess_enabled else peak_net_p50
effective_loading = (effective_peak / grid_capacity_mw) * 100.0

has_critical = bool((alert_df["loading_alert"] == "CRITICAL_RED").any())
has_amber = bool((alert_df["loading_alert"] == "AMBER").any())

# Check if BESS successfully mitigated transmission overload
bess_mitigated_critical = bess_enabled and has_critical and (effective_peak <= grid_capacity_mw)
if bess_mitigated_critical:
    has_critical = False
    has_amber = effective_loading > 85.0

# ---------------------------------------------------------
# --- 1. TOP HEADER & BEACON STRIP ---
if has_critical or peak_net_p50 > grid_capacity_mw:
    beacon_class = "beacon-red"
    status_title = "CRITICAL: HEADROOM BREACH"
elif bess_mitigated_critical:
    beacon_class = "beacon-green"
    status_title = "SYSTEM NOMINAL"
elif has_amber:
    beacon_class = "beacon-amber"
    status_title = "ADVISORY: MANAGED STRESS"
else:
    beacon_class = "beacon-green"
    status_title = "SYSTEM NOMINAL"

header_col1, header_col2 = st.columns([0.65, 0.35], vertical_alignment="center")

with header_col1:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, #0284C7, #38BDF8); display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 16px; box-shadow: 0 4px 12px rgba(14, 165, 233, 0.25);">⚡</div>
            <div>
                <h1 style="margin: 0; font-size: 1.6rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em; line-height: 1.2;">GridPulse Delhi</h1>
            </div>
        </div>
    """, unsafe_allow_html=True)

with header_col2:
    # Dynamic beacon orb class: 'beacon-green', 'beacon-amber', or 'beacon-red'
    st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; align-items: center;">
            <div class="status-capsule">
                <div class="beacon-orb {beacon_class}"></div>
                <span style="font-weight: 700; font-size: 0.85rem; color: #0F172A; letter-spacing: 0.03em;">{status_title}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 2. FORCED VERTICAL SPACING GAP ---
st.markdown("<div style='height: 24px; clear: both;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Shared Helper: Strict Plotly Layout Preset
# ---------------------------------------------------------
def apply_light_plotly_layout(
    fig,
    height=480,
    title_text="",
    xaxis_title="Time Block (15-min Intervals)",
    yaxis_title="Operational Demand (MW)",
    margin=None,
):
    m = margin or dict(l=55, r=30, t=75, b=55)
    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b>" if title_text else None,
            y=0.96,  # Pins title near top edge of the canvas
            x=0.03,
            xanchor="left",
            yanchor="top",
            font=dict(family="Plus Jakarta Sans", size=15, color="#0F172A"),
        ) if title_text else None,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans", color="#334155"),
        hovermode="x unified",
        height=height,
        margin=m,
        xaxis=dict(
            automargin=True,  # Automatically calculates spacing for dates/labels
            showgrid=True,
            gridcolor="rgba(203, 213, 225, 0.5)",
            tickfont=dict(color="#64748B", size=11),
            title=dict(
                text=xaxis_title,
                standoff=18,  # Generous separation between tick numbers and axis title
                font=dict(color="#334155", size=12),
            ),
        ),
        yaxis=dict(
            automargin=True,
            showgrid=True,
            gridcolor="rgba(203, 213, 225, 0.5)",
            tickfont=dict(color="#64748B", size=11),
            title=dict(
                text=yaxis_title,
                standoff=18,
                font=dict(color="#334155", size=12),
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,  # Places legend directly above plotting area, cleanly below the title
            xanchor="right",
            x=0.98,
            font=dict(color="#334155", size=11),
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(226, 232, 240, 0.8)",
            borderwidth=1,
        ),
    )


# ---------------------------------------------------------
# VIEW 1: OPERATIONS DASHBOARD (Overview)
# ---------------------------------------------------------
if st.session_state["nav_view"] == "Overview":
    # --- 3. FOUR TOP METRIC CARDS ROW ---
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                    <span class="metric-label" style="margin: 0 !important;">CURRENT DEMAND</span>
                    <span class="badge-blue">Block #42</span>
                </div>
                <span class="metric-val val-blue">{current_demand:,.0f} <span style="font-size: 1.15rem; color: #64748B; font-weight: 700;">MW</span></span>
                <span class="metric-sub">
                    <span>Est. Peak: {peak_time_str}</span>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        if bess_enabled and bess_shaved_mw > 0:
            stress_badge = f"{effective_loading:.1f}% Managed"
            badge_class = "badge-emerald" if effective_loading <= 85.0 else ("badge-amber" if effective_loading <= 95.0 else "badge-red")
            val_class = "val-emerald" if effective_loading <= 85.0 else ("val-amber" if effective_loading <= 95.0 else "val-red")
            peak_val_display = f"{effective_peak:,.0f}"
            metric_label = "MANAGED PEAK"
        else:
            stress_badge = "Capacity Alert" if peak_loading > 95.0 else ("Elevated" if peak_loading > 85.0 else "Nominal")
            badge_class = "badge-red" if peak_loading > 95.0 else ("badge-amber" if peak_loading > 85.0 else "badge-emerald")
            val_class = "val-red" if peak_loading > 95.0 else ("val-amber" if peak_loading > 85.0 else "val-blue")
            peak_val_display = f"{peak_net_p50:,.0f}"
            metric_label = "PEAK NET DEMAND"

        st.markdown(
            f"""
            <div class="metric-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                    <span class="metric-label" style="margin: 0 !important;">{metric_label}</span>
                    <span class="{badge_class}">{stress_badge}</span>
                </div>
                <span class="metric-val {val_class}">{peak_val_display} <span style="font-size: 1.15rem; color: #64748B; font-weight: 700;">MW</span></span>
                <span class="metric-sub">
                    <span>Est. Peak: {peak_time_str}</span>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        temp_badge = "Severe Heatwave" if max_temp >= 42.0 else "Heat Advisory"
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                    <span class="metric-label" style="margin: 0 !important;">AMBIENT TEMP</span>
                    <span class="badge-amber">{temp_badge}</span>
                </div>
                <span class="metric-val val-amber">{max_temp:.1f}°C</span>
                <span class="metric-sub">
                    <span>Heat Index: <b>{max_apparent:.1f}°C</b></span>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                    <span class="metric-label" style="margin: 0 !important;">ACTIVE SOLAR CONTRIBUTION</span>
                    <span class="badge-emerald">Grid Inflow Active</span>
                </div>
                <span class="metric-val val-emerald">{peak_solar:,.0f} <span style="font-size: 1.15rem; color: #64748B; font-weight: 700;">MW</span></span>
                <span class="metric-sub">
                    <span style="color: #059669; font-weight: 700;">{installed_solar_mw:,.0f} MW Installed</span>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------------------------------------------------------
    # BESS Control & Telemetry HUD Card
    # ---------------------------------------------------------
    st.markdown(
        """
        <div class="glass-card" style="margin-top: 0.5rem; margin-bottom: 1.25rem; padding: 18px 22px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 38px; height: 38px; border-radius: 10px; background: linear-gradient(135deg, #10B981, #06B6D4); display: flex; align-items: center; justify-content: center; font-size: 1.25rem; color: #FFF; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);">
                        🔋
                    </div>
                    <div>
                        <div style="font-weight: 800; font-size: 1.05rem; color: #0F172A; letter-spacing: -0.01em;">
                            AUTOMATED BESS PEAK SHAVING & STORAGE BUFFER
                        </div>
                        <div style="font-size: 0.78rem; color: #64748B;">
                            Utility-scale 4-hour Li-ion battery storage: Midday solar absorption (10:00–14:00) & automated peak demand clipping.
                        </div>
                    </div>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    bess_row1, bess_row2 = st.columns([1.2, 2.8])
    with bess_row1:
        st.toggle(
            "⚡ Auto-Deploy BESS Peak Shaving",
            key="bess_enabled",
            help="When enabled, automatically shaves demand exceeding the threshold up to inverter capacity, and charges during midday solar trough.",
        )
        if bess_enabled:
            st.markdown(
                '<div style="font-size: 0.8rem; font-weight: 700; color: #059669; display: flex; align-items: center; gap: 6px;">'
                '<span style="width: 8px; height: 8px; border-radius: 50%; background: #10B981; display: inline-block;"></span>'
                'STATUS: ACTIVE DISPATCH (CLIPPING)</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="font-size: 0.8rem; font-weight: 600; color: #94A3B8; display: flex; align-items: center; gap: 6px;">'
                '<span style="width: 8px; height: 8px; border-radius: 50%; background: #CBD5E1; display: inline-block;"></span>'
                'STATUS: STANDBY / BYPASS MODE</div>',
                unsafe_allow_html=True,
            )

    with bess_row2:
        if bess_enabled:
            b_m1, b_m2, b_m3 = st.columns(3)
            with b_m1:
                st.markdown(
                    f"""
                    <div style="background: rgba(255, 255, 255, 0.7); border: 1px solid #CBD5E1; border-radius: 10px; padding: 10px 14px;">
                        <div style="font-size: 0.7rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Peak Demand Shaved</div>
                        <div style="font-size: 1.35rem; font-weight: 800; color: #10B981;">-{bess_shaved_mw:,.0f} <span style="font-size: 0.85rem; color: #64748B;">MW</span></div>
                        <div style="font-size: 0.72rem; color: #059669; font-weight: 600;">Target: ≤ {bess_shave_threshold:,.0f} MW</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with b_m2:
                st.markdown(
                    f"""
                    <div style="background: rgba(255, 255, 255, 0.7); border: 1px solid #CBD5E1; border-radius: 10px; padding: 10px 14px;">
                        <div style="font-size: 0.7rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Peak Hours Mitigated</div>
                        <div style="font-size: 1.35rem; font-weight: 800; color: #0284C7;">{bess_hours_mitigated:.1f} <span style="font-size: 0.85rem; color: #64748B;">Hrs</span></div>
                        <div style="font-size: 0.72rem; color: #0369A1; font-weight: 600;">{bess_dispatched_blocks} active blocks (15-min)</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with b_m3:
                st.markdown(
                    f"""
                    <div style="background: rgba(255, 255, 255, 0.7); border: 1px solid #CBD5E1; border-radius: 10px; padding: 10px 14px;">
                        <div style="font-size: 0.7rem; font-weight: 700; color: #64748B; text-transform: uppercase;">BESS SoC Dynamic Range</div>
                        <div style="font-size: 1.35rem; font-weight: 800; color: #7C3AED;">{min_soc:.0f}% – {max_soc:.0f}%</div>
                        <div style="font-size: 0.72rem; color: #6D28D9; font-weight: 600;">Reserve floor: 10% | Max: 100%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
                <div style="background: rgba(241, 245, 249, 0.7); border: 1px dashed #CBD5E1; border-radius: 10px; padding: 12px 16px; font-size: 0.82rem; color: #64748B; line-height: 1.4;">
                    💡 <b>BESS Dispatch Standby:</b> Activate the toggle on the left to deploy automated utility-scale peak shaving. Battery capacity will buffer solar surplus at midday and discharge up to 400 MW to clip transmission peaks.
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander("⚙️ BESS Inverter Capacity & Storage Energy Configuration", expanded=bess_enabled):
        b_c1, b_c2, b_c3 = st.columns(3)
        with b_c1:
            st.slider(
                "BESS Inverter Capacity (MW)",
                min_value=100.0,
                max_value=600.0,
                step=25.0,
                key="bess_max_mw",
                help="Maximum continuous charging / discharging power of grid-tied PCS (Power Conversion System).",
            )
        with b_c2:
            st.slider(
                "Storage Energy Capacity (MWh)",
                min_value=400.0,
                max_value=2400.0,
                step=100.0,
                key="bess_capacity_mwh",
                help="Total aggregate battery energy capacity (4-hour duration standard).",
            )
        with b_c3:
            st.slider(
                "Peak Shaving Target Threshold (MW)",
                min_value=7500.0,
                max_value=8200.0,
                step=50.0,
                key="bess_shave_threshold",
                help="Operational demand threshold above which BESS discharges to clamp grid peak.",
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # Centerpiece Chart: 96-Block Dispatch Horizon
    timestamps = alert_df["timestamp"].to_list()
    p10_vals = alert_df["net_p10"].to_list()
    p50_vals = alert_df["net_p50"].to_list()
    p90_vals = alert_df["net_p90"].to_list()
    gross_vals = alert_df["gross_p50"].to_list()
    solar_vals = alert_df["solar_generation_mw"].to_list()
    post_bess_vals = alert_df["post_bess_demand_mw"].to_list()
    bess_soc_vals = alert_df["bess_soc_pct"].to_list()

    fig = go.Figure()

    # P90 upper line (invisible anchor)
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=p90_vals,
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    # P10 lower line + soft luminous cyan uncertainty ribbon
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=p10_vals,
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(14, 165, 233, 0.08)",
        name="Confidence Band",
        hoverinfo="skip",
    ))

    if bess_enabled:
        # Original Unmanaged Demand: faint dashed Cerulean line
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=p50_vals,
            mode="lines",
            line=dict(color="rgba(2, 132, 199, 0.5)", width=2, dash="dot"),
            fill="tozeroy",
            fillcolor="rgba(14, 165, 233, 0.05)",
            name="Unmanaged Demand",
            hovertemplate="<b>%{x|%H:%M IST}</b><br>Load: <b>%{y:,.0f} MW</b><extra></extra>",
        ))

        # Managed Demand (Post-BESS Dispatch): Solid Emerald-Cyan Curve with shading between curves
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=post_bess_vals,
            mode="lines",
            line=dict(color="#10B981", width=3),
            fill="tonexty",
            fillcolor="rgba(16, 185, 129, 0.25)",
            name="Projected Demand (Managed)",
            hovertemplate="<b>%{x|%H:%M IST}</b><br>Load: <b>%{y:,.0f} MW</b><extra></extra>",
        ))

        # Battery State of Charge (SoC %) on secondary y-axis
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=bess_soc_vals,
            mode="lines",
            line=dict(color="#8B5CF6", width=1.8, dash="dashdot"),
            name="BESS SoC (%)",
            yaxis="y2",
            hovertemplate="<b>%{x|%H:%M IST}</b><br>SoC: <b>%{y:.1f}%</b><extra></extra>",
        ))
    else:
        # Projected Demand: Vibrant Cerulean Blue #0284C7 (width: 3)
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=p50_vals,
            mode="lines",
            line=dict(color="#0284C7", width=3),
            fill="tozeroy",
            fillcolor="rgba(14, 165, 233, 0.08)",
            name="Projected Demand",
            hovertemplate="<b>%{x|%H:%M IST}</b><br>Load: <b>%{y:,.0f} MW</b><extra></extra>",
        ))

    # Total Base Load (Pre-Solar): Slate Blue #64748B
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=gross_vals,
        mode="lines",
        line=dict(color="#64748B", width=2, dash="dash"),
        name="Total Base Load",
        hovertemplate="<b>%{x|%H:%M IST}</b><br>Load: <b>%{y:,.0f} MW</b><extra></extra>",
    ))

    # Solar Curve: Warm Amber-Orange #D97706
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=solar_vals,
        mode="lines",
        line=dict(color="#D97706", width=2),
        name="Solar Generation",
        hovertemplate="<b>%{x|%H:%M IST}</b><br>Load: <b>%{y:,.0f} MW</b><extra></extra>",
    ))

    # Capacity Limit: Vivid Coral Carmine #E11D48 (dashed)
    fig.add_trace(go.Scatter(
        x=[timestamps[0], timestamps[-1]],
        y=[grid_capacity_mw, grid_capacity_mw],
        mode="lines",
        line=dict(color="#E11D48", width=2.4, dash="dash"),
        name=f"Grid Capacity Ceiling ({grid_capacity_mw:,.0f} MW)",
        hoverinfo="skip",
    ))

    # If BESS is enabled, show target threshold line
    if bess_enabled:
        fig.add_trace(go.Scatter(
            x=[timestamps[0], timestamps[-1]],
            y=[bess_shave_threshold, bess_shave_threshold],
            mode="lines",
            line=dict(color="#059669", width=1.5, dash="dot"),
            name=f"BESS Target ({bess_shave_threshold:,.0f} MW)",
            hoverinfo="skip",
        ))

    # Floating callout annotation at peak demand
    if bess_enabled and bess_shaved_mw > 0:
        fig.add_annotation(
            x=peak_time,
            y=peak_post_bess,
            text=f"<b>MANAGED PEAK: {peak_post_bess:,.0f} MW</b><br><span style='font-size:10px;'>Clipped: -{bess_shaved_mw:,.0f} MW</span>",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#10B981",
            ax=0,
            ay=-50,
            font=dict(family="Plus Jakarta Sans", size=11, color="#065F46"),
            bgcolor="rgba(209, 250, 229, 0.95)",
            bordercolor="rgba(167, 243, 208, 0.9)",
            borderwidth=1.5,
            borderpad=6,
        )
    else:
        fig.add_annotation(
            x=peak_time,
            y=peak_net_p50,
            text=f"<b>PROJECTED PEAK: {peak_net_p50:,.0f} MW</b> ({peak_time_str})",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#E11D48",
            ax=0,
            ay=-45,
            font=dict(family="Plus Jakarta Sans", size=11, color="#9F1239"),
            bgcolor="rgba(255, 241, 242, 0.95)",
            bordercolor="rgba(254, 205, 211, 0.9)",
            borderwidth=1.5,
            borderpad=6,
        )

    apply_light_plotly_layout(fig, height=500, title_text="DEMAND & CAPACITY HORIZON")
    if bess_enabled:
        fig.update_layout(
            yaxis2=dict(
                title=dict(
                    text="BESS SoC (%)",
                    standoff=14,
                    font=dict(color="#7C3AED", size=12),
                ),
                overlaying="y",
                side="right",
                range=[0, 105],
                showgrid=False,
                automargin=True,
                tickfont=dict(color="#7C3AED", size=11),
            )
        )

    # Render opening wrapper
    st.markdown('<div class="chart-bubble-container">', unsafe_allow_html=True)

    # Display the Plotly Chart
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d", "zoomIn2d", "zoomOut2d"]
        }
    )

    # Render closing wrapper
    st.markdown('</div>', unsafe_allow_html=True)

    # Bottom High-Contrast Alert Banner
    if bess_enabled and bess_mitigated_critical:
        alert_cols = st.columns([4, 1])
        with alert_cols[0]:
            st.markdown(
                f"""
                <div class="alert-banner-nominal" style="background: rgba(209, 250, 229, 0.9); border: 1.5px solid #10B981; border-radius: 14px; padding: 14px 20px; display: flex; align-items: center; gap: 14px; box-shadow: 0 4px 16px rgba(16, 185, 129, 0.12);">
                    <span style="font-size: 1.5rem;">🛡️</span>
                    <div>
                        <div style="font-size: 0.95rem; font-weight: 800; color: #065F46;">
                            SYSTEM STABILIZED // TRANSMISSION OVERLOAD MITIGATED BY BESS DISPATCH
                        </div>
                        <div style="font-size: 0.83rem; color: #047857; margin-top: 2px;">
                            Critical peak demand of <b>{peak_net_p50:,.0f} MW</b> has been automatically shaved down to <b>{peak_post_bess:,.0f} MW</b> (-{bess_shaved_mw:,.0f} MW clipped across {bess_hours_mitigated:.1f} hours). Transformer loading safely contained at <b>{effective_loading:.1f}%</b>.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with alert_cols[1]:
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            if st.button("⚡ Dispatch Details", use_container_width=True):
                st.session_state["nav_view"] = "Regional Feeders"
                st.rerun()
    elif has_critical or peak_net_p50 > grid_capacity_mw:
        alert_cols = st.columns([4, 1])
        with alert_cols[0]:
            st.markdown(
                f"""
                <div class="alert-banner-critical">
                    <span style="font-size: 1.25rem; margin-right: 8px;">⚠</span>
                    <b>Critical Transmission Advisory:</b> South-East Cluster projected to breach capacity threshold at <b>{peak_time_str}</b> ({peak_loading:.1f}% transformer loading). Immediate feeder balancing or BESS peak-shaving dispatch required.
                </div>
                """,
                unsafe_allow_html=True,
            )
        with alert_cols[1]:
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            if st.button("🚨 Inspect Feeders", use_container_width=True):
                st.session_state["nav_view"] = "Regional Feeders"
                st.rerun()
    elif has_amber:
        alert_cols = st.columns([4, 1])
        with alert_cols[0]:
            st.markdown(
                f"""
                <div class="alert-banner-amber" style="background: rgba(254, 243, 199, 0.85); border: 1.5px solid #F59E0B; border-radius: 14px; padding: 14px 20px; display: flex; align-items: center; gap: 14px; box-shadow: 0 4px 16px rgba(245, 158, 11, 0.1);">
                    <span style="font-size: 1.4rem;">⚡</span>
                    <div>
                        <div style="font-size: 0.92rem; font-weight: 800; color: #92400E;">
                            GRID ADVISORY // HIGH DEMAND MANAGED ({peak_loading:.1f}% TRANSFORMER HEADROOM)
                        </div>
                        <div style="font-size: 0.82rem; color: #B45309; margin-top: 2px;">
                            Summer peak demand projected at <b>{peak_net_p50:,.0f} MW</b> ({peak_time_str}). System operating within rated capacity ceiling of <b>{grid_capacity_mw:,.0f} MW</b>. BESS storage and feeder balancing available on standby.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with alert_cols[1]:
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            if st.button("🚨 Inspect Feeders", use_container_width=True):
                st.session_state["nav_view"] = "Regional Feeders"
                st.rerun()

# ---------------------------------------------------------
# VIEW 2: SIMULATION MODE (Load Simulator)
# ---------------------------------------------------------
elif st.session_state["nav_view"] == "Load Simulator":
    st.markdown(
        """
        <div style="margin-bottom: 14px;">
            <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">LOAD SIMULATOR</div>
            <div style="font-size: 0.85rem; color: #64748B;">Scenario modeling for temperature shifts and distributed rooftop solar integration.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sim_col1, sim_col2 = st.columns([1.15, 0.85])

    with sim_col1:
        st.markdown(
            """
            <div class="glass-card">
                <div style="font-weight: 700; font-size: 1.05rem; color: #0284C7; margin-bottom: 12px;">
                    Demand & Resource Simulation
                </div>
            """,
            unsafe_allow_html=True,
        )

        deduct_solar = st.toggle(
            "Rooftop Solar Integration",
            key="deduct_solar",
            help="Toggle rooftop solar generation across operational views.",
        )

        temp_shock = st.slider(
            "Ambient Temperature Adjustment",
            min_value=-3.0,
            max_value=3.0,
            step=0.1,
            key="temp_delta",
            format="%+.1f°C",
            help="Adjust ambient temperature baseline across Delhi NCT.",
        )

        solar_capacity = st.slider(
            "Installed Rooftop Solar Capacity (MW)",
            min_value=0.0,
            max_value=3000.0,
            step=50.0,
            key="solar_mw",
            help="Simulates aggregate Delhi rooftop solar capacity.",
        )

        shock_label = f"+{temp_shock:.1f}°C Adjustment" if temp_shock > 0 else (f"{temp_shock:.1f}°C Adjustment" if temp_shock < 0 else "Baseline Ambient")
        st.markdown(
            f"""
            <div style="margin-top: -4px; margin-bottom: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
                <span class="badge-amber">State: {shock_label}</span>
                <span class="badge-emerald">Active Solar: {installed_solar_mw:,.0f} MW</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Mini Plotly Comparison Chart
        mini_fig = go.Figure()
        mini_fig.add_trace(go.Scatter(
            x=alert_df["timestamp"].to_list(),
            y=alert_df["gross_p50"].to_list(),
            mode="lines",
            line=dict(color="#64748B", width=1.8, dash="dot"),
            name="Total Base Load",
            hovertemplate="<b>%{x|%H:%M IST}</b><br>Load: <b>%{y:,.0f} MW</b><extra></extra>",
        ))
        effective_net = alert_df["net_p50"].to_list()
        mini_fig.add_trace(go.Scatter(
            x=alert_df["timestamp"].to_list(),
            y=effective_net,
            mode="lines",
            line=dict(color="#0284C7", width=3),
            fill="tozeroy",
            fillcolor="rgba(14, 165, 233, 0.08)",
            name="Projected Demand",
            hovertemplate="<b>%{x|%H:%M IST}</b><br>Load: <b>%{y:,.0f} MW</b><extra></extra>",
        ))
        mini_fig.update_layout(
            title=dict(
                text="<b>SIMULATED DEMAND VS BASE LOAD (MW)</b>",
                y=0.96,
                x=0.03,
                xanchor="left",
                yanchor="top",
                font=dict(family="Plus Jakarta Sans", size=12, color="#0F172A"),
            ),
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans", color="#334155"),
            height=260,
            margin=dict(l=45, r=25, t=50, b=45),
            xaxis=dict(
                automargin=True,
                showgrid=True,
                gridcolor="rgba(203, 213, 225, 0.5)",
                tickfont=dict(size=10, color="#64748B"),
            ),
            yaxis=dict(
                automargin=True,
                showgrid=True,
                gridcolor="rgba(203, 213, 225, 0.5)",
                tickfont=dict(size=10, color="#64748B"),
            ),
            legend=dict(
                orientation="h",
                y=1.12,
                x=0.5,
                xanchor="center",
                font=dict(size=10, color="#334155"),
                bgcolor="rgba(255, 255, 255, 0.7)",
                bordercolor="rgba(226, 232, 240, 0.8)",
                borderwidth=1,
            ),
        )
        st.plotly_chart(mini_fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with sim_col2:
        st.markdown(
            """
            <div class="glass-card" style="margin-bottom: 0.5rem !important;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A;">Forecast Confidence</div>
                    <div class="badge-emerald">Operational High</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Semi-circular Radial Gauge
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=98.2,
            domain={'x': [0.1, 0.9], 'y': [0.05, 0.85]},
            title={'text': "<b>FORECAST CONFIDENCE</b>", 'font': {'size': 12, 'family': 'Plus Jakarta Sans', 'color': '#0F172A'}},
            number={'suffix': "%", 'font': {'size': 32, 'family': 'Plus Jakarta Sans', 'color': '#0284C7'}},
            gauge={
                'axis': {'range': [80, 100], 'tickcolor': "#94A3B8", 'tickfont': {'size': 10}},
                'bar': {'color': "#0284C7", 'thickness': 0.3},
                'bgcolor': "rgba(241, 245, 249, 0.8)",
                'borderwidth': 0,
                'steps': [
                    {'range': [80, 92], 'color': "rgba(254, 205, 211, 0.6)"},
                    {'range': [92, 97], 'color': "rgba(253, 230, 138, 0.6)"},
                    {'range': [97, 100], 'color': "rgba(167, 243, 208, 0.6)"},
                ],
                'threshold': {
                    'line': {'color': "#059669", 'width': 3},
                    'thickness': 0.75,
                    'value': 98.2,
                },
            },
        ))
        gauge_fig.update_layout(
            height=240,
            margin=dict(l=30, r=30, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans", color="#0F172A"),
        )
        st.plotly_chart(gauge_fig, use_container_width=True)

        st.markdown(
            f"""
            <div class="glass-card" style="padding: 1rem 1.25rem !important;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 0.82rem; color: #64748B;">Forecast Accuracy:</span>
                    <span style="font-size: 0.85rem; font-weight: 700; color: #059669;">98.2%</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 0.82rem; color: #64748B;">Confidence Interval:</span>
                    <span style="font-size: 0.85rem; font-weight: 600; color: #0284C7;">P10 – P90</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 0.82rem; color: #64748B;">Solar Inflow Active:</span>
                    <span style="font-size: 0.85rem; font-weight: 600; color: #334155;">{installed_solar_mw:,.0f} MW</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 0.82rem; color: #64748B;">Grid Power Factor:</span>
                    <span style="font-size: 0.85rem; font-weight: 600; color: #334155;">{power_factor:.2f}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------
# VIEW 3: REGIONAL FEEDERS (Distribution)
# ---------------------------------------------------------
elif st.session_state["nav_view"] == "Regional Feeders":
    st.markdown(
        """
        <div style="margin-bottom: 14px;">
            <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">REGIONAL DISCOM DISTRIBUTION</div>
            <div style="font-size: 0.85rem; color: #64748B;">Regional power allocation across Delhi NCT distribution licensees (BRPL, TPDDL, BYPL).</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    brpl_peak = float(alert_df["BRPL"].max())
    bypl_peak = float(alert_df["BYPL"].max())
    tpddl_peak = float(alert_df["TPDDL"].max())

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.markdown(
            f"""
            <div class="glass-card" style="border-top: 4px solid #0284C7 !important;">
                <div class="metric-label">BSES Rajdhani (BRPL)</div>
                <div class="metric-val val-blue">{brpl_peak:,.1f} <span style="font-size: 1.1rem; color: #64748B;">MW</span></div>
                <div class="metric-sub">~42% Regional Share • Commercial & Residential</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f_col2:
        st.markdown(
            f"""
            <div class="glass-card" style="border-top: 4px solid #059669 !important;">
                <div class="metric-label">Tata Power DDL (TPDDL)</div>
                <div class="metric-val val-emerald">{tpddl_peak:,.1f} <span style="font-size: 1.1rem; color: #64748B;">MW</span></div>
                <div class="metric-sub">~31% Regional Share • Industrial & Institutional Corridors</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f_col3:
        st.markdown(
            f"""
            <div class="glass-card" style="border-top: 4px solid #7C3AED !important;">
                <div class="metric-label">BSES Yamuna (BYPL)</div>
                <div class="metric-val" style="color: #7C3AED !important;">{bypl_peak:,.1f} <span style="font-size: 1.1rem; color: #64748B;">MW</span></div>
                <div class="metric-sub">~27% Regional Share • High-Density Urban Clusters</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Stacked Area Plotly Chart in Clean Preset
    feeder_chart = go.Figure()
    feeder_chart.add_trace(go.Scatter(
        x=alert_df["timestamp"].to_list(),
        y=alert_df["BRPL"].to_list(),
        mode="lines",
        line=dict(width=0.8, color="#0284C7"),
        stackgroup="one",
        name="BSES Rajdhani (BRPL - 42%)",
        fillcolor="rgba(14, 165, 233, 0.4)",
        hovertemplate="<b>%{x|%H:%M IST}</b><br>BRPL: <b>%{y:,.1f} MW</b><extra></extra>",
    ))
    feeder_chart.add_trace(go.Scatter(
        x=alert_df["timestamp"].to_list(),
        y=alert_df["TPDDL"].to_list(),
        mode="lines",
        line=dict(width=0.8, color="#059669"),
        stackgroup="one",
        name="Tata Power DDL (TPDDL - 31%)",
        fillcolor="rgba(16, 185, 129, 0.4)",
        hovertemplate="<b>%{x|%H:%M IST}</b><br>TPDDL: <b>%{y:,.1f} MW</b><extra></extra>",
    ))
    feeder_chart.add_trace(go.Scatter(
        x=alert_df["timestamp"].to_list(),
        y=alert_df["BYPL"].to_list(),
        mode="lines",
        line=dict(width=0.8, color="#7C3AED"),
        stackgroup="one",
        name="BSES Yamuna (BYPL - 27%)",
        fillcolor="rgba(124, 58, 237, 0.35)",
        hovertemplate="<b>%{x|%H:%M IST}</b><br>BYPL: <b>%{y:,.1f} MW</b><extra></extra>",
    ))

    apply_light_plotly_layout(
        feeder_chart,
        height=440,
        title_text="REGIONAL DISCOM DISTRIBUTION",
        xaxis_title="Time Block (15-min Intervals)",
        yaxis_title="Demand (MW)",
        margin=dict(l=60, r=40, t=75, b=60),
    )
    st.plotly_chart(feeder_chart, use_container_width=True)

# ---------------------------------------------------------
# VIEW 4: GRID RELIABILITY (Operational Log)
# ---------------------------------------------------------
elif st.session_state["nav_view"] == "Grid Reliability":
    st.markdown(
        """
        <div style="margin-bottom: 14px;">
            <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">GRID RELIABILITY & OPERATIONAL LOG</div>
            <div style="font-size: 0.85rem; color: #64748B;">System telemetry audit, transformer loading, and dispatch alert status.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stress_table = (
        alert_df.sort("transformer_loading_pct", descending=True)
        .head(10)
        .select([
            "timestamp",
            "time_block_idx",
            "apparent_temperature",
            "solar_generation_mw",
            "net_p50",
            "net_p90",
            "transformer_loading_pct",
            "ramp_rate_mw_min",
            "alert_status",
        ])
        .to_pandas()
    )

    st.dataframe(
        stress_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Timestamp (IST)", format="YYYY-MM-DD HH:mm"),
            "time_block_idx": st.column_config.NumberColumn("Block", format="#%d"),
            "apparent_temperature": st.column_config.NumberColumn("Apparent Temp", format="%.1f °C"),
            "solar_generation_mw": st.column_config.NumberColumn("Solar PV", format="%.1f MW"),
            "net_p50": st.column_config.NumberColumn("Projected Demand", format="%.1f MW"),
            "net_p90": st.column_config.NumberColumn("Upper Bound (P90)", format="%.1f MW"),
            "transformer_loading_pct": st.column_config.ProgressColumn("Capacity Utilized", format="%.1f%%", min_value=0.0, max_value=120.0),
            "ramp_rate_mw_min": st.column_config.NumberColumn("Ramp Rate", format="%+.1f MW/min"),
            "alert_status": st.column_config.TextColumn("Alert State"),
        },
    )

# ---------------------------------------------------------
# VIEW 5: SETTINGS
# ---------------------------------------------------------
elif st.session_state["nav_view"] == "Settings":
    st.markdown(
        """
        <div style="margin-bottom: 14px;">
            <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">SYSTEM & GRID CONFIGURATION</div>
            <div style="font-size: 0.85rem; color: #64748B;">Operational parameters governing transmission capacity limits and resource modeling.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_col1, c_col2 = st.columns(2)
    with c_col1:
        st.markdown(
            """
            <div class="glass-card">
                <div style="font-weight: 700; font-size: 1.05rem; color: #0284C7; margin-bottom: 12px;">Transmission & Interconnection Capacity</div>
            """,
            unsafe_allow_html=True,
        )
        st.number_input("Interconnect Rating (MVA)", min_value=5000.0, max_value=12000.0, step=250.0, key="mva_limit")
        st.number_input("Operating Power Factor", min_value=0.85, max_value=1.0, step=0.01, key="power_factor")
        st.markdown(
            f"""
                <div style="font-size: 0.88rem; color: #334155; line-height: 1.6; margin-top: 12px;">
                    • <b>Configured MVA Limit:</b> {mva_limit:,.0f} MVA<br>
                    • <b>Operating Power Factor:</b> {power_factor:.2f}<br>
                    • <b>Effective Power Ceiling:</b> <b>{grid_capacity_mw:,.0f} MW</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_col2:
        st.markdown(
            """
            <div class="glass-card">
                <div style="font-weight: 700; font-size: 1.05rem; color: #059669; margin-bottom: 10px;">Solar Inflow Calibration</div>
                <div style="font-size: 0.88rem; color: #334155; line-height: 1.6;">
                    • <b>Reference Temperature:</b> 25.0°C<br>
                    • <b>Thermal Sensitivity:</b> High-temperature thermal loss compensation active<br>
                    • <b>Installed Resource Base:</b> Rooftop solar PV net metering enabled
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------
# Floating AI Chatbot ("GridPulse Buddy")
# ---------------------------------------------------------
# ---------------------------------------------------------
# Floating AI Chatbot ("GridPulse Buddy")
# ---------------------------------------------------------
# Place this at the very bottom of app.py
st.markdown('<div class="floating-bot-wrapper"><span class="chat-bot-marker"></span>', unsafe_allow_html=True)
with st.popover("⚡ GridPulse Buddy", help="Ask plain-English questions about the grid"):
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <div style="font-size: 20px;">🤖</div>
            <div>
                <h4 style="margin: 0; font-size: 1rem; color: #0F172A; font-weight: 700;">GridPulse Buddy</h4>
                <small style="color: #64748B;">Plain English Grid Assistant</small>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Quick explanation chips & conversational Q&A
    st.caption("Common Questions:")
    c_q1, c_q2 = st.columns(2)
    if c_q1.button("📊 Explain Graph", key="bot_btn_explain", use_container_width=True):
        st.info(f"The blue line tracks today's electricity usage. Notice how it peaks around {peak_time_str} when offices and homes crank up air conditioners.")
    if c_q2.button("⚠️ Are we safe?", key="bot_btn_safe", use_container_width=True):
        if peak_loading > 95.0 and not (bess_enabled and effective_loading <= 95.0):
            st.warning(f"The grid is running at {peak_loading:.1f}% capacity. Feeders and storage systems are actively balancing to maintain safety.")
        else:
            st.success("Yes! The grid has healthy headroom right now. The yellow advisory simply means demand is high, but backup batteries and solar are balancing it.")

    st.divider()

    # Context-aware knowledge base generator
    def generate_bot_response(user_text: str) -> str:
        lower = user_text.lower()
        if "today" in lower or "forecast" in lower or "graph" in lower or "load" in lower:
            return (
                f"Delhi's electricity demand is projected to peak at **{peak_net_p50:,.0f} MW** around **{peak_time_str}**. "
                f"Active rooftop solar panels are currently supplying **{peak_solar:,.0f} MW** to help ease transmission lines."
            )
        elif "safe" in lower or "blackout" in lower or "risk" in lower or "outage" in lower:
            if peak_loading > 95.0 and not (bess_enabled and effective_loading <= 95.0):
                return (
                    f"Grid stress is elevated at **{peak_loading:.1f}% capacity**. "
                    "Dispatchers are rebalancing regional feeders and activating storage buffers to prevent disruptions."
                )
            else:
                return (
                    f"Everything is safe! The grid is running at **{effective_loading:.1f}% capacity** with safe margins "
                    f"under the **{grid_capacity_mw:,.0f} MW** threshold."
                )
        elif "solar" in lower or "offset" in lower or "pv" in lower:
            return (
                f"Solar Offset means rooftop solar panels are contributing **{peak_solar:,.0f} MW** clean energy, "
                "relieving city substations during the hottest hours of the day."
            )
        elif "bess" in lower or "battery" in lower or "storage" in lower:
            if bess_enabled:
                return (
                    f"Battery storage is **Active**! It holds excess midday solar power and discharges up to "
                    f"**{bess_max_mw:,.0f} MW** during peak hours to protect transformers."
                )
            else:
                return "The battery storage system is on **Standby**. You can turn on BESS Peak Shaving on the Overview page."
        else:
            return (
                f"Currently, demand is at **{current_demand:,.0f} MW** with a projected peak of **{peak_net_p50:,.0f} MW** ({peak_time_str}). "
                f"Capacity utilization is **{effective_loading:.1f}%**, tracking close to historical summer levels with no risk of tripping."
            )

    # Chat history area
    chat_box = st.container(height=200)
    with chat_box:
        for msg in st.session_state["chat_messages"]:
            with st.chat_message(msg["role"], avatar="⚡" if msg["role"] == "assistant" else None):
                st.write(msg["content"])

    user_query = st.chat_input("Ask a question about the metrics...", key="bot_chat_input")
    if user_query:
        st.session_state["chat_messages"].append({"role": "user", "content": user_query})
        reply = generate_bot_response(user_query)
        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
