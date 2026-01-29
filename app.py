from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
import string
import random
import os

# ---------------- CONFIG ----------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "instance/database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---------------- DATABASE ----------------
db = SQLAlchemy(app)

# ---------------- LOGIN MANAGER ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------- MODELS ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(9), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_url = db.Column(db.String(10), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

# ---------------- CREATE DATABASE (Flask 3 FIX) ----------------
with app.app_context():
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    db.create_all()

# ---------------- USER LOADER ----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- HELPER FUNCTION ----------------
def generate_short_url():
    return "".join(random.choices(string.ascii_letters + string.digits, k=6))

# ---------------- ROUTES ----------------

# LOGIN
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")

    return render_template("login.html")

# SIGNUP
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Username length validation
        if len(username) < 5 or len(username) > 9:
            flash("Username must be between 5 to 9 characters long")
            return redirect(url_for("signup"))

        # Unique username check
        if User.query.filter_by(username=username).first():
            flash("This username already exists...")
            return redirect(url_for("signup"))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful! Please login.")
        return redirect(url_for("login"))

    return render_template("signup.html")

# DASHBOARD (URL SHORTENER)
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    short_url = None

    if request.method == "POST":
        original_url = request.form["url"]
        short_url = generate_short_url()

        url = URL(
            original_url=original_url,
            short_url=short_url,
            user_id=current_user.id
        )
        db.session.add(url)
        db.session.commit()

    urls = URL.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", short_url=short_url, urls=urls)

# REDIRECT SHORT URL
@app.route("/<short>")
def redirect_url(short):
    url = URL.query.filter_by(short_url=short).first_or_404()
    return redirect(url.original_url)

# LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
