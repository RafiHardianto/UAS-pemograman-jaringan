"""
Modul upload file menggunakan protokol TCP (socket.SOCK_STREAM).

Alur:
1. User upload file lewat form web (HTTP) -> Flask menyimpannya sementara di folder temp/
2. Flask (sebagai TCP CLIENT) mengirim file tsb lewat koneksi socket TCP
   ke TCP SERVER yang berjalan di background (thread) pada aplikasi yang sama.
3. TCP SERVER menerima dan menyimpan file ke folder uploads/.

Protokol sederhana yang dipakai:
[4 byte panjang nama file][nama file][8 byte ukuran file][isi file]
"""
import socket
import threading
import os

TCP_IP = "127.0.0.1"
TCP_PORT = 6000
UPLOAD_DIR = "uploads"


def handle_client(conn):
    try:
        name_len = int.from_bytes(conn.recv(4), "big")
        filename = conn.recv(name_len).decode()
        file_size = int.from_bytes(conn.recv(8), "big")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filepath = os.path.join(UPLOAD_DIR, filename)

        received = 0
        with open(filepath, "wb") as f:
            while received < file_size:
                chunk = conn.recv(min(4096, file_size - received))
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)

        print(f"[TCP] File diterima: {filename} ({received} bytes)")
    finally:
        conn.close()


def tcp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((TCP_IP, TCP_PORT))
    sock.listen(5)
    print(f"[TCP] Server upload berjalan di {TCP_IP}:{TCP_PORT}")
    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()


def start_tcp_server_thread():
    threading.Thread(target=tcp_server, daemon=True).start()


def send_file_via_tcp(filepath):
    """Dipanggil dari Flask untuk mengirim file ke TCP server di atas."""
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TCP_IP, TCP_PORT))

    name_bytes = filename.encode()
    sock.send(len(name_bytes).to_bytes(4, "big"))
    sock.send(name_bytes)
    sock.send(file_size.to_bytes(8, "big"))

    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            sock.send(chunk)

    sock.close()
