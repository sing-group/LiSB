import sys
import os
from app import app, cors
from config import routes

if __name__ == "__main__":


    cors.init_app()

    # Run web app
    app.secret_key = os.urandom(24)
    app.run()
