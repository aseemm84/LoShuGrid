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
        You are a master numerologist with deep expertise in Lo Shu Grid analysis, Chinese metaphysics, and Vedic numerology. Provide a detailed, insightful, and holistic analysis of a person's complete numerological profile based ONLY on the data provided. Please don't invent or assume any information.
        Write in a warm, encouraging, and empowering tone, using clear structure with main headings marked as ## and subheadings marked as ###. Use plain text without markdown bolding.


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
- Planet, Element, Direction, Season, Symbolic Colours
- Life area (e.g., Wealth, Relationships, Creativity)
- Strength level (based on count) and its influence
- Real-life example or anecdote demonstrating this energy

## 2. Plane Significance

### Mental Plane (4-9-2):
Discuss the intellect, logic, and analytical thinking based on:
- The strength (count/ frequency of each square) in the Mental Plane (4-9-2).
- Whether the Mental Plane (4-9-2) is in the 'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.

### Emotional Plane (3-5-7)
Discuss the feelings, intuition, and emotional sensitivity based on:
- The strength (count/ frequency of each square) in the Emotional Plane (3-5-7).
- Whether the Emotional Plane (3-5-7) is in the 'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.

### Practical Plane (8-1-6)
Discuss the ability to manifest ideas in the material world based on:
- The strength (count/ frequency of each square) in the Practical Plane (8-1-6).
- Whether the Practical Plane (8-1-6) is in the 'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.

### Thought Plane (4-3-8)
Discuss the ability to generate new ideas and to think in an orderly and methodical manner based on:
- The strength (count/ frequency of each square) in the Thought Plane (4-3-8).
- Whether the Thought Plane (4-3-8) is in the 'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.

### Will Plane (9-5-1)
Discuss the willpower, persistence, and determination to achieve the goals based on:
- The strength (count/ frequency of each square) in the Will Plane (9-5-1).
- Whether the Will Plane (9-5-1) is in the 'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.

### Action Plane (2-7-6)
Discuss the ability to put their thoughts and plans into action based on:
- The strength (count/ frequency of each square) in the Action Plane (2-7-6).
- Whether the Action Plane (2-7-6) is in the 'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.

### Determination Plane (4-5-6)
Discuss the "Rajat Yog" and material assets, specifically land and property, based on:
- The strength (count/ frequency of each square) in the Determination Plane (4-5-6).
- Whether the Determination Plane (4-5-6) is in the 'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.

### Compassion Plane (2-5-8)
Discuss the "Raj Yog" and success, wealth, name, and fame based on:
- The strength (count/ frequency of each square) in the Compassion Plane (2-5-8).
- Whether the Compassion Plane (2-5-8) is in the 'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.

## 3. Core Number Analysis for {name}
### Psychic Number ({psychic})
Discuss inner self, desires, and interpersonal perception based on the Psychic Number ({psychic}) and the planet associated with it.
### Destiny Number ({destiny})
Discuss life purpose, karmic lessons, and ultimate goals based on the Destiny Number ({destiny}) and the planet associated with it.
### Name Number ({name_number})
Discuss talents, modes of expression, and professional potential based on the Name Number ({name_number}) and the planet associated with it.
### Kua Number ({kua})
Discuss personal energy type, favourable directions, compatible elements, and Feng Shui tips based on the Kua Number ({kua}) and the planet associated with it.

### Discuss the combinations of these numbers based on the planets they govern and the mutual relationship (synergy and enmity) of those planets.

## 4. Life Domains
### Education & Learning
Assess learning style, optimal study methods, and academic strengths based on:
-'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.
-Associated square strength in the Lo Shu Grid.
### Career & Profession
Identify suitable fields, work style, leadership qualities, and entrepreneurial potential based on:
-'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.
-Associated square strength in the Lo Shu Grid.
### Finances & Wealth
Evaluate money management, investment outlook, property and luxury inclinations, and legal considerations based on:
-'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.
-Associated square strength in the Lo Shu Grid.
### Travel & Exploration
Indicate favourable travel directions, how journeys support growth, and auspicious timing based on:
-'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.
-Associated square strength in the Lo Shu Grid.
### Family & Relationships
Examine marriage prospects, parenting style, interpersonal harmony, and the guidance of children based on:
-'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.
-Associated square strength in the Lo Shu Grid.
### Health & Wellness
Discuss critical health issues and recommend physical and mental health strategies, and longevity practices based on:
-'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.
-Associated square strength in the Lo Shu Grid.
### Age-Related Phases
Highlight life periods of opportunity and challenge as per numerological cycles based on:
-'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.
-Associated square strength in the Lo Shu Grid.
### Challenges & Opportunities
Summarise major life challenges and potential breakthroughs, with targeted remedies and affirmations based on:
-'Completed Planes' {completed_planes_str} or 'Incomplete Planes' {incomplete_planes_str} list.
-Associated square strength in the Lo Shu Grid.

## 5. Current Year Analysis

Perform the analysis of the current year based on the combination of the current year number {curr_year_num} and the destiny number {destiny}.
Look at the planets associated with these numbers. Additionally, consider the mutual synergy and enmity between these planets.
Provide a very detailed and elaborate analysis for the current year's events, challenges, and opportunities in each of the following fields:
- Health (in 2-3 sentences)
- Family & Relationships (in 2-3 sentences)
- Education (in 2-3 sentences)
- Career (in 2-3 sentences)
- Money and Savings (in 2-3 sentences)
- Overall Happiness (in 2-3 sentences)

## 6. Holistic Synthesis
Integrate all numbers into a cohesive life-purpose narrative, illustrating how strengths overcome gaps and how challenges become catalysts for growth.

## 7. Action Plan & Affirmations
- **Immediate Steps (Next 30 Days):** Three concrete actions.
- **Long-Term Goals (Next Year):** Major milestones aligned with numerology.
- **Remedies:** Identify the squares (at least 3 to 4) which are relatively weak, negative or have missing numbers in the Lo Shu Grid. Identify planets associated with these weak, empty and negative squares. Suggest the remedies related to these planets (as per Vedic Astrology) to strengthen these weak, negative and missing squares. 

## 8. Final Wisdom
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
        "curr_year_num": curr_year_num,
        "counts": counts,
        "completed_planes": completed_planes,
        "incomplete_planes": incomplete_planes
        })
    return response.content
