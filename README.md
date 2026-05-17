# Agile Web Development Project

This repository contains the starter Flask application for the CITS3403
group project. The current concept is a study dashboard where users can create
flashcard study sets, practise with different study modes, and view public study
sets from other users.

## Team Members

| UWA ID   | Name            | GitHub Username |
| --- | --- | --- |
| 24108363 | Silvi Claudia   | Silviclaudia    |
| 24218129 | Casey Leung     | caseyleung1     | 
| 24100961 | Anirudh Kumar   | Biomeac         |
| 24566304 | Vu Hung Nguyen  | hungvu1204      |

## Project Structure

```text
app/
  static/css/        CSS files
  templates/         Jinja HTML templates
  __init__.py        Flask application factory and CLI definitions
  models.py          SQLAlchemy database models
  routes.py          Flask routes (Application path endpoints and core  controller logic)
tests/               Pytest tests (Integration, route and selenium testing)
config.py            Global App configuration
run.py               Local development entry point
seed.py              Database testing 
```

## App Features 
- Flip Mode: Review of Flashcard upgraded with keyboard accessibility controls 
- Quiz Mode: Multiple-choice testing interface, where it pulls a correct definition and 3 wrong terms from other cards within the same study set 
- Time Game: 60 seconds recall challenge, looping the cards with a real time accuracy scoring metric and a countdown clock. 

Performance Tracking: 
- Live Analytics: Each profile keeps track of active user study streaks, completed studied cards, and trends across the week.
- Functional Setting: Setting interface protected by CSRF tokens with email as a username login.

## Run Locally
Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Create and activate a virtual environment in Windows: 
```bash
python -m venv venv
.\venv\Scripts\activate
```

## Install dependencies:

```bash
pip install -r requirements.txt
```

## Initialise database
### A. Recommended for initial setup
```bash
flask init-db
```
### B. Migration Deployment- using existing version control history files
```bash 
flask db upgrade
```

## Start the Flask development server:

```bash
python run.py
```

Open <http://127.0.0.1:5000> in your browser. (If macOS AirPlay Receiver is using
port 5000, either disable it under System Settings → General → AirDrop & Handoff
or set `app.run(port=5001)` in `run.py`.)


## Run Seed Test (Populate the database with sample users and study sets)
Available testing accounts:
Username: demo | Password: demo1234
Username: alice | Password: alice1234
Username: sam | Password: sam1234

```bash
python seed.py
```

## Run Tests

```bash
pytest
```
