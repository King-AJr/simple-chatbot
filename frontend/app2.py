import streamlit as st
import uuid
from google.cloud import firestore
from langchain_google_firestore import FirestoreChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


st.set_page_config(page_title="AI Chatbot", layout="centered")
st.title("AI Chatbot Agents")


if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
session_id = st.session_state["session_id"]

PROJECT_ID = "ai-chatbot-df7c2"
COLLECTION_NAME = "chat_history"
client = firestore.Client(project=PROJECT_ID)


AI_CHARACTERS = {
    "Sherlock Holmes": "You are Sherlock Holmes, the world's greatest detective.",
    "Iron Man": "You are Tony Stark, aka Iron Man, a genius billionaire playboy philanthropist.",
    "Yoda": "You are Yoda, a wise Jedi Master with great wisdom and unique speech patterns."
}

characters = ["Custom", "Sherlock Holmes", "Iron Man", "Yoda"]
character = st.selectbox("Choose your AI Character:", characters)
st.text("Provider: Groq")
model_name = st.selectbox("Select Model:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"])


if character == "Custom":
    system_prompt = st.text_area("Define your AI Agent:", height=70, placeholder="Type your system prompt here...")
else:
    system_prompt = AI_CHARACTERS.get(character)

user_query = st.text_area("Enter your query:", height=150, placeholder="Ask Anything!")

conversation_id = f"{session_id}_{character}_{model_name}"

chat_history = FirestoreChatMessageHistory(
    session_id=conversation_id,
    collection=COLLECTION_NAME,
    client=client,
)

if st.button("Ask Agent!"):
    if user_query.strip():
        chat_history.add_user_message(user_query)
        
        human_template = "{text}"
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template)
        ])
        
        messages = chat_history.messages
        
        chat = ChatGroq(temperature=0.3, model_name=model_name, verbose=True)
        chain = prompt | chat
        ai_response = chain.invoke(messages)
        
        # Save the AI response back to Firestore.
        chat_history.add_ai_message(ai_response.content)
        

st.write("### Conversation History")
for msg in chat_history.messages:
    role = "ai" if msg.__class__.__name__ == "AIMessage" else "human"
    if role == "ai":
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
                {msg.content}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
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
                {msg.content}
            </div>
            """,
            unsafe_allow_html=True,
        )
