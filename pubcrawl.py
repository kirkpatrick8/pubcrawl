import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# Page config
st.set_page_config(page_title="Belfast 12 Pubs of Christmas", page_icon="🍺", layout="wide")

# Initialize session state
if 'current_pub' not in st.session_state:
    st.session_state.current_pub = 0
if 'completed_pubs' not in st.session_state:
    st.session_state.completed_pubs = []

# Belfast pubs data - in specified order with exact coordinates
PUBS_DATA = {
    'name': [
        "Lavery's", 
        "The Points", 
        "Sweet Afton", 
        "Kelly's Cellars",
        "Whites Tavern",
        "The Deer's Head",
        "The John Hewitt",
        "Duke of York",
        "The Harp Bar",
        "The Dirty Onion",
        "Thirsty Goat",
        "Ulster Sports Club"
    ],
    'latitude': [
        54.589539,  # Lavery's
        54.591556,  # Points
        54.595067,  # Sweet Afton
        54.599553,  # Kelly's
        54.600033,  # Whites
        54.601439,  # Deer's Head
        54.601928,  # John Hewitt
        54.601803,  # Duke of York
        54.602000,  # Harp Bar
        54.601556,  # Dirty Onion
        54.601308,  # Thirsty Goat
        54.600733   # Ulster Sports Club
    ],
    'longitude': [
        -5.934469,  # Lavery's
        -5.933333,  # Points
        -5.932894,  # Sweet Afton
        -5.932236,  # Kelly's
        -5.928497,  # Whites
        -5.930294,  # Deer's Head
        -5.928617,  # John Hewitt
        -5.927442,  # Duke of York
        -5.927058,  # Harp Bar
        -5.926673,  # Dirty Onion
        -5.926417,  # Thirsty Goat
        -5.925219   # Ulster Sports Club
    ],
    'rules': [
        "Christmas Jumpers Required",
        "Last Names Only",
        "No Swearing Challenge",
        "Power Hour (Down Drink in 2-3 Gulps)",
        "No Phones & Drink with Left Hand Only",
        "Must Speak in Different Accents",
        "Different Drink Type Required",
        "Must Bow Before Taking a Drink",
        "Double Parked",
        "The Arm Pub - Drink from Someone Else's Arm",
        "No First Names & Photo Challenge",
        "Buddy System - Final Challenge"
    ]
}

def mark_pub_complete():
    if st.session_state.current_pub < 12:
        current_pub = PUBS_DATA['name'][st.session_state.current_pub]
        if current_pub not in st.session_state.completed_pubs:
            st.session_state.completed_pubs.append(current_pub)
            st.session_state.current_pub += 1

def reset_progress():
    st.session_state.current_pub = 0
    st.session_state.completed_pubs = []

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
            st.button("Mark Current Pub as Complete", on_click=mark_pub_complete)
        with col2:
            st.button("Reset Progress", on_click=reset_progress)
    else:
        st.success("🎉 Congratulations! You've completed the Belfast 12 Pubs of Christmas! 🎉")

def show_map():
    st.header("Pub Route Map")
    
    # Create map centered on Belfast (middle of route)
    m = folium.Map(location=[54.595733, -5.930294], zoom_start=15)
    
    # Add markers and route
    for i in range(12):
        color = 'green' if PUBS_DATA['name'][i] in st.session_state.completed_pubs else 'red'
        
        # Add number to popup
        popup_text = f"{i+1}. {PUBS_DATA['name'][i]}<br>{PUBS_DATA['rules'][i]}"
        
        folium.Marker(
            [PUBS_DATA['latitude'][i], PUBS_DATA['longitude'][i]],
            popup=popup_text,
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(m)
        
        # Connect pubs with lines to show route
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
    
    st.dataframe(df, use_container_width=True)

def show_safety_tips():
    st.header("Safety Tips & Guidelines")
    
    st.markdown("""
    ### Important Reminders:
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
    
    ### Walking Distance:
    Total route is approximately 2.5 km
    """)

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

if __name__ == "__main__":
    main()
