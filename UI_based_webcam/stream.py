import os
import time
import queue
import logging
import base64
import threading
from collections import deque

import cv2
from flask import (
    Flask, request, redirect, url_for,
    render_template, session, Response, jsonify
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from passwordtokey import get_encryption_key, DEFAULT_PASSWORD

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "super-secret-session-key"

KEY_FILE       = "aeskey.txt"
PASSWORD_FILE  = "streampassword.txt"

# ---------------------------------------------------------------------------
# In-memory log capture via a custom logging handler
# ---------------------------------------------------------------------------

LOG_BUFFER: deque = deque(maxlen=500)       # ring buffer keeps last 500 lines
LOG_SUBSCRIBERS: list = []                  # SSE subscriber queues
LOG_LOCK = threading.Lock()

class InMemoryHandler(logging.Handler):
    """Pushes formatted log records into the ring buffer and SSE queues."""

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        LOG_BUFFER.append(msg)
        with LOG_LOCK:
            dead = []
            for q in LOG_SUBSCRIBERS:
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    dead.append(q)
            for q in dead:
                LOG_SUBSCRIBERS.remove(q)


def _setup_logging() -> logging.Logger:
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S"
    )
    mem_handler = InMemoryHandler()
    mem_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)

    logger = logging.getLogger("secstream")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(mem_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


log = _setup_logging()

# ---------------------------------------------------------------------------
# Camera state
# ---------------------------------------------------------------------------

cam      = None
cam_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Key / encryption setup
# ---------------------------------------------------------------------------

def load_key() -> bytes:
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r") as f:
            saved_password = f.read().strip()
        log.info("Loaded password from %s", PASSWORD_FILE)
    else:
        saved_password = DEFAULT_PASSWORD
        with open(PASSWORD_FILE, "w") as f:
            f.write(DEFAULT_PASSWORD)
        log.warning("Password file not found — default password written to %s", PASSWORD_FILE)
    return get_encryption_key(saved_password)


key    = load_key()
aesgcm = AESGCM(key)
log.info(
    "AES-128-GCM cipher ready. Key fingerprint (first 8 bytes, hex): %s",
    key[:8].hex().upper()
)

# ---------------------------------------------------------------------------
# Camera helpers
# ---------------------------------------------------------------------------

def init_camera() -> None:
    global cam
    with cam_lock:
        if cam is None or not cam.isOpened():
            log.info("Initialising camera (DirectShow backend)…")
            cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            time.sleep(2)
            if cam.isOpened():
                log.info("Camera opened successfully.")
            else:
                log.error("Failed to open camera on index 0.")


def release_camera() -> None:
    global cam
    with cam_lock:
        if cam is not None and cam.isOpened():
            cam.release()
            cam = None
            log.info("Camera released.")


def get_encrypted_frame():
    global cam
    with cam_lock:
        if cam is None or not cam.isOpened():
            return None, None
        ret, frame = cam.read()

    if not ret:
        log.warning("Camera read failed — skipping frame.")
        return None, None

    _, buffer    = cv2.imencode(".jpg", frame)
    frame_bytes  = buffer.tobytes()
    nonce        = os.urandom(16)
    encrypted    = aesgcm.encrypt(nonce, frame_bytes, None)
    encoded      = base64.b64encode(nonce + encrypted).decode()
    return frame_bytes, encoded


# ---------------------------------------------------------------------------
# Routes — authentication
# ---------------------------------------------------------------------------

@app.route("/")
def login_page():
    if session.get("authenticated"):
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    user_input = request.form.get("password", "")
    if not os.path.exists(PASSWORD_FILE):
        log.error("Password file missing during login attempt.")
        return render_template("login.html", error="Server configuration error."), 500

    with open(PASSWORD_FILE, "r") as f:
        saved_password = f.read().strip()

    if user_input == saved_password:
        session["authenticated"] = True
        log.info("Successful login from %s", request.remote_addr)
        return redirect(url_for("dashboard"))

    log.warning("Failed login attempt from %s", request.remote_addr)
    return render_template("login.html", error="Invalid password."), 401


@app.route("/logout")
def logout():
    session.clear()
    release_camera()
    log.info("Session terminated. Camera released.")
    return redirect(url_for("login_page"))


@app.route("/reset", methods=["GET", "POST"])
def reset():
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        if len(new_password) < 6:
            return render_template("reset.html", error="Password must be at least 6 characters.")

        with open(PASSWORD_FILE, "w") as f:
            f.write(new_password)

        global key, aesgcm
        key    = get_encryption_key(new_password)
        aesgcm = AESGCM(key)
        log.info(
            "Password updated. New key fingerprint: %s",
            key[:8].hex().upper()
        )
        session.clear()
        return redirect(url_for("login_page"))

    return render_template("reset.html")


# ---------------------------------------------------------------------------
# Routes — dashboard
# ---------------------------------------------------------------------------

@app.route("/dashboard")
def dashboard():
    if not session.get("authenticated"):
        return redirect(url_for("login_page"))
    encoded_key = base64.b64encode(key).decode()
    fingerprint = key[:8].hex().upper()
    return render_template("dashboard.html", encoded_key=encoded_key, fingerprint=fingerprint)


# ---------------------------------------------------------------------------
# Routes — streams
# ---------------------------------------------------------------------------

@app.route("/video")
def video_stream():
    if not session.get("authenticated"):
        return redirect(url_for("login_page"))

    def generate():
        init_camera()
        log.info("Video stream started for %s", request.remote_addr)
        try:
            while True:
                frame, _ = get_encrypted_frame()
                if frame is not None:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                    )
                time.sleep(0.04)   # ~25 fps cap
        except GeneratorExit:
            log.info("Video stream closed by client.")

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/encrypted")
def encrypted_stream():
    if not session.get("authenticated"):
        return redirect(url_for("login_page"))

    def generate():
        init_camera()
        log.info("Encrypted stream started for %s", request.remote_addr)
        try:
            while True:
                _, encrypted = get_encrypted_frame()
                if encrypted is not None:
                    yield encrypted + "\n"
                time.sleep(0.04)
        except GeneratorExit:
            log.info("Encrypted stream closed by client.")

    return Response(generate(), mimetype="text/plain")


@app.route("/key")
def show_key():
    if not session.get("authenticated"):
        return redirect(url_for("login_page"))
    encoded_key = base64.b64encode(key).decode("utf-8")
    fingerprint = key[:8].hex().upper()
    return render_template(
        "key_display.html",
        encoded_key=encoded_key,
        fingerprint=fingerprint
    )


# ---------------------------------------------------------------------------
# Routes — status & logs
# ---------------------------------------------------------------------------

@app.route("/status")
def status():
    if not session.get("authenticated"):
        return jsonify({"error": "Unauthorized"}), 401
    with cam_lock:
        cam_open = cam is not None and cam.isOpened()
    return jsonify({
        "camera":      "online" if cam_open else "offline",
        "fingerprint": key[:8].hex().upper(),
        "algorithm":   "AES-128-GCM",
        "server_time": time.strftime("%H:%M:%S")
    })


@app.route("/logs")
def log_stream():
    """Server-Sent Events endpoint — streams live log lines."""
    if not session.get("authenticated"):
        return jsonify({"error": "Unauthorized"}), 401

    subscriber_q: queue.Queue = queue.Queue(maxsize=200)

    # Seed with buffered history
    for line in list(LOG_BUFFER):
        try:
            subscriber_q.put_nowait(line)
        except queue.Full:
            break

    with LOG_LOCK:
        LOG_SUBSCRIBERS.append(subscriber_q)

    def generate():
        try:
            while True:
                try:
                    line = subscriber_q.get(timeout=20)
                    yield f"data: {line}\n\n"
                except queue.Empty:
                    yield ": heartbeat\n\n"
        except GeneratorExit:
            with LOG_LOCK:
                if subscriber_q in LOG_SUBSCRIBERS:
                    LOG_SUBSCRIBERS.remove(subscriber_q)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cert = "server_certificate.crt"
    pkey = "key.pem"

    if not os.path.exists(cert) or not os.path.exists(pkey):
        log.error(
            "SSL certificate or key not found (%s / %s). "
            "Run setup_certs.py first or use start.bat.",
            cert, pkey
        )
        raise SystemExit(1)

    log.info("Starting Secure Media Stream server on https://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, ssl_context=(cert, pkey), threaded=True)
