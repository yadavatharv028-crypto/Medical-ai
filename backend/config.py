"""
config.py
=========
Central configuration for the Flask application.
Edit the DATABASE section to match your local MySQL credentials.
"""

import os

class Config:
    # ── Security ──────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-s3cr3t!")

    # ── MySQL Database ────────────────────────────────────────────
    MYSQL_HOST     = os.environ.get("MYSQL_HOST",     "localhost")
    MYSQL_USER     = os.environ.get("MYSQL_USER",     "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "ganesh")        # ← set your password
    MYSQL_DB       = os.environ.get("MYSQL_DB",       "medical_ai_db")
    MYSQL_PORT     = int(os.environ.get("MYSQL_PORT", 3306))

    # ── Paths ─────────────────────────────────────────────────────
    BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_PATH = os.path.join(BASE_DIR, "backend", "disease_model.pkl")
    META_PATH  = os.path.join(BASE_DIR, "backend", "model_meta.json")

    # ── Session ───────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
