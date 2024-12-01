import streamlit as st
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import pymongo
import fitz  # PyMuPDF
from docx import Document

# MongoDB Setup
mongo_uri = "mongodb+srv://msupran17:supran@supran.afauf7y.mongodb.net/?retryWrites=true&w=majority&appName=Supran"
client = pymongo.MongoClient(mongo_uri)
db = client["Appointments"]
collection = db["appointments"]

# Streamlit UI Setup
st.set_page_config(page_title="MediAssist - Your Virtual Assistant", layout="wide")
st.title("MediAssist: Your AI-powered Virtual Assistant")

# Initialize Llama 2 via LangChain
try:
    llm = Ollama(model="llama2", base_url="http://localhost:11434")
    chat = ChatOllama(llm=llm)
    st.sidebar.success("Connected to Llama 2!")
except Exception as e:
    st.sidebar.error(f"Error connecting to Llama 2: {e}")
    st.stop()

# Initialize Session States
if "conversation_state" not in st.session_state:
    st.session_state["conversation_state"] = "start"  # Default state
    st.session_state["user_data"] = {}  # Store appointment details
    st.session_state["messages"] = [
        SystemMessage(content="You are an AI assistant that helps users make appointments, "
                              "answer general questions, and engage in natural conversations. "
                              "When a user asks to make an appointment, guide them through the process. "
                              "Otherwise, provide helpful responses.")
    ]

# File Upload and Context Extraction
def extract_text_from_pdf(pdf_file):
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    return "".join([pdf_document.load_page(i).get_text("text") for i in range(pdf_document.page_count)])

def extract_text_from_word(word_file):
    document = Document(word_file)
    return "\n".join([p.text for p in document.paragraphs])

def extract_text_from_txt(txt_file):
    return txt_file.read().decode("utf-8")

uploaded_file = st.file_uploader("Upload a hospital document (PDF, DOCX, TXT):", type=["pdf", "docx", "txt"])
document_context = ""

if uploaded_file:
    try:
        if uploaded_file.type == "application/pdf":
            document_context = extract_text_from_pdf(uploaded_file)[:1000]
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            document_context = extract_text_from_word(uploaded_file)[:1000]
        elif uploaded_file.type == "text/plain":
            document_context = extract_text_from_txt(uploaded_file)[:1000]
        st.sidebar.success("Document uploaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error processing document: {e}")

# Function: General Chat Response
def get_chatbot_response(user_input, context=None):
    if context:
        st.session_state["messages"].append(HumanMessage(content=f"Context: {context}"))
    st.session_state["messages"].append(HumanMessage(content=user_input))
    response = chat(st.session_state["messages"])
    st.session_state["messages"].append(AIMessage(content=response.content))
    return response.content

# Display Chat History
st.divider()
for msg in st.session_state["messages"]:
    if isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)
    elif isinstance(msg, AIMessage):
        st.chat_message("assistant").write(msg.content)

# Conversation Flow
user_input = st.text_input("Your message:", key="user_input", label_visibility="collapsed")
if st.button("Send"):
    with st.spinner("Thinking..."):
        if "appointment" in user_input.lower():
            # Switch state to appointment flow
            st.session_state["conversation_state"] = "collect_details"
            response = get_chatbot_response(f"User wants to make an appointment. The message: {user_input}", context=document_context)
        else:
            # General query handling
            response = get_chatbot_response(user_input, context=document_context)
        
        st.session_state["messages"].append(AIMessage(content=response))
        st.chat_message("assistant").write(response)

# Appointment Flow
if st.session_state["conversation_state"] == "collect_details":
    if "name" not in st.session_state["user_data"]:
        response = get_chatbot_response("What is your name?", context=document_context)
        st.session_state["messages"].append(AIMessage(content=response))
        st.session_state["conversation_state"] = "ask_name"
    elif "phone" not in st.session_state["user_data"]:
        response = get_chatbot_response("Please provide your phone number.", context=document_context)
        st.session_state["messages"].append(AIMessage(content=response))
        st.session_state["conversation_state"] = "ask_phone"
    elif "email" not in st.session_state["user_data"]:
        response = get_chatbot_response("What is your email address?", context=document_context)
        st.session_state["messages"].append(AIMessage(content=response))
        st.session_state["conversation_state"] = "ask_email"
    elif "appointment_date" not in st.session_state["user_data"]:
        response = get_chatbot_response("When would you like to schedule the appointment?", context=document_context)
        st.session_state["messages"].append(AIMessage(content=response))
        st.session_state["conversation_state"] = "ask_date"
    else:
        # Final confirmation
        name = st.session_state["user_data"].get("name", "")
        phone = st.session_state["user_data"].get("phone", "")
        email = st.session_state["user_data"].get("email", "")
        date = st.session_state["user_data"].get("appointment_date", "")
        
        appointment_details = f"Name: {name}, Phone: {phone}, Email: {email}, Appointment Date: {date}"
        response = get_chatbot_response(f"Confirm the appointment: {appointment_details}", context=document_context)
        st.session_state["messages"].append(AIMessage(content=response))
        st.session_state["conversation_state"] = "confirm_appointment"

# Confirmation Flow
if st.session_state["conversation_state"] == "confirm_appointment":
    user_input = st.text_input("Confirm Appointment:", label_visibility="collapsed")
    if st.button("Confirm"):
        # Save to MongoDB
        collection.insert_one(st.session_state["user_data"])
        st.session_state["messages"].append(AIMessage(content="Your appointment is confirmed! Thank you."))
        st.session_state["conversation_state"] = "start"  # Reset the state to start new conversation

