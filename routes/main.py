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
