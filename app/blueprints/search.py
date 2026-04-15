from flask import Blueprint, render_template, request
from sqlalchemy import or_

from app.decorators import current_user_id, login_required
from app.extensions import db
from app.models import StudySet, User

search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.route("/")
@login_required
def search_public():
    q = (request.args.get("q") or "").strip()
    uid = current_user_id()
    query = (
        StudySet.query.filter(StudySet.is_public.is_(True))
        .join(User, StudySet.user_id == User.id)
        .order_by(StudySet.title)
    )
    if q:
        like = f"%{q}%"
        query = query.filter(or_(StudySet.title.ilike(like), StudySet.description.ilike(like)))
    sets = query.limit(50).all()
    counts = {}
    for s in sets:
        counts[s.id] = s.cards.count()
    return render_template("search/public.html", sets=sets, counts=counts, q=q, current_user_id=uid)
