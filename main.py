import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import os
import shutil
import datetime
import mysql.connector
from mysql.connector import Error
import subprocess
import time
import pythoncom
import sys
import bcrypt

# ------------------------------------ DEFAULT_WINDOW_SIZE --------------------------------------------

DEFAULT_WINDOW_SIZE = "1000x550"

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
        host='192.168.29.89', #'localhost',
        user='rahulj',
        password='root@123',
        database='doc_workflow'
    )

#------------------------------------- Global Variables ------------------------------------

emp_id = None

# ------------------------------------ Show Role Selection ------------------------------------

def show_login():
    login_window = ctk.CTk()
    login_window.iconbitmap(resource_path("favicon.ico"))
    login_window.title("Login")
    login_window.geometry(DEFAULT_WINDOW_SIZE)
    login_window.configure(bg="#2ebfc1")

    ctk.CTkLabel(login_window, text="User Login").pack(pady=20)

    ctk.CTkLabel(login_window, text="Employee ID").pack()
    emp_id_entry = ctk.CTkEntry(login_window)
    emp_id_entry.pack(pady=5)

    ctk.CTkLabel(login_window, text="Password").pack()
    password_entry = ctk.CTkEntry(login_window, show="*")
    password_entry.pack(pady=5)

    def login():
        emp_id = emp_id_entry.get()
        password = password_entry.get()

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT password, role, force_password_change FROM users WHERE emp_id=%s", (emp_id,))
            result = cursor.fetchone()
            conn.close()

            if result and bcrypt.checkpw(password.encode(), result[0].encode()):
                global logged_in_emp_id
                logged_in_emp_id = emp_id
                role = result[1]

                login_window.destroy()

                if result[2]:  # force_password_change is True
                    force_password_change(emp_id, role)
                else:
                    if role == "editor":
                        open_editor_form()
                    elif role == "qc":
                        open_qc_form()
                    else:
                        messagebox.showerror("Error", f"Unknown role '{role}'")
            else:
                messagebox.showerror("Login Failed", "Invalid credentials")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    ctk.CTkButton(login_window, text="Login", width=150, command=login).pack(pady=10)

    login_window.mainloop()

# ------------------------------------ Login/Signup Page ------------------------------------

def force_password_change(emp_id, role):
        change_window = ctk.CTk()
        change_window.title("Change Password")
        change_window.iconbitmap(resource_path("favicon.ico"))
        change_window.geometry(DEFAULT_WINDOW_SIZE)
        change_window.configure(bg="#2ebfc1")

        ctk.CTkLabel(change_window, text="Change Your Password").pack(pady=10)
        ctk.CTkLabel(change_window, text="New Password").pack()
        new_pw_entry = ctk.CTkEntry(change_window, show="*")
        new_pw_entry.pack(pady=5)

        ctk.CTkLabel(change_window, text="Confirm New Password").pack()
        confirm_pw_entry = ctk.CTkEntry(change_window, show="*")
        confirm_pw_entry.pack(pady=5)

        def update_password():
            new_pw = new_pw_entry.get()
            confirm_pw = confirm_pw_entry.get()

            if not new_pw or new_pw != confirm_pw:
                messagebox.showerror("Error", "Passwords do not match or are empty.")
                return

            try:
                hashed_pw = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET password=%s, force_password_change=FALSE WHERE emp_id=%s AND role=%s",
                            (hashed_pw, emp_id, role))
                conn.commit()
                conn.close()

                messagebox.showinfo("Success", "Password changed. Please login again.")
                change_window.destroy()
                auth_page(role, is_signup=False)

            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(change_window, text="Submit", command=update_password).pack(pady=10)
        ctk.CTkButton(change_window, text="Cancel", command=lambda: (change_window.destroy(), show_login())).pack(pady=5)
        change_window.mainloop()

def auth_page(role, is_signup=False):
    def login():
        emp_id = emp_id_entry.get()
        password = password_entry.get()

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT password, force_password_change FROM users WHERE emp_id=%s AND role=%s", (emp_id, role))
            result = cursor.fetchone()

            if result and bcrypt.checkpw(password.encode(), result[0].encode()):
                global logged_in_emp_id
                logged_in_emp_id = emp_id

                if result[1]:  # force_password_change is True
                    auth_window.destroy()
                    force_password_change(emp_id, role)
                else:
                    auth_window.destroy()
                    if role == "editor":
                        open_editor_form()
                    else:
                        open_qc_form()
            else:
                messagebox.showerror("Login Failed", "Invalid credentials")
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def signup():
        emp_id = emp_id_entry.get()
        dept_name = dept_name_entry.get()
        full_name = full_name_entry.get()
        password = password_entry.get()

        if not emp_id or not password:
            messagebox.showwarning("Missing Info", "Enter employee ID and password")
            return

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE emp_id=%s", (emp_id,))
            if cursor.fetchone():
                messagebox.showerror("Signup Failed", "Employee ID already exists")
            else:
                hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                cursor.execute("INSERT INTO users (emp_id, dept_name, full_name, password, role) VALUES (%s, %s, %s, %s, %s)",
                               (emp_id, dept_name, full_name, hashed_pw, role))
                conn.commit()
                messagebox.showinfo("Signup Success", "Account created! Please log in.")
                auth_window.destroy()
                auth_page(role, is_signup=False)  # Show login form only
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def go_back():
        auth_window.destroy()
        show_login()

    auth_window = ctk.CTk()
    auth_window.title(f"{role.capitalize()} {'Sign Up' if is_signup else 'Login'}")
    auth_window.iconbitmap(resource_path("favicon.ico"))
    auth_window.geometry(DEFAULT_WINDOW_SIZE)
    auth_window.configure(bg="#2ebfc1")

    ctk.CTkLabel(auth_window, text=f"{role.capitalize()} {'Sign Up' if is_signup else 'Login'} Page").pack(anchor='w', padx=10, pady=10)

    ctk.CTkLabel(auth_window, text="Employee ID").pack()
    emp_id_entry = ctk.CTkEntry(auth_window)
    emp_id_entry.pack(pady=10)

    if is_signup:
        ctk.CTkLabel(auth_window, text="Department Name").pack()
        dept_name_entry = ctk.CTkEntry(auth_window)
        dept_name_entry.pack(pady=10)

        ctk.CTkLabel(auth_window, text="Full Name").pack()
        full_name_entry = ctk.CTkEntry(auth_window)
        full_name_entry.pack(pady=10)
    else:
        dept_name_entry = full_name_entry = None  # placeholder

    ctk.CTkLabel(auth_window, text="Password").pack()
    password_entry = ctk.CTkEntry(auth_window, show='*')
    password_entry.pack(pady=10)

    button_frame = ctk.CTkFrame(auth_window)
    button_frame.pack(pady=10)

    if is_signup:
        ctk.CTkButton(button_frame, text="Sign Up", width=150, command=signup).pack(side="left")
    else:
        ctk.CTkButton(button_frame, text="Login", width=150, command=login).pack(side="left")

    ctk.CTkButton(auth_window, text="Back", width=150, command=go_back).pack(pady=5)

    auth_window.mainloop()

# ------------------------------------ Editor Workflow Form ------------------------------------

def open_editor_form():
    def submit():
        order_id = order_entry.get()
        loc = r"\\192.168.29.89\Album 2\Editor Workflow Form"  # Auto path

        if order_id:
            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("SELECT full_name, dept_name FROM users WHERE emp_id=%s", (logged_in_emp_id,))
                result = cursor.fetchone()
                conn.close()

                if not result:
                    messagebox.showerror("Error", "User not found in database.")
                    return

                full_name, dept_name = result

                # 🔁 Select department-specific template
                if dept_name == "OCU":
                    template_filename = "Output_Control_Unit_CheckList-_Operator.docx"
                elif dept_name == "DCP":
                    template_filename = "DCP_CheckList-_Operator.docx"
                else:
                    messagebox.showerror("Error", f"No template available for department: {dept_name}")
                    return

                template = os.path.join(os.path.dirname(__file__), template_filename)
                version = 1
                base_filename = f"{order_id}_{full_name}"
                filename = f"{base_filename}_v{version}.docx"
                full_path = os.path.join(loc, filename)

                # Check for existing versions
                while os.path.exists(full_path):
                    version += 1
                    filename = f"{base_filename}_v{version}.docx"
                    full_path = os.path.join(loc, filename)

                # Copy template
                if dept_name == "OCU":
                    template_filename = "Output_Control_Unit_CheckList-_Operator.docx"
                elif dept_name == "DCP":
                    template_filename = "DCP_CheckList-_Operator.docx"
                else:
                    messagebox.showerror("Error", f"No template defined for department: {dept_name}")
                    return

                template = os.path.join(os.path.dirname(__file__), template_filename)
                shutil.copy(template, full_path)

                open_time = datetime.datetime.now()
                subprocess.Popen(['start', '', full_path], shell=True)
                messagebox.showinfo("Editing", "Click OK when done editing.")
                close_time = datetime.datetime.now()

                # Log activity
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO editor_logs (emp_id, full_name, dept_name, order_id, file_name, open_datetime, submit_datetime)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (logged_in_emp_id, full_name, dept_name, order_id, filename, open_time, close_time))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "File saved and log recorded.")
                root.destroy()
                open_editor_form()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Missing Info", "Order ID is required.")

    def show_feedback():
        try:
            conn = connect_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT q.order_id, q.qc_name, q.feedback, q.submit_datetime
                FROM qc_logs q
                JOIN editor_logs e ON q.order_id = e.order_id
                WHERE e.emp_id = %s AND q.feedback IS NOT NULL
                ORDER BY q.order_id, q.submit_datetime DESC
            """, (logged_in_emp_id,))
            rows = cursor.fetchall()
            conn.close()

            # Deduplicate by order_id, keeping only latest feedback per order
            unique_feedback = {}
            for row in rows:
                if row['order_id'] not in unique_feedback:
                    unique_feedback[row['order_id']] = row

            results = list(unique_feedback.values())

            if not results:
                messagebox.showinfo("No Feedback", "No feedback available.")
                return

            feedback_text = "\n\n".join(
                [f"Order ID: {row['order_id']}\nQC Name: {row['qc_name']}\nFeedback: {row['feedback']}" for row in results]
            )

            feedback_window = ctk.CTkToplevel(root)
            feedback_window.transient(root)
            feedback_window.grab_set()
            feedback_window.focus_force()
            feedback_window.title("Feedback")
            feedback_window.geometry("500x300")
            feedback_window.configure(bg="#2ebfc1")

            ctk.CTkLabel(feedback_window, text="Search Feedback:").pack(pady=(10, 0))
            search_entry = ctk.CTkEntry(feedback_window)
            search_entry.pack(padx=10, fill="x")

            ctk.CTkLabel(feedback_window, text="QC Feedback").pack(pady=5)
            text_box = ctk.CTkTextbox(feedback_window, wrap="word")
            text_box.pack(expand=True, fill="both", padx=10, pady=10)

            # Save all feedback in a list to search/filter
            all_feedback_texts = [
                f"Order ID: {row['order_id']}\nQC Name: {row['qc_name']}\nFeedback: {row['feedback']}" for row in results
            ]

            def update_textbox():
                keyword = search_entry.get().lower()
                filtered = [fb for fb in all_feedback_texts if keyword in fb.lower()]
                text_box.configure(state="normal")
                text_box.delete("1.0", ctk.END)
                if filtered:
                    text_box.insert("1.0", "\n\n".join(filtered))
                else:
                    text_box.insert("1.0", "No matching feedback found.")
                text_box.configure(state="disabled")

            search_entry.bind("<KeyRelease>", lambda e: update_textbox())
            # Initial population
            search_entry.insert(0, "")
            update_textbox()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def go_back():
        root.destroy()
        show_login()

    root = ctk.CTk()
    root.title("Editor Form")
    root.iconbitmap(resource_path("favicon.ico"))
    root.geometry(DEFAULT_WINDOW_SIZE)
    root.configure(bg="#2ebfc1")

    ctk.CTkLabel(root, text="Order ID").pack()
    order_entry = ctk.CTkEntry(root)
    order_entry.pack()
    ctk.CTkButton(root, text="Submit", command=submit).pack(pady=10)
    ctk.CTkButton(root, text="View Feedback", command=show_feedback).pack(pady=5)
    ctk.CTkButton(root, text="Back", command=go_back).pack(pady=5)
    ctk.CTkButton(root, text="Logout",fg_color="#ef1919", text_color="white", command=go_back).pack(pady=50)

    root.mainloop()

# ------------------------------------ QC Workflow Form ------------------------------------

def open_qc_form():
    qc_window = ctk.CTk()
    qc_window.title("QC Form")
    qc_window.iconbitmap(resource_path("favicon.ico"))
    qc_window.geometry(DEFAULT_WINDOW_SIZE)
    qc_window.configure(bg="#2ebfc1")

    def go_back():
        qc_window.destroy()
        show_login()

    def search_and_open_editor_checklist():
        order_id = order_entry.get()
        if not order_id:
            messagebox.showwarning("Missing Info", "Enter Order ID")
            return

        # Fetch QC's department
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT full_name, dept_name FROM users WHERE emp_id=%s", (logged_in_emp_id,))
            result = cursor.fetchone()
            conn.close()

            if not result:
                messagebox.showerror("Error", "User not found.")
                return

            qc_name, dept_name = result

            # Decide checklist template
            if dept_name.upper() == "OCU":
                checklist_template = os.path.join(os.path.dirname(__file__), "Output_Control_Unit_CheckList-_QC.docx")
            elif dept_name.upper() == "DCP":
                checklist_template = os.path.join(os.path.dirname(__file__), "DCP_CheckList-_QC.docx")
            else:
                messagebox.showerror("Error", f"No checklist template defined for department: {dept_name}")
                return
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        # Find matching editor files
        matching_files = []
        for root_dir, _, files in os.walk(r"\\192.168.29.89\Album 2\Editor Workflow Form"):
            for file in files:
                if file.endswith(".docx") and order_id in file:
                    matching_files.append(os.path.join(root_dir, file))

        if not matching_files:
            messagebox.showerror("Not Found", "No files found for given Order ID")
            return

        version_window = ctk.CTkToplevel(qc_window)
        version_window.transient(qc_window)
        version_window.grab_set()
        version_window.focus_force()
        version_window.title("Select File Version")
        version_window.geometry("500x300")
        version_window.configure(bg="#2ebfc1")

        ctk.CTkLabel(version_window, text="Select file version:").pack(pady=5)
        list_frame = ctk.CTkFrame(version_window)
        list_frame.pack(fill="both", expand=True, padx=10)
        scrollbar = ctk.CTkScrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10, width=60)
        for file_path in matching_files:
            file_listbox.insert(ctk.END, file_path)
        file_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=file_listbox.yview)

        def open_selected():
            selected_index = file_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("No Selection", "Please select a file version to open.")
                return

            full_path = file_listbox.get(selected_index[0])
            version_window.destroy()

            editor_open_time = datetime.datetime.now()
            os.startfile(full_path)

            # Save checklist copy in shared QC folder
            qc_folder = r"\\192.168.29.89\Album 2\QC Checklists"
            os.makedirs(qc_folder, exist_ok=True)

            version = 1
            base_name = f"{order_id}_QC_Checklist"
            checklist_filename = f"{base_name}_v{version}.docx"
            checklist_path = os.path.join(qc_folder, checklist_filename)

            while os.path.exists(checklist_path):
                version += 1
                checklist_filename = f"{base_name}_v{version}.docx"
                checklist_path = os.path.join(qc_folder, checklist_filename)

            shutil.copy(checklist_template, checklist_path)

            time.sleep(5)
            checklist_open_time = datetime.datetime.now()
            os.startfile(checklist_path)

            messagebox.showinfo("QC Review", "Click OK after you're done reviewing both documents.")
            editor_close_time = datetime.datetime.now()
            checklist_close_time = datetime.datetime.now()

            feedback_window = ctk.CTkToplevel(qc_window)
            feedback_window.title("Submit Feedback")
            feedback_window.geometry("400x300")
            feedback_window.configure(bg="#2ebfc1")

            ctk.CTkLabel(feedback_window, text="Enter Feedback:").pack(pady=5)
            text_box = ctk.CTkTextbox(feedback_window, wrap="word")
            text_box.pack(expand=True, fill="both", padx=10, pady=10)

            def submit_feedback():
                feedback = text_box.get("1.0", ctk.END).strip()

                try:
                    conn = connect_db()
                    cursor = conn.cursor()

                    # Save logs
                    cursor.execute("""
                        INSERT INTO qc_logs (emp_id, dept_name, qc_name, order_id, file_name, open_datetime, submit_datetime, feedback)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        logged_in_emp_id, dept_name, qc_name, order_id,
                        os.path.basename(full_path), editor_open_time, editor_close_time, feedback
                    ))

                    cursor.execute("""
                        INSERT INTO qc_logs (emp_id, dept_name, qc_name, order_id, file_name, open_datetime, submit_datetime, feedback)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        logged_in_emp_id, dept_name, qc_name, order_id,
                        os.path.basename(checklist_path), checklist_open_time, checklist_close_time, feedback
                    ))

                    conn.commit()
                    conn.close()

                    messagebox.showinfo("Success", "Feedback and logs saved for both documents.")
                    feedback_window.destroy()
                    qc_window.destroy()
                    open_qc_form()

                except Exception as e:
                    messagebox.showerror("Error", str(e))

            ctk.CTkButton(feedback_window, text="Submit Feedback", command=submit_feedback).pack(pady=10)

        ctk.CTkButton(version_window, text="Open Document", command=open_selected).pack(pady=10)

    # GUI Layout
    ctk.CTkLabel(qc_window, text="Order ID").pack()
    order_entry = ctk.CTkEntry(qc_window)
    order_entry.pack()
    ctk.CTkButton(qc_window, text="Search File", command=search_and_open_editor_checklist).pack(pady=10)
    ctk.CTkButton(qc_window, text="Logout", fg_color="#ef1919", command=go_back).pack(pady=10)

    qc_window.mainloop()


# ------------------------------------ Start App ------------------------------------

if __name__ == "__main__":
    show_login()
