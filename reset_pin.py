import sys
from app import app
from models import db, User

def reset_user_pin(username, new_pin):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ Nie znaleziono użytkownika: {username}")
            return
        
        user.pin = str(new_pin)
        db.session.commit()
        print(f"✅ PIN dla użytkownika '{username}' został zmieniony na: {new_pin}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Użycie: python reset_pin.py <NICK> <NOWY_PIN>")
        print("Przykład: python reset_pin.py Magda 1234")
    else:
        nick = sys.argv[1]
        pin = sys.argv[2]
        reset_user_pin(nick, pin)