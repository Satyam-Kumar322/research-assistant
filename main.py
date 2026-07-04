from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os

from database import engine, Base
from mongodb import test_connection

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Intelligent Research Assistant",
    description="Secure User Authentication and Personal Workspace Management",
    version="1.0.0"
)

# ── Startup Event ─────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    await test_connection()

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static & Templates ────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── Routers ───────────────────────────────────────────────────────────────────
from routers import auth, workspace, chat, documents, cleaning, rag

app.include_router(auth.router,      prefix="/api/auth",      tags=["Authentication"])
app.include_router(workspace.router, prefix="/api/workspace",  tags=["Workspace"])
app.include_router(chat.router,      prefix="/api/chat",       tags=["Chat"])
app.include_router(documents.router, prefix="/api/documents",  tags=["Documents"])
app.include_router(cleaning.router,  prefix="/api/cleaning",   tags=["Text Cleaning"])
app.include_router(rag.router,       prefix="/api/rag",        tags=["RAG"])

# ── Firebase Config ───────────────────────────────────────────────────────────
FIREBASE_CONFIG = {
    "apiKey":      os.getenv("FIREBASE_API_KEY", ""),
    "authDomain":  os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "projectId":   os.getenv("FIREBASE_PROJECT_ID", ""),
}

# ── Page Routes ───────────────────────────────────────────────────────────────
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "firebase_config": FIREBASE_CONFIG,
    })

@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {
        "request": request,
        "firebase_config": FIREBASE_CONFIG,
    })

@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/chat")
def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/documents")
def documents_page(request: Request):
    return templates.TemplateResponse("documents.html", {"request": request})