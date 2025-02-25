from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    session_id: str
    character: str           
    model_name: str
    system_prompt: str         
    messages: List[str]
    allow_search: Optional[bool] = False

class ChatResponse(BaseModel):
    response: str