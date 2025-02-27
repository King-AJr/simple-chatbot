import streamlit as st
import uuid
import requests
import yaml
from yaml.loader import SafeLoader

def load_config():
    with open('security.yaml') as file:
        return yaml.load(file, Loader=SafeLoader)

config = load_config()
API_URL = "http://127.0.0.1:9999"  # FastAPI endpoint base URL
st.set_page_config(page_title="AI Chatbot", layout="wide", initial_sidebar_state="collapsed")
# Suppose you have a function that checks with your Flask backend:
def check_backend_login():
    # This is a placeholder: replace it with your actual login check.
    # For example, you might call an endpoint or read a secure cookie.
    # Return a dict with login details if the user is logged in.
    return {"success": True, "username": "jsmith", "name": "John Smith"}

# Attempt to get login status from your backend.
backend_status = check_backend_login()
if backend_status.get("success"):
    st.session_state["authentication_status"] = True
    st.session_state["username"] = backend_status["username"]
    st.session_state["name"] = backend_status["name"]

# --- Authentication Section ---
# Only show the login/register UI if the user is not already logged in.
if not st.session_state.get("authentication_status"):
    auth_option = st.sidebar.radio("Select Option", ["Login", "Register"])

    if auth_option == "Login":
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            session_id = st.session_state.get("session_id", str(uuid.uuid4()))
            payload = {
                "username": username,
                "password": password,
                "action": "login",
                "session_id": session_id
            }
            try:
                response = requests.post(f"{API_URL}/login", json=payload, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data.get("success"):
                    st.success(f"Welcome {data.get('name', username)}!")
                    st.session_state["session_id"] = session_id
                    st.session_state["username"] = username
                    st.session_state["name"] = data.get("name", username)
                else:
                    st.error("Login failed: " + data.get("detail", "Unknown error"))
            except requests.exceptions.RequestException as e:
                st.error(f"Login failed: {e}")
        st.stop()

    elif auth_option == "Register":
        st.header("Register New Account")
        new_name = st.text_input("Name")
        new_username = st.text_input("Username")
        email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        new_password_confirm = st.text_input("Confirm Password", type="password")
        
        if st.button("Register"):
            if new_password == new_password_confirm:
                payload = {
                    "name": new_name,
                    "username": new_username,
                    "password": new_password,
                    "email": email
                }
                try:
                    response = requests.post(f"{API_URL}/register", json=payload, timeout=10)
                    response.raise_for_status()
                    st.success("Registration successful! Please login.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Registration failed: {e}")
            else:
                st.error("Passwords do not match")
        st.stop()

# --- Logout Section ---
# if st.sidebar.button("Logout"):
#     payload = {
#         "username": st.session_state.get("username"),
#         "action": "logout",
#         "session_id": st.session_state.get("session_id")
#     }
#     try:
#         response = requests.post(f"{API_URL}/logout", json=payload, timeout=10)
#         response.raise_for_status()
#         st.success("Logged out successfully!")
#         st.session_state.clear()
#     except requests.exceptions.RequestException:
#         st.error("⚠️ Failed to send logout information to backend.")


# --- Rest of Your Chatbot Code ---

st.markdown(
    """
    <style>
    div[data-testid="stTextArea"] textarea {
        height: 50px !important;
        min-height: 50px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.title("Settings")
    st.text("Provider: Groq")
    model_name = st.selectbox("Select Model:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"])
    if st.button("🆕 New Chat"):
        st.session_state["session_id"] = str(uuid.uuid4())
        st.session_state["conversation"] = []
        st.session_state["custom_prompt"] = ""
        st.experimental_rerun()
    st.subheader("Previous Conversations")
    past_conversations = st.session_state.get("past_conversations", [])
    for conv in past_conversations:
        if st.button(conv):
            st.session_state["session_id"] = conv
            st.experimental_rerun()

st.markdown("<h1 style='text-align: center;'>Team Alpha Chameleon Bot 🦎</h1>", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

characters = [
    {"display": "🦎 Custom", "value": "Custom"},
    {"display": "🕵️ Sherlock Holmes", "value": "Sherlock Holmes"},
    {"display": "🧪 Marie Curie", "value": "Marie Curie"},
    {"display": "🦾 Iron Man", "value": "Iron Man"},
    {"display": "📖 J.K. Rowling", "value": "J.K. Rowling"}
]

st.write("#")
st.markdown("<h4 style='text-align: center; font-weight: bold;'>Choose Your AI Character 🤖</h4>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

selected_character = st.session_state.get("character", "Custom")
for idx, char in enumerate(characters):
    col = [col1, col2, col3][idx % 3]
    if col.button(char["display"], key=char["value"]):
        st.session_state["character"] = char["value"]
        selected_character = char["value"]

system_prompt = ""
if st.session_state.get("character") == "Custom":
    system_prompt = st.text_area("Define your AI Character:", height=30, placeholder="Type your description here...", key="custom_prompt")

user_query = st.chat_input("Chat with Chameleon Bot")

def fetch_history():
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

if user_query and user_query.strip():
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
        # Store past conversation name for easy access
        if "past_conversations" not in st.session_state:
            st.session_state["past_conversations"] = []
        chat_name = f"{selected_character} ({st.session_state['session_id'][:8]})"
        if chat_name not in st.session_state["past_conversations"]:
            st.session_state["past_conversations"].append(chat_name)
    except requests.exceptions.RequestException:
        st.error("⚠️ Error in response! Ensure API is available.")

st.write("---")
history = fetch_history()
for msg in history:
    if msg["role"] == "human":
        st.markdown(f"🙂 **You:** {msg['content']}")
    else:
        st.markdown(f"🤖 {selected_character}: {msg['content']}")
