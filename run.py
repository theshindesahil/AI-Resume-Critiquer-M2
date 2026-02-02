"""
Entry point for Resume Critiquer application.
Simplifies running the Streamlit app.

Usage:
    python run.py
"""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    # Get the src directory
    src_dir = Path(__file__).parent / "src"
    app_file = src_dir / "app.py"

    if not app_file.exists():
        print(f"Error: {app_file} not found!")
        sys.exit(1)

    print(f"Starting Resume Critiquer...")
    print(f"Running: streamlit run {app_file}")

    # Run Streamlit with the app.py file
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_file)
    ])
