from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector
from llama_cpp import Llama
from werkzeug.security import generate_password_hash, check_password_hash

REPO_ID = "bartowski/Qwen2.5-0.5B-Instruct-GGUF"
FILENAME = "Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_sessions'

print(f"Загрузка модели {FILENAME} из {REPO_ID}...")
llm = Llama.from_pretrained(
    repo_id=REPO_ID,
    filename=FILENAME,
    n_ctx=2048,
    verbose=False
)
print("Модель успешно загружена.")

'''
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

        cur.execute('INSERT INTO `transactions`(`user_id`, `type`, `cost`, `description`) VALUES (%s, %s, %s, %s)',
                   (user_id, 'пополнение', 100, 'Приветственный бонус'))
        cnx.commit()
        cnx.close()

        session['user_id'] = user_id
        session['username'] = name
        session['email'] = email
        session['balance'] = 100

        return jsonify({"result": True})
    except Exception as e:
        print("Ошибка регистрации:", e)
        return jsonify({"result": False})


@app.route('/api/chat', methods=['POST'])
def api_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'не авторизован'}), 401

    current_balance = session.get('balance', 0)
    if current_balance < 3:
        return jsonify({'error': 'Недостаточно средств на балансе', 'new_balance': current_balance}), 400

    req = request.get_json(silent=True) or {}
    message = (req.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'пустое сообщение'}), 400

    try:
        cnx = get_db_connection()
        cur = cnx.cursor()

        new_balance = current_balance - 3
        cur.execute('UPDATE users SET balance=%s WHERE id=%s', (new_balance, session['user_id']))
        cur.execute('INSERT INTO `transactions`(`user_id`, `type`, `cost`, `description`) VALUES (%s, %s, %s, %s)',
                   (session['user_id'], 'списание', 3, 'Сообщение в чат с ИИ'))
        cnx.commit()
        cnx.close()

        session['balance'] = new_balance
    except Exception as e:
        print("Ошибка списания баланса:", e)
        return jsonify({'error': 'Ошибка базы данных'}), 500

    messages = [
        {
            "role": "system",
            "content": "Ты полезный ассистент. Отвечай кратко и по-русски."
        }
    ]

    for item in req.get('history', [])[-6:]:
        if item.get('role') in ('user', 'assistant'):
            messages.append({
                "role": item['role'],
                "content": item.get('content', '')
            })

    messages.append({
        "role": "user",
        "content": message
    })

    output = llm.create_chat_completion(
        messages=messages,
        max_tokens=150,
        temperature=0.7
    )

    reply = output['choices'][0]['message']['content'].strip()
    return jsonify({'reply': reply, 'new_balance': new_balance})


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

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user.get('email', '')
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
    if 'user_id' in session:
        return redirect(url_for('to_lk'))
    return render_template('registration_2.html')

@app.route("/login")
def login():
    if 'user_id' in session:
        return redirect(url_for('to_lk'))
    return render_template('login_2.html')

@app.route("/lk")
def to_lk():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    udt = {
        'username': session.get('username'),
        'email': session.get('email', ''),
        'balance': session.get('balance'),
    }
    return render_template('lk_2.html', user=udt)

@app.route("/history")
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        cnx = get_db_connection()
        cur = cnx.cursor(dictionary=True)
        cur.execute('SELECT type, cost, description, created_at FROM transactions WHERE user_id=%s ORDER BY created_at DESC LIMIT 50',
                   (session['user_id'],))
        transactions = cur.fetchall()

        cur.execute('SELECT SUM(cost) as total_spent FROM transactions WHERE user_id=%s AND type=%s',
                   (session['user_id'], 'списание'))
        result = cur.fetchone()
        total_spent = abs(result['total_spent']) if result['total_spent'] else 0
        cnx.close()

        for tx in transactions:
            tx['amount'] = tx['cost'] if tx['type'] == 'пополнение' else -abs(tx['cost'])

        dt = {
            'balance': session.get('balance'),
            'sum_sp': total_spent,
            'transactions': transactions
        }
        return render_template('history_2.html', user=dt)
    except Exception as e:
        print("Ошибка получения истории:", e)
        return render_template('history_2.html', user={'balance': session.get('balance'), 'sum_sp': 0, 'transactions': []})

@app.route("/topup_balance", methods=['POST'])
def topup_balance():
    if 'user_id' not in session:
        return jsonify({"result": False, "error": "Не авторизован"})

    req = request.get_json()
    amount = req.get('amount', 0)

    if not isinstance(amount, (int, float)) or amount < 1 or amount > 10000:
        return jsonify({"result": False, "error": "Сумма должна быть от 1 до 10000 рублей"})

    try:
        cnx = get_db_connection()
        cur = cnx.cursor()

        cur.execute('SELECT balance FROM users WHERE id=%s', (session['user_id'],))
        user = cur.fetchone()
        new_balance = user[0] + amount

        cur.execute('UPDATE users SET balance=%s WHERE id=%s', (new_balance, session['user_id']))
        cur.execute('INSERT INTO `transactions`(`user_id`, `type`, `cost`, `description`) VALUES (%s, %s, %s, %s)',
                   (session['user_id'], 'пополнение', amount, 'Пополнение баланса'))
        cnx.commit()
        cnx.close()

        session['balance'] = new_balance
        return jsonify({"result": True, "new_balance": new_balance})
    except Exception as e:
        print("Ошибка пополнения:", e)
        return jsonify({"result": False, "error": "Ошибка базы данных"})

if __name__ == '__main__':
    app.run(debug=True)
