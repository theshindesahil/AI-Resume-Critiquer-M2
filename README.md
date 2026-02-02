# 📃 AI Resume Critiquer — Mark 2

A powerful, interactive **Streamlit web application** that leverages state-of-the-art AI models (OpenAI, Groq) to provide detailed, structured critique for resumes.

This tool goes beyond simple keyword matching. It uses Large Language Models (LLMs) to analyze your resume's content, clarity, impact, and tailoring for specific roles, offering actionable feedback similar to a professional human review.

---

## 🚀 Key Features

*   **Multi-Model Support**: Choose between top-tier AI providers:
    *   **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4-turbo
    *   **Groq**: Llama 3.3 70B, Mixtral 8x7b (High speed)
*   **Batch Processing**: Upload and analyze multiple resumes (PDF or TXT) continuously.
*   **Intelligent Chunking**: Automatically handles long resumes by splitting them into manageable text segments for thorough analysis.
*   **Deep Analysis**:
    *   **Scores**: 0-10 ratings across 8 categories (Clarity, Skills, ATS, etc.).
    *   **Qualitative Feedback**: Detailed written critique for every section.
    *   **Pros & Cons**: Bulleted lists of strong points and red flags.
    *   **Role Tailoring**: Analyzes how well the resume fits a specific target job role.
*   **Visual Analytics**: Interactive embedded charts (Bar, Radar/Spider, Pie) to visualize skill gaps.
*   **Persistence**: Automatically saves all analysis history to a local **SQLite database**.
*   **Export Options**: Download comprehensive reports in **CSV**, **Excel**, or **JSON** formats.
*   **Modern UI**: Clean, responsive interface with dark/light mode support and smooth animations.

---

## 🛠️ Architecture & Workflow

The application follows a modular architecture:

1.  **Input**: User uploads files (PDF/TXT) via the Streamlit Interface.
2.  **Processing**:
    *   **Extraction**: Text is extracted from raw bytes (`src.utils`).
    *   **Sanitization**: Filenames and content are cleaned.
    *   **Chunking**: Large texts are split with overlap to preserve context.
3.  **Analysis (AI Core)**:
    *   The `AIProvider` factory selects the configured model.
    *   A robust, role-specific prompt is sent to the LLM.
    *   The LLM returns a strictly formatted **JSON** response.
4.  **Aggregation**:
    *   If a resume was chunked, results are logically merged (averaging scores, concatenating unique feedback).
5.  **Storage & Presentation**:
    *   Results are written to `data/resume_analysis.db`.
    *   UI renders cards, metrics, and charts.

---

## ⚙️ Installation & Setup

This project uses modern Python tooling. We recommend **uv** for dependency management, but standard `pip` works too.

### Prerequisites
*   Python 3.10+ installed.
*   API Keys for at least one provider (OpenAI or Groq).

### Method 1: Quick Start with `uv` (Recommended)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/resume-critiquer-mark2.git
    cd resume-critiquer-mark2
    ```

2.  **Configure API Keys**:
    *   Rename `.env.example` to `.env` (or create a new `.env` file).
    *   Add your keys:
        ```env
        OPENAI_API_KEY=sk-...
        GROQ_API_KEY=gsk_...
        ```

3.  **Run the App**:
    ```bash
    uv run streamlit run run.py
    ```
    *(This command automatically handles virtual environment creation and dependency installation)*

### Method 2: Standard Pip

1.  **Create venv**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run**:
    ```bash
    python run.py
    ```

---

## 📖 Usage Guide

1.  **Select Provider**: On the sidebar, choose your preferred AI (e.g., "OpenAI" or "Groq").
2.  **Configure Model**: Detailed models (like GPT-4o) give better qualitative feedback; faster models (like Llama 3.3 or Mixtral) are great for quick checks.
3.  **Set Job Role**: (Optional) Enter "Senior Backend Engineer" or "Product Manager" to get tailored advice.
4.  **Upload**: Drag & Drop your resume PDF/TXT files.
5.  **Analyze**: Click the button. The app will process file-by-file.
6.  **Review**:
    *   Check the **Overall Score**.
    *   Expand **Detailed Feedback** to read specific critiques.
    *   View **Charts** to see your profile balance.
7.  **Export**: Use the buttons at the bottom to save your analysis to CSV or Excel.

---

## � Project Structure

```
resume-critiquer/
├── .env                # API Keys (GitIgnored)
├── run.py              # Entry point script
├── pyproject.toml      # Project dependencies (uv)
├── requirements.txt    # Project dependencies (pip)
├── src/
│   ├── app.py          # Main Streamlit application logic
│   ├── config.py       # Configuration & Constants
│   ├── ai_providers.py # OpenAI/Groq adapter classes
│   └── utils/          # Helper functions
├── data/               # SQLite database storage
└── exports/            # Generated reports
```

---

## 🛠️ Customization

*   **Prompts**: Modify `src/app.py` -> `build_prompt_for_chunk` to change how the AI critiques the resume.
*   **Scoring Categories**: specific categories can be adjusted in `src/config.py`.
*   **Database**: The app uses SQLite. You can view the schema in `data/resume_analysis.db` using any SQLite viewer.

---

## ⚖️ License
MIT License. Feel free to modify and use for personal or professional projects.
