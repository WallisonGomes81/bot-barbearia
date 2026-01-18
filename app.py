from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

# Saldo fictício (temporário – depois vai pro banco)
saldo_atual = 1000.00
gastos = []

@app.route("/")
def home():
    return "🚀 Bot WhatsApp Financeiro rodando"

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    global saldo_atual, gastos

    msg = request.form.get("Body", "").lower().strip()
    resp = MessagingResponse()
    reply = resp.message()

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
        reply.body(f"💰 Seu saldo atual é: R$ {saldo_atual:.2f}")

    elif msg.startswith("gasto"):
        partes = msg.split(" ", 2)

        if len(partes) < 3:
            reply.body(
                "❌ Formato inválido.\n"
                "Use: gasto VALOR DESCRIÇÃO\n"
                "Ex: gasto 30 almoço"
            )
        else:
            try:
                valor = float(partes[1])
                descricao = partes[2]

                saldo_atual -= valor
                gastos.append((valor, descricao))

                reply.body(
                    f"✅ Gasto registrado!\n\n"
                    f"💸 Valor: R$ {valor:.2f}\n"
                    f"📝 Descrição: {descricao}\n"
                    f"💰 Saldo: R$ {saldo_atual:.2f}"
                )
            except ValueError:
                reply.body("❌ Valor inválido. Use números.")

    elif msg == "resumo":
        if not gastos:
            reply.body("📭 Nenhum gasto registrado.")
        else:
            texto = "📊 *Resumo de gastos:*\n\n"
            total = 0

            for valor, desc in gastos:
                texto += f"• R$ {valor:.2f} - {desc}\n"
                total += valor

            texto += f"\n💸 Total gasto: R$ {total:.2f}"
            reply.body(texto)

    else:
        reply.body(
            "❓ Comando não reconhecido.\n"
            "Digite *ajuda* para ver os comandos."
        )

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)