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

# Page config with custom CSS
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
REPO_NAME = "kirkpatrick8/pubcrawl"  # Your specific repo
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

# Load and save functions
@st.cache_data(ttl=60)
def load_data():
    """Load data from GitHub"""
    try:
        participants_file = "participants.csv"
        punishments_file = "punishments.csv"
        
        # Load participants
        content = repo.get_contents(participants_file, ref=BRANCH_NAME)
        participants_df = pd.read_csv(io.StringIO(content.decoded_content.decode()))
        
        # Load punishments
        content = repo.get_contents(punishments_file, ref=BRANCH_NAME)
        punishments_df = pd.read_csv(io.StringIO(content.decoded_content.decode()))
        
        # Ensure achievements column exists
        if 'Achievements' not in participants_df.columns:
            participants_df['Achievements'] = ''
        
        return participants_df, punishments_df
    except Exception as e:
        st.sidebar.error(f"Error loading data: {e}")
        # Return empty DataFrames if files don't exist
        participants_df = pd.DataFrame(columns=['Name', 'CurrentPub', 'CompletedPubs', 'Points', 'Achievements'])
        punishments_df = pd.DataFrame(columns=['Time', 'Name', 'Pub', 'Punishment'])
        return participants_df, punishments_df

def save_data(participants_df, punishments_df):
    """Save data to GitHub"""
    try:
        # Save participants
        participants_content = participants_df.to_csv(index=False)
        try:
            contents = repo.get_contents("participants.csv", ref=BRANCH_NAME)
            repo.update_file(
                "participants.csv",
                f"Update participants - {datetime.now()}",
                participants_content,
                contents.sha,
                branch=BRANCH_NAME
            )
        except GithubException:
            repo.create_file(
                "participants.csv",
                f"Create participants file - {datetime.now()}",
                participants_content,
                branch=BRANCH_NAME
            )
        
        # Save punishments
        punishments_content = punishments_df.to_csv(index=False)
        try:
            contents = repo.get_contents("punishments.csv", ref=BRANCH_NAME)
            repo.update_file(
                "punishments.csv",
                f"Update punishments - {datetime.now()}",
                punishments_content,
                contents.sha,
                branch=BRANCH_NAME
            )
        except GithubException:
            repo.create_file(
                "punishments.csv",
                f"Create punishments file - {datetime.now()}",
                punishments_content,
                branch=BRANCH_NAME
            )
    except Exception as e:
        st.sidebar.error(f"Error saving data: {e}")

def name_entry_modal():
    """Display modal for name entry"""
    if 'current_participant' not in st.session_state:
        st.session_state.current_participant = None
        
    if st.session_state.current_participant is None:
        with st.container():
            st.markdown("### Welcome to the Belfast 12 Pubs of Christmas! 🎄")
            name = st.text_input("Enter your name to begin:")
            if name:
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
                st.session_state.current_participant = name
                st.rerun()

def check_achievements(participants_df, participant_idx):
    """Check and update achievements for a participant"""
    current_participant = participants_df.iloc[participant_idx]
    achievements = current_participant['Achievements'].split(',') if current_participant['Achievements'] else []

    # Example achievement checks
    if len(current_participant['CompletedPubs'].split(',')) >= 3 and "3 Pubs Completed" not in achievements:
        achievements.append("3 Pubs Completed")
        st.success("🎉 Achievement Unlocked: 3 Pubs Completed! 🎉")

    if len(current_participant['CompletedPubs'].split(',')) >= 6 and "6 Pubs Completed" not in achievements:
        achievements.append("6 Pubs Completed")
        st.success("🎉 Achievement Unlocked: 6 Pubs Completed! 🎉")

    if len(current_participant['CompletedPubs'].split(',')) >= 12 and "All Pubs Completed" not in achievements:
        achievements.append("All Pubs Completed")
        st.success("🎉 Achievement Unlocked: All Pubs Completed! 🎉")
    
    participants_df.at[participant_idx, 'Achievements'] = ','.join(achievements)

def show_progress(name):
    """Show progress for current participant"""
    participants_df, _ = load_data()
    participant = participants_df[participants_df['Name'] == name].iloc[0]
    
    st.header(f"Progress Tracker for {name}")
    
    # Progress calculations
    completed_pubs = participant['CompletedPubs'].split(',') if participant['CompletedPubs'] else []
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
        st.success("🎉 You've completed all pubs! 🎉")

def mark_pub_complete(name):
    """Mark current pub as completed and update achievements"""
    participants_df, punishments_df = load_data()
    participant_idx = participants_df[participants_df['Name'] == name].index[0]
    
    current_pub = int(participants_df.loc[participant_idx, 'CurrentPub'])
    completed_pubs = participants_df.loc[participant_idx, 'CompletedPubs'].split(',') if participants_df.loc[participant_idx, 'CompletedPubs'] else []
    
    if current_pub < 12:
        completed_pubs.append(PUBS_DATA['name'][current_pub])
        participants_df.loc[participant_idx, 'CompletedPubs'] = ','.join(completed_pubs)
        participants_df.loc[participant_idx, 'CurrentPub'] = current_pub + 1
        participants_df.loc[participant_idx, 'Points'] += 100
        
        # Check for achievements after updating
        check_achievements(participants_df, participant_idx)

        save_data(participants_df, punishments_df)
        st.rerun()

def show_leaderboard():
    """Display leaderboard"""
    st.header("🏆 Group Progress")
    
    participants_df, punishments_df = load_data()
    
    if not participants_df.empty:
        # Process data for display
        display_data = []
        for _, row in participants_df.iterrows():
            completed_count = len(row['CompletedPubs'].split(',')) if row['CompletedPubs'] else 0
            current_pub = PUBS_DATA['name'][int(row['CurrentPub'])] if int(row['CurrentPub']) < 12 else 'Finished'
            
            display_data.append({
                'Name': row['Name'],
                'Pubs Completed': completed_count,
                'Current Pub': current_pub,
                'Points': int(row['Points']),
                'Achievements': row['Achievements']
            })
        
        df = pd.DataFrame(display_data)
        df = df.sort_values(['Points', 'Pubs Completed'], ascending=[False, False])
        st.dataframe(df, use_container_width=True)
    
    # Show punishment history
    if not punishments_df.empty:
        st.subheader("😈 Punishment History")
        st.dataframe(punishments_df, use_container_width=True)

# Main app logic
name_entry_modal()

if st.session_state.current_participant:
    show_progress(st.session_state.current_participant)
    show_leaderboard()
