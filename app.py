import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from whitenoise import WhiteNoise

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-party-app')
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

# Przykładowa baza w pamięci (zastąp własną logiką, jeśli masz)
users = {}

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Obsługa formularza oraz zapytania JSON z JavaScriptu
        username = None
        if request.is_json:
            data = request.get_json() or {}
            username = data.get('username')
        else:
            username = request.form.get('username')

        if username:
            session['username'] = username
            if request.is_json:
                return jsonify({"success": True})
            return redirect(url_for('index'))
        
        if request.is_json:
            return jsonify({"success": False, "message": "Podaj nazwę użytkownika"}), 400
        flash('Podaj nazwę użytkownika', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json() or {}
    receiver_id = data.get('receiver_id')
    amount = data.get('amount')
    return jsonify({"success": True, "message": f"Przelano {amount} coins!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
