from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
import os
from sqlalchemy.orm import Session
from database import get_db
from utils import get_current_user
import models
import requests
from pydantic import BaseModel
import io
import pypdf
import docx
from pptx import Presentation
import base64
import uuid
from typing import Optional
from datetime import datetime
from mongodb import chat_history_collection

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/")
async def chat(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    workspace_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    target_model = "llama3"
    prompt_context = ""
    document_info = None
    bot_reply = ""

    # 1. Process uploaded file context if any
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext in [".pdf", ".docx", ".txt"]:
            temp_id = str(uuid.uuid4())
            os.makedirs("documents/raw_files", exist_ok=True)
            temp_path = f"documents/raw_files/temp_{temp_id}{ext}"
            file_bytes = await file.read()
            with open(temp_path, "wb") as f:
                f.write(file_bytes)
            
            try:
                from document_processor import process_document
                pages_text, metadata = process_document(temp_path, temp_id, ext)
                full_text = "\n".join(p["text"] for p in pages_text)
                prompt_context = f"Document Context ({file.filename}):\n{full_text}\n\n"
                
                document_info = {
                    "original_filename": file.filename,
                    "file_type": ext.lstrip('.').upper(),
                    "file_size_bytes": metadata.file_size_bytes,
                    "page_count": metadata.page_count,
                    "title": metadata.title,
                    "authors": metadata.authors,
                    "keywords": metadata.keywords,
                }
            except Exception as e:
                print(f"Error processing document in chat: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    # 2. Get Workspace Context
    if workspace_id and not prompt_context:
        from routers.rag import _build_document_lookup
        from vector_store import get_workspace_index
        from rag_engine import rag_query
        
        workspace = db.query(models.Workspace).filter(
            models.Workspace.workspace_id == workspace_id,
            models.Workspace.user_id == current_user.id
        ).first()
        
        if workspace:
            ws_index = get_workspace_index(workspace_id)
            if ws_index.total_vectors > 0:
                document_lookup = _build_document_lookup(db, workspace_id)
                result = rag_query(
                    question=message,
                    workspace_id=workspace_id,
                    top_k=5,
                    similarity_threshold=0.75,
                    document_lookup=document_lookup
                )
                bot_reply = result.get("answer", "")

    # 3. Fallback to basic generation
    if not bot_reply:
        final_prompt = prompt_context + message if prompt_context else message

        # Send message to Ollama LLM
        try:
            payload = {
                "model": target_model,
                "prompt": final_prompt,
                "stream": False
            }

            ollama_response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=300
            )
            ollama_response.raise_for_status()
            bot_reply = ollama_response.json().get("response", "")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    # ── Save to MongoDB Atlas ─────────────────────────────────────────────
    await chat_history_collection.insert_one({
        "user_id":      current_user.id,
        "user_name":    current_user.name,
        "user_email":   current_user.email,
        "session_id":   session_id,
        "user_message": message,
        "bot_reply":    bot_reply,
        "model":        target_model,
        "created_at":   datetime.utcnow()
    })

    # ── Also Save to SQLite (backup) ──────────────────────────────────────
    chat_entry = models.ChatHistory(
        user_id=current_user.id,
        session_id=session_id,
        user_message=message,
        bot_reply=bot_reply
    )
    db.add(chat_entry)
    db.commit()

    return {"reply": bot_reply, "session_id": session_id, "document_info": document_info}


@router.get("/sessions")
async def get_sessions(
    current_user: models.User = Depends(get_current_user)
):
    """Get all chat sessions from MongoDB."""
    from motor.motor_asyncio import AsyncIOMotorClient
    cursor = chat_history_collection.find(
        {"user_id": current_user.id},
        {"session_id": 1, "user_message": 1, "created_at": 1}
    ).sort("created_at", -1)

    sessions = {}
    async for doc in cursor:
        sid = doc["session_id"]
        if sid not in sessions:
            sessions[sid] = {
                "session_id": sid,
                "title": doc["user_message"][:30] + "..." if len(doc["user_message"]) > 30 else doc["user_message"],
                "created_at": str(doc.get("created_at", ""))
            }

    return list(sessions.values())


@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    current_user: models.User = Depends(get_current_user)
):
    """Get chat history for a session from MongoDB."""
    cursor = chat_history_collection.find({
        "user_id": current_user.id,
        "session_id": session_id
    }).sort("created_at", 1)

    history = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["created_at"] = str(doc.get("created_at", ""))
        history.append(doc)

    return history