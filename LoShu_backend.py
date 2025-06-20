from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import re
import pandas as pd
import requests
import json
from datetime import datetime
import streamlit as st


groq = st.secrets["Groq_API_Key"]



llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    groq_api_key=groq,
    temperature=0
    # other params...
)


# --- Core Numerology Functions ---

# Pythagorean numerology chart for name calculation
NAME_CHART = {
    'A': 1, 'J': 1, 'S': 1,
    'B': 2, 'K': 2, 'T': 2,
    'C': 3, 'L': 3, 'U': 3,
    'D': 4, 'M': 4, 'V': 4,
    'E': 5, 'N': 5, 'W': 5,
    'F': 6, 'O': 6, 'X': 6,
    'G': 7, 'P': 7, 'Y': 7,
    'H': 8, 'Q': 8, 'Z': 8,
    'I': 9, 'R': 9
}

def reduce_to_digit(n):
    """Reduces a number to a single digit by summing its digits repeatedly."""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

def calculate_name_number(name):
    """Calculates the numerology number for a given name."""
    name_sum = sum(NAME_CHART.get(char.upper(), 0) for char in name if char.isalpha())
    return reduce_to_digit(name_sum)

def calculate_numbers(name, day, month, year, gender):
    """Calculates all the core numerological numbers and the counts for the grid."""
    # Create the full date string to extract all digits.
    date_str = f"{day:02d}{month:02d}{year}"
    digits = [int(d) for d in date_str]

    # Calculate Psychic, Destiny, and Year Sum numbers.
    psychic = reduce_to_digit(day)
    destiny = reduce_to_digit(sum(digits))
    year_sum = reduce_to_digit(year)
    name_number = calculate_name_number(name)

    # Calculate Kua number based on gender.
    kua = 0
    if gender.lower() == "male":
        kua = 11 - year_sum
        if kua == 10:
            kua = 1
        if kua > 9:
            kua = reduce_to_digit(kua)
    else:  # female
        kua = 4 + year_sum
        if kua > 9:
             kua = reduce_to_digit(kua)
        

    # IMPORTANT: The Name Number and Kua number are included in the list for the grid.
    all_nums = [d for d in digits if d > 0] + [psychic, destiny, kua, name_number]
    
    # Count occurrences of each number from 1 to 9.
    counts = {i: all_nums.count(i) for i in range(1, 10)}
    
    return counts, psychic, destiny, kua, name_number

def build_grid_dataframe(counts):
    """Constructs the Lo Shu Grid as a Pandas DataFrame."""
    grid_layout = [
        [4, 9, 2],
        [3, 5, 7],
        [8, 1, 6]
    ]
    grid_values = []
    for row in grid_layout:
        grid_row = []
        for num in row:
            count = counts.get(num, 0)
            if count == 0:
                grid_row.append("")
            elif count == 1:
                grid_row.append(str(num))
            else:
                grid_row.append(f"{num}({count})")
        grid_values.append(grid_row)
    
    df = pd.DataFrame(
        grid_values,
        index=["Mental Plane", "Emotional Plane", "Practical Plane"],
        columns=["Thought", "Will", "Action"]
    )
    return df

def check_planes(counts):
    """Checks for completed horizontal, vertical, and diagonal planes."""
    planes_list = {
        "Mental Plane (4-9-2)": [4, 9, 2],
        "Emotional Plane (3-5-7)": [3, 5, 7],
        "Practical Plane (8-1-6)": [8, 1, 6],
        "Thought Plane (4-3-8)": [4, 3, 8],
        "Will Plane (9-5-1)": [9, 5, 1],
        "Action Plane (2-7-6)": [2, 7, 6],
        "Determination Plane (4-5-6)": [4, 5, 6],
        "Compassion Plane (2-5-8)": [2, 5, 8]
    }
    completed = [name for name, numbers in planes_list.items() if all(counts.get(num, 0) > 0 for num in numbers)]
    return completed

# --- AI Interpretation Function ---

def generate_interpretation(name, day, month, year, gender, psychic, destiny, kua, name_number, counts, planes):
    """Fetches a numerological interpretation"""
    grid_data = ", ".join([f"{num} (appears {count} time{'s' if count > 1 else ''})" for num, count in counts.items() if count > 0])
    missing_numbers = ", ".join([str(num) for num, count in counts.items() if count == 0])
    completed_planes_str = ", ".join(planes) if planes else 'None'
    
    template = f"""
        You are a master numerologist with deep expertise in Lo Shu Grid analysis, Chinese metaphysics, and Vedic numerology. Provide a detailed, insightful, and holistic analysis of a person's complete numerological profile. 
        Write in a warm, encouraging, and empowering tone with clear structure using ## for main headings and ### for sub-headings. Use plain text without markdown bolding. 
        
        
        **Person's Data:**
        - First Name: {name}
        - Date of Birth: {day}-{month}-{year}
        - Gender: {gender}
        - Psychic Number (Birth Number): {psychic}
        - Destiny Number (Life Path Number): {destiny}
        - Name Number (Expression Number): {name_number}
        - Kua Number: {kua}
        - Numbers in their chart: {grid_data or 'None'}
        - Missing Numbers: {missing_numbers or 'None'}
        
        **Analysis Request:**
        Please provide a comprehensive reading covering the following aspects:

        ## 1. Individual Squares Deep Analysis (all 9 squares in the grid)
        Based on associated Planet, Element, Direction, Season, Colors, Symbolism, Strengthof Square (based on count of Number in the square).
        ## 2. Planes Significance Analysis
        For all Horizontal (Mind: 4-9-2, Emotional: 3-5-7 and Material: 8-1-6) Planes,
        Vertical (Thought: 4-3-8, Willpower: 9-5-1 and Expression: 2-7-6) Planes and
        Diagonal (Golden: 4-5-6 and Silver: 2-5-8) Planes.
        This analysis is based on the completeness, partial completeness or absence of a plane.
        Also, this analysis should be based on the strength of the plane (derived from the count of numbers in each square of the plane).
        ## 3. Psychic Number Analysis ({psychic})
        Explain the deep meaning of their birth day number, inner desires, natural instincts, and how others perceive them.
        ## 4. Destiny Number Analysis ({destiny})
        Detail their life purpose, karmic lessons, ultimate goals, and the path their soul chose for this lifetime.
        ## 5. Name Number Analysis ({name_number})
        Analyze how the vibration of "{name}" influences their expression, talents, and interaction with the world.
        ## 6. Kua Number Analysis ({kua})
        Provide comprehensive Feng Shui guidance including:
        - Personal energy type and characteristics
        - Favourable directions for sleeping, working, and facing
        - Compatible elements and colours
        - Best locations in the home and office
        ## 7. Present Numbers Strengths Analysis
        For each present number in the grid, explain:
        - Natural talents and abilities it provides
        - How it manifests in their personality
        - Career advantages it offers
        - Specific ways to maximise this gift
        ## 8. Missing Numbers Growth Areas Analysis  
        For each missing number in {missing_numbers}, provide:
        - What quality needs development
        - Specific challenges this absence creates
        - Three practical remedies to cultivate this energy
        - Reassurance about growth potential
        ## 9. Completed Planes Special Powers Analysis
        For completed planes in {completed_planes}:
        - Rare abilities and exceptional talents
        - How to use these gifts responsibly
        - Career paths that align with these powers
        - Leadership potential and social impact
        ## 10. Individual Square Strength Assessment
        Rate each square's strength (Weak/Moderate/Strong/Very Strong) based on frequency counts and explain:
        - How this strength level affects their life
        - Optimal ways to leverage strong squares
        - Methods to strengthen weak squares
        ## 11. Holistic Life Integration Reading
        Synthesize all elements into a comprehensive life guidance covering:
        - Their unique energetic signature
        - How all numbers work together synergistically  
        - Life themes and recurring patterns
        - Relationship compatibility insights
        - Career and financial guidance
        - Health and wellness recommendations
        - Spiritual development path
        - Key life lessons and growth opportunities
        - Timing for major life decisions
        - Personal mantras and affirmations
        ## 12. Summary and Overall Guidance
        Provide a concluding summary that synthesizes the key points of the reading. Offer one or two key pieces of actionable advice for {name} to lead a more fulfilling life based on their unique numerological chart.
        **Final Wisdom:**
        Conclude with an inspiring message about their unique gifts, soul purpose, and the beautiful journey their numbers reveal.
        Please ensure every section provides specific, actionable insights tailored to this person's unique numerological blueprint.
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    response = chain.invoke({
        "name": name,
        "day": day,
        "month": month,
        "year": year,
        "gender": gender,
        "psychic": psychic,
        "destiny": destiny,
        "kua": kua,
        "name_number": name_number,
        "counts": counts,
        "planes": planes
        })
    return response.content
