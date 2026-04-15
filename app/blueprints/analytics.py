from datetime import date, timedelta

from flask import Blueprint, render_template

from app.blueprints.auth import user_stats
from app.decorators import current_user_id, login_required
from app.models import QuizAttempt, StudyDayStat, StudyProgress

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.route("/")
@login_required
def analytics():
    uid = current_user_id()
    assert uid is not None
    stats = user_stats(uid)
    studied = StudyProgress.query.filter_by(user_id=uid).count()
    attempts = QuizAttempt.query.filter_by(user_id=uid).order_by(QuizAttempt.id.desc()).limit(50).all()
    correct = sum(a.correct_count or 0 for a in attempts)
    wrong = sum(a.incorrect_count or 0 for a in attempts)
    total_ans = correct + wrong
    accuracy = round(100 * correct / total_ans, 0) if total_ans else 0

    # Last 7 days including today (week Sun-Sat style labels from mock)
    today = date.today()
    start = today - timedelta(days=6)
    rows = (
        StudyDayStat.query.filter(StudyDayStat.user_id == uid, StudyDayStat.day >= start, StudyDayStat.day <= today)
        .order_by(StudyDayStat.day)
        .all()
    )
    day_map = {r.day: r.cards_studied for r in rows}
    labels = []
    values = []
    for i in range(7):
        d = start + timedelta(days=i)
        labels.append(d.strftime("%a").upper()[:3])
        values.append(day_map.get(d, 0))

    return render_template(
        "analytics.html",
        stats=stats,
        cards_studied_count=studied,
        accuracy_pct=int(accuracy),
        streak=stats.get("streak_days", 0),
        chart_labels=labels,
        chart_values=values,
    )
