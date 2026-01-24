from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography import x509

# Load existing cert and key
with open("cert.pem", "rb") as f:
    cert = x509.load_pem_x509_certificate(f.read())

with open("key.pem", "rb") as f:
    key = serialization.load_pem_private_key(f.read(), password=None)

# Convert to PKCS#12 format
p12_data = pkcs12.serialize_key_and_certificates(
    name=b"flask_cert",
    key=key,
    cert=cert,
    cas=None,
    encryption_algorithm=serialization.BestAvailableEncryption(b"flask123")  # Set a password
)

# Save to .p12 file
with open("flask_cert.p12", "wb") as f:
    f.write(p12_data)

print("[Done] Created flask_cert.p12 — password: flask123")
