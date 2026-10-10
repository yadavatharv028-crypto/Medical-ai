"""
app.py
======
Main Flask application for the AI Medical Appointment & Disease Prediction System.
Handles user authentication, disease prediction, appointment booking,
doctor dashboard, and admin dashboard.
"""

import os
import re
import json
import joblib
import numpy as np
import hashlib
from datetime import datetime, date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash
)
import mysql.connector


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.config.from_object("config.Config")


def get_db():
    """Return a new MySQL connection using config values."""
    return mysql.connector.connect(
        host=app.config["MYSQL_HOST"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DB"],
        port=app.config["MYSQL_PORT"],
    )


def query(sql, params=(), fetchone=False, commit=False):
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)

        if commit:
            conn.commit()
            result = cur.lastrowid
        elif fetchone:
            result = cur.fetchone()
        else:
            result = cur.fetchall()

        cur.close()
        conn.close()
        return result

    except Exception as e:
        print("DB ERROR:", e)
        return None


# password hashing
def hash_password(pw: str) -> str:
    """SHA-256 hash of the password (use bcrypt in production)."""
    return hashlib.sha256(pw.encode()).hexdigest()


# model_bundle
_model_bundle = None
_meta = None

def load_model():
    global _model_bundle, _meta
    if _model_bundle is None:
        mp = app.config["MODEL_PATH"]
        if not os.path.exists(mp):
            raise FileNotFoundError(
                "disease_model.pkl not found. Run: python backend/train_model.py"
            )
        _model_bundle = joblib.load(mp)
    if _meta is None:
        with open(app.config["META_PATH"]) as f:
            _meta = json.load(f)
    return _model_bundle, _meta



def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


def doctor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "doctor":
            flash("Doctor access required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email format.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        existing = query("SELECT id FROM users WHERE email = %s", (email,), fetchone=True)
        if existing:
            flash("Email already registered.", "danger")
            return render_template("register.html")

        query(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'patient')",
            (name, email, hash_password(password)),
            commit=True,
        )

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password required.", "danger")
            return render_template("login.html")

        user = query(
            "SELECT * FROM users WHERE email = %s",
            (email,),
            fetchone=True,
        )

        if user and user["password"] == hash_password(password):
            session["user_id"] = user["id"]
            session["name"]    = user["name"]
            session["email"]   = user["email"]
            session["role"]    = user["role"]

            flash("Login successful!", "success")

            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user["role"] == "doctor":
                return redirect(url_for("doctor_dashboard"))
            else:
                return redirect(url_for("dashboard"))

        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))



@app.route("/dashboard")
@login_required
def dashboard():
    # Recent predictions for this user
    predictions = query(
        "SELECT * FROM predictions WHERE user_id = %s ORDER BY date DESC LIMIT 5",
        (session["user_id"],),
    )
    # Upcoming appointments
    appointments = query(
        """SELECT a.*, d.name AS doctor_name, d.specialization
           FROM appointments a
           JOIN doctors d ON a.doctor_id = d.id
           WHERE a.user_id = %s
           ORDER BY a.appointment_date DESC LIMIT 5""",
        (session["user_id"],),
    )
    return render_template(
        "dashboard.html",
        predictions=predictions,
        appointments=appointments,
    )


# ══════════════════════════════════════════════════════════════════════════════
# DISEASE PREDICTION
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    bundle, meta = load_model()
    symptoms = meta["symptoms"]

    if request.method == "POST":
        selected = request.form.getlist("symptoms")
        if not selected:
            flash("Please select at least one symptom.", "warning")
            return render_template("predict.html", symptoms=symptoms)

        # Build feature vector
        feature_vector = [1 if s in selected else 0 for s in symptoms]
        X = np.array([feature_vector])

        model   = bundle["model"]
        encoder = bundle["encoder"]

        pred_idx   = model.predict(X)[0]
        proba      = model.predict_proba(X)[0]
        confidence = round(float(np.max(proba)) * 100, 1)
        disease    = encoder.inverse_transform([pred_idx])[0]

        # Top-3 predictions
        top3_idx  = np.argsort(proba)[::-1][:3]
        top3      = [
            {"disease": encoder.inverse_transform([i])[0], "confidence": round(float(proba[i]) * 100, 1)}
            for i in top3_idx
        ]

        # Save to predictions table
        query(
            """INSERT INTO predictions (user_id, symptoms, predicted_disease, confidence, date)
               VALUES (%s, %s, %s, %s, %s)""",
            (session["user_id"], ", ".join(selected), disease, confidence, datetime.now()),
            commit=True,
        )

        return render_template(
            "predict.html",
            symptoms=symptoms,
            selected=selected,
            disease=disease,
            confidence=confidence,
            top3=top3,
        )

    return render_template("predict.html", symptoms=symptoms)


# AJAX endpoint for prediction
@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    # data     = request.get_json(force=True)
    if not request.is_json:
        return jsonify({"error": "Invalid request"}), 400
    
    data = request.get_json()
    selected = data.get("symptoms", [])

    if not selected:
        return jsonify({"error": "No symptoms provided"}), 400

    bundle, meta = load_model()
    symptoms = meta["symptoms"]
    model    = bundle["model"]
    encoder  = bundle["encoder"]

    feature_vector = [1 if s in selected else 0 for s in symptoms]
    X = np.array([feature_vector])

    pred_idx   = model.predict(X)[0]
    proba      = model.predict_proba(X)[0]
    confidence = round(float(np.max(proba)) * 100, 1)
    disease    = encoder.inverse_transform([pred_idx])[0]

    top3_idx = np.argsort(proba)[::-1][:3]
    top3     = [
        {"disease": encoder.inverse_transform([i])[0], "confidence": round(float(proba[i]) * 100, 1)}
        for i in top3_idx
    ]

    # Persist prediction
    query(
        """INSERT INTO predictions (user_id, symptoms, predicted_disease, confidence, date)
           VALUES (%s, %s, %s, %s, %s)""",
        (session["user_id"], ", ".join(selected), disease, confidence, datetime.now()),
        commit=True,
    )

    return jsonify({"disease": disease, "confidence": confidence, "top3": top3})


# ══════════════════════════════════════════════════════════════════════════════
# APPOINTMENT BOOKING
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/appointment", methods=["GET", "POST"])
@login_required
def appointment():
    specialization = request.args.get("specialization", "")

    doctors = query(
        "SELECT * FROM doctors WHERE specialization LIKE %s ORDER BY name",
        (f"%{specialization}%",),
    ) if specialization else query("SELECT * FROM doctors ORDER BY name")

    specializations = query("SELECT DISTINCT specialization FROM doctors ORDER BY specialization")

    if request.method == "POST":
        doctor_id        = request.form.get("doctor_id")
        appointment_date = request.form.get("appointment_date")

        if not doctor_id or not appointment_date:
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("appointment"))

        # validate doctor
        doctor = query("SELECT * FROM doctors WHERE id = %s", (doctor_id,), fetchone=True)
        if not doctor:
            flash("Invalid doctor selected.", "danger")
            return redirect(url_for("appointment"))

        # validate date
        try:
            appt_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            if appt_date < date.today():
                flash("Cannot book past dates.", "danger")
                return redirect(url_for("appointment"))
        except:
            flash("Invalid date format.", "danger")
            return redirect(url_for("appointment"))

        import html
        symptoms_text = html.escape(request.form.get("symptoms", "").strip())

        query(
            """INSERT INTO appointments
               (user_id, doctor_id, appointment_date, symptoms, status)
               VALUES (%s, %s, %s, %s, 'pending')""",
            (session["user_id"], doctor_id, appointment_date, symptoms_text),
            commit=True,
        )

        flash("Appointment booked successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template(
        "appointment.html",
        doctors=doctors or [],
        specializations=specializations or [],
        selected_spec=specialization,
        now=date.today().isoformat(),
    )


# ══════════════════════════════════════════════════════════════════════════════
# PREDICTION HISTORY
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/history")
@login_required
def history():
    predictions = query(
        "SELECT * FROM predictions WHERE user_id = %s ORDER BY date DESC",
        (session["user_id"],),
    )
    return render_template("history.html", predictions=predictions)


# ══════════════════════════════════════════════════════════════════════════════
# DOCTOR DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/doctor/dashboard")
@login_required
@doctor_required
def doctor_dashboard():
    # Find doctor record linked to logged-in user
    doctor = query(
        "SELECT * FROM doctors WHERE user_id = %s",
        (session["user_id"],),
        fetchone=True,
    )
    if not doctor:
        flash("No doctor profile found.", "danger")
        return redirect(url_for("dashboard"))

    appointments = query(
        """SELECT a.*, u.name AS patient_name, u.email AS patient_email
           FROM appointments a
           JOIN users u ON a.user_id = u.id
           WHERE a.doctor_id = %s
           ORDER BY a.appointment_date DESC""",
        (doctor["id"],),
    )
    return render_template(
        "doctor_dashboard.html",
        doctor=doctor,
        appointments=appointments,
    )


@app.route("/doctor/appointment/<int:appt_id>/status", methods=["POST"])
@login_required
@doctor_required
def update_appointment_status(appt_id):
    status = request.form.get("status")

    doctor = query(
        "SELECT * FROM doctors WHERE user_id = %s",
        (session["user_id"],),
        fetchone=True,
    )

    if not doctor:
        flash("Doctor not found.", "danger")
        return redirect(url_for("dashboard"))

    appt = query(
        "SELECT * FROM appointments WHERE id = %s AND doctor_id = %s",
        (appt_id, doctor["id"]),
        fetchone=True,
    )

    if not appt:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("doctor_dashboard"))

    if status in ("pending", "confirmed", "completed", "cancelled"):
        query(
            "UPDATE appointments SET status = %s WHERE id = %s",
            (status, appt_id),
            commit=True,
        )
        flash("Appointment updated.", "success")

    return redirect(url_for("doctor_dashboard"))

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    users        = query("SELECT * FROM users ORDER BY id DESC") or []
    doctors      = query("SELECT * FROM doctors ORDER BY name") or []
    appointments = query(
        """SELECT a.*, u.name AS patient_name, d.name AS doctor_name
           FROM appointments a
           JOIN users u ON a.user_id = u.id
           JOIN doctors d ON a.doctor_id = d.id
           ORDER BY a.appointment_date DESC"""
    ) or []

    predictions = query(
        """SELECT p.*, u.name AS user_name
           FROM predictions p
           JOIN users u ON p.user_id = u.id
           ORDER BY p.date DESC LIMIT 50"""
    ) or []

    # Safe stats
    pred_count = query("SELECT COUNT(*) AS cnt FROM predictions", fetchone=True)

    stats = {
        "total_users": len([u for u in users if u.get("role") == "patient"]),
        "total_doctors": len(doctors),
        "total_appointments": len(appointments),
        "total_predictions": pred_count["cnt"] if pred_count else 0,
    }

    return render_template(
        "admin_dashboard.html",
        users=users,
        doctors=doctors,
        appointments=appointments,
        predictions=predictions,
        stats=stats,
    )

@app.route("/admin/doctor/add", methods=["POST"])
@login_required
@admin_required
def admin_add_doctor():
    name           = request.form.get("name", "").strip()
    specialization = request.form.get("specialization", "").strip()
    email          = request.form.get("email", "").strip().lower()
    password       = request.form.get("password", "")

    if not all([name, specialization, email, password]):
        flash("All fields are required.", "danger")
        return redirect(url_for("admin_dashboard"))

    # check duplicate email
    existing = query("SELECT id FROM users WHERE email = %s", (email,), fetchone=True)
    if existing:
        flash("Email already exists.", "danger")
        return redirect(url_for("admin_dashboard"))

    # Create user
    user_id = query(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'doctor')",
        (name, email, hash_password(password)),
        commit=True,
    )

    if not user_id:
        flash("Error creating doctor user.", "danger")
        return redirect(url_for("admin_dashboard"))

    # Create doctor profile
    doc = query(
        "INSERT INTO doctors (name, specialization, user_id) VALUES (%s, %s, %s)",
        (name, specialization, user_id),
        commit=True,
    )

    if not doc:
        flash("Doctor profile creation failed.", "danger")
        return redirect(url_for("admin_dashboard"))

    flash(f"Doctor '{name}' added successfully.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/doctor/delete/<int:doctor_id>", methods=["POST"])
@login_required
@admin_required
def admin_delete_doctor(doctor_id):
    doc = query("SELECT * FROM doctors WHERE id = %s", (doctor_id,), fetchone=True)
    if doc:
        query("DELETE FROM doctors WHERE id = %s", (doctor_id,), commit=True)
        query("DELETE FROM users WHERE id = %s", (doc["user_id"],), commit=True)
        flash("Doctor removed.", "success")
    return redirect(url_for("admin_dashboard"))


# ══════════════════════════════════════════════════════════════════════════════
# API: symptoms list (for dynamic frontend)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/symptoms")
@login_required
def api_symptoms():
    _, meta = load_model()
    return jsonify({"symptoms": meta["symptoms"]})


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
