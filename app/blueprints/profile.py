from flask import Blueprint, render_template

from app.blueprints.auth import user_stats
from app.decorators import current_user_id, login_required
from app.extensions import db
from app.models import StudySet

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/")
@login_required
def profile():
    uid = current_user_id()
    assert uid is not None
    stats = user_stats(uid)
    my_sets = StudySet.query.filter_by(user_id=uid).order_by(StudySet.title).limit(20).all()
    card_counts = {s.id: s.cards.count() for s in my_sets}
    return render_template("profile.html", stats=stats, sets=my_sets, card_counts=card_counts)
