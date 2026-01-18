import os
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from database import (
    get_db, close_db, init_db,
    SERVICOS_CATEGORIAS, GASTOS_TIPOS,
    registrar_servico, registrar_gasto,
    obter_saldo, obter_servicos, obter_gastos
)

# ===== Configuração =====
load_dotenv()
app = Flask(__name__)
app.teardown_appcontext(close_db)
init_db()

# ===== Comandos =====
def cmd_oi():
    return "🤖 Olá! Eu sou o bot financeiro da barbearia.\nDigite *ajuda* para ver os comandos."

def cmd_ajuda():
    return (
        "📌 *Comandos disponíveis:*\n\n"
        "💰 saldo → ver saldo atual da barbearia\n"
        "💈 servico VALOR CATEGORIA DESCRIÇÃO → registra receita\n"
        "💸 gasto VALOR TIPO DESCRIÇÃO → registra gasto\n"
        "📊 resumo → mostra resumo completo de receitas, gastos e saldo\n"
        "❓ ajuda → ver todos os comandos"
    )

def cmd_saldo(db):
    return f"💰 Saldo atual: R$ {obter_saldo(db):.2f}"

def cmd_servico(db, partes):
    if len(partes) < 4:
        return "❌ Use: servico VALOR CATEGORIA DESCRIÇÃO"
    try:
        valor = float(partes[1])
        categoria = partes[2].lower()
        descricao = partes[3]
        if categoria not in SERVICOS_CATEGORIAS:
            return f"❌ Categoria inválida. {', '.join(SERVICOS_CATEGORIAS)}"
        registrar_servico(db, valor, categoria, descricao)
        saldo = obter_saldo(db)
        return f"✅ Serviço registrado!\n💸 R$ {valor:.2f}\n🏷 {categoria}\n📝 {descricao}\n💰 Saldo: R$ {saldo:.2f}"
    except ValueError:
        return "❌ Valor inválido."

def cmd_gasto(db, partes):
    if len(partes) < 4:
        return "❌ Use: gasto VALOR TIPO DESCRIÇÃO"
    try:
        valor = float(partes[1])
        tipo = partes[2].lower()
        descricao = partes[3]
        if tipo not in GASTOS_TIPOS:
            return f"❌ Tipo inválido. {', '.join(GASTOS_TIPOS)}"
        registrar_gasto(db, valor, tipo, descricao)
        saldo = obter_saldo(db)
        return f"✅ Gasto registrado!\n💸 R$ {valor:.2f}\n🏷 {tipo}\n📝 {descricao}\n💰 Saldo: R$ {saldo:.2f}"
    except ValueError:
        return "❌ Valor inválido."

def cmd_resumo(db):
    servicos = obter_servicos(db)
    gastos = obter_gastos(db)
    saldo = obter_saldo(db)

    texto = f"📊 *Resumo Financeiro*\n💰 Saldo atual: R$ {saldo:.2f}\n\n"

    if servicos:
        texto += "💈 Receitas:\n"
        total_serv = 0
        categorias = {}
        for s in servicos:
            texto += f"• R$ {s['valor']:.2f} - {s['descricao']} ({s['categoria']})\n"
            total_serv += s['valor']
            categorias[s['categoria']] = categorias.get(s['categoria'], 0) + s['valor']
        texto += f"Total: R$ {total_serv:.2f}\n"
        for cat, val in categorias.items():
            texto += f"• {cat}: R$ {val:.2f}\n"
        texto += "\n"

    if gastos:
        texto += "💸 Gastos:\n"
        total_gastos = 0
        tipos = {}
        for g in gastos:
            texto += f"• R$ {g['valor']:.2f} - {g['descricao']} ({g['tipo']})\n"
            total_gastos += g['valor']
            tipos[g['tipo']] = tipos.get(g['tipo'], 0) + g['valor']
        texto += f"Total: R$ {total_gastos:.2f}\n"
        for t, val in tipos.items():
            texto += f"• {t}: R$ {val:.2f}\n"

    return texto

# ===== Rotas =====
@app.route("/", methods=["GET"])
def index():
    return "<h2>Bot Financeiro no ar ✅</h2>", 200

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg = request.form.get("Body", "").lower().strip()
    from_number = request.form.get("From")
    print(f"[LOG] Mensagem recebida de {from_number}: {msg}")

    resp = MessagingResponse()
    reply = resp.message()
    db = get_db()
    partes = msg.split(" ", 3)

    if msg == "oi":
        reply.body(cmd_oi())
    elif msg == "ajuda":
        reply.body(cmd_ajuda())
    elif msg == "saldo":
        reply.body(cmd_saldo(db))
    elif msg.startswith("servico"):
        reply.body(cmd_servico(db, partes))
    elif msg.startswith("gasto"):
        reply.body(cmd_gasto(db, partes))
    elif msg == "resumo":
        reply.body(cmd_resumo(db))
    else:
        reply.body("❓ Comando não reconhecido.\nDigite *ajuda*.")

    # Retorno para Twilio com Content-Type correto
    return Response(str(resp), mimetype="application/xml")

# ===== Rodar servidor =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
