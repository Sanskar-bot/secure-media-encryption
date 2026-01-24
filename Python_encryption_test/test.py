try:
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes

    # Generate AES key and nonce
    key = get_random_bytes(32)  # 256-bit key
    nonce = get_random_bytes(12)  # Recommended nonce size for GCM

    # Create AES-GCM cipher
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

    # Test message
    plaintext = b"This is a test message."
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    print("pycryptodome is installed and working correctly.")
    print("Encrypted ciphertext (hex):", ciphertext.hex())
    print("Authentication tag (hex):", tag.hex())

except ImportError as e:
    print("pycryptodome is NOT installed.")
    print("ImportError:", e)

except Exception as e:
    print("An error occurred during the test.")
    print("Error:", e)
