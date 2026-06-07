"""Shared visual theme for the Streamlit app.

Aesthetic: "Industrial Precision" — a deep ink sidebar against a paper-white
work area, a single confident teal accent, IBM Plex typography (Sans SC for
bilingual text, Mono for instrument-like metrics). All three pages (main app,
login, admin) pull their look from here so the product stays cohesive.

Icons: structural/decorative marks use inline SVG (src/utils/icons.py);
Streamlit's own buttons use native :material/...: icons.
"""

from __future__ import annotations

import streamlit as st

from src.utils.icons import icon

# Palette ---------------------------------------------------------------------
INK = "#0e1b29"        # sidebar background (deep navy ink)
INK_EDGE = "#0a1420"   # sidebar border
PAPER = "#f4f6f9"      # main work area
CARD = "#ffffff"
LINE = "#e6ecf2"       # hairline borders on light
TEXT = "#15212e"       # primary text on light
MUTED = "#5b6b7c"      # secondary text on light
ACCENT = "#0f766e"     # deep teal — accent on light surfaces
ACCENT_BRIGHT = "#2dd4bf"  # teal highlight on the dark sidebar

_FONTS = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=IBM+Plex+Sans+SC:wght@300;400;500;600;700"
    "&family=IBM+Plex+Mono:wght@400;500;600&display=swap');"
)


def _base_css() -> str:
    return f"""
    {_FONTS}

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
        font-family: 'IBM Plex Sans SC', system-ui, sans-serif;
    }}
    .stApp {{ background: {PAPER}; color: {TEXT}; }}

    /* --- strip Streamlit chrome that overlaps / leaks routing --- */
    [data-testid="stToolbar"] {{ display: none !important; }}
    [data-testid="stDecoration"] {{ display: none !important; }}
    [data-testid="stHeader"] {{ background: transparent !important; }}
    [data-testid="stSidebarNav"] {{ display: none !important; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}

    .block-container {{ padding-top: 2.4rem; max-width: 1100px; }}

    h1, h2, h3, h4 {{ color: {TEXT}; letter-spacing: -0.01em; }}
    .stApp h2 {{ font-size: 1.5rem; font-weight: 600; }}

    .ic {{ display: inline-block; }}

    /* Metrics read like instrument output: mono digits, tight labels */
    [data-testid="stMetricValue"] {{
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600; color: {TEXT}; font-size: 1.5rem;
    }}
    [data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: 0.8rem; }}

    /* Primary + download buttons in accent teal */
    .stButton button[kind="primary"], .stDownloadButton button {{
        background: {ACCENT}; border: 1px solid {ACCENT};
        color: #fff; font-weight: 500; border-radius: 8px;
    }}
    .stButton button[kind="primary"]:hover,
    .stDownloadButton button:hover {{ background: #0c5f59; border-color: #0c5f59; }}
    .stButton button[kind="secondary"] {{
        border-radius: 8px; border: 1px solid {LINE}; color: {TEXT}; font-weight: 500;
    }}
    .stButton button[kind="secondary"]:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}

    /* Step header: SVG icon + teal mono badge + title + optional hint */
    .step-head {{ display: flex; align-items: center; gap: 0.6rem; margin: 0.3rem 0 0.7rem; }}
    .step-badge {{
        display: inline-flex; align-items: center; justify-content: center;
        width: 30px; height: 30px; border-radius: 9px;
        background: {ACCENT}; color: #fff;
        font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.95rem;
        flex: 0 0 auto;
    }}
    .step-ic {{ color: {ACCENT}; display: inline-flex; }}
    .step-title {{ font-size: 1.16rem; font-weight: 600; color: {TEXT}; }}
    .step-hint {{ color: {MUTED}; font-size: 0.8rem; margin: -0.3rem 0 0.5rem 2.6rem; }}

    /* Result + summary cards — style the Streamlit container that holds the
       hidden marker (naked <div> wrappers can't span multiple st elements). */
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .result-card-marker),
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .summary-card-marker) {{
        background: {CARD}; border: 1px solid {LINE}; border-radius: 12px;
        padding: 16px 18px 4px; margin-bottom: 14px;
        box-shadow: 0 1px 2px rgba(16,32,48,0.04);
    }}
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .summary-card-marker) {{
        border-color: #cfe6e2; background: linear-gradient(180deg,#f3fbfa,#ffffff);
    }}
    .result-card-marker, .summary-card-marker {{ display: none; }}
    .card-head {{ display: flex; align-items: center; justify-content: space-between;
                  margin-bottom: 0.5rem; }}
    .card-title {{ display: flex; align-items: center; gap: 0.45rem;
                   font-weight: 600; font-size: 1.02rem; color: {TEXT}; }}
    .card-title .ic {{ color: {ACCENT}; }}
    .mode-pill {{ font-size: 0.78rem; color: {MUTED}; }}
    .tl-caption {{ color: {MUTED}; font-size: 0.8rem; margin: 0.2rem 0 0.35rem; }}

    /* LBR target line */
    .lbr-target {{ font-size: 12px; margin-top: 4px; display:flex; align-items:center; gap:4px; }}
    .lbr-ok {{ color: {ACCENT}; font-weight: 600; }}
    .lbr-warn {{ color: #d97706; font-weight: 600; }}

    .block-container > div {{ animation: fadein 0.4s ease; }}
    @keyframes fadein {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: none; }} }}
    """


def _sidebar_css() -> str:
    return f"""
    [data-testid="stSidebar"] {{
        background: {INK}; border-right: 1px solid {INK_EDGE};
    }}
    [data-testid="stSidebar"] * {{ color: #cdd9e3; }}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{ color: #f2f6fa; }}
    [data-testid="stSidebar"] hr {{ border-color: #1c2c3a; }}

    .sb-brand {{ display: flex; align-items: center; gap: 0.55rem; margin: 0.2rem 0 0.15rem; }}
    .sb-brand .logo {{ color: {ACCENT_BRIGHT}; display: inline-flex; }}
    .sb-brand .name {{ font-size: 1.14rem; font-weight: 600; color: #f2f6fa; line-height: 1.1; }}
    .sb-tag {{ font-size: 11.5px; color: #6f8499; margin: 0 0 0.2rem 0.1rem; letter-spacing: 0.01em; }}
    .sb-section {{ display: flex; align-items: center; gap: 0.4rem;
                   font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.1em;
                   color: #6f8499; margin: 0.4rem 0 0.2rem 0.1rem; }}
    .sb-section .ic {{ color: #6f8499; }}

    [data-testid="stSidebar"] [data-baseweb="radio"] svg {{ fill: {ACCENT_BRIGHT}; }}

    [data-testid="stSidebar"] .stButton button {{
        background: transparent; border: 1px solid #2a3d4f; color: #cdd9e3;
        border-radius: 8px; font-weight: 500;
        justify-content: flex-start; text-align: left;
    }}
    [data-testid="stSidebar"] .stButton button:hover {{
        border-color: {ACCENT_BRIGHT}; color: {ACCENT_BRIGHT}; background: rgba(45,212,191,0.06);
    }}

    .sb-user {{ display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0 0.5rem;
                border-top: 1px solid #1c2c3a; margin-bottom: 0.3rem; }}
    .sb-avatar {{
        width: 38px; height: 38px; border-radius: 10px; flex: 0 0 auto;
        display: flex; align-items: center; justify-content: center;
        background: linear-gradient(135deg, {ACCENT}, {ACCENT_BRIGHT});
        color: #042f2c; font-weight: 700; font-family: 'IBM Plex Mono', monospace;
        font-size: 1.05rem;
    }}
    .sb-user .who {{ line-height: 1.2; }}
    .sb-user .who .u {{ color: #eaf1f7; font-weight: 600; font-size: 0.95rem; }}
    .sb-user .who .f {{ color: #6f8499; font-size: 11.5px; }}

    /* --- pin the user block to the bottom (Streamlit 1.51 DOM, verified) --- */
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
        height: 100%;
        display: flex; flex-direction: column;
    }}
    [data-testid="stSidebarUserContent"] {{
        flex: 1 1 auto;
        display: flex; flex-direction: column;
    }}
    [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] {{
        flex: 1 1 auto;
    }}
    [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"]
        > [data-testid="stVerticalBlock"]:last-child {{
        margin-top: auto;
    }}
    """


def apply_app_theme() -> None:
    """Full theme for the main app and admin console (with dark sidebar)."""
    st.markdown(f"<style>{_base_css()}{_sidebar_css()}</style>", unsafe_allow_html=True)


def apply_auth_theme() -> None:
    """Theme for the login screen: paper background, no sidebar, centered."""
    extra = """
    [data-testid="stSidebar"] { display: none !important; }
    .block-container { max-width: 440px; padding-top: 3.4rem; }
    """
    st.markdown(f"<style>{_base_css()}{extra}</style>", unsafe_allow_html=True)


def step_header(num: int, title: str, icon_name: str = "", hint: str = "") -> None:
    """Numbered step heading: SVG icon + teal mono badge + title (+ hint line)."""
    ic = f'<span class="step-ic">{icon(icon_name, 20)}</span>' if icon_name else ""
    st.markdown(
        f'<div class="step-head"><span class="step-badge">{num}</span>'
        f'{ic}<span class="step-title">{title}</span></div>'
        + (f'<div class="step-hint">{hint}</div>' if hint else ""),
        unsafe_allow_html=True,
    )


def avatar_initial(username: str) -> str:
    return (username[:1] or "?").upper()
