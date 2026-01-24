from Crypto.Cipher import AES

try:
    encrypted_path = r"A:\Minor1\Sample\finalM_check.bin"
    key_path = r"A:\Minor1\Sample\key.bin"
    decrypted_path = r"A:\Minor1\Sample\decrypted_output_final.mp4"

    print("Loading AES key...")
    with open(key_path, 'rb') as f:
        key = f.read()

    print("Reading encrypted file...")
    with open(encrypted_path, 'rb') as f:
        nonce = f.read(16)
        tag = f.read(16)
        ciphertext = f.read()

    print("Decrypting data...")
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    data = cipher.decrypt_and_verify(ciphertext, tag)

    with open(decrypted_path, 'wb') as f:
        f.write(data)
    print(f"Decryption complete. File saved to: {decrypted_path}")

except Exception as e:
    import traceback
    traceback.print_exc()
