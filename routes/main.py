from flask import Blueprint, render_template, request, redirect, url_for, session
# Zaimportuj swoją bazę danych / funkcje db, np.:
# from database import get_db

main_bp = Blueprint('main', __name__)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            db = get_db()
            # Sprawdź, czy użytkownik już istnieje
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if not user:
                # Jeśli nie istnieje, utwórz go i daj 100 coinów na start
                db.execute('INSERT INTO users (username, coins) VALUES (?, ?)', (username, 100))
                db.commit()
                user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('main.index'))
            
    return render_template('login.html')

@main_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
        
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    return render_template('index.html', user=user)
