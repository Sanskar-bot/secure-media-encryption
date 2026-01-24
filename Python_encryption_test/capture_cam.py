import cv2
from flask import Flask, Response

app = Flask(__name__)

def generate():
    cam = cv2.VideoCapture(0)
    while True:
        ret, frame = cam.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video')
def video():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    print("[INFO] Starting Flask server at https://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))
