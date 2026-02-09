# AI RESUME CRITIQUER.
import streamlit as st
import PyPDF2
import io
import os
import time
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from math import ceil
import sqlite3
import re

# Import modules from src package
from src import config, validators, ai_providers
from src.utils import cleanup

# ---------------------------
# Page layout / style tweaks
# ---------------------------
st.set_page_config(page_title=config.APP_TITLE, page_icon=config.PAGE_ICON, layout=config.LAYOUT)
st.markdown(
    """
    <style>
    /* Slightly more modern card look and font */
    html, body, .main { font-family: 'Inter', Arial, sans-serif; }
    .stButton>button {
        background: linear-gradient(180deg, #3cb371, #2e8b57);
        color: white;
        border-radius: 10px;
        padding: 0.5rem 0.9rem;
        font-weight: 600;
    }
    .stButton>button:hover { transform: scale(1.02); }
    .card {
        padding: 1rem 1rem;
        border-radius: 12px;
        background: #ffffff;
        box-shadow: 0 6px 18px rgba(14,30,37,0.06);
        margin-bottom: 1rem;
    }
    .muted { color: #6b7280; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title(config.APP_TITLE)
st.markdown("Upload one or more resumes (PDF / TXT). Features: Multi-Model AI Analysis (OpenAI, Groq), batch processing, and detailed insights.")


# ---------------------------
# Sidebar controls & Configuration
# ---------------------------
st.sidebar.header("⚙️ AI Configuration")

# Provider Selection
selected_provider = st.sidebar.selectbox("Select AI Provider", config.AVAILABLE_PROVIDERS, index=0)

# Dynamic Model Selection based on Provider
available_models = config.PROVIDER_MODELS.get(selected_provider, [])
default_model_index = 0
if selected_provider in config.DEFAULT_MODELS:
    try:
        default_model_index = available_models.index(config.DEFAULT_MODELS[selected_provider])
    except ValueError:
        default_model_index = 0

selected_model = st.sidebar.selectbox("Select Model", available_models, index=default_model_index)

# API Key Management
api_key = ""
env_key_name = ""
if selected_provider == config.PROVIDER_OPENAI:
    env_key_name = "OPENAI_API_KEY"
    api_key = config.OPENAI_API_KEY
elif selected_provider == config.PROVIDER_GROQ:
    env_key_name = "GROQ_API_KEY"
    api_key = config.GROQ_API_KEY

if api_key:
    st.sidebar.success(f"✅ API Key loaded from Environment")
else:
    api_key = st.sidebar.text_input(f"Enter {selected_provider} API Key", type="password", help=f"Set {env_key_name} in .env to skip this.")
    if not api_key:
        st.sidebar.warning(f"⚠️ {selected_provider} requires an API Key")

st.sidebar.markdown("---")
st.sidebar.header("Analysis Settings")
target_role = st.sidebar.text_input("Target job role (optional)", placeholder="e.g., Backend Engineer")
chart_type = st.sidebar.radio("Chart type", options=config.CHART_TYPES)
chunk_chars = st.sidebar.number_input("Chunk size (chars)", min_value=config.MIN_CHUNK_SIZE, max_value=config.MAX_CHUNK_SIZE, value=config.DEFAULT_CHUNK_SIZE, step=500)
chunk_overlap = st.sidebar.number_input("Chunk overlap (chars)", min_value=0, max_value=1000, value=config.DEFAULT_CHUNK_OVERLAP, step=50)
save_to_db = st.sidebar.checkbox("Save analyses to DB", value=True)

# Storage Info
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Storage")
export_summary = cleanup.get_export_summary()
db_size = cleanup.get_database_size()
st.sidebar.markdown(f"**Exports:** {export_summary['total_files']} ({export_summary['total_size_mb']:.1f} MB)")
st.sidebar.markdown(f"**Database:** {db_size:.2f} MB")

if st.sidebar.button("🧹 Clean Old Exports"):
    num_deleted, deleted = cleanup.cleanup_old_exports(max_keep=config.MAX_EXPORTS_TO_KEEP)
    if num_deleted > 0:
        st.sidebar.success(f"Deleted {num_deleted} files")

# ---------------------------
# Initial setup and validation
# ---------------------------
# Create data dirs
cleanup.cleanup_database_on_startup()


# ---------------------------
# Helpers
# ---------------------------
def extract_text_from_pdf_bytes(pdf_bytes):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception:
        return ""

def extract_text_from_uploaded(uploaded_file):
    try:
        content = uploaded_file.read()
        uploaded_file.seek(0)
        if uploaded_file.type == "application/pdf":
            return extract_text_from_pdf_bytes(content)
        else:
            return content.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def chunk_text(text, size=3000, overlap=200):
    if not text: return []
    if size <= 0: return [text]
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + size
        chunks.append(text[start:end])
        if end >= text_len: break
        start = end - overlap if (end - overlap) > start else end
    return chunks

def get_system_instruction():
    return """You are an expert resume reviewer with years of HR and recruitment experience.
    Analyze the resume content provided by the user.
    Output must be a valid JSON object ONLY.
    Follow the structure strictly."""

def build_prompt_for_chunk(resume_chunk, job_role=None):
    role_snip = f"Target role: {job_role}\n" if job_role else ""
    prompt = f"""
    You are an expert resume reviewer with years of HR and recruitment experience.
    Analyze the following resume chunk. Return ONLY a JSON object (no markdown or extra text but explain each and every section in detail.
    Make sure to cover all the little details that should be informed to the user.
    Have a priority on being specific and try not to generalize the response.
    Make sure to have a professional and humanly tone to make a better understanding.
    Be as informative as possible
    Take extra care while explaining the ATS & Keyword section, provide the user with exactly what words to use and why
    Ensure role-specific insights:
    “Tailor the analysis toward the specific type of role the resume seems to target (e.g., IT, Marketing, Finance, Operations) and explicitly mention how well it aligns with that role.”
    Add industry benchmarking:
    “Where possible, compare the resume’s strengths and weaknesses against common industry standards or expectations for the candidate’s field and seniority level.”
    Highlight language/tone use:
    “Comment on the language, tone, and action verbs used in the resume, and suggest stronger alternatives where impact is lacking.”
    Include red flags:
    “Identify any potential red flags (e.g., employment gaps, vague job descriptions, outdated skills) and explain how recruiters or ATS might interpret them.”
    Add keyword strategy detail:
    “In the ats_keywords section, go beyond listing present/missing keywords and provide context for placement (e.g., ‘add “risk management” under your Acme Corp role where you handled compliance processes’).”
    Point out formatting compatibility issues:
    “Note any risks of ATS parsing errors (e.g., tables, graphics, uncommon fonts, headers/footers).”
    Final polish suggestion:
    “Suggest how the candidate can make the resume stand out to a human recruiter after passing ATS (e.g., storytelling, achievement framing).”
    If analysis fails return: {{ "error": "Resume could not be analyzed" }}
    First give the score in each category individually and then give the overall score after aggregation.
    Structure:
    {{
      "scores": {{
        "Content Clarity & Impact": <int 0-10>,
        "Skills Presentation": <int 0-10>,
        "Experience Descriptions": <int 0-10>,
        "Tailoring": <int 0-10>,
        "Structure & Readability": <int 0-10>,
        "Achievements & Metrics": <int 0-10>,
        "ATS & Keywords": <int 0-10>,
        "Specific Improvements": <int 0-10>
      }},
      "overall_score": <int 0-10>,
      "feedback": {{
        "Content Clarity & Impact": "<text>",
        "Skills Presentation": "<text>",
        "Experience Descriptions": "<text>",
        "Tailoring": "<text>",
        "Structure & Readability": "<text>",
        "Achievements & Metrics": "<text>",
        "ATS & Keywords": "<text>",
        "Specific Improvements": "<text>"
      }},
      "recommendations": "<summary>",
      "pros": ["<...>"],
      "cons": ["<...>"]
    }}

    {role_snip}
    Resume chunk:
    {resume_chunk}
    """
    return prompt

def extract_first_json(text):
    """
    Attempt to find and parse the first JSON object in text.
    """
    # Try clean load
    try:
        return json.loads(text)
    except Exception:
        # try regex for balanced braces (best-effort)
        # This regex uses a greedy match; we then try to parse progressively smaller substrings if needed.
        brace_open = [m.start() for m in re.finditer(r"\{", text)]
        for start in brace_open:
            # try to find a matching closing brace by scanning forward
            for end_idx in range(start+1, min(len(text), start+20000)):
                if text[end_idx] == "}":
                    candidate = text[start:end_idx+1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        continue
        # As a last resort, try extracting via broad regex
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    raise ValueError("No valid JSON object found in model response.")


def aggregate_chunk_analyses(chunk_results):
    """
    chunk_results: list of parsed JSON dicts from each chunk
    We average numeric scores, pick the min overall_score? We'll average overall as well.
    For textual feedback, we concatenate unique lines and keep the most common recommendations.
    """
    if not chunk_results:
        return None

    # expected categories
    cats = ["Content Clarity & Impact","Skills Presentation","Experience Descriptions","Tailoring","Structure & Readability","Achievements & Metrics","ATS & Keywords","Specific Improvements"]

    # numeric aggregation
    agg_scores = {cat: [] for cat in cats}
    overall_vals = []
    pros_all = []
    cons_all = []
    feedback_concat = {cat: [] for cat in cats}
    recommendations_all = []

    for ch in chunk_results:
        # if error
        if not isinstance(ch, dict):
            continue
        scores = ch.get("scores", {})
        for cat in cats:
            v = scores.get(cat)
            try:
                if v is not None:
                    agg_scores[cat].append(float(v))
            except Exception:
                pass
        ov = ch.get("overall_score")
        try:
            if ov is not None:
                overall_vals.append(float(ov))
        except Exception:
            pass

        fb = ch.get("feedback", {})
        for cat in cats:
            text = fb.get(cat)
            if text:
                feedback_concat[cat].append(text)

        rec = ch.get("recommendations")
        if rec:
            recommendations_all.append(rec)
        pros_all.extend(ch.get("pros", []) or [])
        cons_all.extend(ch.get("cons", []) or [])

    # compute averages (or 0)
    final_scores = {}
    for cat in cats:
        vals = agg_scores.get(cat, [])
        final_scores[cat] = int(round(sum(vals)/len(vals))) if vals else 0

    final_overall = int(round(sum(overall_vals)/len(overall_vals))) if overall_vals else 0

    # Join feedbacks intelligently (unique, keep order and truncate to reasonable length)
    final_feedback = {}
    for cat in cats:
        pieces = []
        seen = set()
        for p in feedback_concat[cat]:
            p_strip = p.strip()
            if p_strip and p_strip not in seen:
                pieces.append(p_strip)
                seen.add(p_strip)
        final_feedback[cat] = " ".join(pieces)[:1200]  # truncate

    # recommendations: top few unique
    rec_seen = []
    for r in recommendations_all:
        r_strip = r.strip()
        if r_strip and r_strip not in rec_seen:
            rec_seen.append(r_strip)
    final_recommendations = " ".join(rec_seen[:3])[:1000]

    # pros/cons unique
    pros_unique = list(dict.fromkeys([p for p in pros_all if p]))
    cons_unique = list(dict.fromkeys([c for c in cons_all if c]))

    return {
        "scores": final_scores,
        "overall_score": final_overall,
        "feedback": final_feedback,
        "recommendations": final_recommendations,
        "pros": pros_unique,
        "cons": cons_unique
    }

def make_radar_chart(data, title):
    df = pd.DataFrame(dict(r=list(data.values()), theta=list(data.keys())))
    fig = px.line_polar(df, r='r', theta='theta', line_close=True, title=title)
    fig.update_traces(fill='toself')
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])))
    return fig

def make_bar_chart(data, title):
    df = pd.DataFrame(list(data.items()), columns=['Category', 'Score'])
    fig = px.bar(df, x='Category', y='Score', title=title, range_y=[0, 10])
    return fig

def make_pie_chart(data, title):
    df = pd.DataFrame(list(data.items()), columns=['Category', 'Score'])
    fig = px.pie(df, values='Score', names='Category', title=title)
    return fig

# ---------------------------
# SQLite persistence
# ---------------------------
if save_to_db:
    conn = sqlite3.connect(**config.get_db_connection_params())
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY,
        filename TEXT,
        job_role TEXT,
        analysis_time TEXT,
        overall_score REAL,
        scores_json TEXT,
        feedback_json TEXT,
        recommendations TEXT,
        pros_json TEXT,
        cons_json TEXT,
        raw_response TEXT
    )""")
    conn.commit()
else:
    conn = None


# ---------------------------
# Main Logic
# ---------------------------
uploaded_files = st.file_uploader("Upload resumes", type=["pdf", "txt"], accept_multiple_files=True)
analyze_btn = st.button("🔍 Analyze Resume(s)")

if analyze_btn:
    if not uploaded_files:
        st.warning("Please upload a resume.")
        st.stop()

    if not api_key:
        st.error(f"❌ Please provide a {selected_provider} API Key to proceed.")
        st.stop()

    # Initialize Provider
    try:
        ai_client = ai_providers.get_provider(selected_provider, api_key, selected_model)
    except Exception as e:
        st.error(f"Error initializing AI Provider: {e}")
        st.stop()

    st.info(f"🚀 Starting analysis using **{selected_provider}** ({selected_model})...")

    results_records = []
    progress_bar = st.progress(0)

    for idx, up in enumerate(uploaded_files):
        progress_bar.progress(int((idx / len(uploaded_files)) * 100))

        safe_filename = validators.sanitize_filename(up.name)
        st.markdown(f"### 📄 {safe_filename}")

        # Extract
        text = extract_text_from_uploaded(up)
        if not text or len(text) < config.MIN_RESUME_TEXT_LENGTH:
            st.error(f"Could not extract sufficient text from {safe_filename}.")
            continue

        # Chunk
        chunks = chunk_text(text, size=chunk_chars, overlap=chunk_overlap)
        st.write(f"Analyzing {len(chunks)} text segment(s)...")

        chunk_results = []
        for i, ch in enumerate(chunks):
            prompt = build_prompt_for_chunk(ch, target_role)
            try:
                # Call AI Provider
                raw_response = ai_client.generate_critique(prompt, system_instruction=get_system_instruction())
                parsed = extract_first_json(raw_response)
                chunk_results.append(parsed)
            except Exception as e:
                st.error(f"Error analyzing segment {i+1}: {e}")

        # aggregate chunk results
        aggregated = aggregate_chunk_analyses(chunk_results)
        if aggregated is None:
            st.error(f"Could not analyze {safe_filename} (no valid chunk analyses).")
            continue

        scores = aggregated.get("scores", {})

        # Display
        st.markdown('<div class="card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader(f"Overall Score: {aggregated.get('overall_score', 0)}/10")
            st.write(f"**Recommendations:** {aggregated.get('recommendations', 'None')}")
            st.write("**Pros:**")
            st.write(", ".join(aggregated.get("pros", [])))
            st.write("**Cons:**")
            st.write(", ".join(aggregated.get("cons", [])))

        with col2:
            if chart_type == "Radar":
                fig = make_radar_chart(scores, f"Skills Assessment - {safe_filename}")
            elif chart_type == "Pie":
                fig = make_pie_chart(scores, f"Skills Assessment - {safe_filename}")
            else:
                fig = make_bar_chart(scores, f"Skills Assessment - {safe_filename}")
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("Detailed Feedback"):
            for cat, fb in aggregated.get("feedback", {}).items():
                st.markdown(f"**{cat}**: {fb}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Save results
        record = {
            "filename": safe_filename,
            "job_role": target_role,
            "analysis_time": datetime.utcnow().isoformat(),
            "overall_score": aggregated.get("overall_score", 0),
            "scores": aggregated.get("scores", {}),
            "feedback": aggregated.get("feedback", {}),
            "recommendations": aggregated.get("recommendations", ""),
            "pros": aggregated.get("pros", []),
            "cons": aggregated.get("cons", []),
            "raw_response": json.dumps(chunk_results)
        }
        results_records.append(record)

        if save_to_db and conn:
            try:
                c.execute("INSERT INTO analyses (filename, job_role, analysis_time, overall_score, scores_json, feedback_json, recommendations, pros_json, cons_json, raw_response) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (record['filename'], record['job_role'], record['analysis_time'], record['overall_score'],
                          json.dumps(record['scores']), json.dumps(record['feedback']), record['recommendations'],
                          json.dumps(record['pros']), json.dumps(record['cons']), record['raw_response']))
                conn.commit()
            except Exception as e:
                st.warning(f"DB Save Error: {e}")

    progress_bar.progress(100)
    st.success("Analysis Complete!")

    # Export options
    if results_records:
        df = pd.DataFrame([
            {
                "Filename": r["filename"],
                "Score": r["overall_score"],
                "Recommendations": r["recommendations"],
                **{f"Score_{k}": v for k, v in r["scores"].items()}
            }
            for r in results_records
        ])

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV Report", csv, f"resume_report_{ts}.csv", "text/csv")

# Cleanup
if conn:
    conn.close()
