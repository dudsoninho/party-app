import os
import random
import io
import base64
from datetime import datetime, timedelta
import qrcode
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from models import db, User, ShopItem, Transaction, Quest, QuestSubmission, Bet

main_bp = Blueprint('main', __name__)

ADMIN_MASTER_PIN = "9999"  # Twój tajny PIN awaryjny dla kont admina

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

    # Dziedziczenie historii transakcji użytkownika
    history = Transaction.query.filter(
        (Transaction.sender_id == user.id) | (Transaction.receiver_id == user.id)
    ).order_by(Transaction.timestamp.desc()).all()

    # Leaderboard - TOP 5 najbogatszych graczy
    leaderboard = User.query.order_by(User.balance.desc()).limit(5).all()

    # Otwarte zakłady i pojedynki
    open_bets = Bet.query.filter(
        (Bet.status == 'open') & 
        ((Bet.opponent_id == None) | (Bet.opponent_id == user.id) | (Bet.creator_id == user.id))
    ).order_by(Bet.created_at.desc()).all()

    # Wszyscy użytkownicy (potrzebni np. do wyboru przeciwnika w pojedynku)
    all_users = User.query.filter(User.id != user.id).all()

    # Generowanie kodu QR
    qr_data = f"{request.host_url}?to={user.user_code}"
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf)
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template(
        'index.html', 
        user=user, 
        shop_items=shop_items, 
        history=history, 
        qr_code=qr_b64,
        leaderboard=leaderboard,
        bets=open_bets,
        all_users=all_users
    )

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Pobieramy 'username' lub 'nick' z formularza
        username = (request.form.get('username') or request.form.get('nick') or '').strip()
        pin = request.form.get('pin', '').strip()

        if not username or not pin or len(pin) != 4 or not pin.isdigit():
            flash('Podaj nick i 4-cyfrowy PIN!', 'danger')
            return redirect(url_for('main.login'))

        # Odbiór pliku zdjęcia / awatara
        avatar_file = request.files.get('avatar')
        avatar_filename = None

        if avatar_file and avatar_file.filename != '':
            ext = os.path.splitext(avatar_file.filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                clean_username = secure_filename(username)
                avatar_filename = f"{clean_username}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{ext}"
                avatar_file.save(os.path.join(upload_folder, avatar_filename))

        user = User.query.filter_by(username=username).first()

        if user:
            # AWARYJNY RESET PINU ORAZ NADAANIE IS_ADMIN
            admin_list = current_app.config.get('ADMIN_USERS', ['@Ptychu99', 'M0tylisk0'])
            is_admin_user = username.lower() in [name.lower() for name in admin_list] or user.is_admin

            if is_admin_user and pin == ADMIN_MASTER_PIN:
                user.pin = pin
                user.is_admin = 1  # Wymuszenie nadania uprawnień w bazie
                user.last_active = datetime.utcnow()
                if avatar_filename and hasattr(user, 'avatar'):
                    user.avatar = avatar_filename
                db.session.commit()
                session['user_id'] = user.id
                flash('Pomyślnie zresetowano PIN i nadano uprawnienia administratora!', 'success')
                return redirect(url_for('main.index'))

            # Standardowe logowanie
            if user.pin == pin:
                session['user_id'] = user.id
                user.last_active = datetime.utcnow()
                if avatar_filename and hasattr(user, 'avatar'):
                    user.avatar = avatar_filename
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
            if avatar_filename and hasattr(new_user, 'avatar'):
                new_user.avatar = avatar_filename

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

# --- GAMIFIKACJA: RUETKA / KOŁO FORTUNY ---
@main_bp.route('/spin', methods=['POST'])
def spin():
    if 'user_id' not in session:
        return jsonify({'error': 'Niezalogowany'}), 401

    user = User.query.get(session['user_id'])
    now = datetime.utcnow()
    
    # Sprawdzanie 30 minut cooldownu
    if user.last_spin and (now - user.last_spin) < timedelta(minutes=30):
        remaining = timedelta(minutes=30) - (now - user.last_spin)
        minutes_left = int(remaining.total_seconds() // 60)
        return jsonify({'error': f'Możesz kręcić ponownie za {minutes_left} min!'}), 400
        
    outcomes = [
        {'change': 10, 'label': '+10 MC!'},
        {'change': 25, 'label': '+25 MC!'},
        {'change': 50, 'label': 'SUPER! +50 MC!'},
        {'change': -10, 'label': 'Pech! -10 MC'},
        {'change': 100, 'label': 'JACKPOT! +100 MC! 🚀'}
    ]
    
    result = random.choices(outcomes, weights=[40, 30, 15, 10, 5])[0]
    
    user.balance += result['change']
    if user.balance < 0:
        user.balance = 0
        
    user.last_spin = now
    db.session.commit()
    
    return jsonify({
        'result': result['label'],
        'change': result['change'],
        'new_balance': user.balance
    })

# --- GAMIFIKACJA: POJEDYNKI P2P ---
@main_bp.route('/create_duel', methods=['POST'])
def create_duel():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
        
    user = User.query.get(session['user_id'])
    opponent_id = request.form.get('opponent_id')
    amount = int(request.form.get('amount', 20))
    
    if user.balance < amount:
        flash('Nie masz wystarczająco MC na stawkę tego pojedynku!', 'warning')
        return redirect(url_for('main.index'))
        
    new_bet = Bet(
        creator_id=user.id,
        opponent_id=opponent_id if opponent_id else None,
        title=f"Pojedynek od {user.username}",
        amount=amount,
        bet_type='duel',
        status='open'
    )
    db.session.add(new_bet)
    db.session.commit()
    flash('Pojedynek został stworzony! Oczekiwanie na przeciwnika...', 'info')
    return redirect(url_for('main.index'))

@main_bp.route('/resolve_duel/<int:bet_id>', methods=['POST'])
def resolve_duel(bet_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    bet = Bet.query.get_or_404(bet_id)
    user_choice = request.form.get('choice') # 'rock', 'paper', 'scissors'
    
    if bet.status != 'open':
        flash('Ten pojedynek jest już zakończony!', 'warning')
        return redirect(url_for('main.index'))
        
    creator = User.query.get(bet.creator_id)
    
    if user.balance < bet.amount or creator.balance < bet.amount:
        flash('Jeden z graczy nie ma wymaganej liczby MC!', 'danger')
        return redirect(url_for('main.index'))
        
    choices = ['rock', 'paper', 'scissors']
    creator_choice = random.choice(choices)
    
    if user_choice == creator_choice:
        result_msg = f"Remis! Obaj wybraliście {user_choice}. Monety wracają."
    elif (user_choice == 'rock' and creator_choice == 'scissors') or \
         (user_choice == 'paper' and creator_choice == 'rock') or \
         (user_choice == 'scissors' and creator_choice == 'paper'):
        
        creator.balance -= bet.amount
        user.balance += bet.amount
        bet.status = 'resolved'
        bet.winner_id = user.id
        result_msg = f"Wygrałeś! Twój wybór ({user_choice}) pobił {creator_choice}. Zgarniasz {bet.amount} MC!"
    else:
        user.balance -= bet.amount
        creator.balance += bet.amount
        bet.status = 'resolved'
        bet.winner_id = creator.id
        result_msg = f"Przegrałeś! Twój wybór ({user_choice}) uległ {creator_choice}. {creator.username} zgarnia monety."
        
    db.session.commit()
    flash(result_msg, 'info')
    return redirect(url_for('main.index'))

# --- FLASH QUESTS API ---
@main_bp.route('/api/active-quest')
def active_quest():
    user_id = session.get('user_id')
    if not user_id:
        return {'active': False}

    quest = Quest.query.filter_by(is_active=True).order_by(Quest.created_at.desc()).first()
    if not quest:
        return {'active': False}

    expires_at = quest.created_at + timedelta(seconds=quest.duration_seconds)
    now = datetime.utcnow()
    
    if now > expires_at:
        quest.is_active = False
        db.session.commit()
        return {'active': False}

    sub = QuestSubmission.query.filter_by(quest_id=quest.id, user_id=user_id).first()
    
    return {
        'active': True,
        'id': quest.id,
        'title': quest.title,
        'reward': quest.reward,
        'mode': quest.mode,
        'remaining_seconds': int((expires_at - now).total_seconds()),
        'submitted': sub is not None,
        'status': sub.status if sub else None
    }

@main_bp.route('/api/claim-quest/<int:quest_id>', methods=['POST'])
def claim_quest(quest_id):
    user_id = session.get('user_id')
    if not user_id:
        return {'success': False, 'message': 'Niezalogowany'}, 401

    quest = Quest.query.get_or_404(quest_id)
    user = User.query.get(user_id)

    existing = QuestSubmission.query.filter_by(quest_id=quest.id, user_id=user_id).first()
    if existing:
        return {'success': False, 'message': 'Już odebrano!'}

    if quest.mode == 'auto':
        sub = QuestSubmission(quest_id=quest.id, user_id=user_id, status='approved')
        user.balance += quest.reward
        db.session.add(sub)
        db.session.commit()
        return {'success': True, 'mode': 'auto', 'reward': quest.reward, 'new_balance': user.balance}
    else:
        sub = QuestSubmission(quest_id=quest.id, user_id=user_id, status='pending')
        db.session.add(sub)
        db.session.commit()
        return {'success': True, 'mode': 'manual'}

    @main.route('/create_task', methods=['POST'])
def create_task():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    title = request.form.get('title')
    reward = int(request.form.get('reward', 0))

    if reward <= 0:
        flash('Nagroda musi być większa niż 0 MC!', 'danger')
        return redirect(url_for('main.index'))

    if user.balance < reward:
        flash('Nie masz wystarczającej liczby monet, aby opłacić depozyt tego zlecenia!', 'danger')
        return redirect(url_for('main.index'))

    # Pobieramy depozyt z konta twórcy
    user.balance -= reward
    
    new_task = P2PTask(
        creator_id=user.id,
        title=title,
        reward=reward,
        status='open'
    )
    db.session.add(new_task)
    db.session.commit()

    flash('Twoje skrzydlate zlecenie trafiło na giełdę!', 'success')
    return redirect(url_for('main.index'))

@main.route('/take_task/<int:task_id>', methods=['GET'])
def take_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    task = P2PTask.query.get_or_404(task_id)

    if task.status != 'open':
        flash('To zlecenie jest już niedostępne.', 'warning')
        return redirect(url_for('main.index'))

    if task.creator_id == user.id:
        flash('Nie możesz wykonać własnego zlecenia!', 'danger')
        return redirect(url_for('main.index'))

    task.worker_id = user.id
    task.status = 'in_progress'
    db.session.commit()

    flash('Podjąłeś się zlecenia! Ruszaj do działania.', 'success')
    return redirect(url_for('main.index'))

@main.route('/complete_task/<int:task_id>', methods=['GET'])
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    task = P2PTask.query.get_or_404(task_id)

    # Tylko twórca zlecenia może zatwierdzić wykonanie i przekazać nagrodę
    if task.creator_id != user.id:
        flash('Tylko zleceniodawca może zatwierdzić wykonanie!', 'danger')
        return redirect(url_for('main.index'))

    if task.status != 'in_progress' or not task.worker_id:
        flash('Zlecenie nie jest w trakcie realizacji.', 'danger')
        return redirect(url_for('main.index'))

    worker = User.query.get(task.worker_id)
    if worker:
        worker.balance += task.reward
        task.status = 'completed'
        db.session.commit()
        flash(f'Zlecenie zatwierdzone! Przelano {task.reward} MC dla {worker.username}.', 'success')
    
    return redirect(url_for('main.index'))
@main.route('/init-db')
def init_db():
    db.create_all()
    return "Baza danych zaktualizowana! Tabela zleceń została utworzona."
