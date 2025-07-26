from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = "your_secret_key"

def connect_db():
    return mysql.connector.connect(
        host="192.168.29.89",
        user="rahulj",
        password="root@123",
        database="doc_workflow"
    )

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'pass':  # replace with secure check
            session['admin_logged_in'] = True
            return redirect(url_for('add_user'))
        else:
            flash("Invalid admin credentials")
    return render_template('admin_login.html')

@app.route('/add-user', methods=['GET', 'POST'])
def add_user():
    if 'admin_logged_in' not in session:
        return redirect('/admin-login')

    if request.method == 'POST':
        emp_id = request.form['emp_id']
        dept_name = request.form['dept_name']
        full_name = request.form['full_name']
        password = request.form['password']
        role = request.form['role']
        feedback = request.form.get('feedback', '')

        # 🔒 hash the password before saving
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (emp_id, dept_name, full_name, password, role, feedback, force_password_change) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (emp_id, dept_name, full_name, hashed_pw, role, feedback, True))
            conn.commit()
            conn.close()
            flash("User created successfully.")
        except Exception as e:
            flash(str(e))

    return render_template("add_user.html")

@app.route('/show-users-details')
def admin_users():
    search_query = request.args.get('search', '').strip()
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    if search_query:
        cursor.execute("SELECT * FROM users WHERE emp_id LIKE %s", (f"%{search_query}%",))
    else:
        cursor.execute("SELECT * FROM users")

    users = cursor.fetchall()
    conn.close()

    return render_template('show_users_detail.html', users=users)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/editor-logs')
def editor_logs():
    search_query = request.args.get('search', '').strip()
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    if search_query:
        cursor.execute("""
            SELECT full_name, order_id, dept_name, file_name, open_datetime, submit_datetime
            FROM editor_logs
            WHERE order_id LIKE %s OR full_name LIKE %s OR dept_name LIKE %s OR file_name LIKE %s
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT full_name, order_id, dept_name, file_name, open_datetime, submit_datetime FROM editor_logs")
    data = cursor.fetchall()
    conn.close()
    return render_template("editor_logs.html", data=data)

@app.route('/qc-logs')
def qc_logs():
    search_query = request.args.get('search', '').strip()

    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    if search_query:
        cursor.execute("""
            SELECT qc_name, order_id, dept_name, file_name, open_datetime, feedback, submit_datetime
            FROM qc_logs
            WHERE order_id LIKE %s OR qc_name LIKE %s OR dept_name LIKE %s OR file_name LIKE %s
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("""
            SELECT qc_name, order_id, dept_name, file_name, open_datetime, feedback, submit_datetime
            FROM qc_logs
        """)

    data = cursor.fetchall()
    conn.close()

    return render_template("qc_logs.html", data=data)


if __name__ == "__main__":
    app.run(debug=True)
