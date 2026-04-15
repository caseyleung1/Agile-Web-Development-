from functools import wraps

from flask import redirect, request, session, url_for


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)

    return decorated


def current_user_id() -> int | None:
    uid = session.get("user_id")
    return int(uid) if uid is not None else None
