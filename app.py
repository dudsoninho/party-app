import os
from flask import Flask
from config import Config
from models import db
from routes.main import main_bp
from routes.admin import admin_bp
from sqlalchemy import inspect, text

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        
        # Bezpieczne dodawanie brakujących kolumn do istniejącej bazy SQLite
        inspector = inspect(db.engine)
        if 'user' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('user')]
            with db.engine.connect() as conn:
                if 'last_active' not in columns:
                    conn.execute(text('ALTER TABLE user ADD COLUMN last_active DATETIME'))
                    conn.commit()
                if 'last_spin' not in columns:
                    conn.execute(text('ALTER TABLE user ADD COLUMN last_spin DATETIME'))
                    conn.commit()
                if 'is_admin' not in columns:
                    conn.execute(text('ALTER TABLE user ADD COLUMN is_admin INTEGER DEFAULT 0'))
                    conn.commit()

    try:
        from whitenoise import WhiteNoise
        app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(os.path.dirname(__file__), 'static'))
    except ImportError:
        pass

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
