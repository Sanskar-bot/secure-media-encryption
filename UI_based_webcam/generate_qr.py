# generate_qr.py
import socket
import qrcode

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

ip = get_local_ip()
url = f"http://{ip}:7000"
print(f"QR Code URL: {url}")

qr = qrcode.make(url)
qr.save("password_page_qr.png")
print(" QR saved as 'password_page_qr.png'")
