"""
setup_certs.py
==============
Generates a self-signed TLS certificate and RSA private key for the
SecureStream Flask server.  Run this once before starting the application.

Outputs (in the same directory as this script):
  server_certificate.crt  — PEM-encoded X.509 certificate
  key.pem                 — PEM-encoded RSA-2048 private key

Usage:
  python setup_certs.py [--ip <host_ip>]

If --ip is not supplied, the script auto-detects the LAN IP address.
"""

import argparse
import socket
import os
import sys
from datetime import datetime, timedelta, timezone

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509 import IPAddress
    import ipaddress
except ImportError:
    print("[ERROR] 'cryptography' package not found.")
    print("        Install it with:  pip install cryptography")
    sys.exit(1)


def get_local_ip() -> str:
    """Return the primary LAN IP address of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def generate_certificates(host_ip: str, out_dir: str = ".") -> None:
    cert_path = os.path.join(out_dir, "server_certificate.crt")
    key_path  = os.path.join(out_dir, "key.pem")

    print(f"[*] Generating RSA-2048 private key...")
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    print(f"[*] Building self-signed certificate for IP: {host_ip}")
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME,             "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,   "Haryana"),
        x509.NameAttribute(NameOID.LOCALITY_NAME,             "Gurugram"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME,         "SecureStream"),
        x509.NameAttribute(NameOID.COMMON_NAME,               host_ip),
    ])

    now = datetime.now(timezone.utc)
    san = x509.SubjectAlternativeName([
        x509.DNSName("localhost"),
        x509.DNSName(host_ip),
        IPAddress(ipaddress.IPv4Address(host_ip)),
        IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .add_extension(san, critical=False)
        .sign(private_key, hashes.SHA256())
    )

    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"[OK] key.pem               -> {os.path.abspath(key_path)}")
    print(f"[OK] server_certificate.crt -> {os.path.abspath(cert_path)}")
    print()
    print("     Access the stream at:")
    print(f"     https://{host_ip}:5000")
    print(f"     https://localhost:5000")
    print()
    print("     NOTE: Your browser will show a security warning because the")
    print("     certificate is self-signed. This is expected for local use.")
    print("     Proceed by clicking 'Advanced' -> 'Proceed to <IP>'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate self-signed TLS certs for SecureStream.")
    parser.add_argument("--ip", default=None, help="Host IP to embed in certificate (auto-detected if omitted)")
    args = parser.parse_args()

    host_ip = args.ip or get_local_ip()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    generate_certificates(host_ip, out_dir=script_dir)
