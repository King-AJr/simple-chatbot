import streamlit as st
import uuid
import requests

st.set_page_config(page_title="AI Chatbot", layout="centered")
st.title("AI Chatbot Agents")

# Generate or retrieve a unique base session ID for the user.
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

characters = [ "Custom", "Sherlock Holmes", "Iron Man", "Yoda"]
character = st.selectbox("Choose your AI Character:", characters)

st.text("Provider: Groq")
model_name = st.selectbox("Select Model:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"])

if character == "Custom":
    system_prompt = st.text_area("Define your AI Agent:", height=70, placeholder="Type your system prompt here...")

user_query = st.text_area("Enter your query:", height=150, placeholder="Ask Anything!")

API_URL = "http://127.0.0.1:9999"

def fetch_history():
    """Fetch conversation history from the backend for the current composite chat ID."""
    params = {
        "session_id": st.session_state["session_id"],
        "character": character,
        "model_name": model_name,
    }
    history_url = f"{API_URL}/history"
    response = requests.get(history_url, params=params)
    if response.status_code == 200:
        return response.json().get("history", [])
    else:
        st.error("Error fetching chat history!")
        return []

if st.button("Ask Agent!"):
    if user_query.strip():
        payload = {
            "session_id": st.session_state["session_id"],
            "character": character,
            "model_name": model_name,
            "system_prompt": system_prompt if character == "Custom" else "",
            "messages": [user_query],
        }

        response = requests.post(f"{API_URL}/chat", json=payload)
        if response.status_code == 200:
            response_data = response.json()
            # st.subheader("Agent Response")
            # st.markdown(f"**Final Response:** {response_data['response']}")
        else:
            st.error("Error in response!")

# Display conversation history for the current composite chat (session + character + model)
st.write("### Conversation History")
history = fetch_history()
for msg in history:
    if msg["role"] == "ai":
        # AI messages on the left.
        st.markdown(
            f"""
            <div style="
                text-align: left;
                background-color: #000;
                padding: 10px;
                border-radius: 10px;
                margin: 10px 0;
                max-width: 70%;
            ">
                {msg['content']}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Human messages on the right.
        st.markdown(
            f"""
            <div style="
                text-align: right;
                background-color: #262730;
                padding: 10px;
                border-radius: 10px;
                margin: 10px 0;
                max-width: 70%;
                margin-left: auto;
            ">
                {msg['content']}
            </div>
            """,
            unsafe_allow_html=True,
        )
