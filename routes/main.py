import io
import base64
import qrcode
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import get_db_connection

main_bp = Blueprint('main', __name__)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            db = get_db_connection()
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if not user:
                # Zmieniono 'coins' na 'balance' oraz dodano domyślne pole password, jeśli jest wymagane przez model
                db.execute('INSERT INTO users (username, password, balance) VALUES (?, ?, ?)', (username, '', 100))
                db.commit()
                user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            session['user_id'] = user['id']
            session['username'] = user['username']
            db.close()
            return redirect(url_for('main.index'))
            
    return render_template('login.html')

@main_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
        
    db = get_db_connection()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Generowanie kodu QR
    qr_img = qrcode.make(user['username'])
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    db.close()
    
    return render_template('index.html', user=user, qr_code=qr_code_base64)

@main_bp.route('/transfer', methods=['POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
        
    recipient_username = request.form.get('recipient')
    title = request.form.get('title')
    
    try:
        amount = int(request.form.get('amount', 0))
    except ValueError:
        amount = 0
        
    if amount <= 0:
        flash('Kwota przelewu musi być większa od zera.', 'danger')
        return redirect(url_for('main.index'))
        
    db = get_db_connection()
    sender = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if sender['username'] == recipient_username:
        flash('Nie możesz przelać coinów sam do siebie!', 'danger')
        db.close()
        return redirect(url_for('main.index'))
        
    recipient = db.execute('SELECT * FROM users WHERE username = ?', (recipient_username,)).fetchone()
    
    if not recipient:
        flash(f'Użytkownik "{recipient_username}" nie istnieje.', 'danger')
        db.close()
        return redirect(url_for('main.index'))
        
    if sender['balance'] < amount:
        flash('Nie masz wystarczającej liczby coinów na koncie!', 'danger')
        db.close()
        return redirect(url_for('main.index'))
        
    # Wykonanie transakcji na kolumnie balance
    db.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, sender['id']))
    db.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, recipient['id']))
    db.execute('INSERT INTO transactions (sender_id, receiver_id, amount) VALUES (?, ?, ?)', 
               (sender['id'], recipient['id'], amount))
    db.commit()
    db.close()
    
    flash(f'Pomyślnie przelano {amount} coinów do {recipient_username}! Tytuł: "{title}"', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))
