from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root@123",
        database="doc_workflow"
    )

@app.route('/')
def home():
    return "<a href='/editor-logs'>Editor Logs</a> | <a href='/qc-logs'>QC Logs</a>"

@app.route('/editor-logs')
def editor_logs():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT emp_id, emp_name, order_id, open_datetime, submit_datetime FROM editor_logs")
    data = cursor.fetchall()
    conn.close()
    return render_template("editor_logs.html", data=data)

@app.route('/qc-logs')
def qc_logs():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT qc_id, qc_name, order_id, open_datetime, submit_datetime FROM qc_logs")
    data = cursor.fetchall()
    conn.close()
    return render_template("qc_logs.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
