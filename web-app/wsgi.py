import os
from app import app

if __name__ == "__main__":

    # Run web app
    app.secret_key = os.urandom(24)
    app.run()
