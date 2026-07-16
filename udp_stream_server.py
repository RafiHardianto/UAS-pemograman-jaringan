"""
Modul streaming video menggunakan protokol UDP (socket.SOCK_DGRAM).

Alur:
1. udp_sender()  : membaca video (videos/sample.mp4) frame per frame dengan OpenCV,
                   mengubah tiap frame jadi JPEG, lalu mengirimnya sebagai datagram UDP.
2. udp_receiver(): berjalan terus di background (thread), menerima datagram UDP,
                   menyimpan frame terbaru ke variabel global.
3. Flask (/video_feed) membaca frame terbaru itu dan menampilkannya ke browser
   sebagai MJPEG stream (multipart/x-mixed-replace), sehingga terlihat seperti video berjalan.
"""
import socket
import threading
import time
import cv2

UDP_IP = "127.0.0.1"
UDP_PORT = 6001
BUFFER_SIZE = 65535

latest_frame = None
frame_lock = threading.Lock()


def udp_receiver():
    global latest_frame
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(1.0)
    print(f"[UDP] Receiver siap di {UDP_IP}:{UDP_PORT}")
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            with frame_lock:
                latest_frame = data
        except socket.timeout:
            continue


def start_receiver_thread():
    threading.Thread(target=udp_receiver, daemon=True).start()


def udp_sender(video_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"[UDP] Video tidak ditemukan: {video_path}")
        return

    print(f"[UDP] Mulai mengirim video: {video_path}")
    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # ulangi video dari awal (loop)
            continue

        frame = cv2.resize(frame, (480, 360))
        _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        data = buffer.tobytes()

        if len(data) < 60000:  # batas aman ukuran datagram UDP
            sock.sendto(data, (UDP_IP, UDP_PORT))

        time.sleep(1 / 20)  # kira-kira 20 frame per detik


def start_sender_thread(video_path):
    threading.Thread(target=udp_sender, args=(video_path,), daemon=True).start()


def get_latest_frame():
    with frame_lock:
        return latest_frame
