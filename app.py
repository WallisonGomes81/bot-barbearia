from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
import os

app = Flask(__name__)

# Banco SQLite
DB_FILE = "finance.db"

# Inicializa o banco e tabela
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            type TEXT,
            value REAL,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Adiciona transação
def add_transaction(user, t_type, value, description):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (user, type, value, description) VALUES (?, ?, ?, ?)",
        (user, t_type, value, description)
    )
    conn.commit()
    conn.close()

# Calcula saldo
def get_balance(user):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(value) FROM transactions WHERE user=? AND type='income'", (user,))
    income = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(value) FROM transactions WHERE user=? AND type='expense'", (user,))
    expense = cursor.fetchone()[0] or 0
    conn.close()
    return income - expense

# Retorna extrato
def get_history(user):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT type, value, description FROM transactions WHERE user=? ORDER BY id", (user,))
    rows = cursor.fetchall()
    conn.close()
    history = []
    for t_type, value, description in rows:
        prefix = "+" if t_type == "income" else "-"
        history.append(f"{prefix}{value} {description}")
    return history

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip().lower()
    from_number = request.values.get('From', '')
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg.startswith("add "):
        try:
            _, value, *desc = incoming_msg.split()
            value = float(value)
            description = ' '.join(desc) if desc else "Despesa"
            add_transaction(from_number, "expense", value, description)
            saldo = get_balance(from_number)
            msg.body(f"Despesa registrada: {value} ({description})\nSaldo atual: {saldo}")
        except:
            msg.body("Formato inválido! Use: add [valor] [descrição]")

    elif incoming_msg.startswith("income "):
        try:
            _, value, *desc = incoming_msg.split()
            value = float(value)
            description = ' '.join(desc) if desc else "Receita"
            add_transaction(from_number, "income", value, description)
            saldo = get_balance(from_number)
            msg.body(f"Receita registrada: {value} ({description})\nSaldo atual: {saldo}")
        except:
            msg.body("Formato inválido! Use: income [valor] [descrição]")

    elif incoming_msg == "saldo":
        saldo = get_balance(from_number)
        msg.body(f"Seu saldo atual é: {saldo}")

    elif incoming_msg == "extrato":
        history = get_history(from_number)
        if not history:
            history_text = "Nenhuma transação"
        else:
            history_text = "\n".join(history)
        saldo = get_balance(from_number)
        msg.body(f"Extrato:\n{history_text}\nSaldo: {saldo}")

    else:
        msg.body(
            "Comandos disponíveis:\n"
            "- add [valor] [descrição]\n"
            "- income [valor] [descrição]\n"
            "- saldo\n"
            "- extrato"
        )

    return str(resp)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
