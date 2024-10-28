import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from datetime import datetime

# Page config
st.set_page_config(page_title="Belfast 12 Pubs of Christmas", page_icon="🍺", layout="wide")

# Initialize session state
if 'current_pub' not in st.session_state:
    st.session_state.current_pub = 0
if 'completed_pubs' not in st.session_state:
    st.session_state.completed_pubs = []

# Belfast pubs data - ordered for optimal route
PUBS_DATA = {
    'name': [
        "Lavery's", "Whites Tavern", "The Points", "Bittles",
        "The Spaniard", "Sunflower", "The Dirty Onion", "Kelly's Cellars",
        "The Duke of York", "The John Hewitt", "Maddens", "Ulster Sports Club"
    ],
    'latitude': [
        54.5929, 54.5997, 54.6007, 54.5995,
        54.6003, 54.6012, 54.6002, 54.6005,
        54.6003, 54.6008, 54.6004, 54.5999
    ],
    'longitude': [
        -5.9365, -5.9252, -5.9259, -5.9267,
        -5.9273, -5.9285, -5.9278, -5.9282,
        -5.9275, -5.9270, -5.9277, -5.9268
    ],
    'rules': [
        "Christmas Jumpers Required & Last Names Only",
        "No Phones & Drink with Left Hand Only",
        "Tactical Whitey Points System",
        "No Phones & No First Names",
        "Too Glam to Give a Damn - Must Pose for Photos",
        "The Arm Pub - Drink from Someone Else's Arm",
        "Must Bow Before Taking a Drink",
        "Power 2 or 3 (Down Drink in 2-3 Gulps)",
        "Must Speak in Different Accents",
        "Different Drink Type Required",
        "International Drinking Rules",
        "Buddy System - Final Challenge"
    ]
}

def main():
    st.title("🎄 Belfast 12 Pubs of Christmas 🍺")
    
    tabs = st.tabs(["Progress", "Map", "Rules", "Safety Tips"])
    
    with tabs[0]:
        show_progress()
    
    with tabs[1]:
        show_map()
    
    with tabs[2]:
        show_rules()
    
    with tabs[3]:
        show_safety_tips()

def show_progress():
    st.header("Progress Tracker")
    
    # Progress bar
    progress = len(st.session_state.completed_pubs)
    st.progress(progress/12)
    st.write(f"Completed: {progress}/12 pubs")
    
    # Current pub
    if st.session_state.current_pub < 12:
        current_pub = PUBS_DATA['name'][st.session_state.current_pub]
        current_rule = PUBS_DATA['rules'][st.session_state.current_pub]
        
        st.subheader(f"Current Pub: {current_pub}")
        st.info(f"Rule: {current_rule}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Mark Current Pub as Complete"):
                if current_pub not in st.session_state.completed_pubs:
                    st.session_state.completed_pubs.append(current_pub)
                    st.session_state.current_pub += 1
                    st.experimental_rerun()
        with col2:
            if st.button("Reset Progress"):
                st.session_state.current_pub = 0
                st.session_state.completed_pubs = []
                st.experimental_rerun()
    else:
        st.success("🎉 Congratulations! You've completed the Belfast 12 Pubs of Christmas! 🎉")

def show_map():
    st.header("Pub Route Map")
    
    # Create map centered on Belfast
    m = folium.Map(location=[54.5973, -5.9301], zoom_start=15)
    
    # Add markers and route
    for i in range(12):
        color = 'green' if PUBS_DATA['name'][i] in st.session_state.completed_pubs else 'red'
        folium.Marker(
            [PUBS_DATA['latitude'][i], PUBS_DATA['longitude'][i]],
            popup=f"{i+1}. {PUBS_DATA['name'][i]}<br>{PUBS_DATA['rules'][i]}",
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(m)
        
        # Connect pubs with lines
        if i > 0:
            points = [
                [PUBS_DATA['latitude'][i-1], PUBS_DATA['longitude'][i-1]],
                [PUBS_DATA['latitude'][i], PUBS_DATA['longitude'][i]]
            ]
            folium.PolyLine(points, weight=2, color='blue', opacity=0.8).add_to(m)
    
    folium_static(m)

def show_rules():
    st.header("Pub Rules & Information")
    
    # Create and display rules table
    df = pd.DataFrame({
        'Stop': range(1, 13),
        'Pub': PUBS_DATA['name'],
        'Rule': PUBS_DATA['rules'],
        'Status': ['✅' if pub in st.session_state.completed_pubs else '⏳' 
                  for pub in PUBS_DATA['name']]
    })
    
    st.dataframe(df.style.set_properties(**{'text-align': 'left'}), 
                use_container_width=True)

def show_safety_tips():
    st.header("Safety Tips & Guidelines")
    
    st.markdown("""
    ### Important Reminders:
    - 🚶‍♂️ Always have a designated walker/supervisor
    - 🚕 Save local taxi numbers in your phone
    - 💧 Drink water between pubs
    - 🍽️ Eat a proper meal before starting
    - 👥 Stay with your group
    - 📱 Keep your phone charged
    
    ### Emergency Contacts:
    - **Police/Ambulance/Fire**: 999 or 112
    - **Non-emergency police**: 101
    - **Local Taxi Services**:
        - Value Cabs: 028 9080 9080
        - fonacab: 028 9033 3333
    """)

if __name__ == "__main__":
    main()
