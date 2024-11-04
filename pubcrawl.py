import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import time
from datetime import datetime
from github import Github
from github import GithubException
import io

# Page config
st.set_page_config(page_title="Belfast 12 Pubs of Christmas", page_icon="🍺", layout="wide")

# CSS for components
st.markdown("""
    <style>
    .stProgress .st-bo { background-color: #ff4b4b; }
    .stProgress .st-bp { background-color: #28a745; }
    .pub-timer { font-size: 24px; font-weight: bold; color: #ff4b4b; }
    
    /* Achievement styles */
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
    
    /* Wheel styles */
    .wheel-container {
        width: 300px;
        height: 300px;
        margin: 20px auto;
        position: relative;
    }
    .wheel {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        position: relative;
        border: 10px solid #333;
        background: #fff;
        overflow: hidden;
        box-shadow: 0 0 20px rgba(0,0,0,0.2);
    }
    .wheel-section {
        position: absolute;
        width: 50%;
        height: 50%;
        transform-origin: 100% 100%;
        background: #fff;
        border: 1px solid #ccc;
        box-sizing: border-box;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        padding: 10px;
        text-align: center;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(3600deg); }
    }
    .wheel.spinning {
        animation: spin 5s cubic-bezier(0.17, 0.67, 0.12, 0.99);
    }
    .wheel-pointer {
        position: absolute;
        top: -20px;
        left: 50%;
        transform: translateX(-50%);
        width: 40px;
        height: 40px;
        background: #FF4B4B;
        clip-path: polygon(50% 100%, 0 0, 100% 0);
        z-index: 2;
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

# Constants
PUBS_DATA = {
    'name': [
        "Lavery's", "The Points", "Sweet Afton", "Kelly's Cellars",
        "Whites Tavern", "The Deer's Head", "The John Hewitt", "Duke of York",
        "The Harp Bar", "The Dirty Onion", "Thirsty Goat", "Ulster Sports Club"
    ],
    'latitude': [
        54.589539, 54.591556, 54.595067, 54.599553, 54.600033, 54.601439,
        54.601928, 54.601803, 54.602000, 54.601556, 54.601308, 54.600733
    ],
    'longitude': [
        -5.934469, -5.933333, -5.932894, -5.932236, -5.928497, -5.930294,
        -5.928617, -5.927442, -5.927058, -5.926673, -5.926417, -5.925219
    ],
    'rules': [
        "Christmas Jumpers Required", "Last Names Only", "No Swearing Challenge",
        "Power Hour (Down Drink in 2-3 Gulps)", "No Phones & Drink with Left Hand Only",
        "Must Speak in Different Accents", "Different Drink Type Required",
        "Must Bow Before Taking a Drink", "Double Parked",
        "The Arm Pub - Drink from Someone Else's Arm",
        "No First Names & Photo Challenge", "Buddy System - Final Challenge"
    ]
}

PUNISHMENTS = [
    "Buy Mark a Drink", "Irish dance for 30 seconds", "Tell an embarrassing story",
    "Down your drink", "Add a shot to your next drink", "Sing a Christmas carol",
    "Switch drinks with someone", "No phone for next 2 pubs", 
    "Wear your jumper inside out", "Give someone your drink",
    "Talk in an accent for 10 mins", "Do 10 jumping jacks"
]

# Achievement definitions
ACHIEVEMENTS = {
    'first_pub': {'name': 'First Timer', 'desc': 'Complete your first pub', 'points': 100},
    'halfway': {'name': 'Halfway Hero', 'desc': 'Complete 6 pubs', 'points': 250},
    'finisher': {'name': 'Challenge Champion', 'desc': 'Complete all 12 pubs', 'points': 500},
    'rule_breaker': {'name': 'Rule Breaker', 'desc': 'Get punished 3 times', 'points': 150},
    'dance_master': {'name': 'Dance Master', 'desc': 'Get the Irish dance punishment twice', 'points': 150},
    'karaoke_king': {'name': 'Karaoke King/Queen', 'desc': 'Sing two Christmas carols as punishment', 'points': 150},
    'silent_warrior': {'name': 'Silent Warrior', 'desc': 'Complete No Swearing Challenge without punishment', 'points': 200},
    'phone_free': {'name': 'Phone Free Zone', 'desc': 'Complete No Phones rule without checking phone', 'points': 200},
    'perfect_run': {'name': 'Perfect Run', 'desc': 'Complete all pubs with no punishments', 'points': 500},
    'punishment_collector': {'name': 'Punishment Collector', 'desc': 'Receive every type of punishment', 'points': 400},
    'speed_demon': {'name': 'Speed Demon', 'desc': 'Complete route in under 3 hours', 'points': 400},
    'golden_route': {'name': 'Golden Route', 'desc': 'Visit pubs in perfect order without skipping', 'points': 300}
}
# Data management functions
@st.cache_data(ttl=10)  # Cache for 10 seconds
def load_data():
    """Load data from GitHub"""
    try:
        participants_file = "participants.csv"
        punishments_file = "punishments.csv"
        
        try:
            content = repo.get_contents(participants_file, ref=BRANCH_NAME)
            participants_df = pd.read_csv(io.StringIO(content.decoded_content.decode()))
        except:
            participants_df = pd.DataFrame(columns=['Name', 'CurrentPub', 'CompletedPubs', 'Points', 'Achievements', 'StartTime'])
        
        try:
            content = repo.get_contents(punishments_file, ref=BRANCH_NAME)
            punishments_df = pd.read_csv(io.StringIO(content.decoded_content.decode()))
        except:
            punishments_df = pd.DataFrame(columns=['Time', 'Name', 'Pub', 'Punishment'])
        
        return participants_df, punishments_df
    except Exception as e:
        st.sidebar.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=['Name', 'CurrentPub', 'CompletedPubs', 'Points', 'Achievements', 'StartTime']), \
               pd.DataFrame(columns=['Time', 'Name', 'Pub', 'Punishment'])

def save_data(participants_df, punishments_df):
    """Save data to GitHub"""
    try:
        # Save participants
        try:
            contents = repo.get_contents("participants.csv", ref=BRANCH_NAME)
            repo.update_file(
                "participants.csv",
                f"Update participants - {datetime.now()}",
                participants_df.to_csv(index=False),
                contents.sha,
                branch=BRANCH_NAME
            )
        except:
            repo.create_file(
                "participants.csv",
                f"Create participants file - {datetime.now()}",
                participants_df.to_csv(index=False),
                branch=BRANCH_NAME
            )
        
        # Save punishments
        try:
            contents = repo.get_contents("punishments.csv", ref=BRANCH_NAME)
            repo.update_file(
                "punishments.csv",
                f"Update punishments - {datetime.now()}",
                punishments_df.to_csv(index=False),
                contents.sha,
                branch=BRANCH_NAME
            )
        except:
            repo.create_file(
                "punishments.csv",
                f"Create punishments file - {datetime.now()}",
                punishments_df.to_csv(index=False),
                branch=BRANCH_NAME
            )
    except Exception as e:
        st.sidebar.error(f"Error saving data: {e}")

def name_entry_modal():
    """Display name entry modal"""
    if 'current_participant' not in st.session_state:
        st.session_state.current_participant = None
        
    if st.session_state.current_participant is None:
        with st.container():
            st.markdown("### Welcome to the Belfast 12 Pubs of Christmas! 🎄")
            name = st.text_input("Enter your name to begin:")
            if name:
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
                st.session_state.current_participant = name
                st.rerun()

def check_achievements(name, participants_df, punishments_df=None):
    """Check and award achievements"""
    participant = participants_df[participants_df['Name'] == name].iloc[0]
    achievements = [] if pd.isna(participant['Achievements']) else participant['Achievements'].split(',')
    if achievements == ['']:
        achievements = []
    
    completed_pubs = [] if pd.isna(participant['CompletedPubs']) else participant['CompletedPubs'].split(',')
    if completed_pubs == ['']:
        completed_pubs = []
    
    completed_count = len(completed_pubs)
    points_added = 0
    
    def award_achievement(ach_id):
        nonlocal points_added
        if ach_id not in achievements:
            achievements.append(ach_id)
            points_added += ACHIEVEMENTS[ach_id]['points']
            st.balloons()
            st.success(f"🏆 Achievement Unlocked: {ACHIEVEMENTS[ach_id]['name']}!")
    
    # Basic achievements
    if completed_count >= 1:
        award_achievement('first_pub')
    if completed_count >= 6:
        award_achievement('halfway')
    if completed_count == 12:
        award_achievement('finisher')
    
    # Special achievements
    if punishments_df is not None:
        user_punishments = punishments_df[punishments_df['Name'] == name]
        
        # Rule breaker
        if len(user_punishments) >= 3:
            award_achievement('rule_breaker')
        
        # Dance Master
        dance_count = len(user_punishments[user_punishments['Punishment'].str.contains('Irish dance', case=False)])
        if dance_count >= 2:
            award_achievement('dance_master')
        
        # Karaoke King/Queen
        carol_count = len(user_punishments[user_punishments['Punishment'].str.contains('Christmas carol', case=False)])
        if carol_count >= 2:
            award_achievement('karaoke_king')
        
        # Silent Warrior & Phone Free
        if completed_count > 2:  # After pub 3
            no_swearing_punishments = user_punishments[user_punishments['Pub'] == PUBS_DATA['name'][2]]
            if len(no_swearing_punishments) == 0:
                award_achievement('silent_warrior')
        
        if completed_count > 4:  # After pub 5
            no_phone_punishments = user_punishments[user_punishments['Pub'] == PUBS_DATA['name'][4]]
            if len(no_phone_punishments) == 0:
                award_achievement('phone_free')
        
        # Perfect Run
        if completed_count == 12 and len(user_punishments) == 0:
            award_achievement('perfect_run')
        
        # Punishment Collector
        if len(set(user_punishments['Punishment'])) == len(PUNISHMENTS):
            award_achievement('punishment_collector')
    
    # Speed Demon
    if completed_count == 12 and not pd.isna(participant['StartTime']):
        start_time = datetime.fromisoformat(participant['StartTime'])
        end_time = datetime.now()
        total_hours = (end_time - start_time).total_seconds() / 3600
        if total_hours <= 3:
            award_achievement('speed_demon')
    
    # Golden Route
    if completed_count > 0:
        expected_order = PUBS_DATA['name'][:completed_count]
        if completed_pubs == expected_order:
            award_achievement('golden_route')
    
    # Update achievements and points
    participants_df.loc[participants_df['Name'] == name, 'Achievements'] = ','.join(achievements) if achievements else ''
    if points_added > 0:
        participants_df.loc[participants_df['Name'] == name, 'Points'] += points_added
    
    return participants_df

def auto_refresh():
    """Helper function for refreshing the app"""
    st.cache_data.clear()
    time.sleep(0.3)
    st.rerun()
def show_map():
    """Display interactive map"""
    st.header("🗺️ Pub Route Map")
    
    try:
        participants_df, _ = load_data()
        participant = participants_df[participants_df['Name'] == st.session_state.current_participant].iloc[0]
        completed_pubs = [] if pd.isna(participant['CompletedPubs']) else participant['CompletedPubs'].split(',')
        if completed_pubs == ['']:
            completed_pubs = []
        
        m = folium.Map(
            location=[54.595733, -5.930294],
            zoom_start=15,
            tiles="CartoDB positron"
        )
        
        for i, (name, lat, lon) in enumerate(zip(
            PUBS_DATA['name'],
            PUBS_DATA['latitude'],
            PUBS_DATA['longitude']
        )):
            # Determine marker style
            if name in completed_pubs:
                color = 'green'
                icon = 'check'
            elif i == int(participant['CurrentPub']):
                color = 'orange'
                icon = 'beer'
            else:
                color = 'red'
                icon = 'info'
            
            # Create popup content
            popup_text = f"""
                <div style='width:200px'>
                    <h4>{i+1}. {name}</h4>
                    <b>Rule:</b> {PUBS_DATA['rules'][i]}<br>
                    <b>Status:</b> {'✅ Completed' if name in completed_pubs else 
                                  '🎯 Current' if i == int(participant['CurrentPub']) else 
                                  '⏳ Pending'}
                </div>
            """
            
            # Add marker
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{i+1}. {name}",
                icon=folium.Icon(color=color, icon=icon, prefix='fa')
            ).add_to(m)
            
            # Connect pubs with line
            if i > 0:
                folium.PolyLine(
                    locations=[
                        [PUBS_DATA['latitude'][i-1], PUBS_DATA['longitude'][i-1]],
                        [lat, lon]
                    ],
                    weight=3,
                    color='#FF4B4B',
                    opacity=0.8,
                    dash_array='10'
                ).add_to(m)
        
        # Display map with fixed dimensions
        st_folium(m, height=400, width=700)
        
    except Exception as e:
        st.error("Error displaying map. Please refresh the page.")

def show_punishment_wheel():
    """Display punishment wheel"""
    st.header("😈 Rule Breaker's Punishment Wheel")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("Spin the Wheel", type="primary"):
            participants_df, punishments_df = load_data()
            participant = participants_df[participants_df['Name'] == st.session_state.current_participant].iloc[0]
            current_pub = PUBS_DATA['name'][int(participant['CurrentPub'])]
            
            # Create wheel
            colors = ['#FF4B4B', '#4CAF50', '#2196F3', '#FFC107', '#9C27B0', '#FF9800']
            num_sections = len(PUNISHMENTS)
            rotation = 360 / num_sections
            
            wheel_html = """
                <div class="wheel-container">
                    <div class="wheel-pointer"></div>
                    <div class="wheel spinning">
            """
            
            for i, (punishment, color) in enumerate(zip(PUNISHMENTS, colors * (num_sections // len(colors) + 1))):
                wheel_html += f"""
                    <div class="wheel-section" style="
                        background: {color};
                        transform: rotate({i * rotation}deg)">
                        {punishment}
                    </div>
                """
            
            wheel_html += "</div></div>"
            st.markdown(wheel_html, unsafe_allow_html=True)
            
            # Wait for animation
            with st.spinner(""):
                time.sleep(4)
            
            # Select and record punishment
            punishment = random.choice(PUNISHMENTS)
            new_punishment = pd.DataFrame([{
                'Time': datetime.now().strftime('%H:%M:%S'),
                'Name': st.session_state.current_participant,
                'Pub': current_pub,
                'Punishment': punishment
            }])
            punishments_df = pd.concat([punishments_df, new_punishment], ignore_index=True)
            
            # Update achievements
            participants_df = check_achievements(st.session_state.current_participant, participants_df, punishments_df)
            
            save_data(participants_df, punishments_df)
            
            st.snow()
            st.success(f"Your punishment is: {punishment}")
        else:
            # Show static wheel
            colors = ['#FF4B4B', '#4CAF50', '#2196F3', '#FFC107', '#9C27B0', '#FF9800']
            num_sections = len(PUNISHMENTS)
            rotation = 360 / num_sections
            
            wheel_html = """
                <div class="wheel-container">
                    <div class="wheel-pointer"></div>
                    <div class="wheel">
            """
            
            for i, (punishment, color) in enumerate(zip(PUNISHMENTS, colors * (num_sections // len(colors) + 1))):
                wheel_html += f"""
                    <div class="wheel-section" style="
                        background: {color};
                        transform: rotate({i * rotation}deg)">
                        {punishment}
                    </div>
                """
            
            wheel_html += "</div></div>"
            st.markdown(wheel_html, unsafe_allow_html=True)
    
    with col2:
        st.subheader("Recent Punishments")
        _, punishments_df = load_data()
        if not punishments_df.empty:
            recent = punishments_df.tail(5).sort_values('Time', ascending=False)
            st.dataframe(recent[['Time', 'Name', 'Punishment']], hide_index=True)

def show_achievements(name):
    """Display achievements"""
    participants_df = load_data()[0]
    participant = participants_df[participants_df['Name'] == name].iloc[0]
    earned_achievements = [] if pd.isna(participant['Achievements']) else participant['Achievements'].split(',')
    if earned_achievements == ['']:
        earned_achievements = []
    
    st.subheader("🏆 Your Achievements")
    
    categories = {
        "Progress": ['first_pub', 'halfway', 'finisher', 'rule_breaker'],
        "Challenges": ['dance_master', 'karaoke_king', 'silent_warrior', 'phone_free'],
        "Legendary": ['perfect_run', 'punishment_collector', 'speed_demon', 'golden_route']
    }
    
    for category, achievement_ids in categories.items():
        st.markdown(f"### {category}")
        
        # Show earned achievements
        earned_in_category = [ach for ach in achievement_ids if ach in earned_achievements]
        for ach_id in earned_in_category:
            ach = ACHIEVEMENTS[ach_id]
            st.markdown(f"""
                <div class="achievement">
                    <h3>{ach['name']} ✨</h3>
                    <p>{ach['desc']}</p>
                    <small>+{ach['points']} points</small>
                </div>
            """, unsafe_allow_html=True)
        
        # Show locked achievements
        locked_in_category = [ach for ach in achievement_ids if ach not in earned_achievements]
        for ach_id in locked_in_category:
            ach = ACHIEVEMENTS[ach_id]
            st.markdown(f"""
                <div class="locked-achievement">
                    <h3>🔒 {ach['name']}</h3>
                    <p>{ach['desc']}</p>
                    <small>+{ach['points']} points</small>
                </div>
            """, unsafe_allow_html=True)

def show_leaderboard():
    """Display leaderboard"""
    st.header("🏆 Leaderboard")
    
    participants_df, punishments_df = load_data()
    
    if not participants_df.empty:
        # Prepare leaderboard data
        display_data = []
        for _, row in participants_df.iterrows():
            completed_pubs = [] if pd.isna(row['CompletedPubs']) else row['CompletedPubs'].split(',')
            if completed_pubs == ['']:
                completed_pubs = []
            
            achievements = [] if pd.isna(row['Achievements']) else row['Achievements'].split(',')
            if achievements == ['']:
                achievements = []
            
            current_pub = int(row['CurrentPub'])
            current_pub_name = PUBS_DATA['name'][current_pub] if current_pub < 12 else 'Finished!'
            
            display_data.append({
                'Name': row['Name'],
                'Pubs Completed': len(completed_pubs),
                'Current Location': current_pub_name,
                'Points': int(row['Points']),
                'Achievements': len(achievements)
            })
        
        df = pd.DataFrame(display_data)
        df = df.sort_values(['Points', 'Pubs Completed'], ascending=[False, False])
        st.dataframe(df, use_container_width=True)
    
    if not punishments_df.empty:
        st.subheader("😈 Recent Punishments")
        recent = punishments_df.tail(5).sort_values('Time', ascending=False)
        st.dataframe(recent, use_container_width=True)

def main():
    st.title("🎄 Belfast 12 Pubs of Christmas 🍺")
    
    name_entry_modal()
    
    if st.session_state.current_participant:
        # Add refresh button in sidebar
        if st.sidebar.button("Refresh Data"):
            auto_refresh()
        
        # Main navigation
        tabs = st.tabs([
            "👥 Leaderboard",
            "📊 My Progress",
            "🗺️ Map",
            "🎯 Punishment Wheel",
            "🏆 Achievements"
        ])
        
        with tabs[0]:
            show_leaderboard()
        
        with tabs[1]:
            show_progress(st.session_state.current_participant)
        
        with tabs[2]:
            show_map()
        
        with tabs[3]:
            show_punishment_wheel()
        
        with tabs[4]:
            show_achievements(st.session_state.current_participant)

if __name__ == "__main__":
    main()
