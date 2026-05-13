import os
import sqlite3
import shutil
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pdv_pizzaria.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def money_float(value):
    try:
        return float(value)
    except:
        return 0.0


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
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            cliente TEXT,
            telefone TEXT,
            endereco TEXT,
            mesa TEXT,
            pagamento TEXT,
            total REAL NOT NULL,
            criado_em TEXT NOT NULL
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/pizzas", methods=["GET"])
def listar_pizzas():
    conn = get_db()
    pizzas = conn.execute("SELECT * FROM pizzas ORDER BY CAST(codigo AS INTEGER), nome").fetchall()
    conn.close()

    return jsonify([dict(pizza) for pizza in pizzas])


@app.route("/api/pizzas", methods=["POST"])
def salvar_pizza():
    data = request.json

    pizza_id = data.get("id")
    codigo = data.get("codigo", "").strip()
    nome = data.get("nome", "").strip()
    preco_broto = money_float(data.get("preco_broto"))
    preco_grande = money_float(data.get("preco_grande"))

    if not codigo or not nome:
        return jsonify({"erro": "Código e nome são obrigatórios."}), 400

    conn = get_db()
    cursor = conn.cursor()

    if pizza_id:
        cursor.execute("""
            UPDATE pizzas
            SET codigo = ?, nome = ?, preco_broto = ?, preco_grande = ?
            WHERE id = ?
        """, (codigo, nome, preco_broto, preco_grande, pizza_id))
    else:
        cursor.execute("""
            INSERT INTO pizzas (codigo, nome, preco_broto, preco_grande)
            VALUES (?, ?, ?, ?)
        """, (codigo, nome, preco_broto, preco_grande))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/pizzas/<int:pizza_id>", methods=["DELETE"])
def excluir_pizza(pizza_id):
    conn = get_db()
    conn.execute("DELETE FROM pizzas WHERE id = ?", (pizza_id,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/produtos", methods=["GET"])
def listar_produtos():
    conn = get_db()
    produtos = conn.execute("SELECT * FROM produtos ORDER BY tipo, nome").fetchall()
    conn.close()

    return jsonify([dict(produto) for produto in produtos])


@app.route("/api/produtos", methods=["POST"])
def salvar_produto():
    data = request.json

    produto_id = data.get("id")
    tipo = data.get("tipo", "").strip()
    categoria = data.get("categoria", "").strip()
    nome = data.get("nome", "").strip()
    preco = money_float(data.get("preco"))

    if not tipo or not nome:
        return jsonify({"erro": "Tipo e nome são obrigatórios."}), 400

    if tipo != "bebida":
        categoria = ""

    conn = get_db()
    cursor = conn.cursor()

    if produto_id:
        cursor.execute("""
            UPDATE produtos
            SET tipo = ?, categoria = ?, nome = ?, preco = ?
            WHERE id = ?
        """, (tipo, categoria, nome, preco, produto_id))
    else:
        cursor.execute("""
            INSERT INTO produtos (tipo, categoria, nome, preco)
            VALUES (?, ?, ?, ?)
        """, (tipo, categoria, nome, preco))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/produtos/<int:produto_id>", methods=["DELETE"])
def excluir_produto(produto_id):
    conn = get_db()
    conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/pedidos", methods=["GET"])
def listar_pedidos():
    conn = get_db()

    pedidos = conn.execute("""
        SELECT * FROM pedidos
        ORDER BY id DESC
    """).fetchall()

    resultado = []

    for pedido in pedidos:
        itens = conn.execute("""
            SELECT * FROM pedido_itens
            WHERE pedido_id = ?
            ORDER BY id
        """, (pedido["id"],)).fetchall()

        pedido_dict = dict(pedido)
        pedido_dict["itens"] = [dict(item) for item in itens]
        resultado.append(pedido_dict)

    conn.close()

    return jsonify(resultado)


@app.route("/api/pedidos", methods=["POST"])
def criar_pedido():
    data = request.json

    tipo = data.get("tipo")
    cliente = data.get("cliente", "")
    telefone = data.get("telefone", "")
    endereco = data.get("endereco", "")
    mesa = data.get("mesa", "")
    pagamento = data.get("pagamento", "")
    itens = data.get("itens", [])

    if not tipo:
        return jsonify({"erro": "Tipo do pedido é obrigatório."}), 400

    if not itens:
        return jsonify({"erro": "Adicione pelo menos um item."}), 400

    total = sum(money_float(item.get("total")) for item in itens)
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pedidos
        (tipo, cliente, telefone, endereco, mesa, pagamento, total, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (tipo, cliente, telefone, endereco, mesa, pagamento, total, criado_em))

    pedido_id = cursor.lastrowid

    for item in itens:
        cursor.execute("""
            INSERT INTO pedido_itens
            (pedido_id, descricao, quantidade, preco_unitario, total)
            VALUES (?, ?, ?, ?, ?)
        """, (
            pedido_id,
            item.get("descricao"),
            int(item.get("quantidade", 1)),
            money_float(item.get("preco_unitario")),
            money_float(item.get("total"))
        ))

    conn.commit()
    conn.close()

    return jsonify({"ok": True, "pedido_id": pedido_id})


@app.route("/api/comandas", methods=["GET"])
def listar_comandas():
    conn = get_db()

    comandas = conn.execute("""
        SELECT *
        FROM comandas
        WHERE status = 'aberta'
        ORDER BY CAST(mesa AS INTEGER), mesa
    """).fetchall()

    resultado = []

    for comanda in comandas:
        itens = conn.execute("""
            SELECT *
            FROM comanda_itens
            WHERE comanda_id = ?
            ORDER BY id
        """, (comanda["id"],)).fetchall()

        total = sum(float(item["total"]) for item in itens)

        comanda_dict = dict(comanda)
        comanda_dict["itens"] = [dict(item) for item in itens]
        comanda_dict["total"] = total
        resultado.append(comanda_dict)

    conn.close()

    return jsonify(resultado)


@app.route("/api/comandas/adicionar", methods=["POST"])
def adicionar_comanda():
    data = request.json

    mesa = str(data.get("mesa", "")).strip()
    pagamento = data.get("pagamento", "")
    itens = data.get("itens", [])

    if not mesa:
        return jsonify({"erro": "Informe a mesa."}), 400

    if not itens:
        return jsonify({"erro": "Adicione pelo menos um item."}), 400

    conn = get_db()
    cursor = conn.cursor()

    comanda = cursor.execute("""
        SELECT *
        FROM comandas
        WHERE mesa = ? AND status = 'aberta'
        LIMIT 1
    """, (mesa,)).fetchone()

    if comanda:
        comanda_id = comanda["id"]
        cursor.execute("""
            UPDATE comandas
            SET pagamento = ?
            WHERE id = ?
        """, (pagamento, comanda_id))
    else:
        criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO comandas (mesa, status, pagamento, criado_em)
            VALUES (?, 'aberta', ?, ?)
        """, (mesa, pagamento, criado_em))

        comanda_id = cursor.lastrowid

    for item in itens:
        cursor.execute("""
            INSERT INTO comanda_itens
            (comanda_id, descricao, quantidade, preco_unitario, total)
            VALUES (?, ?, ?, ?, ?)
        """, (
            comanda_id,
            item.get("descricao"),
            int(item.get("quantidade", 1)),
            money_float(item.get("preco_unitario")),
            money_float(item.get("total"))
        ))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/comandas/<int:comanda_id>/fechar", methods=["POST"])
def fechar_comanda(comanda_id):
    data = request.json or {}
    pagamento = data.get("pagamento", "")

    conn = get_db()
    cursor = conn.cursor()

    comanda = cursor.execute("""
        SELECT *
        FROM comandas
        WHERE id = ? AND status = 'aberta'
    """, (comanda_id,)).fetchone()

    if not comanda:
        conn.close()
        return jsonify({"erro": "Comanda não encontrada."}), 404

    itens = cursor.execute("""
        SELECT *
        FROM comanda_itens
        WHERE comanda_id = ?
    """, (comanda_id,)).fetchall()

    if not itens:
        conn.close()
        return jsonify({"erro": "Comanda sem itens."}), 400

    total = sum(float(item["total"]) for item in itens)
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO pedidos
        (tipo, cliente, telefone, endereco, mesa, pagamento, total, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Salão",
        f"Mesa {comanda['mesa']}",
        "",
        "",
        comanda["mesa"],
        pagamento or comanda["pagamento"] or "Não informado",
        total,
        criado_em
    ))

    pedido_id = cursor.lastrowid

    for item in itens:
        cursor.execute("""
            INSERT INTO pedido_itens
            (pedido_id, descricao, quantidade, preco_unitario, total)
            VALUES (?, ?, ?, ?, ?)
        """, (
            pedido_id,
            item["descricao"],
            item["quantidade"],
            item["preco_unitario"],
            item["total"]
        ))

    cursor.execute("""
        UPDATE comandas
        SET status = 'fechada', pagamento = ?
        WHERE id = ?
    """, (pagamento or comanda["pagamento"], comanda_id))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/relatorio", methods=["GET"])
def relatorio():
    conn = get_db()

    total_vendas = conn.execute("""
        SELECT COUNT(*) AS total FROM pedidos
    """).fetchone()["total"]

    faturamento = conn.execute("""
        SELECT COALESCE(SUM(total), 0) AS total FROM pedidos
    """).fetchone()["total"]

    comandas_abertas = conn.execute("""
        SELECT COUNT(*) AS total
        FROM comandas
        WHERE status = 'aberta'
    """).fetchone()["total"]

    por_tipo = conn.execute("""
        SELECT tipo, COALESCE(SUM(total), 0) AS total
        FROM pedidos
        GROUP BY tipo
    """).fetchall()

    conn.close()

    return jsonify({
        "total_vendas": total_vendas,
        "faturamento": faturamento,
        "comandas_abertas": comandas_abertas,
        "por_tipo": [dict(item) for item in por_tipo]
    })


@app.route("/api/backup", methods=["POST"])
def criar_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_backup = f"backup_pdv_{agora}.db"
    caminho_backup = os.path.join(BACKUP_DIR, nome_backup)

    shutil.copy2(DB_PATH, caminho_backup)

    return jsonify({
        "ok": True,
        "arquivo": nome_backup
    })


@app.route("/api/backup/download", methods=["GET"])
def baixar_banco():
    return send_file(DB_PATH, as_attachment=True, download_name="pdv_pizzaria.db")


@app.route("/api/sistema/zerar", methods=["POST"])
def zerar_sistema():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM pedido_itens")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM comanda_itens")
    cursor.execute("DELETE FROM comandas")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM pizzas")

    conn.commit()
    conn.close()

    init_db()

    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)