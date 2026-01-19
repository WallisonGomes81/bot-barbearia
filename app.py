from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
import os

app = Flask(__name__)

# Banco de dados SQLite
DB_PATH = "finance.db"

def init_db():
    """Cria o banco se não existir"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            category TEXT,
            amount REAL
        )
    """)
    conn.commit()
    conn.close()

def add_transaction(type_, category, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (type, category, amount) VALUES (?, ?, ?)",
              (type_, category, amount))
    conn.commit()
    conn.close()

def get_balance():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT SUM(CASE WHEN type='income' THEN amount ELSE -amount END) FROM transactions")
    result = c.fetchone()[0]
    conn.close()
    return result or 0

def get_statement():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT type, category, amount FROM transactions ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    if not rows:
        return "Nenhuma transação registrada."
    text = "Últimas transações:\n"
    for t in rows:
        text += f"{t[0].capitalize()} | {t[1]} | R${t[2]:.2f}\n"
    return text

# Inicializa o banco
init_db()

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get("Body", "").strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    try:
        if incoming_msg.startswith("add "):
            # Despesa: add 50 almoço
            parts = incoming_msg.split()
            amount = float(parts[1])
            category = " ".join(parts[2:])
            add_transaction("expense", category, amount)
            msg.body(f"Despesa de R${amount:.2f} em '{category}' registrada ✅")
        elif incoming_msg.startswith("income "):
            # Receita: income 200 salário
            parts = incoming_msg.split()
            amount = float(parts[1])
            category = " ".join(parts[2:])
            add_transaction("income", category, amount)
            msg.body(f"Receita de R${amount:.2f} em '{category}' registrada ✅")
        elif "saldo" in incoming_msg:
            balance = get_balance()
            msg.body(f"Saldo atual: R${balance:.2f}")
        elif "extrato" in incoming_msg:
            msg.body(get_statement())
        else:
            msg.body("Comando não reconhecido.\nUse:\n- add <valor> <categoria>\n- income <valor> <categoria>\n- saldo\n- extrato")
    except Exception as e:
        msg.body(f"Erro ao processar comando: {str(e)}")

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
