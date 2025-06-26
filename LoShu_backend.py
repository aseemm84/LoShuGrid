from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import re
import pandas as pd
import requests
import json
from datetime import datetime, date
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

def year_number(day, month):
    current_date = date.today()
    current_year = current_date.year
    date_str = f"{day:02d}{month:02d}{current_year}"
    digits = [int(d) for d in date_str]
    curr_year_num = reduce_to_digit(sum(digits))
    return curr_year_num

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
    completed = []
    incompleted = []
    for name, numbers in planes_list.items():
        if all(counts.get(num, 0) > 0 for num in numbers):
            completed.append(name)
        else:
            incompleted.append(name)
    return completed, incompleted

# --- AI Interpretation Function ---

def generate_interpretation(name, day, month, year, gender, psychic, destiny, kua, name_number, curr_year_num, counts, completed_planes, incomplete_planes):
    """Fetches a numerological interpretation"""
    grid_data = ", ".join([f"{num} (appears {count} time{'s' if count > 1 else ''})" for num, count in counts.items() if count > 0])
    missing_numbers = ", ".join([str(num) for num, count in counts.items() if count == 0])
    completed_planes_str = ", ".join(completed_planes) if completed_planes else 'None'
    incomplete_planes_str = ", ".join(incomplete_planes) if incomplete_planes else 'None'
    
    template = f"""
        You are a master numerologist with deep expertise in Lo Shu Grid analysis, Chinese metaphysics, and Vedic numerology. Provide a detailed, insightful, and holistic analysis of a person's complete numerological profile based ONLY on the data provided. Do not invent or assume any information.
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
        - Completed Planes: {completed_planes_str}
        - Incomplete Planes: {incomplete_planes_str}
        - Year Number (Current Year Number): {curr_year_num}

        **Analysis Request:**
        Please provide a comprehensive reading covering the following aspects, ensuring the analysis of planes is based on the provided 'Completed Planes' {completed_planes_str} and 'Incomplete Planes' {incomplete_planes_str} lists.

        ## 1. Individual Squares Analysis
For each square (1–9), provide:
### Square
- Planet, Element, Direction, Season, Symbolic Colors
- Life area (e.g., Wealth, Relationships, Creativity)
- Strength level (based on count) and its influence
- Real-life example or anecdote demonstrating this energy

## 2. Plane Significance
### Analyze the person's {name} 

### Horizontal Planes (Mental, Emotional and Practical):
Discuss completeness and strength, linking to memory, feelings, practical skills, based on whether the plane is in the 'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.
### Vertical Planes (Thought, Will and Action)
Analyze determination, planning, communication, and emotional expression, based on whether the plane is in the 'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.
### Diagonal Planes (Determination, Compassion)
Explain rare combinations, property success, fame, and how to harness them, based on whether the plane is in the 'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.

## 3. Core Number Analysis
### Psychic Number ({psychic})
Inner self, desires, and interpersonal perception.
### Destiny Number ({destiny})
Life purpose, karmic lessons, and ultimate goals.
### Name Number ({name_number})
Talents, modes of expression, and professional potential.
### Kua Number ({kua})
Personal energy type, favorable directions, compatible elements, and Feng Shui tips.
### Discuss the combinations of these numbers based on the planets they govern and the mutual relationship of those planets.

## 4. Life Domains
### Education & Learning
Assess learning style, optimal study methods, and academic strengths.
### Career & Profession
Identify suitable fields, work style, leadership qualities, and entrepreneurial potential.
### Finances & Wealth
Evaluate money management, investment outlook, property and luxury inclinations, legal considerations.
### Travel & Exploration
Indicate favorable travel directions, how journeys support growth, and auspicious timing.
### Family & Relationships
Examine marriage prospects, parenting style, interpersonal harmony, and children’s guidance.
### Health & Wellness
Recommend routines, physical and mental health strategies, stress management, and longevity practices.
### Age-Related Phases
Highlight life periods of opportunity and challenge based on numerological cycles.
### Challenges & Opportunities
Summarize major life tests and potential breakthroughs, with targeted remedies and affirmations.

## 5. Completed vs. Missing Planes
- Completed Planes: Analyze the unique talents, career advantages, and social impact based on the {completed_planes_str}.
- Incomplete Planes: Provide remedies, daily rituals, and environmental adjustments (colors, directions, elements) for the {incomplete_planes_str}.

## 6. Current Year Analysis

Perform the analysis of the current year based on the combination of current year number {curr_year_num} and destiny number {destiny}.
Look at the planets associated with these numbers. Also look at the mutual friendship between these numbers and associated planets.
Based on the analysis, predict the current year events, challenges and opportunities.

## 7. Holistic Synthesis
Integrate all numbers into a cohesive life-purpose narrative, illustrating how strengths overcome gaps and how challenges become catalysts for growth.

## 8. Action Plan & Affirmations
- **Immediate Steps (Next 30 Days):** Three concrete actions.
- **Long-Term Goals (Next Year):** Major milestones aligned with numerology.
- **Personal Mantras:** Suggest beej mantras for the planets associated with the weak, empty and negative squares.

## Final Wisdom
Conclude with an inspiring message that highlights the person’s soul mission, unique gifts, and the pathways to a fulfilling, balanced life.
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
        "completed_planes": completed_planes,
        "incomplete_planes": incomplete_planes
        })
    return response.content
