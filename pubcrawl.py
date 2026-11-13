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
st.set_page_config(page_title="Belfast 16 Pubs Crawl", page_icon="🍺", layout="wide")

# Custom CSS with working wheel spin states
st.markdown("""
    <style>
    .stProgress .st-bo { background-color: #ff4b4b; }
    .stProgress .st-bp { background-color: #28a745; }
    .achievement {
        padding: 10px;
        margin: 5px;
        border-radius: 5px;
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
        margin-bottom: 10px;
    }
    .locked-achievement {
        padding: 10px;
        margin: 5px;
        border-radius: 5px;
        background: #f0f2f6;
        opacity: 0.7;
        margin-bottom: 10px;
    }

    /* Wheel Styles */
    .wheel-container {
        width: 300px;
        height: 300px;
        margin: 50px auto;
        position: relative;
        perspective: 1000px;
    }

    .wheel {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        position: relative;
        border: 10px solid gold;
        box-shadow: 0 0 0 10px #333;
        transform: rotate(0deg);
        transition: transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99);
        transform-style: preserve-3d;
    }

    .wheel-section {
        position: absolute;
        width: 50%;
        height: 50%;
        background: var(--color);
        transform-origin: 100% 100%;
        clip-path: polygon(100% 50%, 100% 100%, 0 100%, 0 50%);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .wheel-text {
        position: absolute;
        left: 25%;
        top: 25%;
        transform: rotate(-60deg);
        color: white;
        font-size: 10px;
        font-weight: bold;
        text-shadow: 1px 1px 2px black;
        white-space: nowrap;
    }

    .wheel.spinning {
        transform: rotate(1800deg);
    }

    .wheel-pointer {
        position: absolute;
        top: -20px;
        left: 50%;
        transform: translateX(-50%);
        width: 20px;
        height: 40px;
        background: red;
        clip-path: polygon(50% 100%, 0 0, 100% 0);
        z-index: 2;
    }

    .wheel-center {
        position: absolute;
        width: 40px;
        height: 40px;
        background: gold;
        border: 5px solid #333;
        border-radius: 50%;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 1;
    }
    </style>
""", unsafe_allow_html=True)

# GitHub configuration
GITHUB_TOKEN = st.secrets["Pubcrawl"]["GITHUB_TOKEN"]
REPO_NAME = "kirkpatrick8/pubcrawl"
BRANCH_NAME = "main"

# Initialize GitHub client
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# 16 Pubs Route: Starting at Thirsty Goat -> Ending at Union Street / Boombox
PUBS_DATA = {
    'name': [
        "Thirsty Goat", "The Dirty Onion", "The Harp Bar", "Duke of York",
        "The John Hewitt", "The Deer's Head", "Whites Tavern", "Kelly's Cellars",
        "Sweet Afton", "The Points", "Downstairs Lavery's", "The Crown Liquor Saloon",
        "The Robinson", "The National", "The Spaniard", "Union Street / Boombox"
    ],
    'latitude': [
        54.601308, 54.601556, 54.602000, 54.601803, 
        54.601928, 54.601439, 54.600033, 54.599553, 
        54.595067, 54.591556, 54.589539, 54.595800, 
        54.596200, 54.598100, 54.602500, 54.603200
    ],
    'longitude': [
        -5.926417, -5.926673, -5.927058, -5.927442, 
        -5.928617, -5.930294, -5.928497, -5.932236, 
        -5.932894, -5.933333, -5.934469, -5.931200, 
        -5.930500, -5.929000, -5.926200, -5.925500
    ],
    'rules': [
        "Christmas attire Required & First Toast", "No Phones Allowed", "Switch Drinks with Buddy",
        "Must Bow Before Drinking", "Different Drink Type Required", "Speak in Accents Only",
        "Left Hand Only Challenge", "Power Hour (Down Fast)", "No Swearing Allowed",
        "Last Names Only", "Talk to a Stranger", "Double Parked",
        "Sing a Verse of a Song", "The Arm Drink Challenge", "Compliment the Bartender", "Final Destination Celebration!"
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
    'rule_breaker': {'name': 'Rule Breaker', 'desc': 'Get punished 3 times', 'points': 50},
    'dance_master': {'name': 'Dance Master', 'desc': 'Get the Irish dance punishment twice', 'points': 150},
    'speed_demon': {'name': 'Speed Demon', 'desc': 'Complete route quickly', 'points': 400},
}

@st.cache_data(ttl=10)
def load_data():
    """Load data from GitHub with explicit string types to avoid LossySetitemError"""
    participants_file = "participants.csv"
    punishments_file = "punishments.csv"
    
    try:
        content = repo.get_contents(participants_file, ref=BRANCH_NAME)
        participants_df = pd.read_csv(io.StringIO(content.decoded_content.decode()), dtype=str)
        participants_df['CurrentPub'] = participants_df['CurrentPub'].astype(int)
        participants_df['Points'] = participants_df['Points'].astype(int)
    except GithubException as e:
        if e.status == 404:
            participants_df = pd.DataFrame(columns=['Name', 'CurrentPub', 'CompletedPubs', 'Points', 'Achievements', 'StartTime'])
        else:
            participants_df = pd.DataFrame(columns=['Name', 'CurrentPub', 'CompletedPubs', 'Points', 'Achievements', 'StartTime'])
    
    try:
        content = repo.get_contents(punishments_file, ref=BRANCH_NAME)
        punishments_df = pd.read_csv(io.StringIO(content.decoded_content.decode()), dtype=str)
    except GithubException as e:
        if e.status == 404:
            punishments_df = pd.DataFrame(columns=['Time', 'Name', 'Pub', 'Punishment'])
        else:
            punishments_df = pd.DataFrame(columns=['Time', 'Name', 'Pub', 'Punishment'])
            
    return participants_df, punishments_df

def save_data(participants_df, punishments_df, max_retries=3):
    """Save data to GitHub with retry logic"""
    for attempt in range(max_retries):
        try:
            try:
                contents = repo.get_contents("participants.csv", ref=BRANCH_NAME)
                repo.update_file("participants.csv", f"Update participants - {datetime.now()}", participants_df.to_csv(index=False), contents.sha, branch=BRANCH_NAME)
            except GithubException as e:
                if e.status == 404:
                    repo.create_file("participants.csv", f"Create participants", participants_df.to_csv(index=False), branch=BRANCH_NAME)
                else:
                    raise e
        
            try:
                contents = repo.get_contents("punishments.csv", ref=BRANCH_NAME)
                repo.update_file("punishments.csv", f"Update punishments - {datetime.now()}", punishments_df.to_csv(index=False), contents.sha, branch=BRANCH_NAME)
            except GithubException as e:
                if e.status == 404:
                    repo.create_file("punishments.csv", f"Create punishments", punishments_df.to_csv(index=False), branch=BRANCH_NAME)
                else:
                    raise e
            break
        except Exception as e:
            if attempt == max_retries - 1:
                st.sidebar.error(f"Error saving data: {e}")
            else:
                time.sleep(1)

def auto_refresh():
    st.cache_data.clear()
    time.sleep(0.1)
    st.rerun()

def check_achievements(name, participants_df, punishments_df=None):
    participant = participants_df[participants_df['Name'] == name].iloc[0]
    achievements = [] if pd.isna(participant['Achievements']) or participant['Achievements'] == '' else str(participant['Achievements']).split(',')
    completed_pubs = [] if pd.isna(participant['CompletedPubs']) or participant['CompletedPubs'] == '' else str(participant['CompletedPubs']).split(',')
    
    completed_count = len(completed_pubs)
    points_added = 0
    
    def award_achievement(ach_id):
        nonlocal points_added
        if ach_id not in achievements:
            achievements.append(ach_id)
            points_added += ACHIEVEMENTS[ach_id]['points']
            st.balloons()
            st.success(f"🏆 Achievement Unlocked: {ACHIEVEMENTS[ach_id]['name']}!")
    
    if completed_count >= 1:
        award_achievement('first_pub')
    if completed_count >= 8:
        award_achievement('halfway')
    if completed_count == 16:
        award_achievement('finisher')
        
    participants_df.loc[participants_df['Name'] == name, 'Achievements'] = ','.join(achievements) if achievements else ''
    if points_added > 0:
        participants_df.loc[participants_df['Name'] == name, 'Points'] += points_added
        
    return participants_df

def name_entry_modal():
    if 'current_participant' not in st.session_state:
        st.session_state.current_participant = None
        
    if st.session_state.current_participant is None:
        with st.container():
            st.markdown("### Welcome to the Belfast 16 Pubs Crawl! 🎄🍺")
            name = st.text_input("Enter your name to begin:")
            if name:
                st.session_state.current_participant = name
                participants_df, punishments_df = load_data()
                if name not in participants_df['Name'].values:
                    new_participant = pd.DataFrame([{
                        'Name': name,
                        'CurrentPub': 0,
                        'CompletedPubs': '',
                        'Points': 0,
                        'Achievements': '',
                        'StartTime': datetime.now().isoformat()
                    }])
                    participants_df = pd.concat([participants_df, new_participant], ignore_index=True)
                    save_data(participants_df, punishments_df)
                auto_refresh()

def show_map():
    st.header("🗺️ 16 Pub Route Map (Thirsty Goat to Union Street)")
    try:
        participants_df, _ = load_data()
        participant = participants_df[participants_df['Name'] == st.session_state.current_participant].iloc[0]
        completed_pubs = [] if pd.isna(participant['CompletedPubs']) or participant['CompletedPubs'] == '' else str(participant['CompletedPubs']).split(',')
        
        m = folium.Map(location=[54.600000, -5.928000], zoom_start=15, tiles="CartoDB positron")
        
        for i, (name, lat, lon) in enumerate(zip(PUBS_DATA['name'], PUBS_DATA['latitude'], PUBS_DATA['longitude'])):
            if name in completed_pubs:
                color, icon = 'green', 'check'
            elif i == int(participant['CurrentPub']):
                color, icon = 'orange', 'beer'
            else:
                color, icon = 'red', 'info'
            
            popup_text = f"<b>{i+1}. {name}</b><br>Rule: {PUBS_DATA['rules'][i]}"
            folium.Marker([lat, lon], popup=popup_text, tooltip=f"{i+1}. {name}", icon=folium.Icon(color=color, icon=icon, prefix='fa')).add_to(m)
            
            if i > 0:
                folium.PolyLine([[PUBS_DATA['latitude'][i-1], PUBS_DATA['longitude'][i-1]], [lat, lon]], weight=3, color='#FF4B4B', opacity=0.8, dash_array='10').add_to(m)
                
        st_folium(m, height=450, width=700, returned_objects=[])
    except Exception as e:
        st.error(f"Error displaying map: {e}")

def show_punishment_wheel():
    st.header("😈 Rule Breaker's Wheel")
    wheel_html = """
    <div class="wheel-container">
        <div class="wheel-pointer"></div>
        <div id="wheel" class="wheel">
            <div class="wheel-section" style="--color: #FF4B4B; transform: rotate(0deg);"><span class="wheel-text">Drink</span></div>
            <div class="wheel-section" style="--color: #4CAF50; transform: rotate(45deg);"><span class="wheel-text">Dance</span></div>
            <div class="wheel-section" style="--color: #2196F3; transform: rotate(90deg);"><span class="wheel-text">Story</span></div>
            <div class="wheel-section" style="--color: #FFC107; transform: rotate(135deg);"><span class="wheel-text">Down It</span></div>
            <div class="wheel-section" style="--color: #9C27B0; transform: rotate(180deg);"><span class="wheel-text">Shot</span></div>
            <div class="wheel-section" style="--color: #FF9800; transform: rotate(225deg);"><span class="wheel-text">Carol</span></div>
            <div class="wheel-section" style="--color: #E91E63; transform: rotate(270deg);"><span class="wheel-text">Switch</span></div>
            <div class="wheel-section" style="--color: #00BCD4; transform: rotate(315deg);"><span class="wheel-text">Jumper</span></div>
            <div class="wheel-center"></div>
        </div>
    </div>
    <script>
    function triggerSpin() {
        const wheel = document.getElementById('wheel');
        wheel.style.transform = "rotate(" + (1440 + Math.random() * 360) + "deg)";
    }
    </script>
    """
    
    if st.button("Spin the Wheel", type="primary", key="spin_btn"):
        components.html(wheel_html + "<script>triggerSpin();</script>", height=350)
        with st.spinner("Spinning wheel..."):
            time.sleep(4)
            
        participants_df, punishments_df = load_data()
        participant = participants_df[participants_df['Name'] == st.session_state.current_participant].iloc[0]
        curr_idx = int(participant['CurrentPub'])
        current_pub = PUBS_DATA['name'][curr_idx] if curr_idx < 16 else PUBS_DATA['name'][-1]
        
        punishment = random.choice(PUNISHMENTS)
        new_p = pd.DataFrame([{'Time': datetime.now().strftime('%H:%M:%S'), 'Name': st.session_state.current_participant, 'Pub': current_pub, 'Punishment': punishment}])
        punishments_df = pd.concat([punishments_df, new_p], ignore_index=True)
        save_data(participants_df, punishments_df)
        
        st.snow()
        st.success(f"🎉 Punishment: **{punishment}**")
    else:
        components.html(wheel_html, height=350)

def show_progress(name):
    participants_df, punishments_df = load_data()
    if len(participants_df[participants_df['Name'] == name]) == 0:
        return
        
    participant = participants_df[participants_df['Name'] == name].iloc[0]
    st.header(f"Progress Tracker for {name}")
    
    completed_pubs = [] if pd.isna(participant['CompletedPubs']) or participant['CompletedPubs'] == '' else str(participant['CompletedPubs']).split(',')
    progress = len(completed_pubs)
    current_pub = int(participant['CurrentPub'])
    
    st.progress(progress/16)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Pubs Completed", f"{progress}/16")
    with col2: st.metric("Pubs Remaining", f"{16-progress}")
    with col3: st.metric("Points", int(participant['Points']))
    
    if current_pub < 16:
        current_pub_name = PUBS_DATA['name'][current_pub]
        current_rule = PUBS_DATA['rules'][current_pub]
        
        st.subheader(f"Current Pub: {current_pub_name}")
        st.info(f"Rule: {current_rule}")
        
        if st.button("Mark Current Pub as Complete", type="primary"):
            completed_pubs.append(current_pub_name)
            participant_idx = participants_df[participants_df['Name'] == name].index[0]
            
            participants_df.loc[participant_idx, 'CompletedPubs'] = ','.join(completed_pubs)
            participants_df.loc[participant_idx, 'CurrentPub'] = current_pub + 1
            participants_df.loc[participant_idx, 'Points'] += 100
            
            participants_df = check_achievements(name, participants_df, punishments_df)
            save_data(participants_df, punishments_df)
            auto_refresh()
    else:
        st.success("🎉 Legend! You've completed all 16 Belfast Pubs ending at Union Street / Boombox! 🏆")

def show_leaderboard():
    st.header("🏆 Leaderboard")
    participants_df, punishments_df = load_data()
    
    if not participants_df.empty:
        display_data = []
        for _, row in participants_df.iterrows():
            completed_pubs = [] if pd.isna(row['CompletedPubs']) or row['CompletedPubs'] == '' else str(row['CompletedPubs']).split(',')
            achievements = [] if pd.isna(row['Achievements']) or row['Achievements'] == '' else str(row['Achievements']).split(',')
            current_pub = int(row['CurrentPub'])
            current_pub_name = PUBS_DATA['name'][current_pub] if current_pub < 16 else 'Finished! 🏆'
            
            display_data.append({
                'Name': row['Name'],
                'Pubs Completed': len(completed_pubs),
                'Current Location': current_pub_name,
                'Points': int(row['Points']),
                'Achievements': len(achievements)
            })
        df = pd.DataFrame(display_data).sort_values(['Points', 'Pubs Completed'], ascending=[False, False])
        st.dataframe(df, use_container_width=True)
        
    if not punishments_df.empty:
        st.subheader("😈 Recent Punishments")
        st.dataframe(punishments_df.tail(5).sort_values('Time', ascending=False), use_container_width=True)

def main():
    st.title("🎄 Belfast 16 Pubs Christmas Crawl 🍺")
    name_entry_modal()
    
    if st.session_state.current_participant:
        if st.sidebar.button("Refresh Data"):
            auto_refresh()
            
        tabs = st.tabs(["👥 Leaderboard", "📊 My Progress", "🗺️ Map", "🎯 Punishment Wheel", "🏆 Achievements"])
        with tabs[0]: show_leaderboard()
        with tabs[1]: show_progress(st.session_state.current_participant)
        with tabs[2]: show_map()
        with tabs[3]: show_punishment_wheel()
        with tabs[4]: 
            participants_df, _ = load_data()
            if not participants_df[participants_df['Name'] == st.session_state.current_participant].empty:
                participant = participants_df[participants_df['Name'] == st.session_state.current_participant].iloc[0]
                earned = [] if pd.isna(participant['Achievements']) or participant['Achievements'] == '' else str(participant['Achievements']).split(',')
                st.subheader("🏆 Your Achievements")
                for ach_id, ach in ACHIEVEMENTS.items():
                    if ach_id in earned:
                        st.markdown(f"<div class='achievement'><h3>{ach['name']} ✨</h3><p>{ach['desc']}</p></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='locked-achievement'><h3>🔒 {ach['name']}</h3><p>{ach['desc']}</p></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
