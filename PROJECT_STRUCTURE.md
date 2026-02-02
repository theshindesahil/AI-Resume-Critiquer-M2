# Project Structure

This document outlines the production-ready structure of the Resume Critiquer application.

## Directory Layout

```
resume-critiquer/
├── src/                    # Application source code
│   ├── utils/             # Helper utilities
│   │   ├── __init__.py
│   │   └── cleanup.py     # Text cleanup and sanitization
│   ├── __init__.py
│   ├── app.py             # Main Streamlit application
│   ├── config.py          # Configuration and constants
│   ├── ai_providers.py    # AI provider implementations (OpenAI, Groq)
│   └── validators.py      # Input validation logic
│
├── data/                   # Analysis database storage
│   └── .gitkeep           # Maintain directory in git
│
├── exports/                # Generated analysis reports
│   └── .gitkeep           # Maintain directory in git
│
├── .env                    # API keys and environment variables
├── .gitignore             # Git exclusion rules
├── .python-version        # Python version specification
├── pyproject.toml         # Project metadata and dependencies (uv)
├── README.md              # Project documentation
├── requirements.txt       # Python dependencies (pip)
└── run.py                 # Application entry point
```

## Core Components

### Application Layer (`src/`)

**app.py** — The main application logic
- Streamlit UI and routing
- Resume upload and processing workflow
- AI analysis coordination
- Results visualization (charts, metrics)
- Database operations and export functionality

**config.py** — Centralized configuration
- Analysis categories and scoring rubrics
- Default model settings
- Database schema definitions
- Text processing parameters

**ai_providers.py** — AI provider abstraction
- OpenAI integration (GPT-4o, GPT-4o-mini, GPT-4-turbo)
- Groq integration (Llama 3.3 70B, Mixtral 8x7b)
- Unified interface for multiple providers
- Error handling and retry logic

**validators.py** — Input validation
- Resume file validation (PDF/TXT)
- Text extraction quality checks
- API response validation
- Data sanitization

### Utilities (`src/utils/`)

**cleanup.py** — Text processing utilities
- Filename sanitization
- Content cleanup and normalization
- Character encoding fixes

### Data Layer

**data/** — SQLite database storage
- Stores all analysis history
- Schema auto-created on first run
- Excluded from version control (see `.gitignore`)

**exports/** — Generated reports
- CSV, Excel, and JSON exports
- Auto-timestamped filenames
- Excluded from version control (see `.gitignore`)

## Configuration Files

**pyproject.toml** — Modern Python project specification
- Works with `uv` package manager
- Defines all production dependencies
- Python version requirement (>= 3.14)

**requirements.txt** — Traditional dependency list
- Fallback for pip-based installations
- Mirrors pyproject.toml dependencies

**.env** — Environment variables
- API keys for OpenAI and Groq
- Not tracked in git (security)
- Must be configured before deployment

## Development vs. Production

This structure is optimized for production deployment:

✅ **Included in production:**
- Core application code
- Configuration templates
- Documentation
- Entry points

❌ **Excluded from production:**
- Test files and test data
- Development databases
- Old export files
- Build artifacts (`__pycache__`, `*.egg-info`)
- IDE configuration

## Deployment Checklist

Before deploying to production:

1. **Configure API Keys**
   - Copy `.env` and add your OpenAI/Groq API keys
   - Verify keys are valid with test requests

2. **Install Dependencies**
   ```bash
   # Using uv (recommended)
   uv run streamlit run run.py

   # Or using pip
   pip install -r requirements.txt
   python run.py
   ```

3. **Verify Database Setup**
   - Ensure `data/` directory exists
   - Check write permissions
   - Database will be created automatically on first analysis

4. **Test Core Functionality**
   - Upload a test resume
   - Verify AI analysis completes
   - Check export functionality (CSV/Excel)

5. **Monitor Resources**
   - Set appropriate `max_tokens` limits
   - Monitor API usage and costs
   - Configure rate limiting if needed

## Notes

- The application uses SQLite for simplicity. For production scale with multiple concurrent users, consider PostgreSQL or MySQL.
- All AI analysis is performed server-side; resume text is sent to external APIs (OpenAI/Groq).
- Exported files accumulate in `exports/` — implement periodic cleanup if running long-term.
