from flask import Flask
from config import Config
from routes.main import main_bp
from routes.admin import admin_bp
from models import init_db

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config.from_object(Config)

# Tworzenie tabel bazy danych jeśli nie istnieją
init_db()

# Rejestracja Blueprintów
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(debug=True)
