# Secure Media Encryption System (AES-256-GCM)

## Overview

This project is a **security-engineering focused implementation** of an end-to-end encrypted media handling system. It is designed to explore **real-world cryptographic primitives, authenticated encryption, secure key handling, and integrity verification** using industry-standard techniques.

The system encrypts and decrypts **binary media data (images and videos)** using **AES-256-GCM**, the same authenticated encryption mode used in modern protocols such as **TLS 1.3, QUIC, Signal, and secure cloud storage platforms**.

Unlike basic cryptography demos, this project operates at the **byte level on real media files**, addressing challenges such as nonce management, authentication tags, binary correctness, and tamper detection.

---

## Security Objectives

- **Confidentiality**: Media content remains unreadable without the encryption key
- **Integrity**: Any modification to encrypted data is detected
- **Authenticated Encryption**: Encryption and authentication are cryptographically bound
- **Key Isolation**: Key material is kept separate from encrypted outputs
- **Transport Awareness**: TLS and certificate handling explored for secure delivery

---

## Cryptographic Design

### Algorithm
- **AES-256-GCM (AEAD)**
  - 256-bit symmetric key
  - 96-bit nonce generated per encryption
  - 128-bit authentication tag

### Why AES-GCM?
- Industry-standard authenticated encryption
- Prevents ciphertext tampering and forgery
- Resistant to padding oracle attacks
- Used in TLS, VPNs, secure messaging, and disk encryption

---

## High-Level Architecture

[ Media File ]
↓
[ AES-256-GCM Encryption ]
↓
[ Ciphertext + Nonce + Auth Tag ]
↓
[ Secure Storage / Transport ]
↓
[ AES-256-GCM Decryption ]
↓
[ Original Media Restored ]

yaml
Copy code

Each encryption operation produces:
- Ciphertext
- Nonce
- Authentication tag

All three components are **mandatory** for successful decryption.

---

## Project Structure

secure-media-encryption/
│
├── Python_encryption_test/
│ ├── Photo_encryption.py # Image encryption using AES-GCM
│ ├── Photo_decryption.py # Image decryption & integrity verification
│ ├── semi_final.py # Unified reference implementation
│ ├── video_encrypt.py # Video encryption experiment
│ └── video_decrypt.py # Video decryption experiment
│
├── certificate_experiments/
│ ├── certificate_generator.py # TLS certificate generation
│ └── (certificates excluded from repo)
│
├── README.md
└── .gitignore

yaml
Copy code

> **Security Note:** Cryptographic keys, certificates, encrypted binaries, and media files are intentionally excluded from version control.

---

## File Responsibilities (Detailed)

### `Photo_encryption.py`
- Generates a cryptographically secure **256-bit AES key**
- Generates a unique nonce per encryption
- Encrypts image files in binary mode
- Outputs encrypted binary data with authentication tag

### `Photo_decryption.py`
- Loads encrypted binary input
- Verifies authentication tag integrity
- Rejects modified or corrupted ciphertext
- Restores original image on successful verification

### `semi_final.py`
- Consolidated encryption/decryption workflow
- Demonstrates full lifecycle: encrypt → decrypt → validate
- Serves as the **primary reference implementation**

### Video Encryption Scripts
- Apply AES-GCM to large binary video files
- Validate encryption scalability and correctness
- Demonstrate integrity protection on streaming-sized data

---

## How to Run (Local)

### Requirements
- Python 3.9+
- PyCryptodome

Install dependency:
```bash
pip install pycryptodome
Encrypt an Image
bash
Copy code
python Photo_encryption.py
Decrypt an Image
bash
Copy code
python Photo_decryption.py
File paths for media inputs can be configured inside the scripts.

Key Management (Current Scope)
Encryption keys are generated dynamically per execution

Keys are stored locally only for proof-of-concept validation

No key material is committed to the repository

Planned / Explored Enhancements
Password-based key derivation (PBKDF2 / scrypt)

Secure key storage (hardware-backed or vault-based)

QR-based secure device onboarding

Encrypted key exchange over TLS

Threat Model
Attacker Capabilities
Read access to encrypted files

Ability to modify ciphertext

Network traffic observation

Security Guarantees
Plaintext cannot be recovered without the key

Ciphertext tampering is detected during decryption

Authentication tags prevent forgery

Nonce reuse is explicitly avoided per encryption run

What This Project Is Not
❌ Not a blockchain-based system

❌ Not a cloud storage product

❌ Not UI or frontend focused

This project prioritizes cryptographic correctness and security engineering fundamentals.

Practical Applications
Secure camera and CCTV systems

Encrypted medical image storage

Privacy-preserving video pipelines

End-to-end encrypted media delivery

IoT camera provisioning systems

Entrepreneurial Perspective
This project represents the core cryptographic engine behind secure media platforms. It focuses on building correct, tamper-resistant foundations, which are critical before scaling into production systems or products.

Disclaimer
This project is intended for educational, research, and prototyping purposes only.
It is not production-hardened and does not include operational controls such as access control layers, secure key vaults, or hardened deployment pipelines.

Author
Sanskar
Cybersecurity | Cryptography | Secure Systems Engineering

- 📄 Compress this into **resume bullets**

Just say what you want next.
