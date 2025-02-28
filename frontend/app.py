import streamlit as st
import uuid
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from streamlit_chat import message


# Define logo path
logo_path = "logo.jpg"

# Page config
st.set_page_config(page_title="AI Chatbot", layout="wide", initial_sidebar_state= "collapsed")
# set default text area size for Streamlit with CSS
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
            st.session_state["session_id"] = conv["session_id"]
            st.session_state["character"] = conv["character"]
            st.session_state["model_name"] = conv["model_name"]
            st.rerun()


# Main Title
st.markdown(
    "<h1 style='text-align: center;'>Team Alpha Chameleon Bot 🦎</h1>", 
    unsafe_allow_html=True
)

# Generate or retrieve a unique session ID and messages list if not already set
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Define the characters with a mapping (display text with emoji and plain value)
characters = [
    {"display": "🦎 Custom", "value": "Custom"},
    {"display": "🕵️ Sherlock Holmes", "value": "Sherlock Holmes"},
    {"display": "🧪 Marie Curie", "value": "Marie Curie"},
    {"display": "🦾 Iron Man", "value": "Iron Man"},
    {"display": "📖 J.K. Rowling", "value": "J.K. Rowling"}
]

# Character selection buttons
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
        st.session_state["character"] = char["value"]
        selected_character = char["value"]

# Only show the custom prompt if "Custom" is selected
system_prompt = ""
if st.session_state.get("character") == "Custom":
    system_prompt = st.text_area("Define your AI character with 'You are (character name)':", height=30, placeholder="Type your description here...", key="custom_prompt")

# User query input using chat_input
user_query = st.chat_input("Chat with Chameleon Bot")

API_URL = "http://127.0.0.1:9999"

def fetch_history(session_id, character, model_name):
    """Fetch conversation history from the backend for the given composite chat."""
    params = {
        "session_id": session_id,
        "character": character,
        "model_name": model_name,
    }
    history_url = f"{API_URL}/history"
    try:
        response = requests.get(history_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("history", [])
    except requests.exceptions.RequestException:
        st.error("⚠️ Cannot connect to the backend. Ensure FastAPI is running.")
        return []

if user_query:
    if user_query.strip():
        payload = {
            "session_id": st.session_state["session_id"],
            "character": selected_character,
            "model_name": model_name,
            "system_prompt": system_prompt if selected_character == "Custom" else "",
            "messages": [user_query],
        }
        try:
            response = requests.post(f"{API_URL}/chat", json=payload, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            bot_response = response_data.get("response", "No response received.")
            st.session_state["messages"].append({"role": "human", "content": user_query})
            st.session_state["messages"].append({"role": "ai", "content": bot_response})
            
            # Save this conversation in past_conversations with full details
            if "past_conversations" not in st.session_state:
                st.session_state["past_conversations"] = []
            conversation_id = st.session_state["session_id"]
            chat_name = f"{selected_character} ({conversation_id[:8]})"
            conv = {
                "session_id": conversation_id,
                "character": selected_character,
                "model_name": model_name,
                "display": chat_name
            }
            # Add conversation if not already present
            if conv not in st.session_state["past_conversations"]:
                st.session_state["past_conversations"].append(conv)
        except requests.exceptions.RequestException:
            st.error("⚠️ Error in response! Ensure API is available.")

# Display conversation history with appropriate emojis
st.write("---")  # Divider line
history = fetch_history(st.session_state["session_id"], selected_character, model_name)
st.write(f"*Character: {selected_character}*")
try:
    for msg in history:
        if msg["role"] == "human":
            message(msg['content'], is_user=True)
        else:
            message(msg['content'])
except st.errors.DuplicateWidgetID:
     st.warning("⚠️ Refresh the page and assign your characters using 'You are (character name)' next time")


# Function to generate a PDF with the conversation summary and write it directly to the buffer
def create_pdf_with_logo(buffer, text_content, character_name):
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    
    # Add the company logo (optional)
    logo = Image(logo_path, width=50, height=50)
    story.append(logo)
    story.append(Spacer(1, 12))  # Space between logo and text

    # Add the character name at the top
    styles = getSampleStyleSheet()
    character_header = Paragraph(f"<b>Character:</b> {character_name}", styles['Heading2'])
    story.append(character_header)
    story.append(Spacer(1, 12))  # Space after character name
    
    # Add the conversation history text
    conversation_text = text_content.split("\n")
    for line in conversation_text:
        if line.strip():  # Add only non-empty lines
            paragraph = Paragraph(line, styles['Normal'])
            story.append(paragraph)
            story.append(Spacer(1, 12))  # Add space between each paragraph

    # Build the PDF and write it to the buffer
    doc.build(story)

# Convert the history list to a string
history_str = ""
for msg in history:
    role = msg["role"].capitalize()
    content = msg["content"]
    history_str += f"{role}: {content}\n\n"
    
# Generate the PDF in-memory
pdf_buffer = BytesIO()
create_pdf_with_logo(pdf_buffer, history_str, selected_character)

# Button for downloading chat history
st.download_button(label= "Download conversation", data=pdf_buffer, file_name="chat_history.pdf", 
    mime="application/pdf")
