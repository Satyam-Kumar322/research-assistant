from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from utils import get_current_user
import models
import requests
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/")
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Send message to Ollama LLM
    try:
        ollama_response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": req.message,
                "stream": False
            },
            timeout=60
        )
        bot_reply = ollama_response.json()["response"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    # Save to database
    chat_entry = models.ChatHistory(
        user_id=current_user.id,
        user_message=req.message,
        bot_reply=bot_reply
    )
    db.add(chat_entry)
    db.commit()

    return {"reply": bot_reply}


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    history = db.query(models.ChatHistory)\
                .filter(models.ChatHistory.user_id == current_user.id)\
                .order_by(models.ChatHistory.created_at.desc())\
                .all()
    return history 
