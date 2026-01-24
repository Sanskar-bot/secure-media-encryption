import cv2
import base64
import os
import time
from flask import Flask, Response, stream_with_context
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

app = Flask(__name__)
cam = None

# AES-GCM key setup (128-bit)
key = AESGCM.generate_key(bit_length=128)
aesgcm = AESGCM(key)

def init_camera():
    global cam
    if cam is None or not cam.isOpened():
        print("[INFO] Initializing webcam...")
        # Use CAP_DSHOW backend on Windows for better support
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        time.sleep(2)  # Give camera time to warm up
        if not cam.isOpened():
            raise RuntimeError("[ERROR] Could not open webcam.")
        print("[INFO] Webcam initialized.")

def get_encrypted_frame():
    global cam
    if cam is None or not cam.isOpened():
        print("[WARN] Camera not ready.")
        return None, None

    ret, frame = cam.read()
    if not ret:
        print("[WARN] Failed to grab frame.")
        return None, None

    success, buffer = cv2.imencode('.jpg', frame)
    if not success:
        print("[WARN] Failed to encode frame.")
        return None, None

    frame_bytes = buffer.tobytes()
    nonce = os.urandom(16)  # 16-byte nonce (must match client expectations)

    try:
        encrypted_data = aesgcm.encrypt(nonce, frame_bytes, None)
        payload = nonce + encrypted_data
        encoded_payload = base64.b64encode(payload).decode('utf-8')
        return frame_bytes, encoded_payload
    except Exception as e:
        print(f"[ERROR] Encryption failed: {e}")
        return None, None

@app.route('/')
def index():
    return '''
    <h2>Welcome to Encrypted Webcam Stream</h2>
    <ul>
        <li><a href="/video">Live Stream</a></li>
        <li><a href="/encrypted">Encrypted Stream</a></li>
        <li><a href="/key">Encryption Key</a></li>
    </ul>
    '''

@app.route('/video')
def video_stream():
    def generate():
        init_camera()
        while True:
            frame, _ = get_encrypted_frame()
            if frame:
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
                )
            time.sleep(0.05)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/encrypted')
def encrypted_stream():
    def generate():
        init_camera()
        while True:
            _, encoded_frame = get_encrypted_frame()
            if encoded_frame:
                yield encoded_frame + "\n"
            time.sleep(0.05)
    return Response(stream_with_context(generate()), mimetype='text/plain')

@app.route('/key')
def show_key():
    encoded_key = base64.b64encode(key).decode('utf-8')
    return f"AES-GCM 128-bit Key (Base64): {encoded_key}"

# NOTE: Removed teardown_appcontext to prevent camera from being released after each request

if __name__ == '__main__':
    try:
        print("[INFO] Starting HTTP Flask server at http://0.0.0.0:5000")
        init_camera()
        app.run(
         host='0.0.0.0',
         port=5000,
         debug=False,
          ssl_context=('server_certificate.crt', 'key.pem')  # ✅ Enable HTTPS
         )
    finally:
        if cam and cam.isOpened():
            cam.release()
            print("[INFO] Webcam released on exit.")
