from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from whitenoise import WhiteNoise
import sqlite3
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')
app.secret_key = 'motylcoin-super-bezpieczny-klucz-sesji'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tworzenie tabel, jeśli nie istnieją
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
    
    # Bezpieczna migracja kolumny hasła w razie potrzeby
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'password' not in columns:
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN password TEXT NOT NULL DEFAULT ""')
        except sqlite3.OperationalError:
            pass
            
    conn.commit()
    conn.close()

init_db()

@app.route('/', strict_slashes=False)
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    users = conn.execute('SELECT id, username FROM users WHERE id != ?', (session['user_id'],)).fetchall()
    conn.close()
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
        
    return render_template('index.html', user=user, users=users)

@app.route('/login', methods=['GET', 'POST'], strict_slashes=False)
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('index'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'], strict_slashes=False)
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Uzupełnij wszystkie pola!')
            return render_template('register.html')

        is_admin = 1 if username.lower() in ['admin', 'magda'] else 0
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, is_admin, balance) VALUES (?, ?, ?, 100)', 
                         (username, password, is_admin))
            conn.commit()
            conn.close()
            flash('Konto utworzone! Możesz się zalogować.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Użytkownik o takiej nazwie już istnieje!')
            
    return render_template('register.html')

@app.route('/transfer', methods=['POST'], strict_slashes=False)
def transfer():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Niezalogowany'}), 401
        
    sender_id = session['user_id']
    receiver_id = request.form.get('receiver_id')
    
    try:
        amount = int(request.form.get('amount', 0))
    except ValueError:
        return jsonify({'success': False, 'message': 'Niepoprawna kwota'}), 400

    if amount <= 0:
        return jsonify({'success': False, 'message': 'Kwota musi być większa od 0'}), 400
        
    conn = get_db_connection()
    sender = conn.execute('SELECT balance FROM users WHERE id = ?', (sender_id,)).fetchone()
    
    if not sender or sender['balance'] < amount:
        conn.close()
        return jsonify({'success': False, 'message': 'Brak wystarczających środków'}), 400
        
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, sender_id))
    cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, receiver_id))
    cursor.execute('INSERT INTO transactions (sender_id, receiver_id, amount) VALUES (?, ?, ?)', 
                   (sender_id, receiver_id, amount))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Przelew wysłany!'})

@app.route('/logout', strict_slashes=False)
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin', strict_slashes=False)
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    return render_template('admin.html', users=users)

@app.route('/admin/add_coins', methods=['POST'], strict_slashes=False)
def admin_add_coins():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Brak uprawnień'}), 403

    user_id = request.form.get('user_id')
    try:
        amount = int(request.form.get('amount', 0))
    except ValueError:
        return jsonify({'success': False, 'message': 'Niepoprawna kwota'}), 400

    conn = get_db_connection()
    conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
