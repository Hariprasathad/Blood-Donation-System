from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime
from flask_mail import Mail, Message
import random
import string
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key_default")

# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "blood_donation")

# ===================== DB HELPER ======================

def get_db_connection(use_database=True):
    """
    Connects to MySQL database.
    If use_database is False, connects to MySQL server only (for creating DB).
    """
    config = {
        'host': DB_HOST,
        'user': DB_USER,
        'password': DB_PASSWORD
    }
    if use_database:
        config['database'] = DB_NAME
        
    conn = mysql.connector.connect(**config)
    return conn

def init_db():
    """Initializes the MySQL database with necessary tables."""
    try:
        # 1. Connect to Server and Create Database if not exists
        conn = get_db_connection(use_database=False)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.close()

        # 2. Connect to Database and Create Tables
        conn = get_db_connection(use_database=True)
        cursor = conn.cursor()
        
        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                phone VARCHAR(20),
                blood_group VARCHAR(5),
                address TEXT,
                password VARCHAR(255) NOT NULL
            )
        """)

        # Donors Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS donors (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                blood_group VARCHAR(5),
                phone VARCHAR(20),
                city VARCHAR(100),
                units INT,
                description TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Approvals Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                donor_id INT NOT NULL,
                approved_by INT NOT NULL,
                approved_at DATETIME,
                FOREIGN KEY (donor_id) REFERENCES donors (id) ON DELETE CASCADE,
                FOREIGN KEY (approved_by) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Daily Usage Stats Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                request_count INT DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()
        print("MySQL Database initialized successfully.")

    except mysql.connector.Error as err:
        print(f"Error initializing database: {err}")
        print("Please ensure MySQL is running and credentials in app.py are correct.")

# ===================== AUTH ======================

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if 'otp' not in session or 'register_data' not in session:
        flash("Session expired or invalid request. Please register again.", "warning")
        return redirect(url_for("register"))
    
    if request.method == "POST":
        user_otp = request.form.get("otp")
        if user_otp == session['otp']:
            data = session['register_data']
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, phone, blood_group, address, password) VALUES (%s, %s, %s, %s, %s, %s)",
                    (data['name'], data['email'], data['phone'], data['blood_group'], data['address'], data['password'])
                )
                conn.commit()
                # Clear session
                session.pop('otp', None)
                session.pop('register_data', None)
                
                flash("Email verified and registered successfully! Please login.", "success")
                return redirect(url_for("login"))
            except mysql.connector.Error as err:
                flash(f"Database error: {err}", "danger")
                return redirect(url_for("register"))
            finally:
                if 'conn' in locals() and conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            flash("Invalid OTP! Please try again.", "danger")
    
    return render_template("verify_otp.html")

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

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True) # Use dictionary cursor for easier access
            
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            existing = cursor.fetchone()
            
            if existing: # Check if email already registered
                flash("Email already registered!", "danger")
                return redirect(url_for("register"))
            
            # Generate OTP
            otp = ''.join(random.choices(string.digits, k=6))
            session['otp'] = otp
            session['register_data'] = {
                'name': name,
                'email': email,
                'phone': phone,
                'blood_group': blood_group,
                'address': address,
                'password': password
            }

            # Send OTP Email
            try:
                msg = Message('Verify Your Email - BloodLink', sender=app.config['MAIL_USERNAME'], recipients=[email])
                msg.body = f'Your OTP for registration is: {otp}'
                mail.send(msg)
                flash("OTP sent to your email. Please verify.", "info")
                return redirect(url_for("verify_otp"))
            except Exception as e:
                flash(f"Error sending email: {str(e)}", "danger")
                return redirect(url_for("register"))

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "danger")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
            user = cursor.fetchone()
            
            if user:
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]
                flash("Login successful!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid email or password!", "danger")
                return redirect(url_for("login"))
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "danger")
        finally:
            if 'conn' in locals() and conn.is_connected():
                if 'cursor' in locals():
                    cursor.close()
                conn.close()

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            
            if user:
                otp = ''.join(random.choices(string.digits, k=6))
                session['reset_otp'] = otp
                session['reset_email'] = email
                
                try:
                    msg = Message('Password Reset OTP - BloodLink', sender=app.config['MAIL_USERNAME'], recipients=[email])
                    msg.body = f'Your OTP for password reset is: {otp}'
                    mail.send(msg)
                    flash("OTP sent to your email. Please verify.", "info")
                    return redirect(url_for("verify_reset_otp"))
                except Exception as e:
                    flash(f"Error sending email: {str(e)}", "danger")
            else:
                flash("Email not found!", "danger")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "danger")
        finally:
            conn.close()
            
    return render_template("forgot_password.html")

@app.route("/verify_reset_otp", methods=["GET", "POST"])
def verify_reset_otp():
    if 'reset_otp' not in session or 'reset_email' not in session:
        flash("Session expired. Please try again.", "warning")
        return redirect(url_for("forgot_password"))
    
    if request.method == "POST":
        user_otp = request.form.get("otp")
        if user_otp == session['reset_otp']:
            session['otp_verified'] = True
            flash("OTP verified. Please reset your password.", "success")
            return redirect(url_for("reset_new_password"))
        else:
            flash("Invalid OTP! Please try again.", "danger")
            
    return render_template("verify_reset_otp.html")

@app.route("/reset_new_password", methods=["GET", "POST"])
def reset_new_password():
    if 'reset_otp' not in session or 'reset_email' not in session or not session.get('otp_verified'):
        flash("Session expired or unauthorized. Please try again.", "warning")
        return redirect(url_for("forgot_password"))
    
    if request.method == "POST":
        new_password = request.form["password"]
        email = session['reset_email']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password=%s WHERE email=%s", (new_password, email))
            conn.commit()
            
            session.pop('reset_otp', None)
            session.pop('reset_email', None)
            session.pop('otp_verified', None)
            
            flash("Password reset successfully! Please login.", "success")
            return redirect(url_for("login"))
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "danger")
        finally:
            conn.close()
            
    return render_template("reset_new_password.html")

# ===================== DASHBOARD ======================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# Gemini Configuration
GEMINI_ERROR = None
GEMINI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
        GEMINI_ERROR = "GEMINI_API_KEY not found in environment"
except ImportError as e:
    print(f"Warning: google-generativeai library not found. Error: {e}")
    GEMINI_AVAILABLE = False
    GEMINI_ERROR = str(e)
except Exception as e:
    print(f"Warning: google-generativeai configuration failed. Error: {e}")
    GEMINI_AVAILABLE = False
    GEMINI_ERROR = str(e)




def get_daily_usage(conn):
    print("DEBUG: Entering get_daily_usage")
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT request_count FROM daily_stats WHERE date = %s", (today,))
        result = cursor.fetchone()
        cursor.close() # Close cursor explicitly
        
        if result:
             print(f"DEBUG: usage found: {result['request_count']}")
             return result['request_count']
        else:
             print("DEBUG: Creating new daily stats entry")
             cursor = conn.cursor()
             cursor.execute("INSERT INTO daily_stats (date, request_count) VALUES (%s, 0)", (today,))
             conn.commit()
             cursor.close()
             return 0
    except Exception as e:
        print(f"Usage Check Error: {e}")
        return 0

def increment_daily_usage(conn):
    print("DEBUG: Entering increment_daily_usage")
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        cursor = conn.cursor()
        cursor.execute("UPDATE daily_stats SET request_count = request_count + 1 WHERE date = %s", (today,))
        conn.commit()
        cursor.close()
        print("DEBUG: Usage incremented")
    except Exception as e:
        print(f"Usage Increment Error: {e}")

def check_grammar_with_gemini(text):
    print(f"DEBUG: Checking grammar for text: {text[:20]}...")
    if not text or not GEMINI_AVAILABLE:
        if not GEMINI_AVAILABLE:
            print("Gemini API skipped: Library not installed.")
            return None, "Library Unavailable"
        return None, "No text"

    # Word Count Limit
    word_count = len(text.split())
    if word_count > 60:
        return None, "Text too long (Max 60 words)"
    

    # DEBUG: List available models to find the correct name
    try:
        print("DEBUG: querying available models...")
        found_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - Found model: {m.name}")
                found_models.append(m.name)
        
        if found_models:
             # If we found models, try those first!
             # prefer flash/pro
             models_to_try = sorted(found_models, key=lambda x: 0 if 'flash' in x else 1 if 'pro' in x else 2)
        else:
             print("DEBUG: No models found with generateContent support.")
             models_to_try = [
                'gemini-1.5-flash', 
                'gemini-1.5-flash-001',
                'models/gemini-1.5-flash',
                'gemini-1.0-pro',
                'gemini-pro'
            ]
    except Exception as e:
        print(f"DEBUG: Could not list models: {e}")
        models_to_try = ['gemini-1.5-flash', 'gemini-1.0-pro', 'gemini-pro']
    
    response = None
    errors = []

    for model_name in models_to_try:
        try:
            print(f"DEBUG: Attempting with model: {model_name}")
            model = genai.GenerativeModel(model_name)
            
            prompt = f"Correct the grammar of the following sentence. return ONLY the corrected sentence. Text: '{text}'"
            
            response = model.generate_content(prompt)
            print(f"DEBUG: Success with {model_name}")
            break
        except Exception as e:
             print(f"DEBUG: Failed with {model_name}. Error: {e}")
             errors.append(f"{model_name}: {e}")
             continue
        
    if not response:
         return None, f"All models failed. Errors: {'; '.join(str(e) for e in errors)}"

    if not response.parts:
         return None, "Empty Response"
         
    suggestion = response.text.replace('"', '').replace("'", "").strip()
    
    if suggestion and suggestion.lower() != text.lower():
         return suggestion, "Success"
    return None, "No improvement needed"


# ===================== SEND BLOOD ======================

@app.route("/send", methods=["GET", "POST"])
def send():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    # Daily Limit Removed - Now using word limit per request
    current_usage = 0 # Placeholder if needed for template compatibility or just remove
    limit_reached = False 
    
    can_use_gemini = GEMINI_AVAILABLE

    if request.method == "POST":
        print("DEBUG: Processing POST request")
        blood_group = request.form["blood_group"]
        phone = request.form["phone"]
        city = request.form["city"]
        units = request.form["units"]
        description = request.form.get("description", "")
        if not description:
            description = "-"
        
        suggestion = None
        ai_status_msg = ""

        final_description = description
        
        if description != "-" and can_use_gemini:
             # Check limits logic if you had it, or just proceed
             print("DEBUG: Calling grammar check")
             suggestion, ai_status_msg = check_grammar_with_gemini(description)
             if suggestion:
                 print("DEBUG: Incrementing usage")
                 increment_daily_usage(conn)
                 final_description = f"{description}\n\n[AI Suggestion]: {suggestion}"

        try:
            # Re-use connection or get cursor from existing
            if not conn.is_connected():
                conn = get_db_connection()
            
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO donors (user_id, blood_group, phone, city, units, description) VALUES (%s, %s, %s, %s, %s, %s)",
                (session["user_id"], blood_group, phone, city, units, final_description)
            )
            conn.commit()
            
            flash("Blood request submitted successfully!", "success")
            
            return redirect(url_for("send_history"))
        except mysql.connector.Error as err:
            flash(f"Error submitting request: {err}", "danger")
        finally:
            if 'conn' in locals() and conn.is_connected():
                if 'cursor' in locals():
                    cursor.close()
                conn.close()

    conn.close() # Close the initial connection for GET or before render
    return render_template("send.html", gemini_available=can_use_gemini, limit_reached=limit_reached, usage_count=current_usage, gemini_error=GEMINI_ERROR)

@app.route("/send_history")
def send_history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.id, u.name AS donor_name, u.email AS donor_email, d.phone AS donor_phone,
                d.city, d.blood_group, d.units, d.description,
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
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
        return redirect(url_for("dashboard"))
    finally:
        if 'conn' in locals() and conn.is_connected():
            if 'cursor' in locals():
                cursor.close()
            conn.close()

@app.route("/delete_request/<int:request_id>", methods=["POST"])
def delete_request(request_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify the request belongs to the user
        cursor.execute("SELECT id FROM donors WHERE id = %s AND user_id = %s", (request_id, session["user_id"]))
        request_exists = cursor.fetchone()
        
        if request_exists:
            cursor.execute("DELETE FROM donors WHERE id = %s", (request_id,))
            conn.commit()
            flash("Blood request deleted successfully.", "success")
        else:
            flash("Request not found or unauthorized.", "danger")
            
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
    finally:
        if 'conn' in locals() and conn.is_connected():
            if 'cursor' in locals():
                cursor.close()
            conn.close()
            
    return redirect(url_for("send_history"))


# ===================== RECEIVE BLOOD ======================

@app.route("/received_request")
def received_request():
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.id, u.name AS donor_name, u.email AS donor_email, d.phone AS donor_phone,
                d.city, d.blood_group, d.units, d.description,
                CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END AS is_approved
            FROM donors d
            JOIN users u ON d.user_id = u.id
            LEFT JOIN approvals a ON d.id = a.donor_id
            WHERE d.user_id != %s AND a.id IS NULL
            ORDER BY d.id DESC
        """, (session["user_id"],))
        donors = cursor.fetchall()
        return render_template("received_request.html", donors=donors)
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
        return redirect(url_for("dashboard"))
    finally:
        if 'conn' in locals() and conn.is_connected():
            if 'cursor' in locals():
                cursor.close()
            conn.close()

@app.route("/approve/<int:donor_id>", methods=["POST"])
def approve_donor(donor_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    approved_by = session["user_id"]
    approved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO approvals (donor_id, approved_by, approved_at) VALUES (%s, %s, %s)",
            (donor_id, approved_by, approved_at)
        )
        conn.commit()
        flash("Request accepted! Thank you for donating.", "success")
    except mysql.connector.Error as err:
        flash(f"Error approving donor: {err}", "danger")
    finally:
        if 'conn' in locals() and conn.is_connected():
            if 'cursor' in locals():
                cursor.close()
            conn.close()

    return redirect(url_for("received_request"))

@app.route("/receive_history")
def receive_history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.name AS patient_name, u.email AS patient_email, d.phone AS patient_contact,
                d.city, d.blood_group, d.units, d.description,
                u2.name AS donor_name, u2.phone AS donor_phone,
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
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
        return redirect(url_for("dashboard"))
    finally:
        if 'conn' in locals() and conn.is_connected():
            if 'cursor' in locals():
                cursor.close()
            conn.close()

# ===================== RUN ======================

if __name__ == "__main__":
    init_db()  # Initialize DB on first run (Requires MySQL server running)
    app.run(debug=True)
