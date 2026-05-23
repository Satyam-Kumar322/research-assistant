from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import auth, workspace

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Intelligent Research Assistant",
    description="Secure User Authentication and Personal Workspace Management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(workspace.router, prefix="/api/workspace", tags=["Workspace"])

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
 web: uvicorn main:app --host 0.0.0.0 --port $PORT

web: uvicorn main:app --host 0.0.0.0 --port $PORT
