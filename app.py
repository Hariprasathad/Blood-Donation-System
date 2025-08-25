from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ===================== DB CONNECTION ======================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="7777",      # change if needed
    database="blood_db"   # must be created in MySQL
)
cursor = db.cursor(dictionary=True)

# ===================== AUTH ======================

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        blood_group = request.form["blood_group"]
        address = request.form["address"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing = cursor.fetchone()
        if existing:
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        cursor.execute(
            "INSERT INTO users (name, email, phone, blood_group, address, password) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, email, phone, blood_group, address, password)
        )
        db.commit()
        flash("Registered successfully! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# ===================== DASHBOARD ======================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# ===================== SEND BLOOD ======================

@app.route("/send", methods=["GET", "POST"])
def send():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        blood_group = request.form["blood_group"]
        phone = request.form["phone"]
        city = request.form["city"]
        units = request.form["units"]

        cursor.execute(
            "INSERT INTO donors (user_id, blood_group, phone, city, units) VALUES (%s, %s, %s, %s, %s)",
            (session["user_id"], blood_group, phone, city, units)
        )
        db.commit()

        flash("Blood details submitted successfully!", "success")
        return redirect(url_for("send_history"))

    return render_template("send.html")

@app.route("/send_history")
def send_history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor.execute("""
        SELECT u.name AS donor_name, u.email AS donor_email, u.phone AS donor_phone,
               d.city, d.blood_group, d.units,
               a.approved_at,
               u2.name AS approver_name, u2.email AS approver_email, u2.phone AS approver_phone
        FROM donors d
        JOIN users u ON d.user_id = u.id
        LEFT JOIN approvals a ON d.id = a.donor_id
        LEFT JOIN users u2 ON a.approved_by = u2.id
        WHERE u.id = %s
        ORDER BY d.id DESC
    """, (session["user_id"],))
    history = cursor.fetchall()

    return render_template("send_history.html", history=history)

# ===================== RECEIVE BLOOD ======================

@app.route("/received_request")
def received_request():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor.execute("""
        SELECT d.id, u.name AS donor_name, u.email AS donor_email, u.phone AS donor_phone,
               d.city, d.blood_group, d.units,
               CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END AS is_approved
        FROM donors d
        JOIN users u ON d.user_id = u.id
        LEFT JOIN approvals a ON d.id = a.donor_id
        ORDER BY d.id DESC
    """)
    donors = cursor.fetchall()

    return render_template("received_request.html", donors=donors)

@app.route("/approve/<int:donor_id>", methods=["POST"])
def approve_donor(donor_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    approved_by = session["user_id"]
    approved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO approvals (donor_id, approved_by, approved_at) VALUES (%s, %s, %s)",
        (donor_id, approved_by, approved_at)
    )
    db.commit()

    flash("Donor approved successfully!", "success")
    return redirect(url_for("received_request"))

@app.route("/receive_history")
def receive_history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor.execute("""
        SELECT u.name AS donor_name, u.email AS donor_email, u.phone AS donor_phone,
               d.city, d.blood_group, d.units,
               u2.name AS approver_name, u2.email AS approver_email, u2.phone AS approver_phone,
               a.approved_at
        FROM approvals a
        JOIN donors d ON a.donor_id = d.id
        JOIN users u ON d.user_id = u.id
        JOIN users u2 ON a.approved_by = u2.id
        WHERE a.approved_by = %s
        ORDER BY a.id DESC
    """, (session["user_id"],))
    history = cursor.fetchall()

    return render_template("receive_history.html", history=history)

# ===================== RUN ======================

if __name__ == "__main__":
    app.run(debug=True)
