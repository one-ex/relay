
import os
import requests
from flask import Flask, request, jsonify
import logging
from logging.handlers import RotatingFileHandler
import time
import random

app = Flask(__name__)

# --- Konfigurasi Logging ---
# Simpan log di file 'relay_debug.log' di direktori yang sama dengan aplikasi
log_file = 'relay_debug.log'
# Atur logger untuk menangkap semua level dari DEBUG ke atas
handler = RotatingFileHandler(log_file, maxBytes=100000, backupCount=5)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

# Ambil token bot dan secret key dari environment variables untuk keamanan
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RELAY_SECRET_KEY = os.environ.get("RELAY_SECRET_KEY")

def make_request_with_retry(method_func, *args, **kwargs):
    """
    Fungsi untuk melakukan HTTP request dengan retry logic dan exponential backoff.
    Menangani ProxyError dan koneksi timeout dari PythonAnywhere.
    """
    max_retries = 3
    base_delay = 1.0  # Base delay in seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            app.logger.info(f"Attempting request (attempt {attempt}/{max_retries})")
            response = method_func(*args, **kwargs)
            response.raise_for_status()
            
            app.logger.info(f"Request successful on attempt {attempt}")
            return response
            
        except (requests.exceptions.ProxyError, 
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException) as e:
            
            if attempt == max_retries:
                app.logger.error(f"Request failed after {max_retries} attempts: {str(e)}")
                raise e
            
            # Calculate exponential backoff with jitter
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            app.logger.warning(f"Request failed (attempt {attempt}/{max_retries}): {str(e)}. Retrying in {delay:.1f}s...")
            time.sleep(delay)
    
    return None

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint sederhana untuk memeriksa apakah aplikasi relay berjalan."""
    app.logger.info("Health check endpoint was hit.")
    return "Relay is alive!", 200

@app.route('/bot<path:token>/<path:method>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def forward_to_telegram(token, method):
    """
    Meneruskan permintaan dari bot ke API Telegram, termasuk query string.
    URL dibuat semirip mungkin dengan API aslinya untuk kompatibilitas.
    """
    app.logger.debug("--- REQUEST START ---")
    app.logger.debug(f"Incoming Request: {request.method} {request.full_path}")
    app.logger.debug(f"Incoming Headers: {request.headers}")
    app.logger.debug(f"Extracted token: {token}")
    app.logger.debug(f"Extracted method: {method}")
    
    # Baca body mentah untuk logging
    raw_body = request.get_data(as_text=True)
    app.logger.debug(f"Incoming Raw Body: {raw_body}")

    # 1. Verifikasi Keamanan
    # Pastikan permintaan datang dari bot kita di Hugging Face.
    if request.headers.get('X-Relay-Secret') != RELAY_SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    # 2. Verifikasi Token (opsional, tapi lapisan keamanan tambahan yang bagus)
    # Decode token yang mungkin di-encode
    import urllib.parse
    decoded_token = urllib.parse.unquote_plus(token)
    app.logger.debug(f"Decoded token: {decoded_token}")
    if decoded_token != TELEGRAM_BOT_TOKEN:
        return jsonify({"error": "Invalid bot token"}), 403

    # 3. Ambil data dari permintaan yang dikirim oleh bot Hugging Face
    # Gunakan force=True untuk mencoba parsing JSON bahkan jika header tidak tepat,
    # dan tangani kasus di mana body mungkin kosong.
    try:
        data = request.get_json(force=True)
        if data is None:
            data = {}
    except Exception as e:
        app.logger.warning(f"Could not parse JSON, falling back to empty dict. Error: {e}")
        data = {}
    app.logger.debug(f"Parsed JSON Body: {data}")

    # 4. Bangun ulang URL lengkap, termasuk query string
    query_string = request.query_string.decode('utf-8')
    # Gunakan decoded token untuk URL Telegram
    telegram_api_url = f"https://api.telegram.org/bot{decoded_token}/{method}"
    if query_string:
        telegram_api_url += f"?{query_string}"
    
    app.logger.debug(f"URL to Telegram: {telegram_api_url}")

    try:
        # Gunakan method HTTP yang sama yang diterima dengan retry logic
        if request.method == 'GET':
            res = make_request_with_retry(requests.get, telegram_api_url, params=data if data else None, timeout=30, stream=True)
        elif request.method == 'POST':
            res = make_request_with_retry(requests.post, telegram_api_url, json=data, timeout=30, stream=True)
        elif request.method == 'PUT':
            res = make_request_with_retry(requests.put, telegram_api_url, json=data, timeout=30, stream=True)
        elif request.method == 'DELETE':
            res = make_request_with_retry(requests.delete, telegram_api_url, json=data, timeout=30, stream=True)
        else:
            res = make_request_with_retry(requests.request, request.method, telegram_api_url, json=data, timeout=30, stream=True)
        
        # res sudah di-raise_for_status() di dalam make_request_with_retry

        # Baca konten respons untuk logging dan untuk dikirim kembali
        response_content = res.content
        
        # Buat header balasan yang bersih untuk menghindari masalah proxy/decoding.
        # Jangan teruskan semua header dari Telegram, karena bisa menyebabkan
        # несоответствие (mismatch) seperti Content-Encoding.
        clean_headers = {
            'Content-Type': res.headers.get('Content-Type', 'application/json'),
            'Content-Length': str(len(response_content))
        }
        
        app.logger.debug(f"Telegram Response Status: {res.status_code}")
        app.logger.debug(f"Telegram Response Body: {response_content.decode('utf-8')}")
        app.logger.debug(f"Cleaned Headers to Bot: {clean_headers}")
        app.logger.debug("--- REQUEST END ---")

        # Kirim respons kembali ke bot Hugging Face dengan header yang bersih
        return app.response_class(
            response_content, 
            headers=clean_headers, 
            status=res.status_code
        )

    except (requests.exceptions.ProxyError, 
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException) as e:
        # Tangani error koneksi atau timeout setelah semua retry attempts
        error_message = f"Failed to relay request to Telegram after retries: {str(e)}"
        app.logger.error(error_message)
        app.logger.debug("--- REQUEST END (ERROR) ---")
        return jsonify({"error": error_message}), 502 # 502 Bad Gateway

if __name__ == '__main__':
    # Ini hanya untuk testing lokal, di PythonAnywhere akan dijalankan oleh WSGI server
    app.run(debug=True)