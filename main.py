import tkinter as tk
from tkinter import messagebox, filedialog
import os
import shutil
import datetime
import mysql.connector
from mysql.connector import Error
import subprocess
import pythoncom
import sys
import bcrypt

# ------------------------------------ DEFAULT_WINDOW_SIZE --------------------------------------------

DEFAULT_WINDOW_SIZE = "400x250"

# ------------------------------------ Path helper for PyInstaller ------------------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ------------------------------------ MySQL DB Connection ------------------------------------
def connect_db():
    return mysql.connector.connect(
        host='localhost',#'192.168.29.172',
        user='Test',
        password='root@123',
        database='doc_workflow'
    )

# ------------------------------------ Show Role Selection ------------------------------------
def show_login():
    def editor_login():
        login_window.destroy()
        auth_page(role="editor")

    def qc_login():
        login_window.destroy()
        auth_page(role="qc")

    login_window = tk.Tk()
    login_window.iconbitmap(resource_path("CDR_LOGO_Black.ico"))
    login_window.title("Editor Workflow Form")
    login_window.geometry(DEFAULT_WINDOW_SIZE)

    tk.Label(login_window, text="Login as:").pack(pady=10)
    tk.Button(login_window, text="Editor", width=20, command=editor_login).pack(pady=5)
    tk.Button(login_window, text="QC", width=20, command=qc_login).pack(pady=5)

    login_window.mainloop()

# ------------------------------------ Login/Signup Page ------------------------------------
def auth_page(role):
    def login():
        username = username_entry.get()
        password = password_entry.get()

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username=%s AND role=%s", (username, role))
            result = cursor.fetchone()
            conn.close()

            if result and bcrypt.checkpw(password.encode(), result[0].encode()):
                auth_window.destroy()
                if role == "editor":
                    open_editor_form()
                else:
                    open_qc_form()
            else:
                messagebox.showerror("Login Failed", "Invalid credentials")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def signup():
        username = username_entry.get()
        password = password_entry.get()

        if not username or not password:
            messagebox.showwarning("Missing Info", "Enter username and password")
            return

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                messagebox.showerror("Signup Failed", "Username already exists")
            else:
                hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                               (username, hashed_pw, role))
                conn.commit()
                messagebox.showinfo("Signup Success", "Account created! Please log in.")
                auth_window.destroy()
                auth_page(role)  # Refresh login page after signup
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def go_back():
        auth_window.destroy()
        show_login()

    auth_window = tk.Tk()
    auth_window.title(f"{role.capitalize()} Authentication")
    auth_window.iconbitmap(resource_path("CDR_LOGO_Black.ico"))
    auth_window.geometry(DEFAULT_WINDOW_SIZE)

    tk.Button(auth_window, text="Back", width=20, command=go_back).pack(pady=5)

    tk.Label(auth_window, text=f"{role.capitalize()} Login/Signup").pack(pady=10)
    tk.Label(auth_window, text="Username").pack()
    username_entry = tk.Entry(auth_window)
    username_entry.pack()

    tk.Label(auth_window, text="Password").pack()
    password_entry = tk.Entry(auth_window, show='*')
    password_entry.pack()

    tk.Button(auth_window, text="Login", command=login).pack(pady=5)
    tk.Button(auth_window, text="Sign Up", command=signup).pack()

    auth_window.mainloop()


# ------------------------------------ Editor Workflow Form ------------------------------------
def open_editor_form():
    def submit():
        emp_id = emp_entry.get()
        emp_name = name_entry.get()
        order_id = order_entry.get()
        loc = filedialog.askdirectory(title="Select Save Location")

        if emp_id and emp_name and order_id and loc:
            filename = f"{emp_id}_{order_id}.docx"
            full_path = os.path.join(loc, filename)
            template = os.path.join(os.path.dirname(__file__), "30-SportWorkflow-blank v1.docx")

            if os.path.exists(full_path):
                messagebox.showwarning("File Exists", f"The file {filename} already exists. Choose a different Order ID or location.")
                return

            try:
                shutil.copy(template, full_path)
                open_time = datetime.datetime.now()
                subprocess.Popen(['start', '', full_path], shell=True)
                messagebox.showinfo("Editing", "Please complete editing and click OK when done.")
                close_time = datetime.datetime.now()

                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO editor_logs (emp_id, emp_name, order_id, open_datetime, submit_datetime) VALUES (%s, %s, %s, %s, %s)", 
                    (emp_id, emp_name, order_id, open_time, close_time))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "File created and log saved.")
                root.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Missing Info", "Please fill all fields.")

    def go_back():
        root.destroy()
        show_login()

    root = tk.Tk()
    root.title("Editor Form")
    root.iconbitmap(resource_path("CDR_LOGO_Black.ico"))
    root.geometry(DEFAULT_WINDOW_SIZE)

    tk.Button(root, text="Back", width=20, command=go_back).pack(pady=5)

    tk.Label(root, text="Employee ID").pack()
    emp_entry = tk.Entry(root)
    emp_entry.pack()

    tk.Label(root, text="Employee Name").pack()
    name_entry = tk.Entry(root)
    name_entry.pack()

    tk.Label(root, text="Order ID").pack()
    order_entry = tk.Entry(root)
    order_entry.pack()

    tk.Button(root, text="Submit", command=submit).pack(pady=10)
    root.mainloop()

# ------------------------------------ QC Workflow Form ------------------------------------
def open_qc_form():
    def search_and_open():
        order_id = order_entry.get()
        if not order_id:
            messagebox.showwarning("Missing Info", "Enter Order ID")
            return

        qc_name = qc_name_entry.get()
        if not qc_name:
            messagebox.showwarning("Missing Info", "Enter QC Name")
            return

        qc_id = qc_id_entry.get()
        if not qc_id:
            messagebox.showwarning("Missing Info", "Enter QC ID")
            return

        file_found = False
        for root_dir, _, files in os.walk(r"\\192.168.29.89\Album 2\Editor Workflow Form"):
            for file in files:
                if file.endswith(".docx") and order_id in file:
                    full_path = os.path.join(root_dir, file)
                    file_found = True
                    break
            if file_found:
                break

        if not file_found:
            messagebox.showerror("Not Found", "File not found for given Order ID")
            return

        open_time = datetime.datetime.now()
        subprocess.Popen(['start', '', full_path], shell=True)

        def on_done():
            close_time = datetime.datetime.now()
            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO qc_logs (qc_id, qc_name, order_id, open_datetime, submit_datetime) VALUES (%s,%s, %s, %s, %s)",
                               (qc_id, qc_name, order_id, open_time, close_time))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "QC Log saved.")
                qc_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        done_btn = tk.Button(qc_window, text="Done Reviewing", command=on_done)
        done_btn.pack(pady=10)

    def go_back():
        qc_window.destroy()
        show_login()

    qc_window = tk.Tk()
    qc_window.title("QC Form")
    qc_window.iconbitmap(resource_path("CDR_LOGO_Black.ico"))
    qc_window.geometry(DEFAULT_WINDOW_SIZE)

    tk.Button(qc_window, text="Back", width=20, command=go_back).pack(pady=5)

    tk.Label(qc_window, text="QC ID").pack()
    qc_id_entry = tk.Entry(qc_window)
    qc_id_entry.pack()

    tk.Label(qc_window, text="QC NAME").pack()
    qc_name_entry = tk.Entry(qc_window)
    qc_name_entry.pack()

    tk.Label(qc_window, text="Order ID").pack()
    order_entry = tk.Entry(qc_window)
    order_entry.pack()

    tk.Button(qc_window, text="Open Document", command=search_and_open).pack(pady=10)
    qc_window.mainloop()

# ------------------------------------ Start App ------------------------------------
if __name__ == "__main__":
    show_login()
