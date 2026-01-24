import requests
import base64
import cv2
import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Replace with your actual key from the /key route
base64_key = "QvWzV6OiFShlL/KFQtLWxQ=="
key = base64.b64decode(base64_key)
aesgcm = AESGCM(key)

# Replace with your server's IP if needed
URL = "http://127.0.0.1:5000/encrypted"

def decrypt_and_show():
    print("[INFO] Connecting to encrypted stream...")
    with requests.get(URL, stream=True) as response:
        if response.status_code != 200:
            print("[ERROR] Could not connect to stream.")
            return

        for line in response.iter_lines():
            if not line:
                continue

            try:
                payload = base64.b64decode(line.strip())
                nonce = payload[:16]
                ciphertext = payload[16:]
                decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)

                # Decode JPEG bytes to an OpenCV image
                np_arr = np.frombuffer(decrypted_data, dtype=np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                frame = cv2.flip(frame, 1)  # 1 means horizontal flip (mirror)

                if frame is not None:
                    cv2.imshow("Decrypted Live Stream", frame)

                # Exit if user presses 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception as e:
                print(f"[ERROR] Decryption or decoding failed: {e}")

    cv2.destroyAllWindows()
    print("[INFO] Stream ended or window closed.")

if __name__ == "__main__":
    decrypt_and_show()
