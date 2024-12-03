import streamlit as st
from dateutil import parser
from datetime import datetime, timedelta

# Function to parse natural language date and time
def parse_natural_language_datetime(input_text):
    try:
        # Parse the input text to datetime
        parsed_datetime = parser.parse(input_text, fuzzy=True)
        # Return the date in DD/MM/YY format
        return parsed_datetime.strftime("%d/%m/%y")
    except Exception:
        return None

# Function to handle relative dates like "today", "tomorrow", "day after tomorrow"
def get_relative_date(input_text):
    today = datetime.now()

    # Handling specific relative date phrases
    if "today" in input_text.lower():
        return today.strftime("%d/%m/%y")

    elif "tomorrow" in input_text.lower():
        tomorrow = today + timedelta(days=1)
        return tomorrow.strftime("%d/%m/%y")

    elif "day after tomorrow" in input_text.lower():
        day_after_tomorrow = today + timedelta(days=2)
        return day_after_tomorrow.strftime("%d/%m/%y")

    # Handling "coming" day references (e.g., "coming Saturday")
    day_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    for day_name, day_index in day_map.items():
        if day_name in input_text.lower():
            current_day_index = today.weekday()
            delta_days = (day_index - current_day_index) % 7
            if delta_days == 0:
                delta_days = 7  # If the day is today but referenced as "coming," move to next week
            target_date = today + timedelta(days=delta_days)
            return target_date.strftime("%d/%m/%y")

    return "I couldn't understand the date. Please provide a valid reference."

# Streamlit UI setup
st.set_page_config(page_title="Date Parser Chatbot", layout="wide")
st.header("Welcome to the Date Parser Chatbot")

# Chat history management
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Function to handle user input and generate chatbot response
def handle_user_input(input_text):
    response = None
    # Try to parse a date from user input
    parsed_date = parse_natural_language_datetime(input_text)
    if parsed_date:
        response = f"The date you mentioned is: {parsed_date}."
    else:
        # Handle relative dates like "today", "tomorrow", etc.
        response = get_relative_date(input_text)
        if response == "I couldn't understand the date. Please provide a valid reference.":
            response = "I couldn't understand the date. Could you please rephrase it?"

    return response

# Display chat messages
def display_chat():
    for msg in st.session_state['chat_history']:
        if msg['role'] == 'user':
            st.chat_message("user").write(msg['content'])
        elif msg['role'] == 'assistant':
            st.chat_message("assistant").write(msg['content'])

# Get user input
user_input = st.text_input("Type your message here:", key="user_input")

if user_input:
    # Store user input in the chat history
    st.session_state['chat_history'].append({'role': 'user', 'content': user_input})

    # Generate and store chatbot response
    bot_response = handle_user_input(user_input)
    st.session_state['chat_history'].append({'role': 'assistant', 'content': bot_response})

    # Display the updated chat
    display_chat()

