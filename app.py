from flask import Flask, render_template, request, redirect, url_for, flash, session, Blueprint
import sqlite3
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'super-tajny-klucz-zmien-go-na-produkcji'

main_bp = Blueprint('main', __name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            balance INTEGER DEFAULT 100
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            amount INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@main_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    users = conn.execute('SELECT id, username FROM users WHERE id != ?', (session['user_id'],)).fetchall()
    conn.close()
    
    if not user:
        session.clear()
        return redirect(url_for('main.login'))
        
    return render_template('index.html', user=user, users=users)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('main.index'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło')
            
    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, balance) VALUES (?, ?, ?)', (username, password, 100))
            conn.commit()
            conn.close()
            flash('Konto utworzone! Możesz się zalogować.')
            return redirect(url_for('main.login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Użytkownik o takiej nazwie już istnieje!')
            
    return render_template('register.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main_bp.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('main.index'))
        
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    return render_template('admin.html', users=users)

app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)
