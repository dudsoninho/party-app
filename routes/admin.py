from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models import get_db_connection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin', strict_slashes=False)
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('main.index'))
        
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    return render_template('admin.html', users=users)

@admin_bp.route('/admin/add_coins', methods=['POST'], strict_slashes=False)
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
