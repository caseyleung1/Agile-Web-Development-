# StudyFlash — CITS3403 agile web project

Quizlet-inspired flashcard platform: **Flask**, **SQLite**, **Jinja2**, **Tailwind CSS**, vanilla JavaScript for study modes.

**Project folder (clone location):** use your actual path, e.g. `~/Agile_Web_Development` or `/Users/<you>/Agile_Web_Development`. All commands below assume your shell’s current directory is **that** folder (not another repo such as `Assignment_comp1005_40`).

## Requirements

- Python 3.11+
- Node.js 18+ (for Tailwind build)

## Setup

```bash
cd /path/to/Agile_Web_Development
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # edit FLASK_SECRET_KEY; optional OPENAI_API_KEY
npm install
npm run build:css
python scripts/seed_demo.py # optional demo user and sets
```

## Run

From the same project directory:

```bash
export FLASK_APP=run.py
flask run --debug
```

Alternatively: `python run.py` (same directory).

Open http://127.0.0.1:5000 — register an account or use the demo login from `scripts/seed_demo.py` (`demo@example.com` / `password123`).

## AI flashcards

Optional: set `OPENAI_API_KEY` and optionally `OPENAI_API_BASE` / `OPENAI_MODEL` in `.env`. Without a key, the UI still loads but generation returns a clear message.

## Project layout

- `app/` — application package (blueprints, models, templates)
- `static/css/` — Tailwind input (`input.css`) and built `app.css` (generated; do not edit `app.css` by hand)
- `Images/` — design reference PNGs
- `scripts/seed_demo.py` — optional sample data

## Team

Align roles and sprints with your unit’s agile requirements and your GitHub board.

## Fast start

If paths/env keep getting mixed up, run this from anywhere:

```bash
/Users/biomeac/Agile_Web_Development/scripts/dev.sh
```

It automatically switches to the correct project folder, ensures deps are installed, builds CSS, seeds demo data, and starts Flask.
