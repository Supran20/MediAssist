import streamlit as st
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import fitz  # PyMuPDF
from docx import Document  # For Word files
import dateparser
from datetime import datetime, timedelta

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text += page.get_text("text")  # Extract text from each page
    return text

# Function to extract text from Word document
def extract_text_from_word(word_file):
    document = Document(word_file)
    text = ""
    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"
    return text

# Function to extract text from plain text files
def extract_text_from_txt(txt_file):
    return txt_file.read().decode("utf-8")

# Function to parse and format date (including relative dates like "tomorrow" and "next Monday")
def parse_date(input_date):
    # Mapping days of the week to integers (Monday = 0, Sunday = 6)
    days_of_week = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    # Handle "today" and "tomorrow"
    if input_date.lower() == "today":
        today = datetime.today()
        return today.strftime("%d-%m-%Y")
    elif input_date.lower() == "tomorrow":
        tomorrow = datetime.today() + timedelta(days=1)
        return tomorrow.strftime("%d-%m-%Y")
    
    # Handle "next <day>"
    for day_name, day_number in days_of_week.items():
        if f"next {day_name}" in input_date.lower():
            today = datetime.today()
            days_ahead = day_number - today.weekday()
            if days_ahead <= 0:  # If the day has already passed for this week, get it for the next week
                days_ahead += 7
            next_day = today + timedelta(days=days_ahead)
            return next_day.strftime("%d-%m-%Y")
    
    # Try parsing specific dates like "17 December 2024"
    parsed_date = dateparser.parse(input_date)
    if parsed_date:
        return parsed_date.strftime("%d-%m-%Y")
    else:
        return None

# Streamlit UI setup
st.set_page_config(page_title="MediAssist - Your Virtual Health Assistant", layout="wide")
st.header("Welcome to MediAssist - Your Virtual Health Assistant")

# Initialize session state for conversation
if 'flowmessages' not in st.session_state:
    st.session_state['flowmessages'] = [
        SystemMessage(content=""" 
You are MediAssist, an AI-powered virtual health assistant. You are here to provide helpful, accurate, and empathetic responses to patients and visitors. 
You can answer questions about the hospital's services, departments, staff, and general health information, including medicine and disease-related queries.

When a user asks to book an appointment, you will:
1. Ask for the user's full name in a conversational manner.
2. Ask for the user's phone number in a conversational manner.
3. Ask for the user's email address in a conversational manner.
4. Ask for the user's physical address in a conversational manner.
5. Ask for the appointment date and time in a conversational manner.
6. After collecting all the details, ask: "Would you like to confirm?"
7. If the user responds positively, display the details (full name, email, physical address, phone, appointment date and time) they provided in a conversational way.

You must handle all patient information with care and provide a confirmation message once all details are collected and the appointment is booked.

If the user is not asking to book an appointment, do not prompt for these details.
""")
    ]

# Initialize the Ollama LLM with the "llama2" model
try:
    llm = Ollama(model="llama2", base_url="http://localhost:11434")
    chat = ChatOllama(llm=llm)
    st.sidebar.success("Successfully connected to the 'llama2' model.")
except Exception as e:
    st.sidebar.error(f"Error initializing Ollama: {e}")
    st.stop()

# Function to get chatbot response
def get_chatmodel_response(question, context=None):
    # Prepare user input message and optional context
    if context:
        st.session_state['flowmessages'].append(HumanMessage(content=f"Document: {context}"))
    st.session_state['flowmessages'].append(HumanMessage(content=question))
    
    # Get AI response
    response = chat(st.session_state['flowmessages'])
    st.session_state['flowmessages'].append(AIMessage(content=response.content))
    
    return response.content

# File upload for hospital documents
uploaded_file = st.file_uploader("Upload a hospital document (optional)", type=["pdf", "docx", "txt"])
document_context = ""

if uploaded_file:
    # Check the file type and extract text accordingly
    if uploaded_file.type == "application/pdf":
        document_context = extract_text_from_pdf(uploaded_file)[:1000]
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        document_context = extract_text_from_word(uploaded_file)[:1000]
    elif uploaded_file.type == "text/plain":
        document_context = extract_text_from_txt(uploaded_file)[:1000]
    else:
        st.error("Unsupported file type.")
        document_context = ""

    if document_context:
        st.sidebar.success("Document loaded successfully!")

# Display chat history (always above the input box)
st.divider()  # Adds a visual divider between chat history and input box
chat_container = st.container()  # Create a container for chat history

with chat_container:
    for msg in st.session_state['flowmessages']:
        if isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)
        elif isinstance(msg, AIMessage):
            st.chat_message("assistant").write(msg.content)

# Always keep the input box at the bottom
st.divider()  # Add a divider for better UI
input_text = st.text_input("Type your message here:", key="input_text", label_visibility="collapsed")
submit_button = st.button("Send")

# Appointment details state
if 'appointment_details' not in st.session_state:
    st.session_state['appointment_details'] = {}

# Handle the flow of conversation for appointment booking
if submit_button and input_text:
    with st.spinner("Thinking..."):
        response = get_chatmodel_response(input_text, context=document_context if uploaded_file else None)
    
    # Display the new messages immediately
    with chat_container:  # Ensure new messages appear at the top
        st.chat_message("user").write(input_text)
        st.chat_message("assistant").write(response)
    
    # Handling appointment details collection
    if "book an appointment" in input_text.lower():
        if 'name' not in st.session_state['appointment_details']:
            st.session_state['appointment_details']['name'] = input_text
            st.session_state['flowmessages'].append(AIMessage(content="Great! Could you please provide your phone number?"))
        elif 'phone' not in st.session_state['appointment_details']:
            st.session_state['appointment_details']['phone'] = input_text
            st.session_state['flowmessages'].append(AIMessage(content="Got it! Could you please share your email address?"))
        elif 'email' not in st.session_state['appointment_details']:
            st.session_state['appointment_details']['email'] = input_text
            st.session_state['flowmessages'].append(AIMessage(content="Thanks! Could you please provide your physical address?"))
        elif 'address' not in st.session_state['appointment_details']:
            st.session_state['appointment_details']['address'] = input_text
            st.session_state['flowmessages'].append(AIMessage(content="Awesome! What date and time would you like to schedule the appointment?"))
        elif 'appointment_date' not in st.session_state['appointment_details']:
            # Parse the date provided by the user
            parsed_date = parse_date(input_text)
            if parsed_date:
                st.session_state['appointment_details']['appointment_date'] = parsed_date
                st.session_state['flowmessages'].append(AIMessage(content="Great! Could you also provide a time for your appointment?"))
            else:
                st.session_state['flowmessages'].append(AIMessage(content="Sorry, I couldn't understand the date. Could you please provide it in a different format?"))
                
        # After all details are collected, ask for confirmation
        if all(key in st.session_state['appointment_details'] for key in ['name', 'phone', 'email', 'address', 'appointment_date', 'appointment_time']):
            details = st.session_state['appointment_details']
            st.session_state['flowmessages'].append(AIMessage(content=f"Please confirm the following details:\n"
                                                                 f"Date: {details['appointment_date']}\n"
                                                                 f"Time: {details['appointment_time']}\n"
                                                                 f"Full name: {details['name']}\n"
                                                                 f"Phone number: {details['phone']}\n"
                                                                 f"Email address: {details['email']}"))
            st.session_state['appointment_details'] = {}  # Reset after confirmation
