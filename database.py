import os
import sqlite3
from datetime import datetime, date

from config import DB_PATH, BACKUP_DIR


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def money_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def agora_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hoje_inicio():
    return date.today().strftime("%Y-%m-%d") + " 00:00:00"


def hoje_fim():
    return date.today().strftime("%Y-%m-%d") + " 23:59:59"


def column_exists(conn, table, column):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in rows)


def get_caixa_aberto(conn):
    return conn.execute("""
        SELECT *
        FROM caixas
        WHERE status = 'aberto'
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()


def calcular_valor_caixa(conn, caixa_id):
    caixa = conn.execute("""
        SELECT *
        FROM caixas
        WHERE id = ?
    """, (caixa_id,)).fetchone()

    if not caixa:
        return 0.0

    valor_inicial = money_float(caixa["valor_inicial"])

    vendas = conn.execute("""
        SELECT COALESCE(SUM(total), 0) AS total
        FROM pedidos
        WHERE caixa_id = ?
    """, (caixa_id,)).fetchone()["total"]

    reforcos = conn.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM caixa_movimentos
        WHERE caixa_id = ? AND tipo = 'reforco'
    """, (caixa_id,)).fetchone()["total"]

    sangrias = conn.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM caixa_movimentos
        WHERE caixa_id = ? AND tipo = 'sangria'
    """, (caixa_id,)).fetchone()["total"]

    return valor_inicial + money_float(vendas) + money_float(reforcos) - money_float(sangrias)


def init_db():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pizzas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            nome TEXT NOT NULL,
            preco_broto REAL NOT NULL,
            preco_grande REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            categoria TEXT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS caixas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL DEFAULT 'aberto',
            valor_inicial REAL NOT NULL DEFAULT 0,
            valor_final_informado REAL,
            valor_sistema REAL,
            observacao TEXT,
            aberto_por TEXT,
            fechado_por TEXT,
            aberto_em TEXT NOT NULL,
            fechado_em TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS caixa_movimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caixa_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            criado_em TEXT NOT NULL,
            FOREIGN KEY (caixa_id) REFERENCES caixas(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            cliente TEXT,
            telefone TEXT,
            endereco TEXT,
            mesa TEXT,
            pagamento TEXT,
            observacao TEXT,
            total REAL NOT NULL,
            criado_em TEXT NOT NULL,
            caixa_id INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedido_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comandas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mesa TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'aberta',
            pagamento TEXT,
            observacao TEXT,
            criado_em TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comanda_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comanda_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (comanda_id) REFERENCES comandas(id)
        )
    """)

    conn.commit()

    if not column_exists(conn, "pedidos", "caixa_id"):
        cursor.execute("ALTER TABLE pedidos ADD COLUMN caixa_id INTEGER")

    if not column_exists(conn, "pedidos", "observacao"):
        cursor.execute("ALTER TABLE pedidos ADD COLUMN observacao TEXT")

    if not column_exists(conn, "comandas", "observacao"):
        cursor.execute("ALTER TABLE comandas ADD COLUMN observacao TEXT")

    conn.commit()

    cursor.execute("SELECT COUNT(*) AS total FROM pizzas")
    total_pizzas = cursor.fetchone()["total"]

    if total_pizzas == 0:
        pizzas_padrao = [
            ("01", "Mussarela", 25.00, 45.00),
            ("02", "Calabresa", 27.00, 48.00),
            ("03", "Portuguesa", 30.00, 55.00),
            ("04", "Frango com Catupiry", 32.00, 58.00),
        ]

        cursor.executemany("""
            INSERT INTO pizzas (codigo, nome, preco_broto, preco_grande)
            VALUES (?, ?, ?, ?)
        """, pizzas_padrao)

    cursor.execute("SELECT COUNT(*) AS total FROM produtos")
    total_produtos = cursor.fetchone()["total"]

    if total_produtos == 0:
        produtos_padrao = [
            ("borda", "", "Sem borda", 0.00),
            ("borda", "", "Borda Catupiry", 8.00),
            ("borda", "", "Borda Cheddar", 8.00),
            ("bebida", "Refrigerante", "Coca-Cola 2L", 14.00),
            ("bebida", "Refrigerante", "Guaraná 2L", 12.00),
            ("bebida", "Cerveja", "Heineken Long Neck", 10.00),
            ("bebida", "Vinho", "Vinho da casa", 45.00),
            ("adicional", "", "Mussarela extra", 7.00),
        ]

        cursor.executemany("""
            INSERT INTO produtos (tipo, categoria, nome, preco)
            VALUES (?, ?, ?, ?)
        """, produtos_padrao)

    conn.commit()
    conn.close()