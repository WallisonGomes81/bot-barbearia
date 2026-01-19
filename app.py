from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# ------------------------------
# Conexão com PostgreSQL via variáveis de ambiente
# ------------------------------
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", 5432)
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# ------------------------------
# Inicializa banco e tabela
# ------------------------------
def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id SERIAL PRIMARY KEY,
            tipo VARCHAR(10),
            categoria VARCHAR(50),
            descricao TEXT,
            valor NUMERIC(10,2),
            data TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ------------------------------
# Funções do bot
# ------------------------------
def add_transacao(tipo, categoria, descricao, valor):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO transacoes (tipo, categoria, descricao, valor, data) VALUES (%s,%s,%s,%s,%s)",
        (tipo, categoria, descricao, valor, datetime.now())
    )
    conn.commit()
    conn.close()

def get_saldo():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT SUM(CASE WHEN tipo='entrada' THEN valor ELSE -valor END) FROM transacoes")
    saldo = c.fetchone()[0] or 0
    conn.close()
    return float(saldo)

def get_historico(limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT tipo, categoria, descricao, valor, data FROM transacoes ORDER BY data DESC LIMIT %s", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

# ------------------------------
# Rota raiz para teste no navegador
# ------------------------------
@app.route("/")
def index():
    return "🤖 Bot financeiro da barbearia online ✅"

# ------------------------------
# Rota do Twilio WhatsApp
# ------------------------------
@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    msg = request.form.get('Body', '').lower()
    resp = MessagingResponse()

    try:
        if msg.startswith("entrada"):
            parts = msg.split(" ", 3)
            valor = float(parts[1])
            categoria = parts[2] if len(parts) > 2 else "Sem categoria"
            descricao = parts[3] if len(parts) > 3 else "Sem descrição"
            add_transacao("entrada", categoria, descricao, valor)
            resp.message(f"✅ Entrada registrada: R${valor} - {categoria} - {descricao}")

        elif msg.startswith("saida"):
            parts = msg.split(" ", 3)
            valor = float(parts[1])
            categoria = parts[2] if len(parts) > 2 else "Sem categoria"
            descricao = parts[3] if len(parts) > 3 else "Sem descrição"
            add_transacao("saida", categoria, descricao, valor)
            resp.message(f"✅ Saída registrada: R${valor} - {categoria} - {descricao}")

        elif msg.startswith("saldo"):
            saldo = get_saldo()
            resp.message(f"💰 Saldo atual: R${saldo:.2f}")

        elif msg.startswith("historico"):
            historico = get_historico(10)
            if not historico:
                resp.message("📄 Nenhuma transação registrada.")
            else:
                texto = "📄 Últimas transações:\n"
                for t in historico:
                    tipo, cat, desc, val, data = t
                    texto += f"{tipo.upper()} | {cat} | {desc} | R${val:.2f} | {data.strftime('%d/%m %H:%M')}\n"
                resp.message(texto)

        else:
            resp.message(
                "📌 Comandos disponíveis:\n"
                "entrada VALOR CATEGORIA DESCRIÇÃO\n"
                "saida VALOR CATEGORIA DESCRIÇÃO\n"
                "saldo\n"
                "historico"
            )

    except Exception as e:
        resp.message(f"❌ Erro: {e}")

    return str(resp)

# ------------------------------
# Executa localmente
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)
