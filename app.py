import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "campus_lost_found.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    items = db.relationship("Item", backref="owner", lazy=True)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    item_type = db.Column(db.String(10), nullable=False)  # Lost / Found
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="Active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.context_processor
def inject_user():
    user = db.session.get(User, session["user_id"]) if "user_id" in session else None
    return {"current_user": user}


@app.route("/")
def index():
    query = Item.query.filter_by(status="Active")

    item_type = request.args.get("type", "")
    category = request.args.get("category", "")
    search = request.args.get("search", "").strip()

    if item_type in {"Lost", "Found"}:
        query = query.filter_by(item_type=item_type)
    if category:
        query = query.filter_by(category=category)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Item.title.ilike(pattern),
                Item.description.ilike(pattern),
                Item.location.ilike(pattern),
            )
        )

    items = query.order_by(Item.created_at.desc()).all()
    return render_template("index.html", items=items, selected_type=item_type,
                           selected_category=category, search=search)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return render_template("register.html")

        user = User(name=name, email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Account created. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Welcome back!", "success")
            return redirect(url_for("index"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if request.method == "POST":
        image = request.files.get("image")
        filename = None

        if image and image.filename:
            if not allowed_file(image.filename):
                flash("Only PNG, JPG, JPEG, GIF and WEBP images are allowed.", "error")
                return render_template("report.html")
            filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{secure_filename(image.filename)}"
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        item = Item(
            title=request.form["title"].strip(),
            description=request.form["description"].strip(),
            category=request.form["category"],
            location=request.form["location"].strip(),
            item_type=request.form["item_type"],
            image=filename,
            user_id=session["user_id"],
        )

        if not item.title or not item.description or not item.location:
            flash("Please fill in all required fields.", "error")
            return render_template("report.html")

        db.session.add(item)
        db.session.commit()
        flash("Item reported successfully.", "success")
        return redirect(url_for("item_detail", item_id=item.id))

    return render_template("report.html")


@app.route("/item/<int:item_id>")
def item_detail(item_id):
    item = db.get_or_404(Item, item_id)
    return render_template("item_detail.html", item=item)


@app.route("/item/<int:item_id>/resolve", methods=["POST"])
@login_required
def resolve_item(item_id):
    item = db.get_or_404(Item, item_id)

    if item.user_id != session["user_id"]:
        flash("You can only close your own reports.", "error")
        return redirect(url_for("item_detail", item_id=item.id))

    item.status = "Resolved"
    db.session.commit()
    flash("Report marked as resolved.", "success")
    return redirect(url_for("item_detail", item_id=item.id))


@app.route("/my-items")
@login_required
def my_items():
    items = Item.query.filter_by(user_id=session["user_id"]).order_by(Item.created_at.desc()).all()
    return render_template("my_items.html", items=items)


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
