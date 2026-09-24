"""
helpers.py
Session-based auth helpers shared by all route blueprints.
"""
from functools import wraps
from flask import session, redirect, url_for, flash, g
from db import query


def get_current_user():
    """Return the logged-in user's row (dict) or None. Cached on flask.g."""
    if "user" in g:
        return g.user

    user_id = session.get("user_id")
    if not user_id:
        g.user = None
        return None

    g.user = query(
        "SELECT id, role, name, email, phone, address, latitude, longitude, "
        "is_verified, created_at FROM users WHERE id = %s",
        (user_id,),
        fetchone=True,
    )
    return g.user


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped


def role_required(role):
    """Restrict a route to a single role, e.g. @role_required('provider')."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user:
                flash("Please log in to continue.", "error")
                return redirect(url_for("auth.login"))
            if user["role"] != role:
                flash("You don't have access to that page.", "error")
                return redirect(url_for("auth.home"))
            return view_func(*args, **kwargs)
        return wrapped
    return decorator
