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

# Custom CSS
st.markdown("""
    <style>
    .stProgress .st-bo { background-color: #ff4b4b; }
    .stProgress .st-bp { background-color: #28a745; }
    .pub-timer { font-size: 24px; font-weight: bold; color: #ff4b4b; }
    .achievement {
        padding: 10px;
        margin: 5px;
        border-radius: 5px;
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
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

ACHIEVEMENTS = {
    'first_pub': {'name': 'First Timer', 'desc': 'Complete your first pub', 'points': 100},
    'halfway': {'name': 'Halfway Hero', 'desc': 'Complete 6 pubs', 'points': 250},
    'finisher': {'name': 'Challenge Champion', 'desc': 'Complete all 12 pubs', 'points': 500},
    'rule_breaker': {'name': 'Rule Breaker', 'desc': 'Get punished 3 times', 'points': 150}
}

# Load and save functions
@st.cache_data(ttl=60)
def load_data():
    """Load data from GitHub"""
    try:
        participants_file = "participants.csv"
        punishments_file = "punishments.csv"
        
        try:
            # Load participants
            content = repo.get_contents(participants_file, ref=BRANCH_NAME)
            participants_df = pd.read_csv(io.StringIO(content.decoded_content.decode()))
        except:
            # Create empty participants DataFrame if file doesn't exist
            participants_df = pd.DataFrame(columns=['Name', 'CurrentPub', 'CompletedPubs', 'Points', 'Achievements'])
        
        try:
            # Load punishments
            content = repo.get_contents(punishments_file, ref=BRANCH_NAME)
            punishments_df = pd.read_csv(io.StringIO(content.decoded_content.decode()))
        except:
            # Create empty punishments DataFrame if file doesn't exist
            punishments_df = pd.DataFrame(columns=['Time', 'Name', 'Pub', 'Punishment'])
        
        return participants_df, punishments_df
    except Exception as e:
        st.sidebar.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=['Name', 'CurrentPub', 'CompletedPubs', 'Points', 'Achievements']), \
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

def check_achievements(name, participants_df):
    """Check and award achievements"""
    participant = participants_df[participants_df['Name'] == name].iloc[0]
    achievements = [] if pd.isna(participant['Achievements']) else participant['Achievements'].split(',')
    completed_pubs = [] if pd.isna(participant['CompletedPubs']) else participant['CompletedPubs'].split(',')
    completed_count = len(completed_pubs) if completed_pubs != [''] else 0
    
    # First pub achievement
    if completed_count >= 1 and 'first_pub' not in achievements:
        achievements.append('first_pub')
        st.balloons()
        st.success(f"🏆 Achievement Unlocked: {ACHIEVEMENTS['first_pub']['name']}!")
    
    # Halfway achievement
    if completed_count >= 6 and 'halfway' not in achievements:
        achievements.append('halfway')
        st.balloons()
        st.success(f"🏆 Achievement Unlocked: {ACHIEVEMENTS['halfway']['name']}!")
    
    # Finisher achievement
    if completed_count == 12 and 'finisher' not in achievements:
        achievements.append('finisher')
        st.balloons()
        st.success(f"🏆 Achievement Unlocked: {ACHIEVEMENTS['finisher']['name']}!")
    
    # Update achievements in DataFrame
    participants_df.loc[participants_df['Name'] == name, 'Achievements'] = ','.join(achievements)
    return participants_df

def name_entry_modal():
    """Display name entry modal"""
    if 'current_participant' not in st.session_state:
        st.session_state.current_participant = None
        
    if st.session_state.current_participant is None:
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
                    'Achievements': ''
                }])
                participants_df = pd.concat([participants_df, new_participant], ignore_index=True)
                save_data(participants_df, punishments_df)
            st.session_state.current_participant = name
            st.rerun()

def show_progress(name):
    """Show progress for current participant"""
    participants_df, _ = load_data()
    
    if name not in participants_df['Name'].values:
        new_participant = pd.DataFrame([{
            'Name': name,
            'CurrentPub': 0,
            'CompletedPubs': '',
            'Points': 0,
            'Achievements': ''
        }])
        participants_df = pd.concat([participants_df, new_participant], ignore_index=True)
        save_data(participants_df, load_data()[1])
    
    participant = participants_df[participants_df['Name'] == name].iloc[0]
    
    st.header(f"Progress Tracker for {name}")
    
    # Progress calculations
    completed_pubs = [] if pd.isna(participant['CompletedPubs']) else participant['CompletedPubs'].split(',')
    if completed_pubs == ['']:
        completed_pubs = []
    progress = len(completed_pubs)
    current_pub = int(participant['CurrentPub'])
    
    # Display progress
    st.progress(progress/12)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pubs Completed", f"{progress}/12")
    with col2:
        st.metric("Pubs Remaining", f"{12-progress}")
    with col3:
        st.metric("Points", int(participant['Points']))
    
    # Current pub information
    if current_pub < 12:
        current_pub_name = PUBS_DATA['name'][current_pub]
        current_rule = PUBS_DATA['rules'][current_pub]
        
        st.subheader(f"Current Pub: {current_pub_name}")
        st.info(f"Rule: {current_rule}")
        
        if st.button("Mark Current Pub as Complete", type="primary"):
            mark_pub_complete(name)
    else:
        st.success("🎉 Congratulations! You've completed the Belfast 12 Pubs of Christmas! 🎉")

def mark_pub_complete(name):
    """Mark current pub as completed"""
    participants_df, punishments_df = load_data()
    participant_idx = participants_df[participants_df['Name'] == name].index[0]
    
    current_pub = int(participants_df.loc[participant_idx, 'CurrentPub'])
    completed_pubs = [] if pd.isna(participants_df.loc[participant_idx, 'CompletedPubs']) else \
                    participants_df.loc[participant_idx, 'CompletedPubs'].split(',')
    
    if completed_pubs == ['']:
        completed_pubs = []
        
    if current_pub < 12:
        completed_pubs.append(PUBS_DATA['name'][current_pub])
        participants_df.loc[participant_idx, 'CompletedPubs'] = ','.join(completed_pubs)
        participants_df.loc[participant_idx, 'CurrentPub'] = current_pub + 1
        participants_df.loc[participant_idx, 'Points'] += 100
        
        # Check achievements
        participants_df = check_achievements(name, participants_df)
        
        save_data(participants_df, punishments_df)
        st.rerun()

def show_map():
    """Display interactive map"""
    st.header("🗺️ Pub Route Map")
    
    participants_df, _ = load_data()
    participant = participants_df[participants_df['Name'] == st.session_state.current_participant].iloc[0]
    completed_pubs = [] if pd.isna(participant['CompletedPubs']) else participant['CompletedPubs'].split(',')
    if completed_pubs == ['']:
        completed_pubs = []
    
    m = folium.Map(location=[54.595733, -5.930294], zoom_start=15)
    
    for i, (name, lat, lon) in enumerate(zip(
        PUBS_DATA['name'],
        PUBS_DATA['latitude'],
        PUBS_DATA['longitude']
    )):
        # Determine marker color
        if name in completed_pubs:
            color = 'green'
            icon = 'check'
        elif i == int(participant['CurrentPub']):
            color = 'orange'
            icon = 'info-sign'
        else:
            color = 'red'
            icon = 'beer'
        
        popup_text = f"""
            <div style='width:200px'>
                <h4>{i+1}. {name}</h4>
                <b>Rule:</b> {PUBS_DATA['rules'][i]}<br>
                <b>Status:</b> {'Completed' if name in completed_pubs else 'Current' if i == int(participant['CurrentPub']) else 'Pending'}
            </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color=color, icon=icon, prefix='fa')
        ).add_to(m)
        
        if i > 0:
            points = [
                [PUBS_DATA['latitude'][i-1], PUBS_DATA['longitude'][i-1]],
                [lat, lon]
            ]
            folium.PolyLine(points, weight=2, color='blue', opacity=0.8).add_to(m)
    
    st_folium(m)

def show_punishment_wheel():
    """Display punishment wheel"""
    st.header("😈 Rule Breaker's Punishment Wheel")
    
    if st.button("Spin the Wheel", type="primary"):
        participants_df, punishments_df = load_data()
        participant = participants_df[participants_df['Name'] == st.session_state.current_participant].iloc[0]
        current_pub = PUBS_DATA['name'][int(participant['CurrentPub'])]
        
        with st.spinner("The wheel is spinning..."):
            time.sleep(1.5)
        
        punishment = random.choice(PUNISHMENTS)
        
        # Record punishment
        new_punishment = pd.DataFrame([{
            'Time': datetime.now().strftime('%H:%M:%S'),
            'Name': st.session_state.current_participant,
            'Pub': current_pub,
            'Punishment': punishment
        }])
        punishments_df = pd.concat([punishments_df, new_punishment], ignore_index=True)
        
        # Check rule breaker achievement
        if len(punishments_df[punishments_df['Name'] == st.session_state.current_participant]) >= 3:
            achievements = [] if pd.isna(participant['Achievements']) else participant['Achievements'].split(',')
            if 'rule_breaker' not in achievements:
                achievements.append('rule_breaker')
                participants_df.loc[participants_df['Name'] == st.session_state.current_participant, 'Achievements'] = ','.join(achievements)
                st.balloons()
                st.success(f"🏆 Achievement Unlocked: {ACHIEVEMENTS['rule_breaker']['name']}!")
        
        save_data(participants_df, punishments_df)
        
        st.snow()
        st.success(f"Your punishment is: {punishment}")

def show_leaderboard():
    """Display leaderboard"""
    st.header("🏆 Leaderboard")
    
    participants_df, punishments_df = load_data()
    
    if not participants_df.empty:
        # Process data for display
        display_data = []
        for _, row in participants_df.iterrows():
            completed_count = len(row['CompletedPubs'].split(',')) if not pd.isna(row['CompletedPubs']) and row['CompletedPubs'] != '' else 0
            achievements_count = len(row['Achievements'].split(',')) if not pd.isna(row['Achievements']) and row['Achievements'] != '' else 0
            
            display_data.append({
                'Name': row['Name'],
                'Pubs Completed': completed_count,
                'Points': int(row['Points']),
                'Achievements': achievements_count
            })
        
        df = pd.DataFrame(display_data)
        df = df.sort_values(['Points', 'Pubs Completed'], ascending=[False, False])
        st.dataframe(df, use_container_width=True)
    
    # Show punishment history
    if not punishments_df.empty:
        st.subheader("😈 Punishment History")
        st.dataframe(punishments_df, use_container_width=True)

def show_achievements(name):
    """Display achievements for a participant"""
    participants_df = load_data()[0]
    participant = participants_df[participants_df['Name'] == name].iloc[0]
    achievements = [] if pd.isna(participant['Achievements']) else participant['Achievements'].split(',')
    
    st.subheader("🏆 Your Achievements")
    
    if achievements and achievements != ['']:
        for ach_id in achievements:
            ach = ACHIEVEMENTS[ach_id]
            st.markdown(f"""
                <div class="achievement">
                    <h3>{ach['name']}</h3>
                    <p>{ach['desc']}</p>
                    <small>+{ach['points']} points</small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Complete challenges to earn achievements!")

def main():
    st.title("🎄 Belfast 12 Pubs of Christmas 🍺")
    
    # Show name entry modal
    name_entry_modal()
    
    if st.session_state.current_participant:
        # Add refresh button in sidebar
        if st.sidebar.button("Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
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
