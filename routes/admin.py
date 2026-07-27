from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models import get_db_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def check_admin():
    if not session.get('is_admin'):
        return redirect(url_for('main.index'))

@admin_bp.route('/')
def admin_panel():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    items = conn.execute('SELECT * FROM shop_items').fetchall()
    conn.close()
    return render_template('admin.html', users=users, items=items)

@admin_bp.route('/adjust_balance', methods=['POST'])
def adjust_balance():
    data = request.json
    user_id = data.get('user_id')
    amount = int(data.get('amount', 0))
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@admin_bp.route('/kick_user', methods=['POST'])
def kick_user():
    data = request.json
    user_id = data.get('user_id')
    
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})