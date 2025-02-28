import streamlit as st
import uuid
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from streamlit_chat import message
from interact_with_db import get_bot_response, get_history

# ---------- CONFIGURATION AND INITIALIZATION ----------
logo_path = "logo.jpg"

# Set page configuration
st.set_page_config(page_title="AI Chatbot", layout="wide", initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    /* Adjust the height of the text area */
    div[data-testid="stTextArea"] textarea {
        height: 50px !important;
        min-height: 50px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state variables if they don't exist
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

# ---------- SIDEBAR (SETTINGS, NEW CHAT, HISTORY) ----------
# Sidebar
with st.sidebar:
    st.subheader("Settings ⚙️")
    st.text("Provider: Groq")
    model_name = st.selectbox("Select Model:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"])

    # New Chat Button
    if st.button("🆕 New Chat"):
        st.session_state["session_id"] = str(uuid.uuid4())
        st.session_state["messages"] = []
        st.session_state["custom_prompt"] = ""
        st.session_state["character"] = "Custom"  # default value
        st.rerun()

    # Past Conversations List (each conversation stores full details)
    st.subheader("History 📜")
    past_conversations = st.session_state.get("past_conversations", [])
    for i, conv in enumerate(past_conversations):
        if st.button(conv["display"], key=f"{conv['session_id']}_{i}"):
            # Update session state keys for the selected conversation
            st.session_state["session_id"] = conv["session_id"]
            st.session_state["character"] = conv["character"]
            st.session_state["model_name"] = conv["model_name"]
            # Fetch the past conversation history from Firestore using your get_history function
            history_data = get_history(
                st.session_state["session_id"],
                st.session_state["character"],
                st.session_state["model_name"]
            )
            # Update the messages list with the fetched history
            st.session_state["messages"] = history_data.get("history", [])
            st.rerun()

# ---------- MAIN TITLE AND CHARACTER SELECTION ----------
st.markdown(
    "<h1 style='text-align: center;'>Team Alpha Chameleon Bot 🦎</h1>", 
    unsafe_allow_html=True
)

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state["messages"] = []
session_id = st.session_state["session_id"]


characters = [
    {"display": "🦎 Custom", "value": "Custom"},
    {"display": "🕵️ Sherlock Holmes", "value": "Sherlock Holmes"},
    {"display": "🧪 Marie Curie", "value": "Marie Curie"},
    {"display": "🦾 Iron Man", "value": "Iron Man"},
    {"display": "📖 J.K. Rowling", "value": "J.K. Rowling"}
]



st.write("#")
st.markdown(
    "<h5 style='text-align: center; font-weight: bold;'>Choose Your AI Character 🤖</h5>", 
    unsafe_allow_html=True
)
col1, col2, col3 = st.columns(3)
selected_character = st.session_state.get("character", "Custom")

for idx, char in enumerate(characters):
    col = [col1, col2, col3][idx % 3]
    if col.button(char["display"], key=char["value"]):
        # Only update if the character has really changed
        if st.session_state["character"] != char["value"]:
            st.session_state["character"] = char["value"]
            # Clear the conversation history for the new character
            st.session_state["messages"] = []
            st.rerun()

system_prompt = ""
if st.session_state.get("character") == "Custom":
    system_prompt = st.text_area("Define your AI Agent:", placeholder="Type your description here...", key="custom_prompt")

# ---------- CHAT INPUT AND RESPONSE HANDLING ----------

user_query = st.chat_input("Chat with Chameleon Bot")

if user_query and user_query.strip():
    chat_response = get_bot_response(user_query, selected_character, st.session_state["model_name"], system_prompt, session_id)

    bot_response = chat_response.response
    
    # Append the new messages to session state
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

# ---------- DISPLAY CONVERSATION HISTORY ----------

st.write("---")
st.write(f"*Character: {selected_character}*")
for msg in st.session_state["messages"]:
    if msg["role"] == "human":
        message(msg["content"], is_user=True)
    else:
        message(msg["content"])

# ---------- PDF GENERATION FOR CONVERSATION DOWNLOAD ----------

def create_pdf_with_logo(buffer, text_content, character_name):
    """
    Generates a PDF file in-memory that includes the company logo,
    character name, and the conversation text.
    """
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    
    # Add the company logo (if exists)
    try:
        logo = RLImage(logo_path, width=50, height=50)
        story.append(logo)
        story.append(Spacer(1, 12))
    except Exception as e:
        st.error(f"Error loading logo: {str(e)}")
    
    # Add the character name header
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
    
    # Build the PDF and write it to the buffer
    doc.build(story)

# Convert the conversation messages to a text summary
history_str = ""
for msg in st.session_state["messages"]:
    role = msg["role"].capitalize()
    content = msg["content"]
    history_str += f"{role}: {content}\n\n"

pdf_buffer = BytesIO()
create_pdf_with_logo(pdf_buffer, history_str, selected_character)
pdf_buffer.seek(0)  # reset buffer position

st.download_button(
    label="Download conversation",
    data=pdf_buffer,
    file_name="chat_history.pdf",
    mime="application/pdf"
)
