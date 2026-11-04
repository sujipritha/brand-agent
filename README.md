# Brand Face-Off — Competitor Analysis Agent

## Run in VS Code
1. Open this folder in VS Code (File > Open Folder)
2. Terminal > New Terminal, then:
   python -m venv venv
   venv\Scripts\activate        (Mac/Linux: source venv/bin/activate)
   pip install -r requirements.txt
   uvicorn app:app --reload
3. Open http://127.0.0.1:8000

Optional: set ANTHROPIC_API_KEY to add a Claude-written summary.
Demo data lives in collect() in app.py; replace it with real API calls.
