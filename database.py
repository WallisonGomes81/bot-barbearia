import sqlite3
from flask import g

DB_PATH = "barbearia.db"

def get_db():
    """Retorna a conexão SQLite do request."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Fecha conexão SQLite ao final do request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Inicializa o banco de dados com tabelas padrão."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

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

# ===== Funções auxiliares =====
SERVICOS_CATEGORIAS = ["cabelo","barba","pigmentacao","combo","outros"]
GASTOS_TIPOS = ["investimento","variavel","fixo"]

def atualizar_saldo(db, valor, operacao="add"):
    """Atualiza saldo de forma atômica."""
    if operacao == "add":
        db.execute("UPDATE saldo SET valor = valor + ? WHERE id = 1", (valor,))
    elif operacao == "sub":
        db.execute("UPDATE saldo SET valor = valor - ? WHERE id = 1", (valor,))
    db.commit()

def obter_saldo(db):
    """Retorna o saldo atual."""
    return db.execute("SELECT valor FROM saldo WHERE id = 1").fetchone()["valor"]

def registrar_servico(db, valor, categoria, descricao):
    """Registra serviço e atualiza saldo."""
    atualizar_saldo(db, valor, "add")
    db.execute(
        "INSERT INTO servicos (valor, descricao, categoria) VALUES (?, ?, ?)",
        (valor, descricao, categoria)
    )
    db.commit()

def registrar_gasto(db, valor, tipo, descricao):
    """Registra gasto e atualiza saldo."""
    atualizar_saldo(db, valor, "sub")
    db.execute(
        "INSERT INTO gastos (valor, descricao, tipo) VALUES (?, ?, ?)",
        (valor, descricao, tipo)
    )
    db.commit()

def obter_servicos(db):
    return db.execute("SELECT * FROM servicos").fetchall()

def obter_gastos(db):
    return db.execute("SELECT * FROM gastos").fetchall()
