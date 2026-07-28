from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Transaction, ShopItem
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        user = User.query.get(session['user_id'])
        if not user or user.is_admin != 1:
            flash('Brak uprawnień administratora.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/', methods=['GET'])
@admin_required
def admin_panel():
    users = User.query.all()
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    shop_items = ShopItem.query.all()
    return render_template('admin.html', users=users, transactions=transactions, shop_items=shop_items)

@admin_bp.route('/add_coins', methods=['POST'])
@admin_required
def add_coins():
    user_id = request.form.get('user_id')
    try:
        amount = int(request.form.get('amount', 0))
    except ValueError:
        flash('Nieprawidłowa wartość.', 'danger')
        return redirect(url_for('admin.admin_panel'))
        
    user = User.query.get(user_id)
    if user:
        user.balance += amount
        db.session.commit()
        flash(f'Zaktualizowano saldo użytkownika {user.username} o {amount} MC.', 'success')
    else:
        flash('Nie znaleziono użytkownika.', 'danger')
        
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/add_shop_item', methods=['POST'])
@admin_required
def add_shop_item():
    name = request.form.get('name')
    try:
        price = int(request.form.get('price', 0))
    except ValueError:
        flash('Nieprawidłowa cena.', 'danger')
        return redirect(url_for('admin.admin_panel'))
        
    description = request.form.get('description', '')
    icon = request.form.get('icon', '🎁')
    
    item = ShopItem(name=name, price=price, description=description, icon=icon)
    db.session.add(item)
    db.session.commit()
    flash('Dodano nowy przedmiot do sklepu!', 'success')
    return redirect(url_for('admin.admin_panel'))
