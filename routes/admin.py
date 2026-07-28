from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, ShopItem, Transaction, Quest, QuestSubmission

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def check_admin():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get(session['user_id'])
    if not user or user.is_admin != 1:
        flash('Brak uprawnień administratora!', 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/')
def admin_panel():
    users = User.query.all()
    items = ShopItem.query.all()
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    
    # Użytkownik uznawany za aktywnego, jeśli wykonał akcję w ciągu ostatnich 5 minut
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    online_users = [u for u in users if getattr(u, 'last_active', None) and u.last_active >= five_minutes_ago]

    # Pobieramy zgłoszenia wyzwań oczekujące na akceptację Admina (dla Trybu Weryfikacji)
    pending_submissions = QuestSubmission.query.filter_by(status='pending').order_by(QuestSubmission.created_at.asc()).all()

    return render_template(
        'admin.html',
        users=users,
        items=items,
        transactions=transactions,
        online_users=online_users,
        pending_submissions=pending_submissions
    )

@admin_bp.route('/add_item', methods=['POST'])
@admin_bp.route('/add-item', methods=['POST'])
def add_shop_item():
    name = request.form.get('name')
    price = request.form.get('price', 0)
    description = request.form.get('description', '')
    icon = request.form.get('icon', '🍹')

    if name and price:
        item = ShopItem(name=name, price=float(price), description=description, icon=icon)
        db.session.add(item)
        db.session.commit()
        flash('Dodano nowy przedmiot do sklepu!', 'success')
    else:
        flash('Wypełnij wszystkie wymagane pola.', 'warning')

    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin == 1:
        flash('Nie można usunąć administratora!', 'danger')
        return redirect(url_for('admin.admin_panel'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'Usunięto użytkownika {user.username}.', 'success')
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/set_balance/<int:user_id>', methods=['POST'])
@admin_bp.route('/set-balance/<int:user_id>', methods=['POST'])
def set_balance(user_id):
    user = User.query.get_or_404(user_id)
    new_balance = request.form.get('balance')
    if new_balance is not None:
        user.balance = float(new_balance)
        db.session.commit()
        flash(f'Zmieniono saldo użytkownika {user.username} na {user.balance} MC.', 'success')
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/reset_all', methods=['POST'])
def reset_all():
    try:
        new_balance = int(request.form.get('amount', 100))
        if new_balance < 0:
            flash("Kwota nie może być ujemna!", "warning")
            return redirect(url_for('admin.admin_panel'))
            
        User.query.update({User.balance: new_balance})
        db.session.commit()
        
        flash(f"Zresetowano salda wszystkich graczy do {new_balance} MotylCoinów!", "success")
    except ValueError:
        flash("Wprowadzono niepoprawną kwotę.", "danger")
        
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/revert_tx/<int:tx_id>', methods=['POST'])
def revert_transaction(tx_id):
    tx = Transaction.query.get_or_404(tx_id)

    if tx.is_reverted:
        flash("Ta transakcja została już wcześniej cofnięta!", "warning")
        return redirect(url_for('admin.admin_panel'))

    tx.sender.balance += tx.amount
    tx.receiver.balance -= tx.amount
    tx.is_reverted = True

    db.session.commit()
    flash(f"Cofnięto transakcję #{tx.id} ({tx.amount} MC od {tx.sender.username} do {tx.receiver.username}).", "success")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/create_quest', methods=['POST'])
def create_quest():
    title = request.form.get('title')
    reward = int(request.form.get('reward', 50))
    duration = int(request.form.get('duration', 60))
    mode = request.form.get('mode', 'auto')

    if title:
        # Dezaktywujemy poprzednie aktywne wyzwania
        Quest.query.filter_by(is_active=True).update({Quest.is_active: False})
        
        new_quest = Quest(title=title, reward=reward, duration_seconds=duration, mode=mode)
        db.session.add(new_quest)
        db.session.commit()
        flash('🚀 Odpalono nowe Wyzwanie Flash!', 'success')
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/review_submission/<int:sub_id>/<string:action>', methods=['POST'])
def review_submission(sub_id, action):
    sub = QuestSubmission.query.get_or_404(sub_id)
    if sub.status == 'pending':
        if action == 'approve':
            sub.status = 'approved'
            sub.user.balance += sub.quest.reward
            flash(f'Zatwierdzono +{sub.quest.reward} MC dla {sub.user.username}!', 'success')
        elif action == 'reject':
            sub.status = 'rejected'
            flash(f'Odrzucono zgłoszenie gracza {sub.user.username}.', 'info')
        db.session.commit()
    return redirect(url_for('admin.admin_panel'))
