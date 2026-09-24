"""
routes/auth.py
Landing page + role-based registration (with mandatory document upload
for Providers/NGOs) + login/logout.
"""
import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from db import query
from helpers import get_current_user

auth_bp = Blueprint("auth", __name__)

ALLOWED_DOC_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}


def _allowed_file(filename, allowed):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def _save_document(file_storage, subfolder):
    """Save an uploaded document with a unique name, return its stored path."""
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(folder, exist_ok=True)
    full_path = os.path.join(folder, unique_name)
    file_storage.save(full_path)
    return os.path.join(subfolder, unique_name)


@auth_bp.route("/")
def home():
    user = get_current_user()
    if user:
        if user["role"] == "provider":
            return redirect(url_for("provider.dashboard"))
        if user["role"] == "ngo":
            return redirect(url_for("ngo.discover"))
        if user["role"] == "volunteer":
            return redirect(url_for("volunteer.dashboard"))
    return render_template("home.html")


@auth_bp.route("/register/<role>", methods=["GET", "POST"])
def register(role):
    if role not in ("provider", "ngo", "volunteer"):
        flash("Unknown account type.", "error")
        return redirect(url_for("auth.home"))

    if request.method == "GET":
        return render_template("register.html", role=role)

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    latitude = request.form.get("latitude") or None
    longitude = request.form.get("longitude") or None

    if not name or not email or not password:
        flash("Name, email and password are required.", "error")
        return render_template("register.html", role=role, form=request.form)

    existing = query("SELECT id FROM users WHERE email = %s", (email,), fetchone=True)
    if existing:
        flash("An account with that email already exists.", "error")
        return render_template("register.html", role=role, form=request.form)

    # Providers and NGOs must upload a verification document
    doc_file = request.files.get("document")
    if role in ("provider", "ngo"):
        if not doc_file or doc_file.filename == "":
            flash("A verification document is required for this account type.", "error")
            return render_template("register.html", role=role, form=request.form)
        if not _allowed_file(doc_file.filename, ALLOWED_DOC_EXTENSIONS):
            flash("Document must be a PDF, PNG or JPG file.", "error")
            return render_template("register.html", role=role, form=request.form)

    password_hash = generate_password_hash(password)

    new_user = query(
        """
        INSERT INTO users (role, name, email, password_hash, phone, address, latitude, longitude)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (role, name, email, password_hash, phone, address, latitude, longitude),
        fetchone=True,
        commit=True,
    )
    user_id = new_user["id"]

    if role in ("provider", "ngo") and doc_file:
        doc_type = "FSSAI/Health License" if role == "provider" else "NGO Registration Certificate"
        stored_path = _save_document(doc_file, "documents")
        query(
            "INSERT INTO documents (user_id, doc_type, file_path) VALUES (%s, %s, %s)",
            (user_id, doc_type, stored_path),
            commit=True,
        )

    flash("Account created! Please log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = query(
        "SELECT id, role, name, password_hash FROM users WHERE email = %s",
        (email,),
        fetchone=True,
    )

    if not user or not check_password_hash(user["password_hash"], password):
        flash("Invalid email or password.", "error")
        return render_template("login.html", email=email)

    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    flash(f"Welcome back, {user['name']}!", "success")

    if user["role"] == "provider":
        return redirect(url_for("provider.dashboard"))
    if user["role"] == "ngo":
        return redirect(url_for("ngo.discover"))
    return redirect(url_for("volunteer.dashboard"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.home"))
