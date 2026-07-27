from flask import Flask
from config import Config
from models import init_db
from routes.main import main_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.config.from_object(Config)

# Inicjalizacja bazy SQLite
init_db()

# Rejestracja modułów
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
