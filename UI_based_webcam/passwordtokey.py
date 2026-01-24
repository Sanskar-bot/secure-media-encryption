# passwordtokey.py

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

# Constants
DEFAULT_PASSWORD = "admin123"           # Login password
SALT = b"StaticSaltForStream"           # Common salt for AES
MASTER_SECRET = "myfixedlocalmasterkey" # Used to encrypt password
PASSWORD_FILE = "streampassword.txt"    # File to store encrypted password
KEY_FILE = "aeskey.txt"                 # File to store AES key


def get_encryption_key(password: str, salt: bytes = SALT):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=16,  # AES-128
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def encrypt_password(password: str) -> str:
    """Encrypts the password using Fernet and derived 32-byte key."""
    fernet_key = base64.urlsafe_b64encode(derive_key(MASTER_SECRET, 32))  # Fernet requires 32-byte base64
    fernet = Fernet(fernet_key)
    return fernet.encrypt(password.encode()).decode()

def save_encrypted_password_and_key(password: str):
    # Derive and save 16-byte AES key
    aes_key = derive_key(password, 16)
    with open(KEY_FILE, "wb") as f:
        f.write(aes_key)

    # Encrypt and save login password
    encrypted_password = encrypt_password(password)
    with open(PASSWORD_FILE, "w") as f:
        f.write(encrypted_password)

if __name__ == "__main__":
    save_encrypted_password_and_key(DEFAULT_PASSWORD)
    print(" Encrypted password and AES key saved.")
