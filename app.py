from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key

bcrypt = Bcrypt(app)

# Database config
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '7777',  # Change to your MySQL password
    'database': 'blood_donation'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        blood_group = request.form['blood_group']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already registered.', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor.execute(
            "INSERT INTO users (name, email, phone, blood_group, password) VALUES (%s, %s, %s, %s, %s)",
            (name, email, phone, blood_group, hashed_password)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['phone'] = user['phone']
            session['blood_group'] = user['blood_group']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT recipient, blood_group, DATE_FORMAT(date, '%Y-%m-%d') AS date FROM send_history WHERE user_id = %s ORDER BY date DESC",
        (user_id,)
    )
    send_history = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('dashboard.html',
                           name=session.get('name'),
                           email=session.get('email'),
                           phone=session.get('phone'),
                           blood_group=session.get('blood_group'),
                           send_history=send_history)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
