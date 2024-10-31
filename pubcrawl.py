import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import random
import time
from datetime import datetime, timedelta
import json

# Page config with custom CSS
st.set_page_config(page_title="Belfast 12 Pubs of Christmas", page_icon="🍺", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .stProgress .st-bo { background-color: #ff4b4b; }
    .stProgress .st-bp { background-color: #28a745; }
    .pub-timer { font-size: 24px; font-weight: bold; color: #ff4b4b; }
    .badge { 
        padding: 10px;
        margin: 5px;
        border-radius: 50%;
        background: linear-gradient(45deg, #FFD700, #FFA500);
        width: 100px;
        height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        color: white;
        font-weight: bold;
    }
    .achievement {
        padding: 10px;
        margin: 5px;
        border-radius: 5px;
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
INITIAL_SESSION_STATE = {
    'start_time': None,
    'pub_times': {},
    'current_pub': 0,
    'completed_pubs': [],
    'punishment_history': [],
    'achievements': set(),
    'points': 0,
    'drinks_consumed': [],
    'selected_route': 'default',
    'group_members': [],
    'emergency_contact': None
}

for key, value in INITIAL_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

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
    ],
    'recommended_drinks': [
        "Guinness", "Irish Whiskey", "Christmas Cocktail", "Traditional Ale",
        "Mulled Wine", "Local Craft Beer", "Irish Coffee", "Hot Toddy",
        "Festive Shot", "Winter Warmer", "House Special", "Victory Pint"
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
    'speed_demon': {'name': 'Speed Demon', 'desc': 'Complete 3 pubs under 90 minutes', 'icon': '🏃'},
    'rule_master': {'name': 'Rule Master', 'desc': 'Follow all rules in 5 consecutive pubs', 'icon': '👑'},
    'safety_first': {'name': 'Safety First', 'desc': 'Take 3 water breaks', 'icon': '🚰'},
    'group_leader': {'name': 'Group Leader', 'desc': 'Keep group together for 6 pubs', 'icon': '👥'},
    'half_way_hero': {'name': 'Half Way Hero', 'desc': 'Complete 6 pubs', 'icon': '🏆'},
    'finish_line': {'name': 'Finish Line', 'desc': 'Complete all 12 pubs', 'icon': '🎉'},
    'designated_hero': {'name': 'Designated Hero', 'desc': 'Be the designated driver', 'icon': '🚗'}
}

POINTS_SYSTEM = {
    'pub_completion': 100,
    'rule_followed': 50,
    'quick_completion': 75,
    'group_intact': 25,
    'water_break': 20,
    'designated_driver': 150
}

# Helper Functions
def calculate_bac(weight_kg, gender, drinks, hours):
    """Calculate Blood Alcohol Content"""
    gender_constants = {'male': 0.68, 'female': 0.55, 'other': 0.615}
    r = gender_constants.get(gender, gender_constants['other'])
    alcohol_grams = sum(drink['alcohol_grams'] for drink in drinks)
    bac = ((alcohol_grams * 100) / (weight_kg * r)) - (0.015 * hours)
    return max(0, bac)

def get_drink_recommendation(current_bac, time_since_last):
    """Get drink spacing recommendation"""
    if current_bac > 0.08:
        return "🚫 Please take a break and drink water"
    elif current_bac > 0.05:
        return "⚠️ Consider waiting 30 minutes before next drink"
    elif time_since_last and time_since_last < timedelta(minutes=30):
        return "⏰ Consider spacing drinks further apart"
    return "✅ Safe to proceed with next drink"

def start_challenge():
    """Initialize the challenge"""
    if st.session_state.start_time is None:
        st.session_state.start_time = datetime.now()

def mark_pub_complete():
    """Mark current pub as completed"""
    if st.session_state.current_pub < 12:
        current_pub = PUBS_DATA['name'][st.session_state.current_pub]
        if current_pub not in st.session_state.completed_pubs:
            st.session_state.completed_pubs.append(current_pub)
            st.session_state.pub_times[current_pub] = {
                'completion_time': datetime.now(),
                'duration': datetime.now() - st.session_state.start_time
            }
            st.session_state.points += POINTS_SYSTEM['pub_completion']
            st.session_state.current_pub += 1
            check_achievements()

def reset_progress():
    """Reset all progress"""
    if st.button("Reset Progress", type="secondary"):
        confirm = st.checkbox("Are you sure? This will reset all progress!")
        if confirm:
            for key, value in INITIAL_SESSION_STATE.items():
                st.session_state[key] = value
            st.experimental_rerun()

def check_achievements():
    """Check and award achievements"""
    progress = len(st.session_state.completed_pubs)
    
    # Half Way Hero
    if progress >= 6 and 'half_way_hero' not in st.session_state.achievements:
        st.session_state.achievements.add('half_way_hero')
        st.session_state.points += 200
        st.success("🏆 Achievement Unlocked: Half Way Hero!")
    
    # Finish Line
    if progress == 12 and 'finish_line' not in st.session_state.achievements:
        st.session_state.achievements.add('finish_line')
        st.session_state.points += 500
        st.success("🎉 Achievement Unlocked: Finish Line!")
    
    # Speed Demon
    quick_completions = sum(1 for pub in st.session_state.pub_times.values() 
                          if pub['duration'].total_seconds() < 1800)
    if quick_completions >= 3 and 'speed_demon' not in st.session_state.achievements:
        st.session_state.achievements.add('speed_demon')
        st.session_state.points += 300
        st.success("🏃 Achievement Unlocked: Speed Demon!")

# Main Display Functions
def show_progress():
    """Display progress tracking interface"""
    st.header("Progress Tracker")
    
    # Start button and timer
    if st.session_state.start_time is None:
        st.button("Start Challenge", on_click=start_challenge, type="primary")
    else:
        elapsed = datetime.now() - st.session_state.start_time
        hours, remainder = divmod(elapsed.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        st.markdown(f"""
            <div class="pub-timer">
            Time Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}
            </div>
        """, unsafe_allow_html=True)
    
    # Progress metrics
    progress = len(st.session_state.completed_pubs)
    st.progress(progress/12)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pubs Completed", f"{progress}/12")
    with col2:
        st.metric("Pubs Remaining", f"{12-progress}")
    with col3:
        if progress > 0 and st.session_state.start_time:
            elapsed = datetime.now() - st.session_state.start_time
            avg_time = elapsed.seconds / progress / 60
            st.metric("Avg. Time per Pub", f"{avg_time:.1f} min")
    
    # Current pub information
    if st.session_state.current_pub < 12:
        current_pub = PUBS_DATA['name'][st.session_state.current_pub]
        current_rule = PUBS_DATA['rules'][st.session_state.current_pub]
        recommended_drink = PUBS_DATA['recommended_drinks'][st.session_state.current_pub]
        
        st.subheader(f"Current Pub: {current_pub}")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Rule: {current_rule}")
        with col2:
            st.success(f"Recommended Drink: {recommended_drink}")
        
        if st.button("Mark Current Pub as Complete", type="primary"):
            mark_pub_complete()
            st.experimental_rerun()
    else:
        st.success("🎉 Congratulations! You've completed the Belfast 12 Pubs of Christmas! 🎉")
        if st.session_state.start_time:
            total_time = datetime.now() - st.session_state.start_time
            st.info(f"Total Time: {total_time.seconds//3600} hours, {(total_time.seconds//60)%60} minutes")

def show_map():
    """Display interactive map"""
    st.header("Candy Cane Pub Route Map")
    
    m = folium.Map(
        location=[54.595733, -5.930294],
        zoom_start=15,
        tiles='CartoDB positron'
    )
    
    for i in range(12):
        is_completed = PUBS_DATA['name'][i] in st.session_state.completed_pubs
        is_current = i == st.session_state.current_pub
        
        if is_completed:
            color = 'green'
            icon = 'check'
        elif is_current:
            color = 'orange'
            icon = 'info-sign'
        else:
            color = 'red'
            icon = 'beer'
        
        popup_content = f"""
            <div style='width:200px'>
                <h4>{i+1}. {PUBS_DATA['name'][i]}</h4>
                <b>Rule:</b> {PUBS_DATA['rules'][i]}<br>
                <b>Drink:</b> {PUBS_DATA['recommended_drinks'][i]}<br>
                <b>Status:</b> {'Completed' if is_completed else 'Current' if is_current else 'Pending'}
            </div>
        """
        
        folium.Marker(
            [PUBS_DATA['latitude'][i], PUBS_DATA['longitude'][i]],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color=color, icon=icon, prefix='fa')
        ).add_to(m)
        
        if i > 0:
            points = [
                [PUBS_DATA['latitude'][i-1], PUBS_DATA['longitude'][i-1]],
                [PUBS_DATA['latitude'][i], PUBS_DATA['longitude'][i]]
            ]
            folium.PolyLine(
                points,
                weight=3,
                color='#FF4B4B',
                opacity=0.8,
                dash_array='10'
            ).add_to(m)
    
    folium_static(m)

def show_safety_dashboard():
    """Display safety features"""
    st.header("🛡️ Safety Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🧮 BAC Calculator")
        weight = st.number_input("Weight (kg)", min_value=40, max_value=200, value=70)
        gender = st.selectbox("Gender", options=['male', 'female', 'other'])
        
        drink_types = {
            'Beer (330ml, 5%)': 13,
            'Wine (175ml, 12%)': 17,
            'Spirit (25ml, 40%)': 8,
            'Cocktail (250ml, 10%)': 20
        }
        
        if st.button("Add Drink"):
            drink_choice = st.selectbox("Select drink", options=list(drink_types.keys()))
            st.session_state.drinks_consumed.append({
                'type': drink_choice,
                'time': datetime.now(),
                'alcohol_grams': drink_types[drink_choice]
            })
        
        if st.session_state.drinks_consumed:
            hours_drinking = (datetime.now() - st.session_state.drinks_consumed[0]['time']).total_seconds() / 3600
            current_bac = calculate_bac(weight, gender, st.session_state.drinks_consumed, hours_drinking)
            
            bac_color = 'red' if current_bac > 0.08 else 'orange' if current_bac > 0.05 else 'green'
            st.markdown(f"<h3 style='color: {bac_color}'>BAC: {current_bac:.3f}</h3>", unsafe_allow_html=True)
            
            recommendation = get_drink_recommendation(
                current_bac,
                datetime.now() - st.session_state.drinks_consumed[-1]['time']
            )
            st.info(recommendation)
    
    with col2:
        st.subheader("🚕 Taxi Booking")
        pickup_location = st.text_input("Pickup Location", 
                                      value=PUBS_DATA['name'][st.session_state.current_pub])
        destination = st.text_input("Destination")
        passengers = st.number_input("Number of Passengers", 1, 8, 4)
        
        if st.button("Book Taxi"):
            st.success("Taxi booking simulation - In a real app, this would connect to a taxi API")
            st.balloons()

def show_punishment_wheel():
    """Display punishment wheel interface"""
    st.header("Rule Breaker's Punishment Wheel")
    
    col1, col2 = st.columns([2,1])
    
    with col1:
        rule_breaker = st.text_input("Enter rule breaker's name:", "")
        current_pub = PUBS_DATA['name'][st.session_state.current_pub] if st.session_state.current_pub < 12 else 'Completed'
        
        if st.button("Spin the Wheel", type="primary"):
            punishment = random.choice(PUNISHMENTS)
            
            with st.spinner("The wheel is spinning..."):
                time.sleep(1.5)
            
            st.snow()
            st.success(f"🎯 {rule_breaker if rule_breaker else 'Rule Breaker'} must: {punishment}")
            
            st.session_state.punishment_history.append({
                'Time': datetime.now().strftime('%H:%M:%S'),
                'Name': rule_breaker if rule_breaker else 'Anonymous',
                'Pub': current_pub,
                'Punishment': punishment
            })
    
    with col2:
        if st.session_state.punishment_history:
            st.subheader("Punishment Stats")
            total_punishments = len(st.session_state.punishment_history)
            st.metric("Total Punishments", total_punishments)
            
            if total_punishments > 0:
                top_offender = pd.DataFrame(st.session_state.punishment_history)['Name'].mode().iloc[0]
                st.metric("Top Rule Breaker", top_offender)
    
    if st.session_state.punishment_history:
        st.subheader("Punishment History")
        history_df = pd.DataFrame(st.session_state.punishment_history)
        st.dataframe(history_df, use_container_width=True)
        
        if st.button("Clear History"):
            st.session_state.punishment_history = []
            st.experimental_rerun()

def show_achievements():
    """Display achievements and points"""
    st.header("🏆 Achievements & Points")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric("Total Points", st.session_state.points)
        st.progress(min(1.0, len(st.session_state.achievements) / len(ACHIEVEMENTS)))
        
    with col2:
        st.subheader("Earned Achievements")
        achieved = st.session_state.achievements
        
        for ach_id, ach_data in ACHIEVEMENTS.items():
            if ach_id in achieved:
                st.markdown(f"""
                    <div class="achievement">
                        {ach_data['icon']} {ach_data['name']}<br>
                        <small>{ach_data['desc']}</small>
                    </div>
                """, unsafe_allow_html=True)

def main():
    """Main application"""
    st.title("🎄 Belfast 12 Pubs of Christmas 🍺")
    st.markdown("*The Ultimate Christmas Pub Crawl Experience*")
    
    tabs = st.tabs([
        "📊 Progress",
        "🗺️ Map",
        "🎯 Punishment Wheel",
        "🛡️ Safety",
        "🏆 Achievements"
    ])
    
    with tabs[0]:
        show_progress()
        reset_progress()
    
    with tabs[1]:
        show_map()
    
    with tabs[2]:
        show_punishment_wheel()
    
    with tabs[3]:
        show_safety_dashboard()
    
    with tabs[4]:
        show_achievements()

if __name__ == "__main__":
    main()
