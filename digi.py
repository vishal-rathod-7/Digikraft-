from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
import mysql.connector
import os
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)
app.secret_key = "supersecretkey"

# ==== Upload folder (C drive) ====
UPLOAD_FOLDER = r"C:\Digikraft-folder\uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ==== Database connection ====
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="8265",
        database="digikraft"
    )

# ------------------------- Register -------------------------
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "INSERT INTO users (fullname, email, phone, dob, password) VALUES (%s, %s, %s, %s, %s)",
            (data['fullname'], data['email'], data['phone'], data['dob'], data['password'])
        )
        conn.commit()
        return jsonify({"message": "User registered successfully"})
    except mysql.connector.IntegrityError:
        return jsonify({"message": "Email already exists"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ------------------------- Login -------------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"message": "Invalid Email or Password"}), 401

    if user['status'] != 'active':
        return jsonify({"message": "Your account is suspended or inactive. Please contact admin."}), 403

    return jsonify({"message": "Login Successful", "user": user})

# ------------------------- Verify user -------------------------
@app.route('/verify_user', methods=['POST'])
def verify_user():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s AND dob=%s", (data['email'], data['dob']))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({"status": "success" if user else "fail"})
#-----------------------------Admin varify pass-----------------
@app.route('/Adminverify_user', methods=['POST'])
def admin_verify_user():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM admin WHERE email=%s AND dob=%s",
        (data['email'], data['dob'])
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({"status": "success" if user else "fail"})

# ------------------------- Reset password -------------------------
@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE users SET password=%s WHERE email=%s", (data['password'], data['email']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"})
# ----------------------Admin Reset password -------------------------
@app.route('/Adminreset_password', methods=['POST'])
def admin_reset_password(): 
    data = request.json
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE admin SET password=%s WHERE email=%s", 
                   (data['password'], data['email']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"})


# ------------------------- Upload document -------------------------
from datetime import datetime
import pytz
ist = pytz.timezone("Asia/Kolkata")
uploaded_at = datetime.now(ist)
uploaded_at = datetime.now(ist).isoformat()  
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files['file']
    user_email = request.form['email']

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)

    
    ist = pytz.timezone("Asia/Kolkata")
    uploaded_at = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO documents (user_email, filename, filepath, uploaded_at, size) VALUES (%s, %s, %s, %s, %s)",
        (user_email, filename, file_path, uploaded_at, file_size)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "File uploaded successfully"}

# ------------------------- Get files -------------------------
@app.route('/get_files', methods=['POST'])
def get_files():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, filename, filepath, uploaded_at FROM documents WHERE user_email=%s ORDER BY uploaded_at DESC", (data['email'],))
    files = cursor.fetchall()
    cursor.close()
    conn.close()

    for f in files:
        f["url"] = f"/download_file/{f['filename']}"

    return jsonify({"files": files})

# --- dowvn load and viwe- Admin----------
@app.route('/download_file/<path:filename>')
def serve_upload(filename):
    if filename.startswith('uploads/'):
        filename = filename.replace('uploads/', '', 1)
    safe_name = secure_filename(filename)
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    if not os.path.exists(full_path):
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_name)


# ------------------------- Download by ID -------------------------
@app.route('/download/<int:file_id>')
def download_by_id(file_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT filename FROM documents WHERE id=%s", (file_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        abort(404)

    return send_from_directory(app.config['UPLOAD_FOLDER'], secure_filename(row["filename"]), as_attachment=True)

# ------------------------- Delete file -------------------------
@app.route('/delete_file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT filename FROM documents WHERE id=%s", (file_id,))
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        return jsonify({"message": "File not found"}), 404

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], row['filename'])

    try:
        if os.path.exists(file_path):
            os.remove(file_path)

        cursor.execute("DELETE FROM documents WHERE id=%s", (file_id,))
        conn.commit()
        return jsonify({"message": "File deleted successfully"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# -------------------------
# Admin Login
# -------------------------
@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admin WHERE email=%s AND password=%s", (email, password))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()

    if admin:
        return jsonify({"message": "Admin Login Successful", "admin": admin})
    else:
        return jsonify({"message": "Invalid Admin Email or Password"}), 401
#--------------------------------------------------------------------------------------
#------------user list show
#--------------------------------------------------------------------------------------
@app.route('/get_all_users')
def get_all_users():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, fullname, email, status FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"users": users})

#--------------------------------------------------------------------------------------
#------------Document list show
#--------------------------------------------------------------------------------------
@app.route('/admin/get_all_documents')
def get_all_documents():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"files": files})
#--------------------------------------------------------------------------------------
#------------index page documets/user count 
@app.route('/count_users')
def count_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return jsonify({"total_users": total})
#---------------------------------------
@app.route('/count_documents')
def count_documents():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return jsonify({"total_docs": total})

#--------------------------------------------------------------------------------------
# ----------------- Admin: Get users -----------------
@app.route('/admin/get_users')
def admin_get_users():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, fullname, email, phone, status, dob, created_at FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"users": users})

# ----------------- Admin: Get documents -----------------
@app.route('/admin/get_documents')
def admin_get_documents():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, user_email, filename, filepath, uploaded_at FROM documents ORDER BY uploaded_at DESC")
    docs = cursor.fetchall()
    cursor.close()
    conn.close()
    for d in docs:
        d["url"] = f"/download_file/{d['filepath']}"
    return jsonify({"documents": docs})


# ----------------- Admin: Dashboard stats -----------------
@app.route('/admin/dashboard_stats')
def admin_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE status='active'")
    active_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM documents WHERE DATE(uploaded_at) = CURDATE()")
    today_docs = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    # storage_used can be added by summing file sizes if you store that in DB
    return jsonify({
        "total_users": total_users,
        "total_docs": total_docs,
        "active_users": active_users,
        "today_docs": today_docs,
        "storage_used": "—"
    })

# ----------------- Admin: Update user status -----------------
@app.route('/admin/update_user_status', methods=['POST'])
def admin_update_user_status():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status=%s WHERE id=%s", (data['status'], data['id']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Status updated"})

# ----------------- Admin: Delete user (and optionally their docs) -----------------
@app.route('/admin/delete_user', methods=['POST'])
def admin_delete_user():
    data = request.json
    user_id = data.get('id')
    if not user_id:
        return jsonify({"message":"Missing id"}), 400
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # find user's email
    cursor.execute("SELECT email FROM users WHERE id=%s", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close(); conn.close()
        return jsonify({"message":"User not found"}), 404
    email = row['email']
    # delete files from disk
    cursor.execute("SELECT filepath FROM documents WHERE user_email=%s", (email,))
    files = cursor.fetchall()
    for f in files:
        try:
            path = os.path.join(app.config['UPLOAD_FOLDER'], f['filepath'])
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            pass
    # delete documents rows
    cursor.execute("DELETE FROM documents WHERE user_email=%s", (email,))
    # delete user
    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message":"User and their documents deleted"})

# ----------------- Admin: Delete one document -----------------
@app.route('/admin/delete_document', methods=['POST'])
def admin_delete_document():
    data = request.json
    file_id = data.get('id')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT filepath FROM documents WHERE id=%s", (file_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close(); conn.close()
        return jsonify({"message":"File not found"}), 404
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], row['filepath'])
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass
    cursor.execute("DELETE FROM documents WHERE id=%s", (file_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message":"File deleted"})
#----------------docs info users----------
@app.route("/stats/user_files", methods=["POST"])
def user_files():
    data = request.json
    email = data.get("email")
    if not email:
        return jsonify({"error": "No email provided"}), 400
    
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM files WHERE email=%s", (email,))
    total = cursor.fetchone()[0]
    return jsonify({"user_files": total})
# ------------------------- Get Last Upload -------------------------
@app.route("/last_upload")
def last_upload():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT uploaded_at FROM documents ORDER BY uploaded_at DESC LIMIT 1")
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        
        original = row['uploaded_at']

        
        only_date = original.strftime("%m/%d/%Y")

        return jsonify({"last_upload": only_date})

    return jsonify({"last_upload": "–"})
# ------------------------- contact Massage -------------------------
@app.route("/send-message", methods=["POST"])
def send_message():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    subject = data.get("subject")
    message = data.get("message")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO contact_messages (name, email, subject, message)
        VALUES (%s, %s, %s, %s)
    """, (name, email, subject, message))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Message sent successfully!"})
@app.route("/get-messages", methods=["GET"])
def get_messages():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM contact_messages ORDER BY id DESC")
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(data)

# ------------------------- Run -------------------------
if __name__ == "__main__":
    app.run(debug=True)
