import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from whitenoise import WhiteNoise
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-party-app')
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            coins INTEGER DEFAULT 100,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if not user:
                cursor.execute('INSERT INTO users (username, coins, is_admin) VALUES (?, 100, 0)', (username,))
                conn.commit()
            conn.close()
            
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO users (username, coins, is_admin) VALUES (?, 100, 0)', (username,))
                conn.commit()
            except sqlite3.IntegrityError:
                pass
            conn.close()
            
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json() or {}
    receiver_id = data.get('receiver_id')
    amount = data.get('amount')
    return jsonify({"success": True, "message": f"Przelano {amount} coins!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
