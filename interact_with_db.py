
import logging
import os
from fastapi import HTTPException
from schema import ChatResponse
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from google.cloud import firestore
from langchain_google_firestore import FirestoreChatMessageHistory
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
COLLECTION_NAME = "chat_history"

client = firestore.Client(project=PROJECT_ID)

def get_bot_response(user_query, character, model_name, system_prompt, session_id):
    """
    Generate an AI response.
    This function uses OpenAI's ChatCompletion API. Make sure to set your API key in st.secrets.
    The selected model (from the sidebar) is ignored for the API call and GPT-3.5-turbo is used instead.
    """

    AI_CHARACTERS = {
        "Sherlock Holmes": "You are Sherlock Holmes, the world's greatest detective.",
        "Marie Curie": "You are Marie Curie, the first woman to win a Nobel Prize and the only person to win in two scientific fields (Physics and Chemistry)",
        "Iron Man": "You are Tony Stark, aka Iron Man, a genius billionaire playboy philanthropist.",
        "J.K. Rowling": "You are J.K. Rowling, a British author best known for creating the Harry Potter series, which is one of the best-selling book franchises in history"
    }       

    conversation_id = f"{session_id}_{character}_{model_name}"
    
    chat_history = FirestoreChatMessageHistory(
        session_id=conversation_id,
        collection=COLLECTION_NAME,
        client=client,
    )

    if character in AI_CHARACTERS:
        system_prompt = AI_CHARACTERS[character]
    else:
        if system_prompt.strip():
            system_prompt = system_prompt
        else:
            raise HTTPException(status_code=400, detail="No valid character prompt provided.")

    chat = ChatGroq(temperature=0.3, model_name=model_name, verbose=True)

    human = "{text}"
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", human)])

    chat_history.add_user_message(user_query)
    chain = prompt | chat
    ai_response = chain.invoke(chat_history.messages)
    chat_history.add_ai_message(ai_response.content)

    return ChatResponse(response=ai_response.content)


def get_history(session_id: str, character: str, model_name: str):
    """
    Retrieve chat history for the given composite key.
    """
    conversation_id = f"{session_id}_{character}_{model_name}"
    chat_history = FirestoreChatMessageHistory(
        session_id=conversation_id,
        collection=COLLECTION_NAME,
        client=client,
    )

    conversation = []
    for msg in chat_history.messages:
        role = "ai" if msg.__class__.__name__ == "AIMessage" else "human"
        conversation.append({"role": role, "content": msg.content})

    return {"history": conversation}