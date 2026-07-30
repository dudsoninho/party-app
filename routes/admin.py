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

    # Pobieramy zgłoszenia wyzwań oczekujące na akceptację Admina
    pending_submissions = QuestSubmission.query.filter_by(status='pending').order_by(QuestSubmission.created_at.asc()).all()

    return render_template(
        'admin.html',
        users=users,
        items=items,
        transactions=transactions,
        online_users=online_users,
        pending_submissions=pending_submissions
    )

@admin_bp.route('/seed_shop', methods=['POST'])
def seed_shop():
    items = [
        # Interakcje z Magdą & Śpiew
        {"name": "Nektarowy Duet z Królową Magdą 🎤", "price": 50, "description": "Wspólne odśpiewanie wybranego kawałka na środku parkietu przy DJ-u + toast z Jubilatką!", "icon": "🎤"},
        {"name": "Szybka Metamorfoza: Karykatura 60s 🎨", "price": 35, "description": "Magda ma dokładnie 60 sekund na narysowanie Twojego portretu w motylej oprawie na Brystolu.", "icon": "🎨"},
        {"name": "Królewski Taniec Skrzydeł 💃", "price": 45, "description": "Rezerwacja 1 pełnego tańca z Magdą przy jej ulubionym kawałku.", "icon": "💃"},
        {"name": "Gorące Krzesło Królowej Motyli 🔥", "price": 40, "description": "Zadajesz Magdzie przez mikrofon 1 dowolne pytanie, na które MUSI odpowiedzieć bez ściemniania.", "icon": "🔥"},
        {"name": "Kropelka Nektaru: Toast Urodzinowy 🥂", "price": 30, "description": "Wypicie specjalnego motylego szota z Magdą przy barze z bojowym okrzykiem roju.", "icon": "🥂"},
        {"name": "Fotka w Łuskach Skrzydeł (Instax) 📸", "price": 80, "description": "Pamiątkowe zdjęcie Instax z Magdą w ozdobnej motylej ramce.", "icon": "📸"},

        # Siatkówka Plażowa
        {"name": "Wiatr w Skrzydła: Gwizdek Veto 🏐", "price": 40, "description": "Jednorazowe powtórzenie dowolnego punktu w meczu siatkówki.", "icon": "🏐"},
        {"name": "Migracja Roju: Zmiana Pola 🌬️", "price": 30, "description": "Zmuszasz drużynę przeciwną do natychmiastowej zmiany stron boiska w siatkówce.", "icon": "🌬️"},
        {"name": "Bojowy Pyłek Motyli (Doping DJ-a) 📣", "price": 25, "description": "DJ puszcza z głośników Twój utwór motywacyjny podczas Twojego serwu.", "icon": "📣"},

        # Grill & Nektarium
        {"name": "Pierwszy Nektar z Rusztu 🥩", "price": 35, "description": "Dostęp do pierwszej, najgorętszej porcji prosto z grilla poza kolejnością gąsienic.", "icon": "🥩"},
        {"name": "Pracowity Trzmiel: Dostawca Drinków 🍹", "price": 50, "description": "Wyznaczona osoba z roju przynosi Ci 2 kolejne drinki bezpośrednio do leżaka.", "icon": "🍹"},
        {"name": "Przelot nad Gąsienicami (Bez Kolejki) 🦋", "price": 50, "description": "Ominięcie całej kolejki do baru lub grilla z powołaniem się na status Motylej Arystokracji.", "icon": "🦋"},

        # Kahoot & Strefa Chillout
        {"name": "Podwójny Pyłek Mądrości (Kahoot Bonus) 🧠", "price": 60, "description": "Jeśli zajmiesz miejsce w TOP 5 w Kahoocie, Twoja wygrana w Motyl Coinach podwaja się!", "icon": "🧠"},
        {"name": "Kokon VIP na Brystolu 🖌️", "price": 25, "description": "Rezerwacja centralnego miejsca z motylą ramką VIP na pamiątkowym plakacie.", "icon": "🖌️"},
        {"name": "Kokon Spokoju: Rezerwacja VIP Leżaka 🛋️", "price": 60, "description": "Tabliczka 'ZAREZERWOWANE DLA KRÓLEWSKIEGO MOTYLA' na wybrany leżak na całą noc.", "icon": "🛋️"},

        # DJ, Parkiet & Przywileje
        {"name": "Solowy Lot Motyla na Parkiecie 🪩", "price": 30, "description": "DJ zatrzymuje na chwilę tłum, tworzy okręg i ogłasza Twój solowy popis taneczny!", "icon": "🪩"},
        {"name": "Wielka Gąsienica Imprezowa (Pociąg) 🚂", "price": 35, "description": "Puszczenie kultowego utworu i poprowadzenie pociągu gąsienic przez teren resortu.", "icon": "🚂"},
        {"name": "Metamorfoza Stylu DJ-a (5 Minut) 🎶", "price": 60, "description": "Narzucenie DJ-owi natychmiastowej zmiany gatunku muzyki na 5 minut.", "icon": "🎶"},
        {"name": "Trzepot Skrzydeł DJ-a (Wybór Piosenki) 🎵", "price": 30, "description": "Prawo do zamówienia 1 utworu u DJ-a poza kolejnością.", "icon": "🎵"},
        {"name": "Władca Motylej Konsoli (DJ 10 min) 🎧", "price": 120, "description": "Przejęcie konsoli i puszczenie własnej playlisty z telefonu przez 10 minut.", "icon": "🎧"},
        {"name": "Wylinka ze Sprzątania 🧹", "price": 150, "description": "Bilet zwalniający ze sprzątania i nocnych porządków na koniec imprezy.", "icon": "🧹"},

        # Licytacja 23:00
        {"name": "Tajemniczy Kokon Metamorfozy (Mystery Box) 📦", "price": 80, "description": "[LICYTACJA 23:00] Zapudłowany gadżet niespodzianka (przekąski, gadżety, niespodzianki).", "icon": "📦"},
        {"name": "Eliksir Odrodzenia Motyla (Kac-Kiler) 💊", "price": 100, "description": "[LICYTACJA 23:00] Izotonik, zupka chińska, aspiryna, woda na ciężki poranek.", "icon": "💊"},
        {"name": "Złota Gąsienica Sezonu (Statuetka) 🏆", "price": 200, "description": "[LICYTACJA 23:00] Główny dyplom i statuetka Przyjaciela Sezonu Piaseczno Beach Resort.", "icon": "🏆"},
        {"name": "Złoty Żeton Skrzydlatego Życzenia 🎫", "price": 250, "description": "[LICYTACJA 23:00] Prawo do wymyślenia 1 zadania dla Organizatora w przyszłości!", "icon": "🎫"}
    ]

    added_count = 0
    for item_data in items:
        existing = ShopItem.query.filter_by(name=item_data["name"]).first()
        if not existing:
            new_item = ShopItem(
                name=item_data["name"],
                price=item_data["price"],
                description=item_data["description"],
                icon=item_data.get("icon", "🍹")
            )
            db.session.add(new_item)
            added_count += 1
            
    db.session.commit()
    flash(f"Dodano {added_count} nowych motylich przedmiotów do sklepu!", "success")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/add_item', methods=['POST'])
@admin_bp.route('/add-item', methods=['POST'])
def add_shop_item():
    name = request.form.get('name')
    price = request.form.get('price', 0)
    description = request.form.get('description', '')
    icon = request.form.get('icon', '🍹')

    if name and price:
        try:
            item = ShopItem(name=name, price=int(price), description=description, icon=icon)
            db.session.add(item)
            db.session.commit()
            flash('Dodano nowy przedmiot do sklepu!', 'success')
        except ValueError:
            flash('Cena musi być liczbą całkowitą!', 'danger')
    else:
        flash('Wypełnij wszystkie wymagane pola.', 'warning')

    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/delete_shop_item/<int:item_id>', methods=['POST'])
def delete_shop_item(item_id):
    item = ShopItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash(f"Usunięto przedmiot: {item.name}", "info")
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
        try:
            user.balance = int(new_balance)
            db.session.commit()
            flash(f'Zmieniono saldo użytkownika {user.username} na {user.balance} MC.', 'success')
        except ValueError:
            flash('Saldo musi być liczbą całkowitą!', 'danger')
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

@admin_bp.route('/quick_reward', methods=['POST'])
def quick_reward():
    user_id = request.form.get('user_id', type=int)
    amount = request.form.get('amount', type=int)
    title = request.form.get('title', 'Nagroda Agendowa')

    user = User.query.get_or_404(user_id)
    if amount is not None:
        user.balance += amount
        tx = Transaction(sender_id=session['user_id'], receiver_id=user.id, amount=amount, title=title)
        db.session.add(tx)
        db.session.commit()
        flash(f'Przyznano +{amount} MC użytkownikowi {user.username} za: "{title}"!', 'success')
    else:
        flash('Niepoprawna kwota nagrody.', 'danger')
        
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/reset_pin/<int:user_id>', methods=['POST'])
def reset_user_pin_admin(user_id):
    user = User.query.get_or_404(user_id)
    new_pin = request.form.get('new_pin', '').strip()
    
    if len(new_pin) == 4 and new_pin.isdigit():
        user.pin = new_pin
        db.session.commit()
        flash(f'Zmieniono PIN użytkownika {user.username} na {new_pin}.', 'success')
    else:
        flash('PIN musi składać się dokładnie z 4 cyfr!', 'danger')
        
    return redirect(url_for('admin.admin_panel'))
