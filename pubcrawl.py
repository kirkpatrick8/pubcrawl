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
GITHUB_TOKEN = st.secrets["Pubcrawl"]["GITHUB_TOKEN"]  # Updated
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
    participant = participants_df[participants_df['Name'] == name].iloc[0]
    
    st.header(f"Progress Tracker for {name}")
    
    # Progress calculations
    completed_pubs = participant['CompletedPubs'].split(',') if isinstance(participant['CompletedPubs'], str) else []
    progress = len(completed_pubs)
    current_pub = int(participant['CurrentPub'])
    
    # Display progress
    st.progress(progress/12)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Completed Pubs", progress, "12")
    
    with col2:
        st.metric("Current Pub", PUBS_DATA['name'][current_pub] if current_pub < len(PUBS_DATA['name']) else "N/A")

def show_leaderboard():
    """Display leaderboard for participants"""
    participants_df, _ = load_data()
    
    # Process data for display
    display_data = []
    for _, row in participants_df.iterrows():
        completed_count = len(row['CompletedPubs'].split(',')) if isinstance(row['CompletedPubs'], str) else 0
        current_pub = PUBS_DATA['name'][int(row['CurrentPub'])] if row['CurrentPub'] is not None else "N/A"
        
        display_data.append({
            "Name": row['Name'],
            "Completed Pubs": completed_count,
            "Current Pub": current_pub,
            "Points": int(row['Points'])
        })
    
    # Display leaderboard
    leaderboard_df = pd.DataFrame(display_data)
    st.write(leaderboard_df)

def show_map():
    """Display a map with pub locations"""
    # Create a base map
    base_map = folium.Map(location=[54.589539, -5.934469], zoom_start=14)

    # Add markers for each pub
    for name, lat, lon in zip(PUBS_DATA['name'], PUBS_DATA['latitude'], PUBS_DATA['longitude']):
        folium.Marker(
            location=[lat, lon],
            popup=name,
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(base_map)

    # Render the map in Streamlit
    st_folium(base_map, width=700)

# Define functions for Rules, Punishments, and Safety Tips
def show_rules():
    """Display the rules"""
    st.markdown("### Rules")
    for rule in PUBS_DATA['rules']:
        st.write(f"- {rule}")

def show_punishments():
    """Display the punishments"""
    st.markdown("### Punishments")
    st.write("1. Example Punishment 1")
    st.write("2. Example Punishment 2")

def show_safety_tips():
    """Display safety tips"""
    st.markdown("### Safety Tips")
    st.write("1. Stay hydrated.")
    st.write("2. Have a buddy system.")

# Main script logic
if __name__ == "__main__":
    name_entry_modal()
    
    if st.session_state.current_participant:
        st.sidebar.title("Options")
        st.sidebar.button("Reset Progress", on_click=lambda: reset_progress(st.session_state.current_participant))
        
        # Show tabs for the different sections
        tabs = st.tabs(["Maps", "Rules", "Punishments", "Safety Tips", "Leaderboard"])

        with tabs[0]:
            show_map()  # Your existing map function

        with tabs[1]:
            show_rules()  # Define this function to display the rules

        with tabs[2]:
            show_punishments()  # Define this function to display punishments

        with tabs[3]:
            show_safety_tips()  # Define this function to display safety tips

        with tabs[4]:
            show_leaderboard()  # Your existing leaderboard function
