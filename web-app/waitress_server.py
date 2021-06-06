#!/etc/spamfilter/venv/bin/python3.8

from waitress import serve
from app import app

serve(app)
