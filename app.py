"""
Aplikasi Web UAS Pemrograman Jaringan
Fitur: Login + verifikasi email, Upload file via TCP, Streaming video via UDP.
"""
import os
import sqlite3
import secrets
import smtplib
from functools import wraps
from email.mime.text import MIMEText

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()  # membaca file .env (jika ada) dan memuatnya sebagai environment variable

from database import init_db, get_db
from tcp_upload_server import start_tcp_server_thread, send_file_via_tcp, UPLOAD_DIR
from udp_stream_server import start_receiver_thread, start_sender_thread, get_latest_frame

app = Flask(__name__)
app.secret_key = "ganti-dengan-secret-key-anda-sendiri"

# ------------------------------------------------------------------
# KONFIGURASI EMAIL (pakai Gmail App Password, BUKAN password Gmail biasa)
# Cara membuat App Password: myaccount.google.com/apppasswords
# Lalu isi lewat environment variable, contoh (Linux/Mac):
#   export MAIL_USER="emailanda@gmail.com"
#   export MAIL_PASS="xxxx xxxx xxxx xxxx"
# ------------------------------------------------------------------
EMAIL_ADDRESS = os.environ.get("MAIL_USER", "email_anda@gmail.com")
EMAIL_PASSWORD = os.environ.get("MAIL_PASS", "app_password_anda")


def send_verification_email(to_email, token):
    link = url_for("verify_email", token=token, _external=True)
    body = f"Halo,\n\nKlik link berikut untuk memverifikasi akun Anda:\n{link}\n\nTerima kasih."
    msg = MIMEText(body)
    msg["Subject"] = "Verifikasi Akun - UAS Pemrograman Jaringan"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ------------------------------------------------------------------
# ROUTES: AUTH
# ------------------------------------------------------------------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        token = secrets.token_urlsafe(16)
        pw_hash = generate_password_hash(password)

        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO users (username, email, password_hash, verify_token) VALUES (?, ?, ?, ?)",
                    (username, email, pw_hash, token),
                )
                db.commit()
            send_verification_email(email, token)
            flash("Registrasi berhasil! Silakan cek email Anda untuk verifikasi akun.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username atau email sudah digunakan.")
        except Exception as e:
            flash(f"Registrasi tersimpan, tetapi gagal mengirim email: {e}")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/verify/<token>")
def verify_email(token):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE verify_token = ?", (token,)).fetchone()
        if user:
            db.execute("UPDATE users SET is_verified = 1 WHERE id = ?", (user["id"],))
            db.commit()
            flash("Email berhasil diverifikasi. Silakan login.")
        else:
            flash("Token verifikasi tidak valid.")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            if not user["is_verified"]:
                flash("Akun belum diverifikasi. Silakan cek email Anda.")
                return redirect(url_for("login"))
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        flash("Username atau password salah.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------------------------
# ROUTES: DASHBOARD
# ------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session["username"])


# ------------------------------------------------------------------
# ROUTES: UPLOAD FILE VIA TCP
# ------------------------------------------------------------------
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename:
            os.makedirs("temp", exist_ok=True)
            temp_path = os.path.join("temp", secure_filename(file.filename))
            file.save(temp_path)

            send_file_via_tcp(temp_path)  # <-- di sinilah pengiriman via socket TCP terjadi

            os.remove(temp_path)
            flash(f"File '{file.filename}' berhasil diupload melalui protokol TCP.")
        else:
            flash("Pilih file terlebih dahulu.")

    files = os.listdir(UPLOAD_DIR) if os.path.exists(UPLOAD_DIR) else []
    return render_template("upload.html", files=files)


# ------------------------------------------------------------------
# ROUTES: STREAMING VIDEO VIA UDP
# ------------------------------------------------------------------
@app.route("/stream")
@login_required
def stream():
    return render_template("stream.html")


@app.route("/stream/start")
@login_required
def stream_start():
    start_sender_thread("videos/sample.mp4")
    return "", 204


def generate_mjpeg():
    while True:
        frame = get_latest_frame()
        if frame:
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@app.route("/video_feed")
def video_feed():
    return Response(generate_mjpeg(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    init_db()
    start_tcp_server_thread()
    start_receiver_thread()
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True, use_reloader=False)
