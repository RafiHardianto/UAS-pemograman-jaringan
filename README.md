# UAS Pemrograman Jaringan — Aplikasi Web (TCP Upload + UDP Streaming)

Aplikasi web sederhana yang memenuhi semua syarat tugas:
- Interface (UI) web
- Sistem login + verifikasi email
- Upload file via protokol **TCP**
- Streaming video via protokol **UDP**
- Siap deploy dengan **Cloudflare**

## 1. Struktur Proyek
```
uas-pemjar/
├── app.py                  # Aplikasi Flask utama (routing, login, dsb)
├── database.py             # Setup SQLite
├── tcp_upload_server.py    # Server + client TCP untuk upload file
├── udp_stream_server.py    # Server UDP untuk streaming video
├── requirements.txt
├── templates/              # Halaman HTML
├── static/style.css
├── videos/sample.mp4       # <-- taruh video contoh di sini (untuk demo streaming)
├── uploads/                # File hasil upload akan tersimpan di sini
└── db.sqlite3              # Dibuat otomatis saat pertama kali dijalankan
```

## 2. Instalasi
```bash
pip install -r requirements.txt
```

## 3. Konfigurasi Email (verifikasi login)
Gunakan **Gmail App Password** (bukan password Gmail biasa):
1. Aktifkan verifikasi 2 langkah di akun Google Anda.
2. Buka https://myaccount.google.com/apppasswords
3. Buat App Password baru, salin 16 digit kodenya.
4. Set environment variable sebelum menjalankan aplikasi:

Linux/Mac:
```bash
export MAIL_USER="email_anda@gmail.com"
export MAIL_PASS="xxxxxxxxxxxxxxxx"
```

Windows (PowerShell):
```powershell
$env:MAIL_USER="email_anda@gmail.com"
$env:MAIL_PASS="xxxxxxxxxxxxxxxx"
```

## 4. Siapkan video contoh untuk streaming
Taruh file video pendek (mp4, ukuran kecil) di:
```
videos/sample.mp4
```

## 5. Menjalankan Aplikasi
```bash
python app.py
```
Buka browser ke: `http://localhost:5000`

Yang terjadi di background saat `python app.py` dijalankan:
- Flask server (HTTP) jalan di port **5000**
- TCP server (upload) otomatis jalan di port **6000**
- UDP receiver (streaming) otomatis jalan di port **6001**

## 6. Alur Demo (sesuai poin presentasi)
1. **Registrasi** → isi form di `/register` → cek email → klik link verifikasi.
2. **Login** → hanya bisa login setelah email diverifikasi.
3. **Upload file (TCP)** → menu "Upload (TCP)" → pilih file → klik Upload.
   File dikirim lewat socket TCP ke port 6000, lalu tersimpan di folder `uploads/`.
4. **Streaming video (UDP)** → menu "Streaming (UDP)" → klik "Mulai Streaming".
   Video dibaca lewat OpenCV, dikirim per-frame lewat socket UDP ke port 6001,
   lalu ditampilkan sebagai video berjalan di browser.

## 7. Deploy dengan Cloudflare (DNS Cloudflare)
Cara paling sederhana adalah menggunakan **Cloudflare Tunnel** — tidak perlu sewa VPS,
cukup jalankan aplikasi di laptop/PC, lalu ekspos ke internet lewat domain Cloudflare
yang sudah disediakan kelas.

1. Install cloudflared:
   - Windows/Mac/Linux: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
2. Login ke akun Cloudflare kelas:
   ```bash
   cloudflared tunnel login
   ```
3. Buat tunnel:
   ```bash
   cloudflared tunnel create uas-pemjar
   ```
4. Arahkan domain/subdomain (DNS) ke tunnel:
   ```bash
   cloudflared tunnel route dns uas-pemjar nama-subdomain-anda.domainkelas.com
   ```
5. Jalankan tunnel ke aplikasi lokal (port 5000):
   ```bash
   cloudflared tunnel run --url http://localhost:5000 uas-pemjar
   ```
6. Aplikasi otomatis bisa diakses lewat `https://nama-subdomain-anda.domainkelas.com`

**Catatan:** jika hanya butuh demo cepat tanpa setup DNS permanen, bisa pakai Quick Tunnel:
```bash
cloudflared tunnel --url http://localhost:5000
```
Ini akan memberi URL sementara `https://xxxxx.trycloudflare.com`.

## 8. Upload ke GitHub
```bash
git init
git add .
git commit -m "UAS Pemrograman Jaringan - TCP Upload & UDP Streaming"
git branch -M main
git remote add origin https://github.com/username-anda/uas-pemjar.git
git push -u origin main
```
Pastikan file `db.sqlite3`, folder `uploads/`, `temp/`, dan video besar **tidak** ikut diupload
(tambahkan ke `.gitignore`, sudah disediakan).

## 9. Catatan Keamanan (untuk keperluan akademik)
- `app.secret_key` dan password email sebaiknya tidak di-hardcode di source code final —
  gunakan environment variable seperti dicontohkan di atas.
- Password user disimpan dalam bentuk hash (`werkzeug.security.generate_password_hash`), bukan plain text.
