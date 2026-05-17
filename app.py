from flask import Flask

from config import SECRET_KEY
from database import init_db
from routes import register_blueprints


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    register_blueprints(app)

    return app


app = create_app()


if __name__ == "__main__":
    init_db()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )