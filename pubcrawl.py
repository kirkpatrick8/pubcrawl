# Mark's Belfast Christmas 16-Pub Crawl — Streamlit app
# Mobile-first festive UI, Folium map, spinning punishment wheel, achievements
# Entry point for Streamlit Cloud: pubcrawl.py

from __future__ import annotations

import colorsys
import html
import io
import math
import random
import time
from datetime import datetime
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Belfast 16 Pubs Christmas Loop",
    page_icon="🎄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_DIR = Path(__file__).resolve().parent


# High-contrast CSS inlined so the app works even if theme.css is missing on Cloud
INLINE_THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,800&family=Source+Sans+3:wght@500;700;800&display=swap');
html,body,[class*="css"],.stMarkdown,p,label,span{font-family:'Source Sans 3','Segoe UI',sans-serif!important;color:#140c08!important;}
.stApp{background:linear-gradient(180deg,#ffe7c2 0%,#ffd9a8 40%,#fff0dc 100%);color:#140c08;}
h1,h2,h3,h4,.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{font-family:Fraunces,Georgia,serif!important;color:#140c08!important;font-weight:800!important;}
.stCaption,[data-testid="stCaptionContainer"]{color:#3d2a1f!important;font-weight:600!important;}
.brand-hero{text-align:center;padding:0.8rem 0.4rem 0.3rem;}
.brand-hero .brand{font-family:Fraunces,Georgia,serif;font-size:clamp(1.55rem,6vw,2.4rem);font-weight:800;color:#b01030;margin:0;line-height:1.1;}
.brand-hero .tagline{color:#3d2a1f;font-size:1.05rem;font-weight:700;margin:0.35rem 0 0;}
.metric-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:0.55rem;margin:0.7rem 0 1rem;}
.metric-card{background:#fff;border:3px solid #8b5a2b;border-radius:12px;padding:0.75rem 0.4rem;text-align:center;}
.metric-card .val{font-family:Fraunces,Georgia,serif;font-size:1.6rem;font-weight:800;color:#b01030;line-height:1.1;}
.metric-card .lbl{font-size:0.75rem;font-weight:800;text-transform:uppercase;color:#3d2a1f;margin-top:0.2rem;}
.pub-card{background:#fff;border:3px solid #8b5a2b;border-left:8px solid #b01030;border-radius:12px;padding:1rem;margin:0.7rem 0 1rem;}
.pub-card h3{margin:0 0 0.35rem!important;color:#140c08!important;font-size:1.2rem!important;}
.pub-card p{margin:0;color:#3d2a1f;font-size:1.05rem;font-weight:600;}
.achievement{padding:0.85rem 1rem;margin:0.45rem 0;border-radius:10px;background:#0a5c42;color:#fff!important;font-weight:800;border:3px solid #063d2c;}
.locked-achievement{padding:0.85rem 1rem;margin:0.45rem 0;border-radius:10px;background:#fff;border:3px solid #5c4033;color:#140c08!important;font-weight:700;}
iframe[title="streamlit_folium.st_folium"]{width:100%!important;max-width:100%!important;}
.stButton>button{border-radius:10px!important;font-weight:800!important;font-size:1.05rem!important;}
.stButton>button[kind="primary"],.stButton>button[data-testid="baseButton-primary"]{background:#b01030!important;color:#fff!important;border:3px solid #7a0b22!important;}
section[data-testid="stSidebar"]{background:#ffe7c2;border-right:3px solid #8b5a2b;}
div[data-baseweb="tab-list"] button{font-weight:800!important;color:#140c08!important;}
div[data-baseweb="tab-list"] button[aria-selected="true"]{color:#b01030!important;}
@media (max-width:640px){.block-container{padding-top:0.7rem!important;padding-left:0.65rem!important;padding-right:0.65rem!important;}}
"""


def inject_theme() -> None:
    css_path = APP_DIR / "theme.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else INLINE_THEME_CSS
    # Always append inline rules so contrast stays strong even if an old theme.css is present
    st.markdown("<style>\n" + css + "\n" + INLINE_THEME_CSS + "\n</style>", unsafe_allow_html=True)


inject_theme()

PARTICIPANTS_CSV = APP_DIR / "participants.csv"
PUNISHMENTS_CSV = APP_DIR / "punishments.csv"
PARTICIPANT_COLS = ["Name", "CurrentPub", "CompletedPubs", "Points", "Achievements", "StartTime"]
PUNISHMENT_COLS = ["Time", "Name", "Pub", "Punishment"]

try:
    GITHUB_TOKEN = st.secrets["Pubcrawl"]["GITHUB_TOKEN"]
except Exception:
    GITHUB_TOKEN = ""

REPO_NAME = "kirkpatrick8/pubcrawl"
BRANCH_NAME = "main"

repo = None
if GITHUB_TOKEN:
    try:
        from github import Github

        repo = Github(GITHUB_TOKEN).get_repo(REPO_NAME)
    except Exception as e:
        st.sidebar.warning("GitHub unavailable — using local CSV. (%s)" % e)
        repo = None

USE_GITHUB = repo is not None


def _empty_participants() -> pd.DataFrame:
    return pd.DataFrame(columns=PARTICIPANT_COLS)


def _empty_punishments() -> pd.DataFrame:
    return pd.DataFrame(columns=PUNISHMENT_COLS)


def _ensure_local_templates() -> None:
    if not PARTICIPANTS_CSV.exists():
        _empty_participants().to_csv(PARTICIPANTS_CSV, index=False)
    if not PUNISHMENTS_CSV.exists():
        _empty_punishments().to_csv(PUNISHMENTS_CSV, index=False)


def _load_github_csv(filename: str, columns: list) -> pd.DataFrame:
    assert repo is not None
    try:
        content = repo.get_contents(filename, ref=BRANCH_NAME)
        df = pd.read_csv(io.StringIO(content.decoded_content.decode()), dtype=str)
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df[columns]
    except Exception:
        return pd.DataFrame(columns=columns)


def _save_github_csv(filename: str, df: pd.DataFrame) -> None:
    assert repo is not None
    payload = df.to_csv(index=False)
    try:
        existing = repo.get_contents(filename, ref=BRANCH_NAME)
        repo.update_file(filename, "Update " + filename, payload, existing.sha, branch=BRANCH_NAME)
    except Exception:
        repo.create_file(filename, "Create " + filename, payload, branch=BRANCH_NAME)


@st.cache_data(ttl=5)
def load_data():
    if USE_GITHUB:
        participants_df = _load_github_csv("participants.csv", PARTICIPANT_COLS)
        punishments_df = _load_github_csv("punishments.csv", PUNISHMENT_COLS)
    else:
        _ensure_local_templates()
        try:
            participants_df = pd.read_csv(PARTICIPANTS_CSV, dtype=str)
            for col in PARTICIPANT_COLS:
                if col not in participants_df.columns:
                    participants_df[col] = ""
            participants_df = participants_df[PARTICIPANT_COLS]
        except Exception:
            participants_df = _empty_participants()
        try:
            punishments_df = pd.read_csv(PUNISHMENTS_CSV, dtype=str)
            for col in PUNISHMENT_COLS:
                if col not in punishments_df.columns:
                    punishments_df[col] = ""
            punishments_df = punishments_df[PUNISHMENT_COLS]
        except Exception:
            punishments_df = _empty_punishments()

    if not participants_df.empty:
        participants_df["CurrentPub"] = (
            pd.to_numeric(participants_df["CurrentPub"], errors="coerce").fillna(0).astype(int)
        )
        participants_df["Points"] = (
            pd.to_numeric(participants_df["Points"], errors="coerce").fillna(0).astype(int)
        )
        participants_df["CompletedPubs"] = participants_df["CompletedPubs"].fillna("")
        participants_df["Achievements"] = participants_df["Achievements"].fillna("")
    return participants_df, punishments_df


def save_data(participants_df: pd.DataFrame, punishments_df: pd.DataFrame) -> None:
    try:
        if USE_GITHUB:
            _save_github_csv("participants.csv", participants_df)
            _save_github_csv("punishments.csv", punishments_df)
        else:
            _ensure_local_templates()
            participants_df.to_csv(PARTICIPANTS_CSV, index=False)
            punishments_df.to_csv(PUNISHMENTS_CSV, index=False)
            st.session_state["_local_participants"] = participants_df.to_csv(index=False)
            st.session_state["_local_punishments"] = punishments_df.to_csv(index=False)
    except Exception as e:
        st.session_state["_local_participants"] = participants_df.to_csv(index=False)
        st.session_state["_local_punishments"] = punishments_df.to_csv(index=False)
        st.sidebar.error("Save error (using session fallback): %s" % e)


def auto_refresh() -> None:
    st.cache_data.clear()
    time.sleep(0.05)
    st.rerun()


# 16 stops: start Three Sheets, finish Boombox; loops revisit Duke + Deer's Head
PUBS_DATA = {
    "name": [
        "1. Three Sheets (Start)",
        "2. The Crown Liquor Saloon",
        "3. Kelly's Cellars",
        "4. The Deer's Head",
        "5. Ulster Sports Club",
        "6. Music Room",
        "7. Whites Tavern",
        "8. The John Hewitt",
        "9. Duke of York",
        "10. The Dirty Onion",
        "11. Second Fiddle",
        "12. The Harp Bar",
        "13. The Spaniard",
        "14. Duke of York (Loop)",
        "15. The Deer's Head (Loop)",
        "16. Boombox (Final!)",
    ],
    "latitude": [
        54.592256,
        54.595800,
        54.599553,
        54.601439,
        54.599650,
        54.599720,
        54.600033,
        54.601928,
        54.601803,
        54.601556,
        54.601480,
        54.602000,
        54.602500,
        54.601803,
        54.601439,
        54.604231,
    ],
    "longitude": [
        -5.930879,
        -5.931200,
        -5.932236,
        -5.930294,
        -5.928900,
        -5.928850,
        -5.928497,
        -5.928617,
        -5.927442,
        -5.926673,
        -5.926550,
        -5.927058,
        -5.926200,
        -5.927442,
        -5.930294,
        -5.931129,
    ],
    "rules": [
        "Christmas attire required & first toast",
        "Speak in accents only",
        "Different drink type required",
        "Left hand only challenge",
        "Power hour (fast drink)",
        "Last names only",
        "Talk to a stranger",
        "Double parked",
        "Sing a verse of a song",
        "Must bow before drinking",
        "Switch drinks with buddy",
        "No phones allowed",
        "Compliment the bartender",
        "Reverse toast (loop revisit)",
        "Group hug photo (loop revisit)",
        "Final destination celebration!",
    ],
}

PUNISHMENTS = [
    "Buy Mark a Drink",
    "Irish dance for 30 seconds",
    "Touch your Toes",
    "Down your drink",
    "Shot for you or a friend",
    "Sing a Christmas carol",
    "Switch drinks with someone",
    "No Punishment",
    "Wear your jumper inside out",
    "Give someone your drink",
    "Talk in an accent for 10 mins",
    "Tell a fake back story to a random person",
]

ACHIEVEMENTS = {
    "first_pub": {"name": "First Timer", "desc": "Complete your first pub", "points": 100},
    "halfway": {"name": "Halfway Hero", "desc": "Complete 8 pubs", "points": 250},
    "finisher": {"name": "Challenge Champion", "desc": "Complete all 16 pubs", "points": 1500},
    "loop_legend": {"name": "Loop Legend", "desc": "Revisit a loop stop", "points": 150},
}


def completed_list(raw) -> list:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return []
    return [p for p in str(raw).split(",") if p and p != "nan"]


def achievement_keys(raw) -> set:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return set()
    return {a for a in str(raw).split(",") if a and a != "nan"}


def award_achievements(participants_df: pd.DataFrame, idx: int, completed: list) -> list:
    unlocked_now = []
    have = achievement_keys(participants_df.loc[idx, "Achievements"])
    progress = len(completed)
    checks = [
        ("first_pub", progress >= 1),
        ("halfway", progress >= 8),
        ("finisher", progress >= 16),
        ("loop_legend", any("(Loop)" in p for p in completed)),
    ]
    for key, ok in checks:
        if ok and key not in have:
            have.add(key)
            participants_df.loc[idx, "Points"] = int(participants_df.loc[idx, "Points"]) + int(
                ACHIEVEMENTS[key]["points"]
            )
            unlocked_now.append(ACHIEVEMENTS[key]["name"])
    participants_df.loc[idx, "Achievements"] = ",".join(sorted(have))
    return unlocked_now


def _wheel_colors(n: int) -> list:
    base = [
        "#c41e3a",
        "#0b6e4f",
        "#d4a017",
        "#e85d04",
        "#1d7874",
        "#9b2226",
        "#2a9d8f",
        "#bc6c25",
        "#e63946",
        "#457b9d",
        "#f4a261",
        "#264653",
    ]
    if n <= len(base):
        return base[:n]
    colors = []
    for i in range(n):
        h = (i / n + 0.02) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.72, 0.88)
        colors.append("#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255)))
    return colors


def build_wheel_html(punishments: list, spin_deg=None, result_label: str = "") -> str:
    """Labeled conic wheel. When spin_deg is set, JS animates 0 -> target (real spin)."""
    n = len(punishments)
    colors = _wheel_colors(n)
    seg = 360.0 / n
    stops = []
    for i, c in enumerate(colors):
        start = i * seg
        end = (i + 1) * seg
        stops.append("%s %.4fdeg %.4fdeg" % (c, start, end))
    gradient = ", ".join(stops)

    labels_html = []
    for i, label in enumerate(punishments):
        mid = i * seg + seg / 2.0
        short = label if len(label) <= 18 else label[:16] + "..."
        safe = html.escape(short)
        labels_html.append(
            '<div class="seg-label" style="transform:rotate(%.3fdeg) translateY(-145px) rotate(90deg);">%s</div>'
            % (mid, safe)
        )
    labels_joined = "".join(labels_html)
    result_safe = html.escape(result_label) if result_label else ""

    # JS starts at 0deg then transitions to target — Streamlit remount alone does not animate
    if spin_deg is None:
        script = ""
        result_block = ""
    else:
        script = (
            "<script>(function(){var w=document.getElementById('wheel');"
            "var r=document.getElementById('result');"
            "if(!w)return;"
            "w.style.transition='none';"
            "w.style.transform='rotate(0deg)';"
            "requestAnimationFrame(function(){requestAnimationFrame(function(){"
            "w.style.transition='transform 3.2s cubic-bezier(0.12,0.75,0.08,1)';"
            "w.style.transform='rotate(%.2fdeg)';"
            "});});"
            "setTimeout(function(){if(r){r.style.opacity='1';}},3300);"
            "})();</script>"
        ) % spin_deg
        result_block = (
            "<div id='result' style='opacity:0;transition:opacity 0.3s;margin:10px auto 0;"
            "max-width:340px;padding:12px 14px;background:#b01030;color:#fff;font-weight:800;"
            "font-size:1.05rem;border-radius:10px;border:3px solid #7a0b22;text-align:center;'>"
            "Landed on: %s</div>"
        ) % result_safe

    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>",
        "<style>",
        "body{margin:0;background:transparent;font-family:'Segoe UI',system-ui,sans-serif;}",
        ".wrap{position:relative;width:360px;height:360px;max-width:92vw;margin:24px auto 6px;}",
        ".pointer{position:absolute;top:-22px;left:50%;transform:translateX(-50%);z-index:6;",
        "width:0;height:0;border-left:18px solid transparent;border-right:18px solid transparent;",
        "border-top:34px solid #b01030;filter:drop-shadow(0 2px 3px rgba(0,0,0,0.35));}",
        ".pointer:after{content:'';position:absolute;top:-38px;left:-7px;width:14px;height:14px;",
        "background:#ffd700;border:3px solid #140c08;border-radius:50%;}",
        ".wheel{width:100%;height:100%;border-radius:50%;border:10px solid #140c08;",
        "box-shadow:0 10px 28px rgba(20,12,8,0.28),inset 0 0 0 5px #fff8f0;",
        "background:conic-gradient(from -90deg,",
        gradient,
        ");position:relative;transform:rotate(0deg);}",
        ".hub{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);",
        "width:52px;height:52px;border-radius:50%;z-index:3;",
        "background:radial-gradient(circle at 35% 30%,#fff3c4,#d4a017 55%,#8a6a0a);",
        "border:4px solid #140c08;}",
        ".seg-label{position:absolute;top:50%;left:50%;width:120px;margin-left:-60px;margin-top:-9px;",
        "font-size:11px;font-weight:800;color:#fff;text-shadow:0 0 3px #000,0 1px 2px #000;",
        "text-align:center;line-height:1.05;pointer-events:none;}",
        ".hint{text-align:center;color:#140c08;font-weight:700;font-size:13px;margin-top:4px;}",
        "</style></head><body>",
        "<div class='wrap'><div class='pointer'></div><div class='wheel' id='wheel'>",
        labels_joined,
        "<div class='hub'></div></div></div>",
        "<div class='hint'>Pointer at top — watch it spin</div>",
        result_block,
        script,
        "</body></html>",
    ]
    return "".join(parts)


def spin_target_degrees(index: int, n: int, extra_turns: int = 5) -> float:
    seg = 360.0 / n
    mid_from_top = index * seg + seg / 2.0
    return extra_turns * 360.0 + (360.0 - mid_from_top)


def name_entry_modal() -> None:
    if "current_participant" not in st.session_state:
        st.session_state.current_participant = None

    if st.session_state.current_participant:
        return

    st.markdown(
        "<div class='brand-hero'>"
        "<p class='brand'>Mark's Belfast Christmas Crawl</p>"
        "<p class='tagline'>16 pubs · Cathedral Quarter loop · "
        "start at Three Sheets, finish at Boombox</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([0.2, 1.6, 0.2])
    with col2:
        name = st.text_input("Enter your name to join the crawl", placeholder="Your name")
        if st.button("Start Crawling!", type="primary", use_container_width=True):
            cleaned = name.strip()
            if cleaned:
                st.session_state.current_participant = cleaned
                participants_df, punishments_df = load_data()
                if cleaned not in participants_df["Name"].astype(str).values:
                    new_p = pd.DataFrame(
                        [
                            {
                                "Name": cleaned,
                                "CurrentPub": 0,
                                "CompletedPubs": "",
                                "Points": 0,
                                "Achievements": "",
                                "StartTime": datetime.now().isoformat(timespec="seconds"),
                            }
                        ]
                    )
                    participants_df = pd.concat([participants_df, new_p], ignore_index=True)
                    save_data(participants_df, punishments_df)
                auto_refresh()
            else:
                st.warning("Please enter a name.")


def show_map() -> None:
    st.subheader("16-pub city centre & Cathedral Quarter loop")
    try:
        participants_df, _ = load_data()
        row = participants_df[participants_df["Name"] == st.session_state.current_participant]
        if row.empty:
            st.info("Join the crawl to see your progress on the map.")
            return
        participant = row.iloc[0]
        completed = completed_list(participant["CompletedPubs"])
        current_idx = int(participant["CurrentPub"])

        # OpenStreetMap — free, no API key (CartoDB positron now requires a key)
        m = folium.Map(
            location=[54.5988, -5.9295],
            zoom_start=14,
            tiles=None,
            control_scale=True,
        )
        folium.TileLayer(
            tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr="&copy; OpenStreetMap contributors",
            name="OpenStreetMap",
            max_zoom=19,
        ).add_to(m)

        coords = list(zip(PUBS_DATA["latitude"], PUBS_DATA["longitude"]))
        folium.PolyLine(coords, color="#b01030", weight=6, opacity=0.9, tooltip="Crawl route").add_to(m)

        for i, (name, lat, lon) in enumerate(
            zip(PUBS_DATA["name"], PUBS_DATA["latitude"], PUBS_DATA["longitude"])
        ):
            if name in completed:
                label_bg = "#0a5c42"
            elif i == current_idx:
                label_bg = "#e67e00"
            else:
                label_bg = "#b01030"

            # One clear numbered pin per stop (no overlapping CircleMarker + label)
            icon_html = (
                '<div style="width:30px;height:30px;border-radius:50%%;'
                "background:%s;color:#fff;border:3px solid #140c08;"
                "font-weight:800;font-size:13px;line-height:24px;text-align:center;"
                'box-shadow:0 2px 5px rgba(0,0,0,0.35);">%d</div>'
            ) % (label_bg, i + 1)
            folium.Marker(
                [lat, lon],
                popup=folium.Popup("<b>%s</b>" % html.escape(name), max_width=240),
                tooltip=name,
                icon=folium.DivIcon(
                    icon_size=(30, 30),
                    icon_anchor=(15, 15),
                    html=icon_html,
                ),
            ).add_to(m)

        m.fit_bounds(coords, padding=(28, 28))
        st_folium(m, height=480, use_container_width=True, returned_objects=[])
        st.caption("Green = done · Orange = current · Red = upcoming · Line = walking route")
    except Exception as e:
        st.error("Map rendering error: %s" % e)


def show_punishment_wheel() -> None:
    st.subheader("Rule Breaker's Punishment Wheel")
    st.caption("Tap spin — the wheel really rotates, then shows what you landed on.")

    n = len(PUNISHMENTS)
    if "wheel_spin_deg" not in st.session_state:
        st.session_state.wheel_spin_deg = None
    if "wheel_result" not in st.session_state:
        st.session_state.wheel_result = None
    if "wheel_token" not in st.session_state:
        st.session_state.wheel_token = 0

    if st.button("Spin the Wheel!", type="primary", use_container_width=True):
        idx = random.randrange(n)
        deg = spin_target_degrees(idx, n, extra_turns=random.randint(4, 6))
        st.session_state.wheel_spin_deg = deg
        st.session_state.wheel_result = PUNISHMENTS[idx]
        st.session_state.wheel_token = int(st.session_state.wheel_token) + 1
        # Log immediately — no 4s sleep (that made the app feel stuck/slow)
        participants_df, punishments_df = load_data()
        row = participants_df[participants_df["Name"] == st.session_state.current_participant]
        curr = int(row.iloc[0]["CurrentPub"]) if not row.empty else 0
        pub_name = PUBS_DATA["name"][min(curr, 15)]
        new_p = pd.DataFrame(
            [
                {
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Name": st.session_state.current_participant,
                    "Pub": pub_name,
                    "Punishment": PUNISHMENTS[idx],
                }
            ]
        )
        punishments_df = pd.concat([punishments_df, new_p], ignore_index=True)
        save_data(participants_df, punishments_df)
        st.cache_data.clear()

    # Include token in HTML so Streamlit remounts the iframe and JS spin runs every click
    wheel_html = build_wheel_html(
        PUNISHMENTS,
        spin_deg=st.session_state.wheel_spin_deg,
        result_label=st.session_state.wheel_result or "",
    )
    wheel_html = wheel_html.replace(
        "<body>",
        "<body data-spin='%d'>" % int(st.session_state.wheel_token),
        1,
    )
    components.html(wheel_html, height=520)

    if st.session_state.wheel_result:
        st.success("Punishment: **%s**" % st.session_state.wheel_result)


def show_achievements(participant_row) -> None:
    st.markdown("#### Achievements")
    have = achievement_keys(participant_row["Achievements"])
    for key, meta in ACHIEVEMENTS.items():
        if key in have:
            st.markdown(
                "<div class='achievement'>Unlocked · %s — %s (+%s pts)</div>"
                % (html.escape(meta["name"]), html.escape(meta["desc"]), meta["points"]),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='locked-achievement'>Locked · %s — %s (+%s pts)</div>"
                % (html.escape(meta["name"]), html.escape(meta["desc"]), meta["points"]),
                unsafe_allow_html=True,
            )


def show_progress(name: str) -> None:
    participants_df, punishments_df = load_data()
    if participants_df.empty or name not in participants_df["Name"].astype(str).values:
        st.warning("Participant not found — try rejoining.")
        return

    participant = participants_df[participants_df["Name"] == name].iloc[0]
    completed = completed_list(participant["CompletedPubs"])
    progress = len(completed)
    current_pub_idx = int(participant["CurrentPub"])

    st.progress(progress / 16)
    st.markdown(
        "<div class='metric-strip'>"
        "<div class='metric-card'><div class='val'>%d/16</div><div class='lbl'>Completed</div></div>"
        "<div class='metric-card'><div class='val'>%d</div><div class='lbl'>Remaining</div></div>"
        "<div class='metric-card'><div class='val'>%d</div><div class='lbl'>Points</div></div>"
        "</div>"
        % (progress, 16 - progress, int(participant["Points"])),
        unsafe_allow_html=True,
    )

    show_achievements(participant)

    if current_pub_idx < 16:
        pub_name = PUBS_DATA["name"][current_pub_idx]
        pub_rule = PUBS_DATA["rules"][current_pub_idx]
        st.markdown(
            "<div class='pub-card'><h3>Current stop: %s</h3>"
            "<p><b>Challenge rule:</b> %s</p></div>"
            % (html.escape(pub_name), html.escape(pub_rule)),
            unsafe_allow_html=True,
        )
        if st.button("Mark Pub as Complete (+100 pts)", type="primary", use_container_width=True):
            completed.append(pub_name)
            idx = participants_df[participants_df["Name"] == name].index[0]
            participants_df.loc[idx, "CompletedPubs"] = ",".join(completed)
            participants_df.loc[idx, "CurrentPub"] = current_pub_idx + 1
            participants_df.loc[idx, "Points"] = int(participants_df.loc[idx, "Points"]) + 100
            newly = award_achievements(participants_df, idx, completed)
            save_data(participants_df, punishments_df)
            if newly:
                st.session_state["_flash_achievements"] = newly
            auto_refresh()
    else:
        st.success("Absolute legend — you've finished the 16-pub loop at Boombox!")

    if st.session_state.get("_flash_achievements"):
        for a in st.session_state.pop("_flash_achievements"):
            st.toast("Achievement unlocked: %s" % a)


def show_leaderboard() -> None:
    st.subheader("Live Crawl Leaderboard")
    participants_df, punishments_df = load_data()

    if not participants_df.empty:
        board = []
        for _, row in participants_df.iterrows():
            comp = completed_list(row["CompletedPubs"])
            ach = achievement_keys(row["Achievements"])
            board.append(
                {
                    "Name": row["Name"],
                    "Pubs Completed": len(comp),
                    "Points": int(row["Points"]),
                    "Achievements": len(ach),
                }
            )
        df = pd.DataFrame(board).sort_values(["Points", "Pubs Completed"], ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No crawlers yet — be the first.")

    if not punishments_df.empty:
        st.subheader("Recent Punishments Log")
        st.dataframe(
            punishments_df.tail(8).sort_values("Time", ascending=False),
            use_container_width=True,
            hide_index=True,
        )


def show_route_list() -> None:
    with st.expander("Full 16-pub order", expanded=False):
        for i, name in enumerate(PUBS_DATA["name"], start=1):
            st.write("%d. %s" % (i, name.replace("%d. " % i, "")))


def main() -> None:
    name_entry_modal()

    if not st.session_state.current_participant:
        show_route_list()
        mode = "GitHub CSV" if USE_GITHUB else "local CSV (offline demo)"
        st.caption("Persistence: " + mode)
        return

    st.markdown(
        "<div class='brand-hero' style='padding-top:0.4rem;'>"
        "<p class='brand' style='font-size:clamp(1.4rem,5vw,2rem);'>Mark's Belfast Christmas Crawl</p>"
        "<p class='tagline'>Good luck, %s!</p></div>"
        % html.escape(st.session_state.current_participant),
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("**Crawler:** `%s`" % st.session_state.current_participant)
        st.caption("GitHub CSV" if USE_GITHUB else "Local CSV mode")
        if st.button("Refresh Data", use_container_width=True):
            auto_refresh()
        if st.button("Switch crawler", use_container_width=True):
            st.session_state.current_participant = None
            auto_refresh()

    tabs = st.tabs(["Progress", "Loop Map", "Wheel", "Leaderboard"])
    with tabs[0]:
        show_progress(st.session_state.current_participant)
        show_route_list()
    with tabs[1]:
        show_map()
    with tabs[2]:
        show_punishment_wheel()
    with tabs[3]:
        show_leaderboard()


if __name__ == "__main__":
    main()

