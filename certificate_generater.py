from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta

# Replace with your actual IP (Common Name)
common_name = "192.168.1.8"

# Generate RSA private key
key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Write the private key to a file
with open("key.pem", "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,  # PKCS#1
        encryption_algorithm=serialization.NoEncryption()
    ))

# Certificate subject and issuer (self-signed)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Haryana"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Gurugram"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "μcr"),
    x509.NameAttribute(NameOID.COMMON_NAME, common_name),
])

# Build the certificate
cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.utcnow()
).not_valid_after(
    datetime.utcnow() + timedelta(days=365)
).add_extension(
    x509.SubjectAlternativeName([x509.DNSName(common_name)]),
    critical=False,
).sign(key, hashes.SHA256())

# Write the certificate to a file
with open("cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("[done] cert.pem and key.pem generated successfully.")
