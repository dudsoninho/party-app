import io
import base64
import qrcode
from flask import Blueprint, render_template, request, redirect, url_for, session

main_bp = Blueprint('main', __name__)

# ... (funkcja login pozostaje bez zmian)

@main_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
        
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Generowanie kodu QR na podstawie nazwy użytkownika (lub ID)
    qr_img = qrcode.make(user['username'])
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return render_template('index.html', user=user, qr_code=qr_code_base64)

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

main_bp = Blueprint('main', __name__)

# ... (funkcje login i index pozostają bez zmian)

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
        
    db = get_db()
    sender = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if sender['username'] == recipient_username:
        flash('Nie możesz przelać coinów sam do siebie!', 'danger')
        return redirect(url_for('main.index'))
        
    recipient = db.execute('SELECT * FROM users WHERE username = ?', (recipient_username,)).fetchone()
    
    if not recipient:
        flash(f'Użytkownik "{recipient_username}" nie istnieje.', 'danger')
        return redirect(url_for('main.index'))
        
    if sender['coins'] < amount:
        flash('Nie masz wystarczającej liczby coinów na koncie!', 'danger')
        return redirect(url_for('main.index'))
        
    # Wykonanie transakcji (odejmowanie i dodawanie coinów)
    db.execute('UPDATE users SET coins = coins - ? WHERE id = ?', (amount, sender['id']))
    db.execute('UPDATE users SET coins = coins + ? WHERE id = ?', (amount, recipient['id']))
    db.commit()
    
    flash(f'Pomyślnie przelano {amount} coinów do {recipient_username}! Tytuł: "{title}"', 'success')
    return redirect(url_for('main.index'))
