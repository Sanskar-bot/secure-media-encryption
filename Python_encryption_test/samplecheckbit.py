import os
from Crypto.Cipher import AES
import traceback

# ====== File Paths ======
enc_path = r"A:\Minor1\Sample\finalM_check.bin"
key_path = r"A:\Minor1\Sample\key.bin"
out_path = r"A:\Minor1\Sample\decrypted_output_final.mp4"

print("Starting decryption on PC...")

try:
    print("Checking if files exist...")
    if not os.path.exists(key_path):
        print("Key file not found!")
    else:
        print("Key file found.")

    if not os.path.exists(enc_path):
        print("Encrypted file not found!")
    else:
        print("Encrypted file found.")

    print("Loading AES key...")
    with open(key_path, 'rb') as f:
        key = f.read()
    print(f"Key length: {len(key)} bytes")

    print("Reading encrypted file...")
    with open(enc_path, 'rb') as f:
        nonce = f.read(16)  # AES-GCM standard nonce size
        tag = f.read(16)
        ciphertext = f.read()

    print(f"Nonce: {nonce.hex()}")
    print(f"Tag: {tag.hex()}")
    print(f"Ciphertext size: {len(ciphertext)} bytes")
    print("Decrypting...")

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)

    with open(out_path, 'wb') as f:
        f.write(decrypted_data)

    print(f"Decryption complete. File saved to: {out_path}")

    # ===== Launch video =====
    print("Playing video...")
    os.startfile(out_path)

except Exception as e:
    print("Decryption failed!")
    traceback.print_exc()
