from flask import Flask
from whitenoise import WhiteNoise
from config import Config
from models import init_db

# Import blueprintów z folderu routes
from routes.main import main_bp
from routes.admin import admin_bp

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config.from_object(Config)

# Obsługa statycznych plików na Renderze
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

# Inicjalizacja lub aktualizacja bazy danych
init_db()

# Rejestracja ścieżek
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(debug=True)
