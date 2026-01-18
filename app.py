import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3

app = Flask(__name__)
DB_PATH = "barbearia.db"

# ===== Banco de dados =====
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    
    # Saldo inicial
    db.execute("""
        CREATE TABLE IF NOT EXISTS saldo (
            id INTEGER PRIMARY KEY,
            valor REAL
        )
    """)
    db.execute("INSERT OR IGNORE INTO saldo (id, valor) VALUES (1, 0)")
    
    # Serviços realizados (receitas)
    db.execute("""
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            valor REAL,
            descricao TEXT,
            categoria TEXT CHECK(categoria IN ('cabelo','barba','pigmentacao','combo','outros'))
        )
    """)
    
    # Gastos da barbearia
    db.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            valor REAL,
            descricao TEXT,
            tipo TEXT CHECK(tipo IN ('investimento','variavel','fixo'))
        )
    """)
    
    db.commit()
    db.close()

init_db()

# ===== Categorias =====
SERVICOS_CATEGORIAS = ["cabelo","barba","pigmentacao","combo","outros"]
GASTOS_TIPOS = ["investimento","variavel","fixo"]

# ===== Comandos =====
def cmd_oi():
    return "🤖 Olá! Eu sou o bot financeiro da barbearia.\nDigite *ajuda* para ver os comandos."

def cmd_ajuda():
    return (
        "📌 *Comandos disponíveis:*\n\n"
        "💰 *Saldo da barbearia:*\n"
        "• saldo → ver saldo atual da barbearia\n\n"
        "💈 *Registrar serviços (aumenta saldo):*\n"
        "• servico VALOR CATEGORIA DESCRIÇÃO → registra receita de serviço\n"
        "  Ex: servico 50 cabelo corte masculino\n"
        "  Categorias válidas: cabelo, barba, pigmentacao, combo, outros\n\n"
        "💸 *Registrar gastos (diminui saldo):*\n"
        "• gasto VALOR TIPO DESCRIÇÃO → registra gasto da barbearia\n"
        "  Ex: gasto 200 investimento cadeira nova\n"
        "  Tipos válidos: investimento, variavel, fixo\n\n"
        "📊 *Resumo financeiro:*\n"
        "• resumo → mostra resumo completo de receitas, gastos e saldo\n\n"
        "❓ Outros:\n"
        "• ajuda → ver todos os comandos"
    )


def cmd_saldo(db):
    saldo = db.execute("SELECT valor FROM saldo WHERE id = 1").fetchone()
    return f"💰 Saldo atual da barbearia: R$ {saldo['valor']:.2f}"

def cmd_servico(db, partes):
    if len(partes) < 4:
        return "❌ Use: servico VALOR CATEGORIA DESCRIÇÃO\nEx: servico 50 cabelo corte masculino"
    
    try:
        valor = float(partes[1])
        categoria = partes[2].lower()
        descricao = partes[3]
        
        if categoria not in SERVICOS_CATEGORIAS:
            return f"❌ Categoria inválida.\nCategorias válidas: {', '.join(SERVICOS_CATEGORIAS)}"
        
        # Atualiza saldo
        saldo = db.execute("SELECT valor FROM saldo WHERE id = 1").fetchone()
        novo_saldo = saldo["valor"] + valor

        db.execute("UPDATE saldo SET valor = ? WHERE id = 1", (novo_saldo,))
        db.execute("INSERT INTO servicos (valor, descricao, categoria) VALUES (?, ?, ?)",
                   (valor, descricao, categoria))
        db.commit()

        return (f"✅ Serviço registrado!\n\n"
                f"💸 Valor: R$ {valor:.2f}\n"
                f"🏷 Categoria: {categoria}\n"
                f"📝 {descricao}\n"
                f"💰 Saldo atual: R$ {novo_saldo:.2f}")

    except ValueError:
        return "❌ Valor inválido."

def cmd_gasto(db, partes):
    if len(partes) < 4:
        return "❌ Use: gasto VALOR TIPO DESCRIÇÃO\nEx: gasto 200 investimento cadeira nova"
    
    try:
        valor = float(partes[1])
        tipo = partes[2].lower()
        descricao = partes[3]
        
        if tipo not in GASTOS_TIPOS:
            return f"❌ Tipo inválido.\nTipos válidos: {', '.join(GASTOS_TIPOS)}"
        
        # Atualiza saldo
        saldo = db.execute("SELECT valor FROM saldo WHERE id = 1").fetchone()
        novo_saldo = saldo["valor"] - valor

        db.execute("UPDATE saldo SET valor = ? WHERE id = 1", (novo_saldo,))
        db.execute("INSERT INTO gastos (valor, descricao, tipo) VALUES (?, ?, ?)",
                   (valor, descricao, tipo))
        db.commit()

        return (f"✅ Gasto registrado!\n\n"
                f"💸 Valor: R$ {valor:.2f}\n"
                f"🏷 Tipo: {tipo}\n"
                f"📝 {descricao}\n"
                f"💰 Saldo atual: R$ {novo_saldo:.2f}")

    except ValueError:
        return "❌ Valor inválido."

def cmd_resumo(db):
    servicos = db.execute("SELECT * FROM servicos").fetchall()
    gastos = db.execute("SELECT * FROM gastos").fetchall()
    saldo = db.execute("SELECT valor FROM saldo WHERE id = 1").fetchone()["valor"]

    texto = f"📊 *Resumo Financeiro da Barbearia*\n💰 Saldo atual: R$ {saldo:.2f}\n\n"
    
    if servicos:
        texto += "💈 *Receitas por serviços:*\n"
        total_servicos = 0
        por_categoria = {}
        for s in servicos:
            texto += f"• R$ {s['valor']:.2f} - {s['descricao']} ({s['categoria']})\n"
            total_servicos += s["valor"]
            por_categoria[s["categoria"]] = por_categoria.get(s["categoria"], 0) + s["valor"]
        texto += f"Total serviços: R$ {total_servicos:.2f}\n"
        for cat, val in por_categoria.items():
            texto += f"• {cat}: R$ {val:.2f}\n"
        texto += "\n"
    else:
        texto += "📭 Nenhum serviço registrado.\n\n"

    if gastos:
        texto += "💸 *Gastos da barbearia:*\n"
        total_gastos = 0
        por_tipo = {}
        for g in gastos:
            texto += f"• R$ {g['valor']:.2f} - {g['descricao']} ({g['tipo']})\n"
            total_gastos += g["valor"]
            por_tipo[g["tipo"]] = por_tipo.get(g["tipo"], 0) + g["valor"]
        texto += f"Total gastos: R$ {total_gastos:.2f}\n"
        for t, val in por_tipo.items():
            texto += f"• {t}: R$ {val:.2f}\n"
    else:
        texto += "📭 Nenhum gasto registrado.\n"

    return texto

# ===== Rota principal =====
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg = request.form.get("Body", "").lower().strip()
    resp = MessagingResponse()
    reply = resp.message()
    db = get_db()
    partes = msg.split(" ", 3)  # Comando + 3 argumentos possíveis

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

    db.close()
    return str(resp)

# ===== Rodar servidor =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)