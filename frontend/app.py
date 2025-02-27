import streamlit as st
import uuid
import requests

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
    st.title("Settings")
    st.text("Provider: Groq")
    model_name = st.selectbox("Select Model:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"])
    
    # New Chat Button
    if st.button("🆕 New Chat"):
        st.session_state["session_id"] = str(uuid.uuid4())
        st.session_state["conversation"] = []
        st.session_state["custom_prompt"] = ""
        st.experimental_rerun()
    
    # Conversation History List
    st.subheader("Previous Conversations")
    past_conversations = st.session_state.get("past_conversations", [])
    for conv in past_conversations:
        if st.button(conv):
            st.session_state["session_id"] = conv
            st.experimental_rerun()

# Title
st.markdown(
    "<h1 style='text-align: center;'>Team Alpha Chameleon Bot 🦎</h1>", 
    unsafe_allow_html=True
)

# Generate or retrieve a unique session ID
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

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
    "<h4 style='text-align: center; font-weight: bold;'>Choose Your AI Character 🤖</h4>", 
    unsafe_allow_html=True
)
col1, col2, col3 = st.columns(3)

selected_character = st.session_state.get("character", "Custom")

for idx, char in enumerate(characters):
    col = [col1, col2, col3][idx % 3]
    if col.button(char["display"], key=char["value"]):
        st.session_state["character"] = char["value"]
        selected_character = char["value"]

# Custom prompt input if "Custom" is selected
system_prompt = ""
if st.session_state.get("character") == "Custom":
    system_prompt = st.text_area("Define your AI Character:", height=30, placeholder="Type your description here...", key="custom_prompt")

# User query input
user_query = st.chat_input("Chat with Chameleon Bot")

API_URL = "http://127.0.0.1:9999"

def fetch_history():
    """Fetch conversation history from the backend for the current session."""
    params = {
        "session_id": st.session_state["session_id"],
        "character": selected_character,
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
            
            # Store past conversations
            if "past_conversations" not in st.session_state:
                st.session_state["past_conversations"] = []
            chat_name = f"{selected_character} ({st.session_state['session_id'][:8]})"
            if chat_name not in st.session_state["past_conversations"]:
                st.session_state["past_conversations"].append(chat_name)
        except requests.exceptions.RequestException:
            st.error("⚠️ Error in response! Ensure API is available.")

# Display conversation history
st.write("---")  # Divider line
history = fetch_history()
for msg in history:
    if msg["role"] == "human":
        st.markdown(f"🙂 **You:** {msg['content']}")
    else:
        st.markdown(f"🤖 **Bot:** {msg['content']}")
