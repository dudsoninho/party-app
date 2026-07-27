from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models import get_db_connection

main_bp = Blueprint('main', __name__)

@main_bp.route('/', strict_slashes=False)
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

@main_bp.route('/login', methods=['GET', 'POST'], strict_slashes=False)
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        
        if not username:
            return render_template('login.html')
            
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if not user:
            is_admin = 1 if username.lower() in ['admin', 'magda'] else 0
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password, is_admin, balance) VALUES (?, ?, ?, 100)', 
                         (username, '', is_admin))
            conn.commit()
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
        conn.close()
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['is_admin'] = user['is_admin']
        return redirect(url_for('main.index'))
            
    return render_template('login.html')

@main_bp.route('/transfer', methods=['POST'], strict_slashes=False)
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

@main_bp.route('/logout', strict_slashes=False)
def logout():
    session.clear()
    return redirect(url_for('main.login'))
