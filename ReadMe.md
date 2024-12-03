# MediAssist - Virtual Health Assistant Chatbot

## Overview

MediAssist is an AI-powered chatbot designed to assist users with healthcare-related queries. It uses LangChain and the LLaMA2 model to process natural language queries, provide helpful responses, and offer a conversational flow for booking health appointments.

This project integrates document-based querying, conversational forms for collecting user details, and integrates a date parser for recognizing and processing dates in various formats. Users can interact with the chatbot, upload documents, and book appointments seamlessly.

## Features

- **Document Querying**: Upload PDF, Word, or text files for the chatbot to extract and respond to questions based on the content of the document.
- **Conversational Form**: Collect user information such as Name, Phone Number, Email, and Appointment details when users request to book an appointment.
- **Date Recognition**: The chatbot can understand and extract dates from natural language inputs (e.g., "next Monday", "tomorrow", or specific dates like "17 December 2024").
- **Validation**: The chatbot validates user inputs, such as ensuring valid email, phone number formats, and correct date formatting.
