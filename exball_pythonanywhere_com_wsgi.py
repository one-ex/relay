# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.
#
# The below has been auto-generated for your Flask project

import sys
import os

# Tambahkan path proyek Anda ke sys.path
path = '/home/exball/relay-app'
if path not in sys.path:
    sys.path.insert(0, path)

# Atur variabel lingkungan
os.environ['TELEGRAM_BOT_TOKEN'] = '8772175831:AAGrHg6FIOpIw-9TpUskcjOkvyhgJH5TSGs'
os.environ['RELAY_SECRET_KEY'] = '12e485bf6055db595c510786444c50348e220592bc41c4ce5298bf0875f58915'

# Impor aplikasi Flask
from relay_app import app as application