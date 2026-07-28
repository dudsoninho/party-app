from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Transaction, ShopItem
import qrcode
import base64
from io import BytesIO
import random

main_bp = Blueprint('main', __name__)

def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def generate_unique_code():
    existing = {u.user_code for u in User.query.all()}
    for _ in range(100):
        code = f"{random.randint(1, 99):02d}"
        if code not in existing:
            return code
    return '99'

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        if not username:
            flash('Podaj poprawny nick.', 'danger')
            return redirect(url_for('main.login'))
        
        user = User.query.filter_by(username=username).first()
        if not user:
            is_admin_val = 1 if username in ['admin', 'magda'] else 0
            user_code_val = generate_unique_code()
            user = User(
                username=username, 
                user_code=user_code_val, 
                balance=100, 
                is_admin=is_admin_val
            )
            db.session.add(user)
            db.session.commit()
            flash(f'Twój unikalny kod ID to: {user_code_val}. Otrzymałeś 100 Motyl Coinów na start!', 'success')
        
        session['user_id'] = user.id
        return redirect(url_for('main.index'))
    
    return render_template('login.html')

@main_bp.route('/', methods=['GET'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.login'))
    
    shop_items = ShopItem.query.all()
    qr_data = f"MOTYLCOIN_USER:{user.user_code}"
    qr_code = generate_qr(qr_data)
    
    return render_template('index.html', user=user, shop_items=shop_items, qr_code=qr_code)

@main_bp.route('/transfer', methods=['POST'])
def transfer():
    if 'user_id' not in session:
        return {'success': False, 'message': 'Brak autoryzacji.'}, 401
    
    sender = User.query.get(session['user_id'])
    data = request.get_json() if request.is_json else request.form
    
    receiver_input = str(data.get('receiver_id', '')).strip().lower()
    try:
        amount = int(data.get('amount', 0))
    except ValueError:
        return {'success': False, 'message': 'Nieprawidłowa kwota.'}, 400
    
    title = data.get('title', 'Przelew P2P').strip()
    
    if amount <= 0:
        return {'success': False, 'message': 'Kwota musi być większa od zera.'}, 400
        
    if sender.balance < amount:
        return {'success': False, 'message': 'Niewystarczająca ilość Motyl Coinów.'}, 400
        
    receiver = User.query.filter((User.user_code == receiver_input) | (User.username == receiver_input)).first()
    
    if not receiver:
        return {'success': False, 'message': 'Nie znaleziono odbiorcy o takim ID lub nicku.'}, 404
        
    if sender.id == receiver.id:
        return {'success': False, 'message': 'Nie możesz przelać środków do samego siebie.'}, 400
        
    sender.balance -= amount
    receiver.balance += amount
    
    tx = Transaction(
        sender_id=sender.id,
        receiver_id=receiver.id,
        amount=amount,
        title=title
    )
    db.session.add(tx)
    db.session.commit()
    
    if request.is_json:
        return {'success': True, 'message': f'Przelew w wysokości {amount} MC powiódł się!'}
    
    flash(f'Przelew w wysokości {amount} MC powiódł się!', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/buy_item/<int:item_id>', methods=['POST'])
def buy_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
        
    user = User.query.get(session['user_id'])
    item = ShopItem.query.get_or_404(item_id)
    
    if user.balance < item.price:
        flash('Za mało Motyl Coinów, aby kupić ten przedmiot!', 'danger')
        return redirect(url_for('main.index'))
        
    user.balance -= item.price
    tx = Transaction(
        sender_id=user.id,
        receiver_id=user.id,
        amount=item.price,
        title=f"Zakup w sklepie: {item.name}"
    )
    db.session.add(tx)
    db.session.commit()
    
    flash(f'Zakupiono pomyślnie: {item.name}!', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('main.login'))
