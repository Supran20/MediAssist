import pymongo
import streamlit as st
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage, SystemMessage, AIMessage

# MongoDB Atlas connection string
mongo_uri = "mongodb+srv://msupran17:supran@supran.afauf7y.mongodb.net/?retryWrites=true&w=majority&appName=Supran"
client = pymongo.MongoClient(mongo_uri)

# Specify the database and collection
db = client['Appointments']  # Use the 'Appointments' database
collection = db['appointments']  # Use the 'appointments' collection

# Initialize Streamlit UI
st.set_page_config(page_title="MediAssist - Appointment Chatbot", layout="wide")
st.header("Welcome to MediAssist - Your Virtual Health Assistant")

# Initialize session state for conversation
if 'flowmessages' not in st.session_state:
    st.session_state['flowmessages'] = [
        SystemMessage(content="You are MediAssist, an AI-powered virtual health assistant. You are here to help users with making appointments. Ask for their name, address, email, and phone number when they show interest in making an appointment.")
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
def get_chatmodel_response(question):
    st.session_state['flowmessages'].append(HumanMessage(content=question))
    response = chat(st.session_state['flowmessages'])
    st.session_state['flowmessages'].append(AIMessage(content=response.content))
    return response.content

# Function to store appointment details in MongoDB
def store_appointment_details(name, address, email, phone):
    appointment = {
        "name": name,
        "address": address,
        "email": email,
        "phone": phone
    }
    result = collection.insert_one(appointment)
    return result.inserted_id

# Function to validate user inputs
def validate_input(name, phone, email):
    if not phone.isdigit():
        return "Phone number should be numeric."
    if "@" not in email or "." not in email:
        return "Please provide a valid email address."
    return None

# Chatbot's flow
appointment_flow = {
    "name": None,
    "address": None,
    "email": None,
    "phone": None
}

if 'state' not in st.session_state:
    st.session_state['state'] = "start"

# Ask if the user wants to make an appointment
if st.session_state['state'] == "start":
    input_text = st.text_input("Ask a question related to making an appointment:", key="input_text_start")
    submit_button = st.button("Ask")

    if submit_button and input_text:
        response = get_chatmodel_response(input_text)
        if "make an appointment" in input_text.lower():
            st.session_state['state'] = "ask_details"
            response = "Sure! May I have your name, address, phone number, and email address?"
        st.chat_message("user").write(input_text)
        st.chat_message("assistant").write(response)

# Ask for user details if they want to make an appointment
if st.session_state['state'] == "ask_details":
    name_input = st.text_input("Please provide your name:", key="input_name")
    address_input = st.text_input("Please provide your address:", key="input_address")
    email_input = st.text_input("Please provide your email:", key="input_email")
    phone_input = st.text_input("Please provide your phone number:", key="input_phone")
    submit_button = st.button("Submit Appointment Details")

    if submit_button:
        # Validate the inputs
        validation_error = validate_input(name_input, phone_input, email_input)
        if validation_error:
            st.chat_message("assistant").write(validation_error)
        else:
            # Store the appointment details in MongoDB
            store_appointment_details(name_input, address_input, email_input, phone_input)
            st.chat_message("assistant").write(f"Thank you, {name_input}. We will contact you soon at {phone_input}.")
            st.session_state['state'] = "start"  # Reset to start
