import os
import uuid
from functools import wraps

from cs50 import SQL
from flask import Flask, render_template, request, redirect, session, abort
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

from analyzer import analyze_image

app = Flask(__name__)

# Seguridad básica
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-this")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # True si usas HTTPS
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB máximo

Session(app)

# Base de datos SQLite
db = SQL("sqlite:///emotion_app.db")

UPLOAD_FOLDER = "static/uploads"
RESULT_FOLDER = "static/results"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def is_valid_image(file_storage):
    try:
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream)
        img.verify()
        file_storage.stream.seek(0)
        return True
    except (UnidentifiedImageError, OSError):
        file_storage.stream.seek(0)
        return False


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.errorhandler(413)
def too_large(e):
    rows = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"]) if session.get("user_id") else []
    username = rows[0]["username"] if rows else "User"
    return render_template("index.html", error="File too large. Maximum size is 5 MB.", username=username), 413


@app.route("/")
@login_required
def index():
    rows = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
    username = rows[0]["username"] if rows else "User"
    return render_template("index.html", username=username)


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    rows = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
    username = rows[0]["username"] if rows else "User"

    if "image" not in request.files:
        return render_template("index.html", error="No file was uploaded.", username=username)

    file = request.files["image"]

    if file.filename == "":
        return render_template("index.html", error="Please select an image.", username=username)

    if not allowed_file(file.filename):
        return render_template(
            "index.html",
            error="Only PNG, JPG, JPEG, and WEBP files are allowed.",
            username=username
        )

    if not is_valid_image(file):
        return render_template(
            "index.html",
            error="Uploaded file is not a valid image.",
            username=username
        )

    unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    input_path = os.path.join(UPLOAD_FOLDER, unique_name)
    output_name = f"result_{unique_name}"
    output_path = os.path.join(RESULT_FOLDER, output_name)

    file.save(input_path)
    detections = analyze_image(input_path, output_path)

    return render_template(
        "result.html",
        original_image=input_path,
        result_image=output_path,
        detections=detections,
        username=username
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username:
            return render_template("login.html", error="Must provide username.")
        if not password:
            return render_template("login.html", error="Must provide password.")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return render_template("login.html", error="Invalid username or password.")

        session["user_id"] = rows[0]["id"]
        return redirect("/")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")

        if not username:
            return render_template("register.html", error="Must provide username.")
        if len(username) > 50:
            return render_template("register.html", error="Username is too long.")
        if not password:
            return render_template("register.html", error="Must provide password.")
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters.")
        if not confirmation:
            return render_template("register.html", error="Must provide password confirmation.")
        if password != confirmation:
            return render_template("register.html", error="Passwords do not match.")

        existing_user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(existing_user) > 0:
            return render_template("register.html", error="Username already exists.")

        password_hash = generate_password_hash(password, method="scrypt", salt_length=16)

        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            username,
            password_hash
        )

        return redirect("/login")

    return render_template("register.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect("/login")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirmation = request.form.get("confirmation", "")

        if not current_password:
            return render_template("change_password.html", error="Must provide current password.")
        if not new_password:
            return render_template("change_password.html", error="Must provide new password.")
        if len(new_password) < 8:
            return render_template("change_password.html", error="New password must be at least 8 characters.")
        if not confirmation:
            return render_template("change_password.html", error="Must confirm new password.")
        if new_password != confirmation:
            return render_template("change_password.html", error="New passwords must match.")

        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        if len(rows) != 1:
            return redirect("/login")

        if not check_password_hash(rows[0]["hash"], current_password):
            return render_template("change_password.html", error="Current password is incorrect.")

        new_hash = generate_password_hash(new_password, method="scrypt", salt_length=16)

        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?",
            new_hash,
            session["user_id"]
        )

        return redirect("/")

    return render_template("change_password.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
