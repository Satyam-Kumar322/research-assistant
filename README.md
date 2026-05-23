# 🔬 Intelligent Research Assistant
### Objective 1 — User Authentication & Personal Workspace Module

Built with **FastAPI** + **SQLAlchemy** + **JWT** + **bcrypt**

---

## 📁 Project Structure

```
research_assistant/
├── main.py              # FastAPI app entry point
├── database.py          # DB engine, session, Base
├── models.py            # SQLAlchemy ORM models (User, Session, Workspace)
├── schemas.py           # Pydantic request/response schemas
├── utils.py             # JWT, bcrypt, auth dependency
├── routers/
│   ├── auth.py          # /api/auth/* endpoints
│   └── workspace.py     # /api/workspace/* endpoints
├── templates/
│   ├── login.html       # Login page UI
│   ├── register.html    # Registration page UI
│   └── dashboard.html   # Personal workspace dashboard
├── static/              # CSS/JS assets
├── requirements.txt
└── .env.example
```

---

## ⚡ Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env and set a strong SECRET_KEY
```

### 3. Run the server
```bash
uvicorn main:app --reload
```

### 4. Open in browser
- **Login page**: http://localhost:8000
- **Register**: http://localhost:8000/register
- **Dashboard**: http://localhost:8000/dashboard
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔐 API Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|--------------|-------------|
| POST | `/api/auth/register` | No | Register new user |
| POST | `/api/auth/login` | No | Login & get JWT token |
| GET | `/api/auth/profile` | ✅ Bearer | Get current user profile |
| GET | `/api/auth/me` | ✅ Bearer | Alias for /profile |
| POST | `/api/auth/logout` | ✅ Bearer | Logout & deactivate session |
| GET | `/api/workspace/` | ✅ Bearer | List user's workspaces |
| POST | `/api/workspace/` | ✅ Bearer | Create new workspace |
| GET | `/api/workspace/{id}` | ✅ Bearer | Get specific workspace |
| DELETE | `/api/workspace/{id}` | ✅ Bearer | Delete workspace |

---

## 🧪 Test with Postman / cURL

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"secret123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"secret123"}'
```

### Access protected route
```bash
curl -X GET http://localhost:8000/api/auth/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

---

## 🗄️ Database

- **Development**: SQLite (auto-created as `research_assistant.db`) — no setup needed
- **Production**: PostgreSQL — update `DATABASE_URL` in `.env`

### Tables
- `users` — User accounts (id, name, email, password_hash, oauth_provider, created_at)
- `sessions` — Login sessions (session_id, user_id, login_time, expiry_time)
- `workspaces` — Research projects (workspace_id, user_id, project_name, description)
- `documents` — Uploaded files (id, workspace_id, filename, file_path)

---

## 🔒 Security Implementation

| Feature | Implementation |
|---------|---------------|
| Password hashing | `bcrypt` via `passlib` |
| Authentication | `JWT` via `python-jose` |
| Token expiry | Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Protected routes | FastAPI `Depends(get_current_user)` middleware |
| Input validation | Pydantic v2 schemas with field validators |
| CORS | Configured in `main.py` |

---

## 📦 Technology Stack

- **Backend**: FastAPI + Uvicorn
- **Database**: SQLAlchemy ORM + SQLite/PostgreSQL
- **Auth**: JWT (python-jose) + bcrypt (passlib)
- **Validation**: Pydantic v2
- **Frontend**: Jinja2 templates + Vanilla JS

---

## 🚀 Production Deployment

1. Set `DATABASE_URL` to your PostgreSQL connection string
2. Generate a strong `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`
3. Set `DEBUG=False`
4. Deploy with: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4`
