from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
import uuid
import logging

from database import get_db
import models
import schemas
from utils import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from firebase_config import verify_firebase_token, is_firebase_initialized

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── POST /api/auth/register ──────────────────────────────────────────────────

@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    - Validates email uniqueness
    - Hashes password using bcrypt
    - Returns JWT access token on success
    """
    # Check for duplicate email
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )

    # Create user with hashed password
    new_user = models.User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create a default workspace for the user
    default_workspace = models.Workspace(
        user_id=new_user.id,
        project_name="My Research",
        description="Default workspace"
    )
    db.add(default_workspace)
    db.commit()

    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return schemas.Token(access_token=access_token, user=new_user)


# ─── POST /api/auth/login ─────────────────────────────────────────────────────

@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user with email and password.
    - Verifies password hash
    - Returns JWT access token on success
    """
    user = db.query(models.User).filter(models.User.email == credentials.email).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Create session record
    session_expiry = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    session = models.Session(
        session_id=str(uuid.uuid4()),
        user_id=user.id,
        expiry_time=session_expiry
    )
    db.add(session)
    db.commit()

    # Generate JWT
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return schemas.Token(access_token=access_token, user=user)


# ─── POST /api/auth/google ────────────────────────────────────────────────────

@router.post("/google", response_model=schemas.Token)
def google_auth(payload: schemas.GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate or register a user via Google OAuth (Firebase).
    - Verifies the Firebase ID token server-side
    - Finds existing user by email or creates a new one
    - Links Google OAuth to existing email/password accounts
    - Returns JWT access token on success
    """
    if not is_firebase_initialized():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google authentication is not configured. Please contact the administrator."
        )

    # Verify the Firebase ID token
    try:
        decoded = verify_firebase_token(payload.id_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.warning(f"Firebase token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google token. Please try signing in again."
        )

    # Extract user info from the decoded token
    firebase_uid = decoded.get("uid")
    email = decoded.get("email")
    name = decoded.get("name") or decoded.get("email", "").split("@")[0]

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account does not have an email address."
        )

    # Look up existing user by email
    user = db.query(models.User).filter(models.User.email == email).first()

    if user:
        # Account linking: attach Google OAuth info if not already set
        if not user.oauth_provider:
            user.oauth_provider = "google"
            user.oauth_id = firebase_uid
            db.commit()
            db.refresh(user)
            logger.info(f"Linked Google OAuth to existing user: {email}")
    else:
        # Create a new user (no password — OAuth-only)
        user = models.User(
            name=name,
            email=email,
            password_hash=None,
            oauth_provider="google",
            oauth_id=firebase_uid,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a default workspace for the new user
        default_workspace = models.Workspace(
            user_id=user.id,
            project_name="My Research",
            description="Default workspace"
        )
        db.add(default_workspace)
        db.commit()
        logger.info(f"Created new Google OAuth user: {email}")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Create session record
    session_expiry = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    session = models.Session(
        session_id=str(uuid.uuid4()),
        user_id=user.id,
        expiry_time=session_expiry
    )
    db.add(session)
    db.commit()

    # Generate JWT
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return schemas.Token(access_token=access_token, user=user)


# ─── GET /api/auth/profile ────────────────────────────────────────────────────

@router.get("/profile", response_model=schemas.UserResponse)
def get_profile(current_user: models.User = Depends(get_current_user)):
    """
    Get the authenticated user's profile.
    Requires: Authorization: Bearer <token>
    """
    return current_user


# ─── POST /api/auth/logout ────────────────────────────────────────────────────

@router.post("/logout", response_model=schemas.MessageResponse)
def logout(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout the current user.
    - Deactivates all active sessions for this user
    Note: JWT is stateless; client should delete the token on their side.
    """
    # Deactivate all active sessions
    db.query(models.Session).filter(
        models.Session.user_id == current_user.id,
        models.Session.is_active == True
    ).update({"is_active": False})
    db.commit()

    return schemas.MessageResponse(message="Successfully logged out")


# ─── GET /api/auth/me ─────────────────────────────────────────────────────────

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Alias for /profile — returns current authenticated user."""
    return current_user

