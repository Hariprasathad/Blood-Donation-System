from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",       # change to your MySQL username
    password="7777",       # change to your MySQL password
    database="blood_donation"
)
cursor = db.cursor(dictionary=True)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/donor', methods=['GET', 'POST'])
def donor():
    if request.method == 'POST':
        name = request.form['name']
        blood_group = request.form['blood_group']
        pincode = int(request.form['pincode'])
        phone = request.form['phone']

        cursor.execute("INSERT INTO donors (name, blood_group, pincode, phone) VALUES (%s, %s, %s, %s)",
                       (name, blood_group, pincode, phone))
        db.commit()
        return redirect('/')
    return render_template("donor.html")

@app.route('/receiver', methods=['GET', 'POST'])
def receiver():
    if request.method == 'POST':
        blood_group = request.form['blood_group']
        pincode = int(request.form['pincode'])

        min_pin = pincode - 1
        max_pin = pincode + 1

        cursor.execute("SELECT * FROM donors WHERE blood_group=%s AND pincode BETWEEN %s AND %s",
                       (blood_group, min_pin, max_pin))
        donors = cursor.fetchall()
        return render_template("results.html", donors=donors)

    return render_template("receiver.html")

if __name__ == "__main__":
    app.run(debug=True)
