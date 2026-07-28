import random
import io
import base64
from datetime import datetime
import qrcode
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, User, ShopItem, Transaction

main_bp = Blueprint('main', __name__)

@main_bp.before_app_request
def update_last_active():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            user.last_active = datetime.utcnow()
            db.session.commit()

def generate_unique_code():
    while True:
        code = f"{random.randint(1, 99):02d}"
        if not User.query.filter_by(user_code=code).first():
            return code

@main_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('main.login'))

    shop_items = ShopItem.query.all()

    # Pobieranie historii transakcji użytkownika
    history = Transaction.query.filter(
        (Transaction.sender_id == user.id) | (Transaction.receiver_id == user.id)
    ).order_by(Transaction.timestamp.desc()).all()

    qr_data = f"{request.host_url}?to={user.user_code}"
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf)
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('index.html', user=user, shop_items=shop_items, history=history, qr_code=qr_b64)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        pin = request.form.get('pin', '').strip()

        if not username or not pin or len(pin) != 4 or not pin.isdigit():
            flash('Podaj nick i 4-cyfrowy PIN!', 'danger')
            return redirect(url_for('main.login'))

        user = User.query.filter_by(username=username).first()

        if user:
            if user.pin == pin:
                session['user_id'] = user.id
                user.last_active = datetime.utcnow()
                db.session.commit()
                return redirect(url_for('main.index'))
            else:
                flash('Niepoprawny PIN dla tego nicku!', 'danger')
                return redirect(url_for('main.login'))
        else:
            admin_list = current_app.config.get('ADMIN_USERS', ['@Ptychu99', 'M0tylisk0'])
            is_admin_flag = 1 if username.lower() in [name.lower() for name in admin_list] else 0
            
            new_code = generate_unique_code()
            new_user = User(
                username=username,
                pin=pin,
                user_code=new_code,
                balance=100,
                is_admin=is_admin_flag,
                last_active=datetime.utcnow()
            )
            db.session.add(new_user)
            db.session.commit()
            
            session['user_id'] = new_user.id
            flash(f'Utworzono nowe konto! Twój kod ID to: {new_code}. Otrzymujesz 100 MC na start!', 'success')
            return redirect(url_for('main.index'))

    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.login'))

@main_bp.route('/transfer', methods=['POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    sender = User.query.get(session['user_id'])
    receiver_input = request.form.get('receiver_id', '').strip()
    amount_str = request.form.get('amount', '0')
    title = request.form.get('title', 'Przelew P2P').strip()

    try:
        amount = int(amount_str)
    except ValueError:
        flash('Nieprawidłowa kwota!', 'danger')
        return redirect(url_for('main.index'))

    if amount <= 0:
        flash('Kwota musi być większa niż 0!', 'danger')
        return redirect(url_for('main.index'))

    if sender.balance < amount:
        flash('Brak wystarczających środków na koncie!', 'danger')
        return redirect(url_for('main.index'))

    receiver = User.query.filter(
        (User.user_code == receiver_input) | (User.username == receiver_input)
    ).first()

    if not receiver:
        flash('Odbiorca nie został znaleziony!', 'danger')
        return redirect(url_for('main.index'))

    if receiver.id == sender.id:
        flash('Nie możesz wysłać przelewu do samego siebie!', 'danger')
        return redirect(url_for('main.index'))

    sender.balance -= amount
    receiver.balance += amount

    tx = Transaction(sender_id=sender.id, receiver_id=receiver.id, amount=amount, title=title)
    db.session.add(tx)
    db.session.commit()

    flash(f'Pomyślnie wysłano {amount} MC do {receiver.username}!', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/buy/<int:item_id>', methods=['POST'])
def buy_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    item = ShopItem.query.get_or_404(item_id)

    if user.balance < item.price:
        flash('Masz za mało Motyl Coinów!', 'danger')
        return redirect(url_for('main.index'))

    user.balance -= item.price
    db.session.commit()

    flash(f'Zakupiono: {item.name} za {item.price} MC!', 'success')
    return redirect(url_for('main.index'))
