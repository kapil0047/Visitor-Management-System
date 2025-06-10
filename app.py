from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/visit')
def visit():
    return render_template('visit.html')

@app.route('/checkin', methods=['POST'])
def checkin():
    name = request.form['name']
    email = request.form.get('email')  # Use .get() to avoid KeyError if missing
    phone = request.form.get('phone')
    employee_to_meet = request.form.get('employee_to_meet')
    visit_reason = request.form.get('visit_reason')
    photo = request.form.get('photo')

    # Save to database
    conn = sqlite3.connect('database/visitors.db')
    c = conn.cursor()
    c.execute("INSERT INTO visitors (name, email, phone, employee_to_meet, visit_reason, photo) VALUES (?, ?, ?, ?, ?, ?)", 
              (name, email, phone, employee_to_meet, visit_reason, photo))
    conn.commit()
    conn.close()

    return "Visitor check-in successful!"

if __name__ == '__main__':
    app.run(debug=True)
