from flask import Flask
from config import Config
from models import db
from routes.main import main_bp
from routes.admin import admin_bp
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    try:
        from whitenoise import WhiteNoise
        app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(os.path.dirname(__file__), 'static'))
    except ImportError:
        pass

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
