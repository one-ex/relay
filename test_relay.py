#!/usr/bin/env python3
import requests
import os

# Simulasikan request dari bot
relay_url = "https://exball.pythonanywhere.com"
token = "8772175831:AAGrHg6FIOpIw-9TpUskcjOkvyhgJH5TSGs"
secret_key = "12e485bf6055db595c510786444c50348e220592bc41c4ce5298bf0875f58915"

# Test endpoint getMe
url = f"{relay_url}/bot{token}/getMe"
headers = {
    "X-Relay-Secret": secret_key
}

print(f"Testing relay at: {url}")
print(f"Headers: {headers}")

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ Relay berfungsi dengan baik!")
    else:
        print(f"\n❌ Relay mengembalikan error: {response.status_code}")
except Exception as e:
    print(f"\n❌ Error saat menguji relay: {e}")