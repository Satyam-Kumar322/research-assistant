import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = "research_assistant"

# ── Async client (for FastAPI routes) ────────────────────────────────────────
async_client = AsyncIOMotorClient(MONGODB_URL)
async_db = async_client[DATABASE_NAME]

# ── Sync client (for simple operations) ──────────────────────────────────────
sync_client = MongoClient(MONGODB_URL)
sync_db = sync_client[DATABASE_NAME]

# ── Collections ───────────────────────────────────────────────────────────────
def get_async_db():
    return async_db

# All collections
users_collection          = async_db["users"]
sessions_collection       = async_db["sessions"]
workspaces_collection     = async_db["workspaces"]
documents_collection      = async_db["documents"]
chat_history_collection   = async_db["chat_history"]
raw_text_collection       = async_db["raw_text"]
clean_text_collection     = async_db["clean_text"]
metadata_collection       = async_db["metadata"]

async def test_connection():
    """Test MongoDB Atlas connection."""
    try:
        await async_client.admin.command("ping")
        print("SUCCESS: MongoDB Atlas connected successfully!")
        return True
    except Exception as e:
        print(f"ERROR: MongoDB connection failed: {e}")
        return False