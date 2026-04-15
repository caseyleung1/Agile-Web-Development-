from flask import Blueprint, redirect, render_template, session, url_for

from app.blueprints.auth import user_stats
from app.decorators import current_user_id, login_required
from app.extensions import db
from app.models import StudySet

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user_id():
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    uid = current_user_id()
    assert uid is not None
    recent = (
        StudySet.query.filter_by(user_id=uid)
        .order_by(StudySet.updated_at.desc(), StudySet.id.desc())
        .limit(4)
        .all()
    )
    stats = user_stats(uid)
    return render_template("dashboard.html", recent_sets=recent, stats=stats)
