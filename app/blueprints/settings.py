from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.decorators import current_user_id, login_required
from app.extensions import db
from app.models import User

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def settings():
    uid = current_user_id()
    assert uid is not None
    u = User.query.get_or_404(uid)
    if request.method == "POST":
        u.full_name = (request.form.get("username") or u.full_name).strip() or u.full_name
        u.email = (request.form.get("email") or u.email).strip().lower() or u.email
        u.title = (request.form.get("title") or "").strip() or None
        u.language = (request.form.get("language") or u.language).strip() or u.language
        u.notify_study_reminder = request.form.get("notify_study_reminder") == "on"
        u.notify_daily_goal = request.form.get("notify_daily_goal") == "on"
        u.notify_friend = request.form.get("notify_friend") == "on"
        u.notify_new_sets = request.form.get("notify_new_sets") == "on"
        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("settings.settings"))
    return render_template("settings.html", user=u)
