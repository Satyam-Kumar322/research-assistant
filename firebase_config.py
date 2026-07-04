"""
Firebase Admin SDK initialization and token verification.

Initializes the Firebase Admin app using a service account key file,
and provides a helper to verify Firebase ID tokens from the client.
"""

import os
import logging

import firebase_admin
from firebase_admin import credentials, auth

logger = logging.getLogger(__name__)

# ─── Initialize Firebase Admin SDK ────────────────────────────────────────────

_service_account_path = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_KEY_PATH",
    "firebase-service-account.json"
)

_firebase_app = None

if os.path.exists(_service_account_path):
    try:
        cred = credentials.Certificate(_service_account_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        logger.warning(f"Failed to initialize Firebase Admin SDK: {e}")
else:
    logger.warning(
        f"Firebase service account key not found at '{_service_account_path}'. "
        "Google OAuth will not work until you place the key file and restart."
    )


def is_firebase_initialized() -> bool:
    """Check whether the Firebase Admin SDK was successfully initialized."""
    return _firebase_app is not None


def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token and return the decoded claims.

    Returns a dict with keys like:
        - uid: Firebase user ID
        - email: user's email
        - name: display name (may be absent)
        - picture: profile photo URL (may be absent)
        - email_verified: bool

    Raises:
        ValueError: if Firebase is not initialized
        firebase_admin.auth.InvalidIdTokenError: if token is invalid/expired
    """
    if not is_firebase_initialized():
        raise ValueError(
            "Firebase Admin SDK is not initialized. "
            "Please place your service account key file and restart the server."
        )

    decoded_token = auth.verify_id_token(id_token)
    return decoded_token
