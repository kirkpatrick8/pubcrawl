"""
Mark's Belfast Christmas 16-Pub Crawl — Streamlit app
Mobile-first festive UI · Folium map · spinning punishment wheel · achievements
"""
from __future__ import annotations
import colorsys
import html
import io
import math
import os
import random
import time
from datetime import datetime
from pathlib import Path
import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium
# ---------------------------------------------------------------------------
# Page + theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Belfast 16 Pubs Christmas Loop",
    page_icon="🎄",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,800&family=Source+Sans+3:wght@400;600;700&display=swap');
    :root {
        --bg: #fff8f0;
        --bg2: #ffe8d6;
        --ink: #1a0f0a;
        --muted: #5c4033;
        --card: #ffffff;
        --accent: #c41e3a;
        --accent2: #0b6e4f;
        --gold: #d4a017;
        --border: #e8c9a8;
    }
    html, body, [class*="css"] {
        font-family: 'Source Sans 3', sans-serif;
        color: var(--ink);
    }
    .stApp {
        background:
            radial-gradient(ellipse at 10% 0%, #ffd6a5 0%, transparent 45%),
            radial-gradient(ellipse at 90% 10%, #ffb3c1 0%, transparent 40%),
            linear-gradient(180deg, #fff8f0 0%, #ffe8d6 55%, #fff1e0 100%);
        color: var(--ink);
    }
    h1, h2, h3, .brand-title {
        font-family: 'Fraunces', Georgia, serif !important;
        color: var(--ink) !important;
        letter-spacing: -0.02em;
    }
    .brand-hero {
        text-align: center;
        padding: 1.2rem 0.5rem 0.4rem;
    }
    .brand-hero .brand {
        font-family: 'Fraunces', Georgia, serif;
        font-size: clamp(1.8rem, 7vw, 2.8rem);
        font-weight: 800;
        color: var(--accent);
        margin: 0;
        line-height: 1.1;
    }
    .brand-hero .tagline {
        color: var(--muted);
        font-size: 1.05rem;
        margin: 0.4rem 0 0;
    }
    .metric-strip {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.6rem;
        margin: 0.8rem 0 1rem;
    }
    .metric-card {
        background: var(--card);
        border: 2px solid var(--border);
        border-radius: 14px;
        padding: 0.85rem 0.5rem;
        text-align: center;
        box-shadow: 0 2px 0 rgba(196, 30, 58, 0.08);
    }
    .metric-card .val {
        font-family: 'Fraunces', Georgia, serif;
        font-size: 1.55rem;
        font-weight: 800;
        color: var(--accent);
        line-height: 1.1;
    }
    .metric-card .lbl {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--muted);
        margin-top: 0.2rem;
    }
    .pub-card {
        background: var(--card);
        border: 2px solid var(--border);
        border-left: 6px solid var(--accent);
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin: 0.8rem 0 1rem;
        box-shadow: 0 3px 0 rgba(11, 110, 79, 0.08);
    }
    .pub-card h3 {
        margin: 0 0 0.35rem !important;
        color: var(--ink) !important;
        font-size: 1.25rem !important;
    }
    .pub-card p { margin: 0; color: var(--muted); font-size: 1.02rem; }
    .achievement {
        padding: 0.85rem 1rem;
        margin: 0.5rem 0;
        border-radius: 12px;
        background: linear-gradient(135deg, #0b6e4f, #14966b);
        color: #fff;
        font-weight: 700;
        border: 2px solid #0a5a41;
    }
    .locked-achievement {
        padding: 0.85rem 1rem;
