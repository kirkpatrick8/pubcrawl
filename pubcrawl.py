import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import time
from datetime import datetime
from github import Github, GithubException
import io
import streamlit.components.v1 as components

# Page config
st.set_page_config(page_title="Belfast 16 Pubs Christmas Loop", page_icon="🍺", layout="wide")

# Modern, High-Contrast Sleek UI Theme & CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .metric-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #374151;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .pub-card {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ef4444;
        margin-bottom: 10px;
    }
    .achievement {
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
        background: linear-gradient(135deg, #059669, #10b981);
        color: white;
        font-weight: bold;
    }
    .locked-achievement {
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
        background: #1f2937;
        border: 1px dashed #4b5563;
        color: #9ca3af;
    }
    /* Wheel Styles */
    .wheel-container {
        width: 300px;
        height: 300px;
        margin: 30px auto;
        position: relative;
    }
    .wheel {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 8px solid #f59e0b;
        position: relative;
        transition: transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99);
        background: #111;
    }
    .wheel-pointer {
        position: absolute;
        top: -25px;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 15px solid transparent;
        border-right: 15px solid transparent;
        border-top: 30px solid #ef4444;
        z-index: 10;
    }
    </style>
""", unsafe_allow_html=True)

# GitHub configuration
try:
    GITHUB_TOKEN = st.secrets["Pubcrawl"]["GITHUB_TOKEN"]
except Exception:
    GITHUB_TOKEN = ""

REPO_NAME = "kirkpatrick8/pubcrawl"
BRANCH_NAME = "main"

# Initialize GitHub client if token is present
g = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None
repo = g.get_repo(REPO_NAME) if g else None

# 16 Pubs Loop Route (Starting at Thirsty Goat, looping city centre & Cathedral Quarter, repeating key stops, ending at Union Street)
PUBS_DATA = {
    'name': [
        "1. Thirsty Goat (Start)", 
        "2. The Deer's Head", 
        "3. The John Hewitt", 
        "4. Whites Tavern",
        "5. Kelly's Cellars", 
        "6. The Points", 
        "7. Downstairs Lavery's", 
        "8. The Crown Liquor Saloon",
        "9. The National", 
        "10. Duke of York", 
        "11. The Harp Bar", 
        "12. The Dirty Onion",
        "13. The Spaniard", 
        "14. Duke of York (Repeat Loop)", 
        "15. The Dirty Onion (Repeat Loop)", 
        "16. Union Street / Boombox (Final!)"
    ],
    'latitude': [
        54.601308, 54.601439, 54.601928, 54.600033, 
        54.599553, 54.591556, 54.589539, 54.595800, 
        54.598100, 54.601803, 54.602000, 54.601556, 
        54.602500, 54.601803, 54.601556, 54.603200
    ],
    'longitude': [
        -5.926417, -5.930294, -5.928617, -5.928497, 
        -5.932236, -5.933333, -5.934469, -5.931200, 
        -5.929000, -5.927442, -5.927058, -5.926673, 
        -5.926200, -5.927442, -5.926673, -5.925500
    ],
    'rules': [
        "Christmas attire Required & First Toast", "Speak in Accents Only", "Different Drink Type Required",
        "Left Hand Only Challenge", "Power Hour (Fast Drink)", "Last Names Only",
        "Talk to a Stranger", "Double Parked", "Sing a Verse of a Song",
        "Must Bow Before Drinking", "Switch Drinks with Buddy", "No Phones Allowed",
        "Compliment the Bartender", "Reverse Toast", "Group Hug Photo", "Final Destination Celebration!"
    ]
}

PUNISHMENTS = [
    "Buy Mark a Drink", "Irish dance for 30 seconds", "Touch your Toes",
    "Down your drink", "Shot for you or a friend", "Sing a Christmas carol",
    "Switch drinks with someone", "No Punishment", 
    "Wear your jumper inside out", "Give someone your drink",
    "Talk in an accent for 10 mins", "Tell a fake back story to a random person"
]

ACHIEVEMENTS = {
    'first_pub': {'name': 'First Timer', 'desc': 'Complete your first pub', 'points': 100},
    'halfway': {'name': 'Halfway Hero', 'desc': 'Complete 8 pubs', 'points': 250},
    'finisher': {'name': 'Challenge Champion', 'desc': 'Complete all 16 pubs', 'points': 1500},
}

@st.cache_data(ttl=5)
def load_data():
    if not repo:
        return pd.DataFrame(columns=['Name', 'CurrentPub', 'CompletedPubs', 'Points', 'Achievements', 'StartTime']), \
               pd.DataFrame(columns=['Time', 'Name', 'Pub', 'Punishment'])
    try:
        content = repo.get_contents("participants.csv", ref=BRANCH_NAME)
        participants_df = pd.read_csv(io.StringIO(content.decoded_content.decode()), dtype=str)
        participants_df['CurrentPub'] = participants_df['CurrentPub'].astype(int)
        participants_df['Points'] = participants_df['Points'].astype(int)
    except Exception:
        participants_df = pd.DataFrame(columns=['Name', 'CurrentPub', 'CompletedPubs', 'Points', 'Achievements', 'StartTime'])
    
    try:
        content = repo.get_contents("punishments.csv", ref=BRANCH_NAME)
        punishments_df = pd.read_csv(io.StringIO(content.decoded_content.decode()), dtype=str)
    except Exception:
        punishments_df = pd.DataFrame(columns=['Time', 'Name', 'Pub', 'Punishment'])
            
    return participants_df, punishments_df

def save_data(participants_df, punishments_df):
    if not repo:
        return
    try:
        try:
            c = repo.get_contents("participants.csv", ref=BRANCH_NAME)
            repo.update_file("participants.csv", "Update", participants_df.to_csv(index=False), c.sha, branch=BRANCH_NAME)
        except Exception:
            repo.create_file("participants.csv", "Create", participants_df.to_csv(index=False), branch=BRANCH_NAME)
        
        try:
            c = repo.get_contents("punishments.csv", ref=BRANCH_NAME)
            repo.update_file("punishments.csv", "Update", punishments_df.to_csv(index=False), c.sha, branch=BRANCH_NAME)
        except Exception:
            repo.create_file("punishments.csv", "Create", punishments_df.to_csv(index=False), branch=BRANCH_NAME)
    except Exception as e:
        st.sidebar.error(f"Save error: {e}")

def auto_refresh():
    st.cache_data.clear()
    time.sleep(0.1)
    st.rerun()

def name_entry_modal():
    if 'current_participant' not in st.session_state:
        st.session_state.current_participant = None
        
    if not st.session_state.current_participant:
        st.markdown("<h2 style='text-align: center; color: #f59e0b;'>🎄 Belfast 16 Pubs Christmas Loop 🍺</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            name = st.text_input("Enter your name to join the crawl:")
            if st.button("Start Crawling!", type="primary", use_container_width=True):
                if name.strip():
                    st.session_state.current_participant = name.strip()
                    participants_df, punishments_df = load_data()
                    if name not in participants_df['Name'].values:
                        new_p = pd.DataFrame([{
                            'Name': name, 'CurrentPub': 0, 'CompletedPubs': '', 
                            'Points': 0, 'Achievements': '', 'StartTime': datetime.now().isoformat()
                        }])
                        participants_df = pd.concat([participants_df, new_p], ignore_index=True)
                        save_data(participants_df, punishments_df)
                    auto_refresh()

def show_map():
    st.subheader("🗺️ 16-Pub City Centre & Cathedral Quarter Loop")
    try:
        participants_df, _ = load_data()
        participant = participants_df[participants_df['Name'] == st.session_state.current_participant].iloc[0]
        completed = str(participant['CompletedPubs']).split(',') if pd.notna(participant['CompletedPubs']) else []
        
        m = folium.Map(location=[54.598000, -5.930000], zoom_start=15, tiles="CartoDB dark_matter")
        
        for i, (name, lat, lon) in enumerate(zip(PUBS_DATA['name'], PUBS_DATA['latitude'], PUBS_DATA['longitude'])):
            color = 'green' if name in completed else ('orange' if i == int(participant['CurrentPub']) else 'red')
            folium.Marker([lat, lon], popup=name, tooltip=name, icon=folium.Icon(color=color, icon='beer', prefix='fa')).add_to(m)
            
            if i > 0:
                folium.PolyLine([[PUBS_DATA['latitude'][i-1], PUBS_DATA['longitude'][i-1]], [lat, lon]], color='#3b82f6', weight=4, opacity=0.8).add_to(m)
                
        st_folium(m, height=450, width=700, returned_objects=[])
    except Exception as e:
        st.error(f"Map rendering error: {e}")

def show_punishment_wheel():
    st.subheader("😈 Rule Breaker's Punishment Wheel")
    wheel_html = """
    <div class="wheel-container">
        <div class="wheel-pointer"></div>
        <div id="wheel" class="wheel"></div>
    </div>
    <script>
    function spin() {
        const wheel = document.getElementById('wheel');
        const randomDegree = 1800 + Math.floor(Math.random() * 360);
        wheel.style.transform = "rotate(" + randomDegree + "deg)";
    }
    </script>
    """
    if st.button("Spin the Wheel!", type="primary"):
        components.html(wheel_html + "<script>spin();</script>", height=350)
        with st.spinner("Determining your fate..."):
            time.sleep(4)
            
        participants_df, punishments_df = load_data()
        participant = participants_df[participants_df['Name'] == st.session_state.current_participant].iloc[0]
        curr = int(participant['CurrentPub'])
        pub_name = PUBS_DATA['name'][curr] if curr < 16 else PUBS_DATA['name'][-1]
        
        punishment = random.choice(PUNISHMENTS)
        new_p = pd.DataFrame([{'Time': datetime.now().strftime('%H:%M:%S'), 'Name': st.session_state.current_participant, 'Pub': pub_name, 'Punishment': punishment}])
        punishments_df = pd.concat([punishments_df, new_p], ignore_index=True)
        save_data(participants_df, punishments_df)
        
        st.success(f"⚠️ **Punishment Assigned:** {punishment}")
    else:
        components.html(wheel_html, height=350)

def show_progress(name):
    participants_df, punishments_df = load_data()
    if participants_df.empty or name not in participants_df['Name'].values:
        return
        
    participant = participants_df[participants_df['Name'] == name].iloc[0]
    completed = [p for p in str(participant['CompletedPubs']).split(',') if p]
    progress = len(completed)
    current_pub_idx = int(participant['CurrentPub'])
    
    st.progress(progress / 16)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Pubs Completed", f"{progress}/16")
    with col2: st.metric("Remaining", f"{16-progress}")
    with col3: st.metric("Total Score", int(participant['Points']))
    
    st.markdown("---")
    
    if current_pub_idx < 16:
        pub_name = PUBS_DATA['name'][current_pub_idx]
        pub_rule = PUBS_DATA['rules'][current_pub_idx]
        
        st.markdown(f"""
            <div class='pub-card'>
                <h3>🎯 Current Stop: {pub_name}</h3>
                <p><b>Challenge Rule:</b> {pub_rule}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ Mark Pub as Complete (+100 pts)", type="primary", use_container_width=True):
            completed.append(pub_name)
            idx = participants_df[participants_df['Name'] == name].index[0]
            participants_df.loc[idx, 'CompletedPubs'] = ','.join(completed)
            participants_df.loc[idx, 'CurrentPub'] = current_pub_idx + 1
            participants_df.loc[idx, 'Points'] += 100
            save_data(participants_df, punishments_df)
            auto_refresh()
    else:
        st.success("🎉 Absolute Legend! You've successfully finished the 16-pub loop at Union Street / Boombox! 🏆")

def show_leaderboard():
    st.subheader("🏆 Live Crawl Leaderboard")
    participants_df, punishments_df = load_data()
    
    if not participants_df.empty:
        board = []
        for _, row in participants_df.iterrows():
            comp = [p for p in str(row['CompletedPubs']).split(',') if p]
            board.append({
                'Name': row['Name'],
                'Pubs Completed': len(comp),
                'Points': int(row['Points'])
            })
        df = pd.DataFrame(board).sort_values(['Points', 'Pubs Completed'], ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    if not punishments_df.empty:
        st.subheader("😈 Recent Punishments Log")
        st.dataframe(punishments_df.tail(5).sort_values('Time', ascending=False), use_container_width=True, hide_index=True)

def main():
    name_entry_modal()
    
    if st.session_state.current_participant:
        st.sidebar.markdown(f"👤 **Cralwer:** `{st.session_state.current_participant}`")
        if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
            auto_refresh()
            
        tabs = st.tabs(["📊 Progress", "🗺️ Loop Map", "🎯 Wheel", "🏆 Leaderboard"])
        with tabs[0]: show_progress(st.session_state.current_participant)
        with tabs[1]: show_map()
        with tabs[2]: show_punishment_wheel()
        with tabs[3]: show_leaderboard()

if __name__ == "__main__":
    main()
