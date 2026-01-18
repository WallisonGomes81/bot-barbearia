from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
import os

app = Flask(__name__)

# =====================
# BANCO DE DADOS
# =====================
def get_db():
    conn = sqlite3.connect("finance.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS saldo (
            id INTEGER PRIMARY KEY,
            valor REAL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            valor REAL,
            descricao TEXT
        )
    """)
    # saldo inicial
    saldo = db.execute("SELECT * FROM saldo").fetchone()
    if saldo is None:
        db.execute("INSERT INTO saldo (id, valor) VALUES (1, 1000)")
    db.commit()
    db.close()

init_db()

# =====================
# ROTAS
# =====================
@app.route("/")
def home():
    return "🚀 Bot WhatsApp Financeiro rodando com banco"

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg = request.form.get("Body", "").lower().strip()
    resp = MessagingResponse()
    reply = resp.message()

    db = get_db()

    # ===== COMANDOS =====

    if msg == "oi":
        reply.body(
            "🤖 Olá! Eu sou seu bot financeiro.\n\n"
            "Digite *ajuda* para ver os comandos."
        )

    elif msg == "ajuda":
        reply.body(
            "📌 *Comandos disponíveis:*\n\n"
            "• saldo → ver saldo\n"
            "• gasto VALOR DESCRIÇÃO\n"
            "  Ex: gasto 50 mercado\n"
            "• resumo → ver gastos\n"
        )

    elif msg == "saldo":
        saldo = db.execute("SELECT valor FROM saldo WHERE id = 1").fetchone()
        reply.body(f"💰 Seu saldo atual é: R$ {saldo['valor']:.2f}")

    elif msg.startswith("gasto"):
        partes = msg.split(" ", 2)

        if len(partes) < 3:
            reply.body(
                "❌ Use: gasto VALOR DESCRIÇÃO\n"
                "Ex: gasto 30 almoço"
            )
        else:
            try:
                valor = float(partes[1])
                descricao = partes[2]

                # Atualiza saldo
                saldo = db.execute("SELECT valor FROM saldo WHERE id = 1").fetchone()
                novo_saldo = saldo["valor"] - valor

                db.execute("UPDATE saldo SET valor = ? WHERE id = 1", (novo_saldo,))
                db.execute(
                    "INSERT INTO gastos (valor, descricao) VALUES (?, ?)",
                    (valor, descricao)
                )
                db.commit()

                reply.body(
                    f"✅ Gasto registrado!\n\n"
                    f"💸 Valor: R$ {valor:.2f}\n"
                    f"📝 {descricao}\n"
                    f"💰 Saldo: R$ {novo_saldo:.2f}"
                )
            except ValueError:
                reply.body("❌ Valor inválido.")

    elif msg == "resumo":
        gastos = db.execute("SELECT * FROM gastos").fetchall()

        if not gastos:
            reply.body("📭 Nenhum gasto registrado.")
        else:
            texto = "📊 *Resumo de gastos:*\n\n"
            total = 0

            for g in gastos:
                texto += f"• R$ {g['valor']:.2f} - {g['descricao']}\n"
                total += g["valor"]

            texto += f"\n💸 Total gasto: R$ {total:.2f}"
            reply.body(texto)

    else:
        reply.body(
            "❓ Comando não reconhecido.\n"
            "Digite *ajuda*."
        )

    db.close()
    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
