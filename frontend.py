import streamlit as st
import pandas as pd
from datetime import datetime
import LoShu_backend

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Lo Shu Grid Numerology",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    /* Main container styling */
    .stApp {
        background-color: #f0f2f6;
    }

    /* Title styling */
    h1 {
        color: #1e3a8a; /* Dark Blue */
        text-align: center;
    }

    /* Subheader styling */
    h2, h3 {
        color: #1e3a8a;
    }

    /* Input widgets styling */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div {
        border-radius: 10px;
        border: 2px solid #93c5fd; /* Light Blue Border */
        background-color: #ffffff;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 10px;
        border: 2px solid #1e3a8a;
        background-color: #2563eb; /* Blue */
        color: white;
        font-weight: bold;
        width: 100%;
        padding: 10px 0;
    }
    .stButton > button:hover {
        background-color: #1d4ed8; /* Darker Blue on hover */
        border-color: #1d4ed8;
    }

    /* DataFrame styling */
    .stDataFrame {
        text-align: center;
    }
    .stDataFrame table {
        margin: auto;
        border: 2px solid #1e3a8a;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .stDataFrame th, .stDataFrame td {
        text-align: center !important;
        padding: 15px;
    }
    
    /* Center the button */
    .stButton {
        display: flex;
        justify-content: center;
    }
    
    /* Result containers */
    .result-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# --- UI Layout ---

st.title("Lo Shu Grid Numerology Calculator")
st.write("") # Spacer

# --- Input Form ---
with st.container():
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        day = st.selectbox("Day", options=list(range(1, 32)), index=0)
    with col2:
        month = st.selectbox("Month", options=list(range(1, 13)), index=0)
    with col3:
        current_year = datetime.now().year
        year = st.number_input("Year", min_value=1900, max_value=current_year, value=2000, step=1)
    with col4:
        gender = st.selectbox("Gender", options=["Male", "Female"])
    with col5:
        name = st.text_input("First Name", placeholder="Enter your first name")

    # Center the button
    button_col = st.columns([2, 1, 2])
    with button_col[1]:
        submit_button = st.button("Create Lo Shu Grid")


# --- Processing and Output ---

if submit_button:
    # --- Input Validation ---
    if not name.strip():
        st.error("Please enter a name.")
    else:
        try:
            # Validate date
            datetime(year, month, day)
            
            with st.spinner("Calculating your numerology report... This may take a moment."):
                # --- Backend Calculations ---
                counts, psychic, destiny, kua, name_number = LoShu_backend.calculate_numbers(name, day, month, year, gender)
                grid_df = LoShu_backend.build_grid_dataframe(counts)
                planes = LoShu_backend.check_planes(counts)
                
                # --- Display Core Numbers and Grid ---
                with st.container():
                    st.markdown("---")
                    st.header("Your Numerology Chart")
                    
                    num_col1, num_col2, num_col3, num_col4 = st.columns(4)
                    num_col1.metric("Psychic Number", psychic)
                    num_col2.metric("Destiny Number", destiny)
                    num_col3.metric("Name Number", name_number)
                    num_col4.metric("Kua Number", kua)

                    grid_col, plane_col = st.columns([1, 1])
                    with grid_col:
                        st.subheader("Lo Shu Grid")
                        st.dataframe(grid_df)
                    
                    with plane_col:
                        st.subheader("Completed Planes")
                        if planes:
                            for plane in planes:
                                st.success(f"✓ {plane}")
                        else:
                            st.info("No completed planes found in your chart.")

                # --- Generate and Display AI Interpretation ---
                with st.container():
                    st.markdown("---")
                    st.header("Your Detailed Numerology Reading")
                    
                    # Call the backend function to get the AI interpretation
                    interpretation = LoShu_backend.generate_interpretation(
                        name, day, month, year, gender, psychic, destiny, kua, name_number, counts, planes
                    )
                    
                    # To properly display the markdown from the backend prompt
                    st.write(interpretation)

        except ValueError:
            st.error("Invalid date. Please check the day, month, and year.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

