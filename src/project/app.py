from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Секретный ключ необходим для безопасной работы сессий
app.secret_key = 'super_secret_key_for_sessions' 

# Вынесем подключение к БД в отдельную функцию для удобства
def get_db_connection():
    return mysql.connector.connect(
        host="185.114.247.43",
        port=3306,
        database="sch688_vvedenie",
        user="sch688_vvedenie",
        password="Qwerty123"
    )
'''
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        database="project_db",
        user="root",
        password="",
        connection_timeout=5
    )
'''

@app.route('/user_register', methods=['POST'])
def user_register():
    req = request.get_json()
    name = req['name']
    email = req['email']
    password = req['password']
    hashed_password = generate_password_hash(password)
    
    try:
        cnx = get_db_connection()
        cur = cnx.cursor()
        cur.execute('INSERT INTO `users`(`username`, `email`, `password_hash`, `balance`) VALUES (%s, %s, %s, %s)', (name, email, hashed_password, 100))
        cnx.commit()
        user_id = cur.lastrowid
        cnx.close()

        session['user_id'] = user_id
        session['username'] = name
        session['email'] = email
        session['balance'] = 100
        
        return jsonify({"result": True})
    except Exception as e:
        print("Ошибка регистрации:", e)
        return jsonify({"result": False})


@app.route('/user_login', methods=['POST'])
def user_login():
    req = request.get_json()
    uname = req['uname']
    password = req['p_hash']
    
    try:
        cnx = get_db_connection()
        cur = cnx.cursor(dictionary=True)
        cur.execute('SELECT * FROM users WHERE username=%s OR email=%s', (uname, uname))
        user = cur.fetchone()
        cnx.close()
        
        # проверяем, существует ли пользователь и совпадает ли хеш пароля
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['balance'] = user.get('balance', 0)
            return jsonify({"result": True})
        else:
            return jsonify({"result": False})
    except Exception as e:
        print("Ошибка входа:", e)
        return jsonify({"result": False})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/")
def registration():
    # есть авторизация => личный кабинет
    if 'user_id' in session:
        return redirect(url_for('to_lk'))
    return render_template('registration.html')

@app.route("/login")
def login():
    if 'user_id' in session:
        return redirect(url_for('to_lk'))
    return render_template('login.html')

@app.route("/lk")
def to_lk():
    # проврека авторизации
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    udt = {
        'username': session.get('username'),
        'email': session.get('email'),
        'balance': session.get('balance'),
    }
    return render_template('lk.html', user=udt)

@app.route("/history")
def history():
    if 'user_id' in session:
        
        return render_template('lk.html', user=user['user'])
    else:
        return render_template('login.html')
REQUEST_COST = 50      # стоимость запроса
PENALTY = 5000         # штраф за тупость

@app.route("/make_request", methods=['POST'])
def make_request():
    if 'user_id' not in session:
        return jsonify({"result": False, "error": "Не авторизован"})

    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    current_balance = session.get('balance', 0)

    # нет денег => надо пополнить
    if current_balance < REQUEST_COST:
        return jsonify({"result": False, "error": "денег закинь"})

    if text == '':
        penalty = True
        new_balance = max(0, current_balance - PENALTY)
    else:
        penalty = False
        new_balance = current_balance - REQUEST_COST

    try:
        cnx = get_db_connection()
        cur = cnx.cursor()
        cur.execute('UPDATE users SET balance=%s WHERE id=%s', (new_balance, session['user_id']))
        cnx.commit()
        cnx.close()

        session['balance'] = new_balance
        return jsonify({"result": True, "new_balance": new_balance, "penalty": penalty})
    except Exception as e:
        print("Ошибка запроса:", e)
        return jsonify({"result": False, "error": "Ошибка базы данных"})

@app.route("/topup", methods=['POST'])
def topup():
    if 'user_id' not in session:
        return jsonify({"result": False, "error": "Не авторизован"})

    new_balance = session.get('balance', 0) + 1000
    try:
        cnx = get_db_connection()
        cur = cnx.cursor()
        cur.execute('UPDATE users SET balance=%s WHERE id=%s', (new_balance, session['user_id']))
        cnx.commit()
        cnx.close()

        session['balance'] = new_balance
        return jsonify({"result": True, "new_balance": new_balance})
    except Exception as e:
        print("Ошибка пополнения:", e)
        return jsonify({"result": False, "error": "Ошибка базы данных"})
if __name__ == '__main__':
    app.run(debug=True)