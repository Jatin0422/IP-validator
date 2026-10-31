# IPLens

Setup (PowerShell): `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1` and `python -m pip install -r requirements.txt`.
Run the API: from the project root, `.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload`.
Run the UI: `cd frontend`, `npm install`, then `npm run dev` (open a second terminal for this).
Run tests: from the project root, `.\.venv\Scripts\python.exe -m pytest backend\test_core.py -q`.
