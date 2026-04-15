from __future__ import annotations

import json
import os
from datetime import date

import requests
from flask import Blueprint, abort, jsonify, request

from app.decorators import current_user_id
from app.extensions import db
from app.models import Card, QuizAttempt, StudyProgress, StudySet, bump_cards_studied

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _require_login():
    uid = current_user_id()
    if not uid:
        abort(401)
    return uid


@api_bp.route("/progress", methods=["POST"])
def save_progress():
    uid = _require_login()
    data = request.get_json(force=True, silent=True) or {}
    card_id = data.get("card_id")
    rating = (data.get("rating") or "").lower()
    if rating not in ("easy", "medium", "hard"):
        return jsonify({"ok": False, "error": "invalid rating"}), 400
    c = Card.query.get_or_404(card_id)
    s = StudySet.query.get_or_404(c.study_set_id)
    if s.user_id != uid and not s.is_public:
        abort(403)
    row = StudyProgress.query.filter_by(user_id=uid, card_id=card_id).first()
    if row:
        row.rating = rating
    else:
        db.session.add(StudyProgress(user_id=uid, card_id=card_id, rating=rating))
    bump_cards_studied(uid, date.today())
    db.session.commit()
    return jsonify({"ok": True})


@api_bp.route("/quiz-attempt", methods=["POST"])
def quiz_attempt():
    uid = _require_login()
    data = request.get_json(force=True, silent=True) or {}
    set_id = data.get("study_set_id")
    mode = data.get("mode") or "quiz"
    if mode not in ("quiz", "timed"):
        mode = "quiz"
    s = StudySet.query.get_or_404(set_id)
    if s.user_id != uid and not s.is_public:
        abort(403)
    attempt = QuizAttempt(
        user_id=uid,
        study_set_id=set_id,
        mode=mode,
        score_percent=data.get("score_percent"),
        correct_count=int(data.get("correct_count") or 0),
        incorrect_count=int(data.get("incorrect_count") or 0),
        missed_count=int(data.get("missed_count") or 0),
        detail_json=json.dumps(data.get("details") or []),
    )
    db.session.add(attempt)
    db.session.commit()
    return jsonify({"ok": True, "id": attempt.id})


@api_bp.route("/ai/generate", methods=["POST"])
def ai_generate():
    _require_login()
    data = request.get_json(force=True, silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"ok": False, "error": "empty prompt"}), 400
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    if not key:
        return jsonify(
            {
                "ok": False,
                "error": "no_api_key",
                "message": "Set OPENAI_API_KEY in .env to enable AI generation.",
            }
        ), 503
    system = (
        "You respond with compact JSON only: "
        '{"question":"...","answer":"...","options":["opt1","opt2","opt3","opt4"]} '
        "where options include the correct answer once and three plausible distractors."
    )
    try:
        r = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt[:12000]},
                ],
                "temperature": 0.4,
            },
            timeout=60,
        )
        r.raise_for_status()
        payload = r.json()
        text = payload["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        parsed = json.loads(text)
        q = parsed.get("question") or ""
        a = parsed.get("answer") or ""
        opts = parsed.get("options") or []
        if len(opts) < 4:
            while len(opts) < 4:
                opts.append(a or "Option")
        opts = [str(x)[:500] for x in opts[:4]]
        correct_index = 0
        for i, o in enumerate(opts):
            if o.strip() == a.strip():
                correct_index = i
                break
        return jsonify(
            {
                "ok": True,
                "question": q,
                "answer": a,
                "options": opts,
                "correct_index": correct_index,
            }
        )
    except Exception as e:
        return jsonify({"ok": False, "error": "ai_failed", "message": str(e)}), 502
