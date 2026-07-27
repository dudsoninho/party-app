from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models import get_db_connection

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if 'user_id' not in session:
        return render_template('login.html')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    users = conn.execute('SELECT id, username FROM users WHERE id != ?', (session['user_id'],)).fetchall()
    items = conn.execute('SELECT * FROM shop_items WHERE stock != 0').fetchall()
    conn.close()
    
    if not user:
        session.clear()
        return redirect(url_for('main.index'))
        
    return render_template('index.html', user=user, users=users, items=items)

@main_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    if not username:
        return redirect(url_for('main.index'))
        
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    if not user:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, balance) VALUES (?, 100)', (username,))
        conn.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user['id']
        
    conn.close()
    session['user_id'] = user_id
    session['username'] = username
    return redirect(url_for('main.index'))

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return login()  # Logika rejestracji jest w naszej apce taka sama jak logowania
    return render_template('login.html')

@main_bp.route('/transfer', methods=['POST'])
def transfer():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Niezalogowany'}), 401
        
    sender_id = session['user_id']
    receiver_id = request.json.get('receiver_id')
    amount = int(request.json.get('amount', 0))
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Nieprawidłowa kwota'})
        
    conn = get_db_connection()
    sender = conn.execute('SELECT balance FROM users WHERE id = ?', (sender_id,)).fetchone()
    
    if not sender or sender['balance'] < amount:
        conn.close()
        return jsonify({'success': False, 'message': 'Brak wystarczających środków'})
        
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, sender_id))
    cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, receiver_id))
    cursor.execute('INSERT INTO transactions (sender_id, receiver_id, amount) VALUES (?, ?, ?)', 
                   (sender_id, receiver_id, amount))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Przelew wykonany!'})
