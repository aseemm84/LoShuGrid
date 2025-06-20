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
        if kua == 5:
            kua = 2
    else:  # female
        kua = 4 + year_sum
        if kua > 9:
             kua = reduce_to_digit(kua)
        if kua == 5:
            kua = 8

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
                grid_row.append("—")
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
        You are an expert numerologist specializing in the Lo Shu Grid system. 
        Provide a detailed, insightful, and positive analysis for a person with the following details. 
        Structure the response with clear headings (using ## for main headings and ### for sub-headings) and paragraphs.
        Do not use markdown for bolding, use plain text.
        
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
        
        ## Core Personality Analysis
        ### Psychic Number ({psychic})
        Explain what the Psychic number reveals about their inner self, desires, and basic character.
        ### Destiny Number ({destiny})
        Explain what the Destiny number reveals about their life's purpose, path, and the lessons they are here to learn.
        ### Name Number ({name_number})
        Explain what the Name Number (derived from '{name}') reveals about their talents, abilities, and potential in the world. This is their mode of expression.
        ### Kua Number ({kua})
        Briefly explain what the Kua number suggests about their personal energy and compatibility with directions.
        
        ## The Lo Shu Grid Breakdown
        ### Strengths (Based on Present Numbers)
        Analyze the meaning of the numbers present in their grid ({grid_data}). What strengths and talents do these numbers indicate?
        ### Challenges (Based on Missing Numbers)
        Analyze the meaning of the numbers missing from their grid ({missing_numbers}). What challenges or areas for growth do these absences suggest?
        
        ## Analysis of Planes
        ### Completed Planes Analysis
        If there are completed planes ({completed_planes_str}), explain the powerful characteristics and abilities these bestow upon the individual.
        ### Guidance for Missing Planes
        If there are no completed planes, offer constructive advice on how the person can compensate for the energies of missing planes in their life.
        
        ## Summary and Overall Guidance
        Provide a concluding summary that synthesizes the key points of the reading. Offer one or two key pieces of actionable advice for {name} to lead a more fulfilling life based on their unique numerological chart.
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
