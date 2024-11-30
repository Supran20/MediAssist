import streamlit as st
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import fitz  # PyMuPDF
from docx import Document  # For Word files

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

# Streamlit UI setup
st.set_page_config(page_title="MediAssist - Your Virtual Health Assistant", layout="wide")
st.header("Welcome to MediAssist - Your Virtual Health Assistant")

# Initialize session state for conversation
if 'flowmessages' not in st.session_state:
    st.session_state['flowmessages'] = [
        SystemMessage(content="You are MediAssist, an AI-powered virtual health assistant. You are here to provide helpful, accurate, and empathetic responses to patients and visitors. You can answer questions about the hospital's services, departments, staff, and general health information.")
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

if submit_button and input_text:
    with st.spinner("Thinking..."):
        response = get_chatmodel_response(input_text, context=document_context if uploaded_file else None)
    # Display the new messages immediately
    with chat_container:  # Ensure new messages appear at the top
        st.chat_message("user").write(input_text)
        st.chat_message("assistant").write(response)