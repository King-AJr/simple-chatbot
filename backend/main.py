# backend/main.py
import logging
from fastapi import FastAPI, HTTPException
from schema import ChatRequest, ChatResponse
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from google.cloud import firestore
from langchain_google_firestore import FirestoreChatMessageHistory
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

PROJECT_ID = "ai-chatbot-df7c2"
COLLECTION_NAME = "chat_history"

client = firestore.Client(project=PROJECT_ID)

# Predefined AI Characters
AI_CHARACTERS = {
    "Sherlock Holmes": "You are Sherlock Holmes, the world's greatest detective.",
    "Iron Man": "You are Tony Stark, aka Iron Man, a genius billionaire playboy philanthropist.",
    "Yoda": "You are Yoda, a wise Jedi Master with great wisdom and unique speech patterns."
}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # Create a composite chat id based on session, character, and model.
    conversation_id = f"{request.session_id}_{request.character}_{request.model_name}"
    
    # Use the composite id for chat history
    chat_history = FirestoreChatMessageHistory(
        session_id=conversation_id,
        collection=COLLECTION_NAME,
        client=client,
    )

    logger.info("Response: %s", request.system_prompt)
    if request.character in AI_CHARACTERS:
        system_prompt = AI_CHARACTERS[request.character]
    else:
        if request.system_prompt.strip():
            system_prompt = request.system_prompt
        else:
            raise HTTPException(status_code=400, detail="No valid character prompt provided.")

    chat = ChatGroq(temperature=0.3, model_name=request.model_name, max_tokens=200, verbose=True)
    human = "{text}"
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", human)])

    chat_history.add_user_message(request.messages[0])
    chain = prompt | chat
    ai_response = chain.invoke({"text": request.messages[0]})
    chat_history.add_ai_message(ai_response.content)

    logger.info("Current Chat History: %s", chat_history.messages)
    return ChatResponse(response=ai_response.content)


@app.get("/history")
async def get_history(session_id: str, character: str, model_name: str):
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
