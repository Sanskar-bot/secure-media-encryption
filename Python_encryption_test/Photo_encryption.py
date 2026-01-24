from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import traceback

try:
    video_path = r"A:\Minor1\Sample\WIN_20250531_11_52_08_Pro.mp4"
    encrypted_path = r"A:\Minor1\Sample\finalM_check.bin"
    key_path = r"A:\Minor1\Sample\key.bin"

    print("Generating AES-256 key...")
    key = get_random_bytes(32)  # 256-bit AES key
    with open(key_path, 'wb') as f:
        f.write(key)
    print(f"Key saved to: {key_path}")
    print(f"Key (hex): {key.hex()}")

    print("Reading video file...")
    with open(video_path, 'rb') as f:
        data = f.read()
    print(f"Video size: {len(data)} bytes")

    print("Encrypting file using AES-GCM...")
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data)

    # Debug information before writing
    print(f"Nonce: {cipher.nonce.hex()}")
    print(f"Tag: {tag.hex()}")
    print(f"Ciphertext size: {len(ciphertext)} bytes")
    print(f"First 16 bytes of ciphertext: {ciphertext[:16].hex()}")

    # Writing encrypted file: nonce (12) + tag (16) + ciphertext
    with open(encrypted_path, 'wb') as f:
        f.write(cipher.nonce)
        f.write(tag)
        f.write(ciphertext)

    print(f"Encryption complete. Encrypted file saved to: {encrypted_path}")

except Exception as e:
    print("Exception occurred:")
    traceback.print_exc()
