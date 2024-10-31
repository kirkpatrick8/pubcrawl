import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
from datetime import datetime
from github import Github, GithubException
import io

# Page configuration
st.set_page_config(page_title="Belfast 12 Pubs of Christmas", page_icon="🍺", layout="wide")

# Custom CSS for styling
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

# Constants for pubs and rules
PUBS_DATA = {
    'name': [
        "Lavery's", "The Points", "Sweet Afton", "Kelly's Cellars",
        "Whites Tavern", "The Deer's Head", "The John Hewitt", "Duke of York",
        "The Harp Bar", "The Dirty Onion", "Thirsty Goat", "Ulster Sports Club"
    ],
    'latitude': [
        54.589539, 54.591556, 54.595067, 54.599553, 54.600033, 
        54.601439, 54.601928, 54.601803, 54.602000, 54.601556, 
        54.601308, 54.600733
    ],
    'longitude': [
        -5.934469, -5.933333, -5.932894, -5.932236, -5.928497, 
        -5.930294, -5.928617, -5.927442, -5.927058, -5.926673, 
        -5.926417, -5.925219
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
        
        return participants_df, punishments_df
    except Exception as e:
        st.sidebar.error(f"Error loading data: {e}")
        # Return empty DataFrames if files don't exist
        participants_df = pd.DataFrame(columns=['Name', 'CurrentPub', 'CompletedPubs', 'Points'])
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

# UI and Logic Functions
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
                        'Points': 0
                    }])
                    participants_df = pd.concat([participants_df, new_participant], ignore_index=True)
                    save_data(participants_df, load_data()[1])
                st.session_state.current_participant = name
                st.rerun()

def show_progress(name):
    """Show progress for current participant"""
    participants_df, _ = load_data()
    
    # Check if participant exists, if not create new entry
    if len(participants_df[participants_df['Name'] == name]) == 0:
        new_participant = {
            'Name': name,
            'CurrentPub': 0,
            'CompletedPubs': '',
            'Points': 0
        }
        participants_df = pd.concat([participants_df, pd.DataFrame([new_participant])], ignore_index=True)
        save_data(participants_df, load_data()[1])
    
    # Now safely get participant data
    participant = participants_df[participants_df['Name'] == name].iloc[0]
    
    st.header(f"Progress Tracker for {name}")
    
    # Progress calculations
    completed_pubs_str = participant['CompletedPubs'] if isinstance(participant['CompletedPubs'], str) else ''
    completed_pubs = completed_pubs_str.split(',') if completed_pubs_str else []
    
    progress = len(completed_pubs)
    current_pub = int(participant['CurrentPub'])
    
    # Display progress
    st.progress(progress / 12)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pubs Completed", f"{progress}/12")
    with col2:
        st.metric("Pubs Remaining", f"{12 - progress}")
    with col3:
        st.metric("Points", int(participant['Points']))
    
    # Current pub information
    if current_pub < 12:
        current_pub_name = PUBS_DATA['name'][current_pub]
        current_rule = PUBS_DATA['rules'][current_pub]
        
        st.subheader(f"Current Pub: {current_pub_name}")
        st.info(f"Rule: {current_rule}")
        
        if st.button("Mark Current Pub as Complete", type="primary"):
            st.write(f"Marking pub complete for {name}...")
            mark_pub_complete(name)
    else:
        st.success("🎉 Congratulations! You've completed the Belfast 12 Pubs of Christmas! 🎉")

def mark_pub_complete(name):
    """Mark current pub as completed"""
    participants_df, punishments_df = load_data()
    
    # Find the participant by name
    matched_participants = participants_df[participants_df['Name'] == name]

    if not matched_participants.empty:  # Check if there are any matches
        participant_idx = matched_participants.index[0]
        
        current_pub = int(participants_df.loc[participant_idx, 'CurrentPub'])
        completed_pubs_str = participants_df.loc[participant_idx, 'CompletedPubs'] if isinstance(participants_df.loc[participant_idx, 'CompletedPubs'], str) else ''
        
        completed_pubs = completed_pubs_str.split(',') if completed_pubs_str else []
        completed_pubs.append(PUBS_DATA['name'][current_pub])
        
        participants_df.at[participant_idx, 'CompletedPubs'] = ','.join(completed_pubs)
        participants_df.at[participant_idx, 'CurrentPub'] = current_pub + 1
        
        # Random punishment assignment
        punishment = random.choice(PUNISHMENTS)
        punishments_df = punishments_df.append({
            'Time': datetime.now(),
            'Name': name,
            'Pub': PUBS_DATA['name'][current_pub],
            'Punishment': punishment
        }, ignore_index=True)
        
        print(f"Recording punishment: {punishment} for {name} at {PUBS_DATA['name'][current_pub]}")

        save_data(participants_df, punishments_df)
        st.success(f"Marked {PUBS_DATA['name'][current_pub]} as complete and assigned punishment: {punishment}")

def show_map():
    """Display map of pubs"""
    map_center = [54.596, -5.930]
    m = folium.Map(location=map_center, zoom_start=14)
    
    for i in range(len(PUBS_DATA['name'])):
        folium.Marker(
            location=[PUBS_DATA['latitude'][i], PUBS_DATA['longitude'][i]],
            popup=PUBS_DATA['name'][i],
            icon=folium.Icon(color='blue')
        ).add_to(m)

    st_folium(m)

# Main Application Logic
name_entry_modal()

if st.session_state.current_participant:
    name = st.session_state.current_participant
    show_progress(name)
    show_map()
