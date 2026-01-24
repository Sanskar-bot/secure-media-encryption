import os, time, cv2, base64
from flask import Flask, request, redirect, url_for, render_template, session, Response
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from passwordtokey import get_encryption_key, DEFAULT_PASSWORD

app = Flask(__name__)
app.secret_key = "super-secret-session-key"
KEY_FILE = "aeskey.txt"
PASSWORD_FILE = "streampassword.txt"
cam = None

# Load key using password from file

def load_key():
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r") as f:
            saved_password = f.read().strip()
    else:
        saved_password = DEFAULT_PASSWORD
        with open(PASSWORD_FILE, "w") as f:
            f.write(DEFAULT_PASSWORD)
    return get_encryption_key(saved_password)

key = load_key()
aesgcm = AESGCM(key)


def init_camera():
    global cam
    if cam is None or not cam.isOpened():
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        time.sleep(2)


def get_encrypted_frame():
    global cam
    ret, frame = cam.read()
    if not ret:
        return None, None
    _, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()
    nonce = os.urandom(16)
    encrypted = aesgcm.encrypt(nonce, frame_bytes, None)
    encoded = base64.b64encode(nonce + encrypted).decode()
    return frame_bytes, encoded


@app.route('/')
def login_page():
    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login():
    user_input = request.form.get("password")
    with open(PASSWORD_FILE, "r") as f:
        saved_password = f.read().strip()
    if user_input == saved_password:
        session['authenticated'] = True
        return redirect(url_for("dashboard"))
    return "Invalid Password", 401


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == "POST":
        new_password = request.form.get("new_password")
        with open(PASSWORD_FILE, "w") as f:
            f.write(new_password)
        global key, aesgcm
        key = get_encryption_key(new_password)
        aesgcm = AESGCM(key)
        return redirect('/')
    return render_template("reset.html")


@app.route('/dashboard')
def dashboard():
    if not session.get("authenticated"):
        return redirect('/')
    encoded_key = base64.b64encode(key).decode()
    return render_template("dashboard.html", encoded_key=encoded_key)


@app.route('/video')
def video_stream():
    def generate():
        init_camera()
        while True:
            frame, _ = get_encrypted_frame()
            if frame:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
            time.sleep(0.05)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/encrypted')
def encrypted_stream():
    def generate():
        init_camera()
        while True:
            _, encrypted = get_encrypted_frame()
            if encrypted:
                yield encrypted + "\n"
            time.sleep(0.05)
    return Response(generate(), mimetype='text/plain')

@app.route('/key')
def show_key():
    encoded_key = base64.b64encode(key).decode('utf-8')
    return f"AES-GCM 128-bit Key (Base64): {encoded_key}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, ssl_context=('server_certificate.crt', 'key.pem'))
