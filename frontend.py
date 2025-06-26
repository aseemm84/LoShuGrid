import streamlit as st
import pandas as pd
from datetime import datetime
import LoShu_backend

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Lo Shu Grid Numerology",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon = "🔮",
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    /* --- General Styling --- */
    .stApp {
        background-color: #f0f2f6;
    }
    h1, h2, h3 {
        color: #1e3a8a; /* Dark Blue */
        text-align: center;
    }

    /* --- Input Widgets --- */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div {
        border-radius: 10px;
        border: 2px solid #93c5fd; /* Light Blue Border */
        background-color: #ffffff;
    }

    /* --- Button --- */
    .stButton > button {
        border-radius: 10px;
        border: 2px solid #1e3a8a;
        background-color: #2563eb;
        color: white;
        font-weight: bold;
        width: 100%;
        padding: 10px 0;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #1d4ed8;
        border-color: #1d4ed8;
    }

    /* --- Card for Output Sections --- */
    .card {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-top: 20px;
        border: 1px solid #e0e0e0;
    }
    
    /* --- Custom Lo Shu Grid --- */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        width: 100%;
        max-width: 300px;
        margin: auto;
        aspect-ratio: 1 / 1;
    }
    .grid-cell {
        background-color: #f8f9fa;
        color: #ced4da;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: bold;
        border: 2px solid #e9ecef;
    }
    .grid-cell.present {
        background-color: #e6f9f1;
        color: #0c854e;
        border: 2px solid #a3e9d1;
    }
    .grid-cell.multiple {
        background-color: #d1f3e3;
        color: #0a6b3e;
        border: 2px solid #77d9b4;
        font-weight: 900;
    }
    .grid-cell-inner {
        position: relative;
    }
    .grid-count {
        position: absolute;
        top: -8px;
        right: -15px;
        font-size: 1rem;
        font-weight: bold;
        color: #dd2c00;
        background-color: #fff;
        border-radius: 50%;
        padding: 2px 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)



def create_grid_html(counts):
    """Generates a styled HTML representation of the Lo Shu Grid."""
    grid_layout = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
    html = '<div class="grid-container">'
    for row in grid_layout:
        for num in row:
            count = counts.get(num, 0)
            cell_class = "grid-cell"
            content = str(num)
            count_badge = ""

            if count > 0:
                cell_class += " present"
                if count > 1:
                    cell_class += " multiple"
                    count_badge = f'<span class="grid-count">{count}</span>'
            else:
                 content = "—" # Display a dash for missing numbers

            html += f'<div class="{cell_class}"><div class="grid-cell-inner">{content}{count_badge}</div></div>'
    html += '</div>'
    return html

# --- UI Layout ---

st.title("🔮 AI Powered Lo Shu Grid Numerology Calculator")
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
        year = st.number_input("Year", min_value=1900, max_value=datetime.now().year, value=2000, step=1)
    with col4:
        gender = st.selectbox("Gender", options=["Male", "Female"])
    with col5:
        name = st.text_input("First Name", placeholder="Enter your first name")

    # Center the button
    button_col = st.columns([2, 1, 2])
    with button_col[1]:
        submit_button = st.button("Create Lo Shu Grid ⊞")


# --- Processing and Output ---
if submit_button:
    if not name.strip():
        st.error("Please enter a name.")
    else:
        try:
            datetime(year, month, day)

            with st.spinner("Analyzing the cosmos for your report... This may take a moment."):
                # --- Backend Calculations ---
                counts, psychic, destiny, kua, name_number = LoShu_backend.calculate_numbers(name, day, month, year, gender)
                completed_planes, incomplete_planes = LoShu_backend.check_planes(counts)
                curr_year_num = LoShu_backend.year_number(day, month)

                # --- Display Core Numbers in a Card ---
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.header("Your Core Numbers")
                num_col1, num_col2, num_col3, num_col4 = st.columns(4)
                num_col1.metric("Psychic Number", psychic, help="Represents your inner self and basic character.")
                num_col2.metric("Destiny Number", destiny, help="Represents your life's purpose and path.")
                num_col3.metric("Name Number", name_number, help="Represents your talents and mode of expression.")
                num_col4.metric("Kua Number", kua, help="Represents your personal energy and compatibility.")
                st.markdown('</div>', unsafe_allow_html=True)

                # --- Display Grid and Planes in separate cards ---
                grid_col, plane_col = st.columns([1, 1])
                with grid_col:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.header("Your Lo Shu Grid ⊞")
                    grid_html = create_grid_html(counts)
                    st.markdown(grid_html, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with plane_col:
                    st.markdown('<div class="card" style="height: 100%;">', unsafe_allow_html=True)
                    st.header("Planes Analysis ▦")

                    st.subheader("Completed Planes")
                    if completed_planes:
                        for plane in completed_planes:
                            st.success(f"✓ {plane}")
                    else:
                        st.info("No completed planes found.")

                    st.subheader("Incomplete Planes")
                    if incomplete_planes:
                        for plane in incomplete_planes:
                            st.error(f"✗ {plane}")
                    else:
                        st.balloons()
                        st.success("Congratulations! All planes are complete!")

                    st.markdown('</div>', unsafe_allow_html=True)


                # --- Generate and Display AI Interpretation in a Card ---
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.header("Your Detailed Numerology Reading ☯")
                interpretation = LoShu_backend.generate_interpretation(
                    name, day, month, year, gender, psychic, destiny, kua, name_number, curr_year_num, counts, completed_planes, incomplete_planes
                )
                st.markdown(interpretation)
                st.markdown('</div>', unsafe_allow_html=True)

        except ValueError:
            st.error("Invalid date. Please check the day, month, and year.")
        except Exception as e:
            st.error(f"An unexpected error occurred. Please ensure your API key is correctly configured. Error: {e}")


# --- Sidebar Configuration ---

st.sidebar.title("About")
st.sidebar.info("""
Welcome to the Lo Shu Grid Numerology Calculator,  an intuitive web application designed to reveal deep numerological insights based on your date of birth and personal numbers. This app combines ancient Chinese numerology—specifically the magic square pattern known as the Lo Shu Grid—with modern AI analysis to offer a holistic personality and life-path reading.

Key Features:
- **Automated Grid Creation: Instantly generates your personalized 3×3 numeric grid from birth date digits, Psychic Number, Destiny Number, and Kua Number.**
- **Visual Strength Mapping: Elegantly color-codes each square to highlight areas of natural aptitude and growth opportunities.**
- **AI-Powered Analysis: Leverages a state-of-the-art language model to produce warm, actionable, and deeply personalized interpretations of every number, square, and plane in your chart.**
- **Holistic Guidance: Provides recommendations for career, relationships, health, and spiritual development tailored to your unique numerological profile.**

Simply enter your birth details and let the Lo Shu Grid Numerology Calculator app guide you towards greater self-understanding and purposeful living.
""")
linkedin_url = "https://www.linkedin.com/in/aseem-mehrotra/"
st.sidebar.markdown(f'<a href="{linkedin_url}" target="_blank"><img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" style="height: 30px;"></a>', unsafe_allow_html=True)
