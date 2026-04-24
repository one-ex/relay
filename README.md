# Telegram Relay untuk PythonAnywhere

Aplikasi Flask sederhana ini berfungsi sebagai relay untuk meneruskan permintaan dari aplikasi bot (misalnya yang di-hosting di Hugging Face) ke API Telegram. Ini berguna untuk melewati batasan firewall pada platform hosting tertentu.

## Pengaturan di PythonAnywhere

1.  **Buat Aplikasi Web Baru:**
    *   Login ke akun PythonAnywhere Anda.
    *   Buka tab "Web".
    *   Klik "Add a new web app".
    *   Pilih "Manual configuration" dan versi Python yang sesuai (misalnya, Python 3.10).

2.  **Upload Kode:**
    *   Buka tab "Files".
    *   Upload `relay_app.py` dan `requirements.txt` ke direktori proyek Anda (misalnya, `/home/yourusername/my-relay-app`).

3.  **Konfigurasi WSGI:**
    *   Kembali ke tab "Web".
    *   Klik file "WSGI configuration file" (misalnya, `/var/www/yourusername_pythonanywhere_com_wsgi.py`).
    *   Edit file tersebut agar terlihat seperti ini, sesuaikan path dengan direktori proyek Anda:

    ```python
    import sys
    import os

    # Tambahkan path proyek Anda ke sys.path
    path = '/home/yourusername/my-relay-app'
    if path not in sys.path:
        sys.path.insert(0, path)

    # Atur variabel lingkungan
    os.environ['TELEGRAM_BOT_TOKEN'] = 'YOUR_TELEGRAM_BOT_TOKEN'
    os.environ['RELAY_SECRET_KEY'] = 'YOUR_SUPER_SECRET_KEY'

    # Impor aplikasi Flask
    from relay_app import app as application
    ```

4.  **Install Dependensi:**
    *   Buka "Consoles" dan mulai "Bash" console.
    *   Navigasi ke direktori proyek Anda: `cd my-relay-app`
    *   Buat dan aktifkan virtual environment (sangat disarankan):
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   Install paket yang dibutuhkan:
        ```bash
        pip install -r requirements.txt
        ```

5.  **Atur Virtualenv untuk Aplikasi Web:**
    *   Kembali ke tab "Web".
    *   Di bagian "Virtualenv", masukkan path ke virtual environment Anda: `/home/yourusername/my-relay-app/venv`.

6.  **Reload Aplikasi:**
    *   Klik tombol "Reload" di tab "Web".
    *   Aplikasi relay Anda sekarang seharusnya sudah aktif di `yourusername.pythonanywhere.com`.

## Variabel Lingkungan

Anda **harus** mengatur variabel lingkungan berikut di file konfigurasi WSGI Anda untuk keamanan:

*   `TELEGRAM_BOT_TOKEN`: Token bot Telegram Anda.
*   `RELAY_SECRET_KEY`: Kunci rahasia yang kuat dan unik. Anda harus membuat ini sendiri (misalnya, menggunakan generator password). Kunci ini akan digunakan untuk mengautentikasi permintaan dari bot Anda di Hugging Face.