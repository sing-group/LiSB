import sys
import os
from app import app
from config import routes

if __name__ == "__main__":
    # Append core module to path and import it
    sys.path.insert(1, routes['base'])
    import core

    # Run web app
    app.secret_key = os.urandom(24)
    app.run()
