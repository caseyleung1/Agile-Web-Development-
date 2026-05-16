# Agile Web Development Project

This repository contains the starter Flask application for the CITS3403
group project. The current concept is a study dashboard where users can create
flashcard study sets, practise with different study modes, and view public study
sets from other users.

## Team Members

| UWA ID   | Name            | GitHub Username |
| 24108363 | Silvi Claudia   | Silviclaudia    |
| 24218129 | Casey Leung     | caseyleung1     | 
| 24100961 | Anirudh Kumar   | Biomeac         |
| 24566304 | Vu Hung Nguyen  | hungvu1204      |

## Project Structure

```text
app/
  static/css/        CSS files
  templates/         Jinja HTML templates
  __init__.py        Flask application factory
  models.py          SQLAlchemy database models
  routes.py          Flask routes
tests/               Pytest tests
config.py            App configuration
run.py               Local development entry point
```

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

## Initialize database
```
flask init-db
```

## Start the Flask development server:

```bash
python run.py
```

Open <http://127.0.0.1:5000> in your browser.

## Run Tests

```bash
pytest
```

## Run Seed Test (Populate the database with sample users and study sets)

```bash
py seed.py
```
