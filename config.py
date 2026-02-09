"""
Configuration module for Resume Critiquer application.
Centralizes all constants, settings, and environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------------------------
# File paths
# ---------------------------
# Get the directory where this config file is located
BASE_DIR = Path(__file__).parent.absolute()

# Data directory (for SQLite database)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Exports directory (for CSV/Excel/JSON exports)
EXPORTS_DIR = BASE_DIR / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)

# Database path - configurable via environment variable
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "resume_analysis.db"))

# ---------------------------
# AI Providers Configuration
# ---------------------------
# Keys from environment (optional, can be set in UI)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Provider Constants
PROVIDER_OPENAI = "OpenAI"
PROVIDER_GROQ = "Groq"

AVAILABLE_PROVIDERS = [PROVIDER_OPENAI, PROVIDER_GROQ]

# Models per Provider
PROVIDER_MODELS = {
    PROVIDER_OPENAI: ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    PROVIDER_GROQ: [
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768"
    ]
}

# Default selections
DEFAULT_PROVIDER = PROVIDER_OPENAI
DEFAULT_MODELS = {
    PROVIDER_OPENAI: "gpt-4o-mini",
    PROVIDER_GROQ: "llama-3.3-70b-versatile"
}

# Model parameters
DEFAULT_MAX_TOKENS = 2000 # Increased for better analysis depth
DEFAULT_TEMPERATURE = 0.15

# ---------------------------
# Resume Analysis Categories
# ---------------------------
ANALYSIS_CATEGORIES = [
    "Content Clarity & Impact",
    "Skills Presentation",
    "Experience Descriptions",
    "Tailoring",
    "Structure & Readability",
    "Achievements & Metrics",
    "ATS & Keywords",
    "Specific Improvements"
]

# ---------------------------
# Chunking Configuration
# ---------------------------
DEFAULT_CHUNK_SIZE = 4000  # characters (Increased safely for modern context windows)
DEFAULT_CHUNK_OVERLAP = 300  # characters
MIN_CHUNK_SIZE = 1000
MAX_CHUNK_SIZE = 15000

# ---------------------------
# File Upload Limits
# ---------------------------
# Maximum file size (10MB is reasonable for resume PDFs)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Maximum number of files per batch upload
MAX_FILES_PER_BATCH = int(os.getenv("MAX_FILES_PER_BATCH", "10"))

# Text validation limits
MIN_RESUME_TEXT_LENGTH = 100  # Minimum characters to consider valid extraction
MAX_RESUME_TEXT_LENGTH = 100000  # Maximum characters (increased for larger context support)

# Allowed file types
ALLOWED_FILE_TYPES = ["pdf", "txt"]

# ---------------------------
# Export & Cleanup Configuration
# ---------------------------
# Number of export files to keep (older ones will be deleted)
MAX_EXPORTS_TO_KEEP = int(os.getenv("MAX_EXPORTS_TO_KEEP", "10"))

# Export file naming pattern
EXPORT_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# ---------------------------
# Chart Configuration
# ---------------------------
CHART_TYPES = ["Bar", "Radar", "Pie"]
DEFAULT_CHART_TYPE = "Bar"

# Score color thresholds
SCORE_HIGH_THRESHOLD = 7.5
SCORE_MEDIUM_THRESHOLD = 5

# ---------------------------
# UI Configuration
# ---------------------------
APP_TITLE = "📃 AI Resume Critiquer — Multi-Model Edition"
PAGE_ICON = "📃"
LAYOUT = "wide"

# ---------------------------
# Validation functions
# ---------------------------
def validate_config():
    """
    Validate basic app setup.
    Detailed key validation is now handled in the UI/Provider logic.
    """
    return True, ""

def get_db_connection_params():
    """Get database connection parameters."""
    return {
        "database": DB_PATH,
        "check_same_thread": False  # Needed for Streamlit's multi-threaded environment
    }
