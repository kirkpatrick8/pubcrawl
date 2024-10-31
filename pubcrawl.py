import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import random
import time
from datetime import datetime, timedelta
import json
import requests
import polyline
import math

# Page config with custom CSS
st.set_page_config(page_title="Belfast 12 Pubs of Christmas", page_icon="🍺", layout="wide")

# Custom CSS with additional styling for badges and achievements
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

# Initialize extended session state
INITIAL_SESSION_STATE = {
    'start_time': None,
    'pub_times': {},
    'current_pub': 0,
    'completed_pubs': [],
    'punishment_history': [],
    'achievements': set(),
    'points': 0,
    'drinks_consumed': [],
    'routes': {},
    'selected_route': 'default',
    'group_members': [],
    'emergency_contact': None
}

for key, value in INITIAL_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Constants and Configuration
POINTS_SYSTEM = {
    'pub_completion': 100,
    'rule_followed': 50,
    'quick_completion': 75,  # Under 30 minutes
    'group_intact': 25,     # Everyone arrives together
    'water_break': 20,      # Taking water breaks
    'designated_driver': 150
}

ACHIEVEMENTS = {
    'speed_demon': {'name': 'Speed Demon', 'desc': 'Complete 3 pubs under 90 minutes', 'icon': '🏃'},
    'rule_master': {'name': 'Rule Master', 'desc': 'Follow all rules in 5 consecutive pubs', 'icon': '👑'},
    'safety_first': {'name': 'Safety First', 'desc': 'Take 3 water breaks', 'icon': '🚰'},
    'group_leader': {'name': 'Group Leader', 'desc': 'Keep group together for 6 pubs', 'icon': '👥'},
    'half_way_hero': {'name': 'Half Way Hero', 'desc': 'Complete 6 pubs', 'icon': '🏆'},
    'finish_line': {'name': 'Finish Line', 'desc': 'Complete all 12 pubs', 'icon': '🎉'},
    'designated_hero': {'name': 'Designated Hero', 'desc': 'Be the designated driver', 'icon': '🚗'}
}

# Enhanced pub data with multiple routes
ROUTES = {
    'default': {
        'name': 'Classic Route',
        'description': 'Traditional route through Belfast',
        'color': '#FF4B4B'
    },
    'alternative_1': {
        'name': 'Cathedral Quarter Focus',
        'description': 'More emphasis on Cathedral Quarter pubs',
        'color': '#4CAF50'
    },
    'alternative_2': {
        'name': 'Quick Route',
        'description': 'Optimized for shortest walking distance',
        'color': '#2196F3'
    }
}

# BAC calculation constants
GENDER_CONSTANTS = {
    'male': 0.68,
    'female': 0.55,
    'other': 0.615  # Average of male and female
}

def calculate_bac(weight_kg, gender, drinks, hours):
    """Calculate Blood Alcohol Content"""
    r = GENDER_CONSTANTS.get(gender, GENDER_CONSTANTS['other'])
    alcohol_grams = sum(drink['alcohol_grams'] for drink in drinks)
    bac = ((alcohol_grams * 100) / (weight_kg * r)) - (0.015 * hours)
    return max(0, bac)

def get_drink_recommendation(current_bac, time_since_last):
    """Get drink spacing recommendation based on BAC and time"""
    if current_bac > 0.08:
        return "🚫 Please take a break and drink water"
    elif current_bac > 0.05:
        return "⚠️ Consider waiting 30 minutes before next drink"
    elif time_since_last and time_since_last < timedelta(minutes=30):
        return "⏰ Consider spacing drinks further apart"
    return "✅ Safe to proceed with next drink"

def get_walking_directions(start_coords, end_coords):
    """Get walking directions between two points using OpenStreetMap"""
    base_url = "https://router.project-osrm.org/route/v1/walking"
    url = f"{base_url}/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}"
    params = {
        "overview": "full",
        "steps": "true",
        "annotations": "true"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data["code"] == "Ok":
            route = data["routes"][0]
            steps = []
            for step in route["legs"][0]["steps"]:
                steps.append({
                    "instruction": step["maneuver"]["instruction"],
                    "distance": step["distance"],
                    "duration": step["duration"]
                })
            return {
                "steps": steps,
                "total_distance": route["distance"],
                "total_duration": route["duration"],
                "geometry": route["geometry"]
            }
    except Exception as e:
        st.error(f"Error fetching directions: {e}")
    return None

class AchievementSystem:
    @staticmethod
    def check_achievements():
        """Check and award achievements"""
        achievements = []
        
        # Speed Demon
        quick_completions = sum(1 for pub, time in st.session_state.pub_times.items() 
                              if time['duration'] < timedelta(minutes=30))
        if quick_completions >= 3:
            achievements.append('speed_demon')
        
        # Half Way Hero
        if len(st.session_state.completed_pubs) >= 6:
            achievements.append('half_way_hero')
        
        # Finish Line
        if len(st.session_state.completed_pubs) == 12:
            achievements.append('finish_line')
        
        # Add achievements and points
        for achievement in achievements:
            if achievement not in st.session_state.achievements:
                st.session_state.achievements.add(achievement)
                st.session_state.points += 200
                st.success(f"🏆 New Achievement: {ACHIEVEMENTS[achievement]['name']}!")

def show_navigation():
    st.header("📍 Navigation")
    
    # Route selection
    route = st.selectbox(
        "Select Route",
        options=list(ROUTES.keys()),
        format_func=lambda x: ROUTES[x]['name'],
        key='selected_route'
    )
    
    st.write(ROUTES[route]['description'])
    
    if st.session_state.current_pub < 12:
        current_idx = st.session_state.current_pub
        next_idx = current_idx + 1
        
        if next_idx < 12:
            current_coords = (PUBS_DATA['latitude'][current_idx], PUBS_DATA['longitude'][current_idx])
            next_coords = (PUBS_DATA['latitude'][next_idx], PUBS_DATA['longitude'][next_idx])
            
            directions = get_walking_directions(current_coords, next_coords)
            
            if directions:
                st.subheader("🚶‍♂️ Walking Directions to Next Pub")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Distance", f"{directions['total_distance']:.0f}m")
                with col2:
                    st.metric("Est. Walking Time", f"{directions['total_duration']//60:.0f}min")
                
                st.subheader("Step-by-Step Directions")
                for i, step in enumerate(directions['steps'], 1):
                    st.write(f"{i}. {step['instruction']} ({step['distance']:.0f}m)")

def show_safety_dashboard():
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

def show_achievements():
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
    st.title("🎄 Belfast 12 Pubs of Christmas 🍺")
    st.markdown("*The Ultimate Christmas Pub Crawl Experience*")
    
    tabs = st.tabs([
        "📊 Progress",
        "🗺️ Map",
        "📍 Navigation",
        "🎯 Challenges",
        "🛡️ Safety",
        "🏆 Achievements"
    ])
    
    with tabs[0]:
        show_progress()
        reset_progress()
    
    with tabs[1]:
        show_map()
    
    with tabs[2]:
        show_navigation()
    
    with tabs[3]:
        show_punishment_wheel()
    
    with tabs[4]:
        show_safety_dashboard()
    
    with tabs[5]:
        show_achievements()
    
    # Check achievements after any action
    AchievementSystem.check_achievements()

if __name__ == "__main__":
    main()
