"""
app.py
SharePlate -- Flask application entrypoint.

Run with:
    python app.py
(after installing requirements.txt and creating the DB from schema.sql)
"""
import os
from flask import Flask, send_from_directory, abort

from routes.auth import auth_bp
from routes.provider import provider_bp
from routes.ngo import ngo_bp
from routes.volunteer import volunteer_bp
from helpers import get_current_user

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit

app.register_blueprint(auth_bp)
app.register_blueprint(provider_bp)
app.register_blueprint(ngo_bp)
app.register_blueprint(volunteer_bp)


@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}


@app.route("/uploads/food/<path:filename>")
def uploaded_food_photo(filename):
    """Food photos are public (shown in the NGO discovery feed)."""
    folder = os.path.join(app.config["UPLOAD_FOLDER"], "food")
    return send_from_directory(folder, filename)


@app.route("/uploads/documents/<path:filename>")
def uploaded_document(filename):
    """Verification documents are private -- only the logged-in owner may view theirs."""
    user = get_current_user()
    if not user:
        abort(403)
    folder = os.path.join(app.config["UPLOAD_FOLDER"], "documents")
    return send_from_directory(folder, filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
