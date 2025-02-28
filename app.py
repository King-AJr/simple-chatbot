import os
import uuid
from io import BytesIO

import pyaudio
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from streamlit_chat import message
from interact_with_db import get_bot_response, get_history
from langchain.memory import ConversationBufferMemory
from utils import record_audio_chunk, transcribe_audio, get_response_llm, play_text_to_speech, load_whisper

# ---------- PAGE CONFIGURATION ----------
st.set_page_config(page_title="AI Chatbot and Voice Assistant", layout="wide", initial_sidebar_state="collapsed")

# ---------- HELPER FUNCTION: PDF GENERATION ----------
def create_pdf_with_logo(buffer, text_content, character_name):
    """
    Generates a PDF file in-memory that includes the company logo,
    character name, and the conversation text.
    """
    logo_path = "logo.jpg"
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    
    # Add the company logo (if available)
    try:
        logo = RLImage(logo_path, width=50, height=50)
        story.append(logo)
        story.append(Spacer(1, 12))
    except Exception as e:
        st.error(f"Error loading logo: {str(e)}")
    
    # Add character name header
    styles = getSampleStyleSheet()
    character_header = Paragraph(f"<b>Character:</b> {character_name}", styles['Heading2'])
    story.append(character_header)
    story.append(Spacer(1, 12))
    
    # Add the conversation history text
    conversation_text = text_content.split("\n")
    for line in conversation_text:
        if line.strip():
            paragraph = Paragraph(line, styles['Normal'])
            story.append(paragraph)
            story.append(Spacer(1, 12))
    
    doc.build(story)

# ---------- TEXT CHAT APPLICATION ----------
def text_chat_app():
    # --- CONFIGURATION AND INITIALIZATION ---
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "past_conversations" not in st.session_state:
        st.session_state["past_conversations"] = []
    if "custom_prompt" not in st.session_state:
        st.session_state["custom_prompt"] = ""
    if "character" not in st.session_state:
        st.session_state["character"] = "Custom"
    if "model_name" not in st.session_state:
        st.session_state["model_name"] = "llama-3.3-70b-versatile"

    # --- SIDEBAR (SETTINGS, NEW CHAT, HISTORY) ---
    with st.sidebar:
        st.subheader("Settings ⚙️")
        st.text("Provider: Groq")
        st.session_state["model_name"] = st.selectbox("Select Model:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"])
        if st.button("🆕 New Chat"):
            st.session_state["session_id"] = str(uuid.uuid4())
            st.session_state["messages"] = []
            st.session_state["custom_prompt"] = ""
            st.session_state["character"] = "Custom"
            st.experimental_rerun()

        st.subheader("History 📜")
        past_conversations = st.session_state.get("past_conversations", [])
        for i, conv in enumerate(past_conversations):
            if st.button(conv["display"], key=f"{conv['session_id']}_{i}"):
                st.session_state["session_id"] = conv["session_id"]
                st.session_state["character"] = conv["character"]
                st.session_state["model_name"] = conv["model_name"]
                # Fetch conversation history using get_history function
                history_data = get_history(
                    st.session_state["session_id"],
                    st.session_state["character"],
                    st.session_state["model_name"]
                )
                st.session_state["messages"] = history_data.get("history", [])
                st.experimental_rerun()

    # --- MAIN TITLE AND CHARACTER SELECTION ---
    st.write("#")
    st.markdown("<h5 style='text-align: center; font-weight: bold;'>Choose Your AI Character 🤖</h5>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    selected_character = st.session_state.get("character", "Custom")
    characters = [
        {"display": "🦎 Custom", "value": "Custom"},
        {"display": "🕵️ Sherlock Holmes", "value": "Sherlock Holmes"},
        {"display": "🧪 Marie Curie", "value": "Marie Curie"},
        {"display": "🦾 Iron Man", "value": "Iron Man"},
        {"display": "📖 J.K. Rowling", "value": "J.K. Rowling"}
    ]
    for idx, char in enumerate(characters):
        col = [col1, col2, col3][idx % 3]
        if col.button(char["display"], key=char["value"]):
            if st.session_state["character"] != char["value"]:
                st.session_state["character"] = char["value"]
                st.session_state["messages"] = []
                st.experimental_rerun()

    system_prompt = ""
    if st.session_state.get("character") == "Custom":
        system_prompt = st.text_area("Define your AI Agent:", placeholder="Type your description here...", key="custom_prompt")

    # --- CHAT INPUT AND RESPONSE HANDLING ---
    user_query = st.chat_input("Chat with AI Bot")
    if user_query and user_query.strip():
        chat_response = get_bot_response(user_query, selected_character, st.session_state["model_name"], system_prompt, st.session_state["session_id"])
        bot_response = chat_response.response

        # Append messages to conversation history
        st.session_state["messages"].append({"role": "human", "content": user_query})
        st.session_state["messages"].append({"role": "ai", "content": bot_response})

        conversation_id = st.session_state["session_id"]
        chat_name = f"{selected_character} ({conversation_id[:8]})"
        conv = {
            "session_id": conversation_id,
            "character": selected_character,
            "model_name": st.session_state["model_name"],
            "display": chat_name
        }
        if conv not in st.session_state["past_conversations"]:
            st.session_state["past_conversations"].append(conv)

    # --- DISPLAY CONVERSATION HISTORY ---
    st.write("---")
    st.write(f"*Character: {selected_character}*")
    for msg in st.session_state["messages"]:
        if msg["role"] == "human":
            message(msg["content"], is_user=True)
        else:
            message(msg["content"])

    # --- PDF GENERATION FOR CONVERSATION DOWNLOAD ---
    history_str = ""
    for msg in st.session_state["messages"]:
        role = msg["role"].capitalize()
        content = msg["content"]
        history_str += f"{role}: {content}\n\n"

    pdf_buffer = BytesIO()
    create_pdf_with_logo(pdf_buffer, history_str, selected_character)
    pdf_buffer.seek(0)
    st.download_button(
        label="Download conversation",
        data=pdf_buffer,
        file_name="chat_history.pdf",
        mime="application/pdf"
    )

# ---------- VOICE ASSISTANT APPLICATION ----------
def voice_assistant_app():
    st.markdown('<h1 style="color: darkblue;">AI Voice Assistant️</h1>', unsafe_allow_html=True)
    
    # Initialize conversation memory for voice assistant
    memory = ConversationBufferMemory(memory_key="chat_history")
    # Load the Whisper model once
    model = load_whisper()
    
    # We simulate one recording session per button press.
    if st.button("Start Recording"):
        # Audio stream initialization
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        
        # Record and save one audio chunk
        record_audio_chunk(audio, stream)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        chunk_file = 'temp_audio_chunk.wav'
        text = transcribe_audio(model, chunk_file)
        if text is not None:
            st.markdown(
                f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">Customer 👤: {text}</div>',
                unsafe_allow_html=True
            )
            try:
                os.remove(chunk_file)
            except Exception as e:
                st.error(f"Error removing temp file: {e}")
            response_llm = get_response_llm(user_question=text, memory=memory)
            st.markdown(
                f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">AI Assistant 🤖: {response_llm}</div>',
                unsafe_allow_html=True
            )
            play_text_to_speech(text=response_llm)
        else:
            st.error("Could not transcribe audio.")

# ---------- MAIN APP: TABS FOR SWITCHING BETWEEN TEXT CHAT AND VOICE ASSISTANT ----------
tabs = st.tabs(["Text Chat", "Voice Assistant"])
with tabs[0]:
    text_chat_app()
with tabs[1]:
    voice_assistant_app()
