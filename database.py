import sqlite3
from flask import g

DB_PATH = "financeiro.db"

SERVICOS_CATEGORIAS = ["corte", "barba", "combo"]
GASTOS_TIPOS = ["produtos", "salario", "outros"]

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def close_db(exception=None):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        valor REAL,
        categoria TEXT,
        descricao TEXT
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        valor REAL,
        tipo TEXT,
        descricao TEXT
    )""")
    db.commit()
    db.close()

def registrar_servico(db, valor, categoria, descricao):
    db.execute("INSERT INTO servicos (valor, categoria, descricao) VALUES (?, ?, ?)", (valor, categoria, descricao))
    db.commit()

def registrar_gasto(db, valor, tipo, descricao):
    db.execute("INSERT INTO gastos (valor, tipo, descricao) VALUES (?, ?, ?)", (valor, tipo, descricao))
    db.commit()

def obter_saldo(db):
    s = db.execute("SELECT SUM(valor) as total FROM servicos").fetchone()["total"] or 0
    g = db.execute("SELECT SUM(valor) as total FROM gastos").fetchone()["total"] or 0
    return s - g

def obter_servicos(db):
    return [dict(row) for row in db.execute("SELECT * FROM servicos").fetchall()]

def obter_gastos(db):
    return [dict(row) for row in db.execute("SELECT * FROM gastos").fetchall()]
