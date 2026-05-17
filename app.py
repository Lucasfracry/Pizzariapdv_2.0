import os
import sqlite3
import shutil
from datetime import datetime, date
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    redirect,
    url_for,
    session
)

app = Flask(__name__)
app.secret_key = "troque-essa-chave-depois-pdv-pizzaria"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pdv_pizzaria.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")


USERS = {
    "admin": {
        "senha": "1234",
        "nome": "Administrador",
        "nivel": "admin"
    },
    "operador": {
        "senha": "1234",
        "nome": "Operador",
        "nivel": "operador"
    }
}


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


def login_required_page(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def login_required_api(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return jsonify({"erro": "Sessão expirada. Faça login novamente."}), 401
        return func(*args, **kwargs)
    return wrapper


def column_exists(conn, table, column):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in rows)


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

    if not column_exists(conn, "pedidos", "caixa_id"):
        cursor.execute("ALTER TABLE pedidos ADD COLUMN caixa_id INTEGER")

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


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("usuario"):
            return redirect(url_for("index"))
        return render_template("login.html")

    usuario = request.form.get("usuario", "").strip()
    senha = request.form.get("senha", "").strip()

    user = USERS.get(usuario)

    if not user or user["senha"] != senha:
        return render_template(
            "login.html",
            erro="Usuário ou senha inválidos."
        )

    session["usuario"] = usuario
    session["nome"] = user["nome"]
    session["nivel"] = user["nivel"]

    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required_page
def index():
    return render_template(
        "index.html",
        usuario=session.get("nome"),
        nivel=session.get("nivel")
    )


@app.route("/cupom/<int:pedido_id>")
@login_required_page
def cupom(pedido_id):
    conn = get_db()

    pedido = conn.execute("""
        SELECT *
        FROM pedidos
        WHERE id = ?
    """, (pedido_id,)).fetchone()

    if not pedido:
        conn.close()
        return "Pedido não encontrado.", 404

    itens = conn.execute("""
        SELECT *
        FROM pedido_itens
        WHERE pedido_id = ?
        ORDER BY id
    """, (pedido_id,)).fetchall()

    conn.close()

    return render_template(
        "cupom.html",
        pedido=dict(pedido),
        itens=[dict(item) for item in itens]
    )


@app.route("/caixa/cupom/<int:caixa_id>")
@login_required_page
def cupom_caixa(caixa_id):
    conn = get_db()

    caixa = conn.execute("""
        SELECT *
        FROM caixas
        WHERE id = ?
    """, (caixa_id,)).fetchone()

    if not caixa:
        conn.close()
        return "Caixa não encontrado.", 404

    pedidos = conn.execute("""
        SELECT *
        FROM pedidos
        WHERE caixa_id = ?
        ORDER BY id
    """, (caixa_id,)).fetchall()

    movimentos = conn.execute("""
        SELECT *
        FROM caixa_movimentos
        WHERE caixa_id = ?
        ORDER BY id
    """, (caixa_id,)).fetchall()

    por_pagamento = conn.execute("""
        SELECT pagamento, COALESCE(SUM(total), 0) AS total
        FROM pedidos
        WHERE caixa_id = ?
        GROUP BY pagamento
        ORDER BY pagamento
    """, (caixa_id,)).fetchall()

    total_vendas = conn.execute("""
        SELECT COALESCE(SUM(total), 0) AS total
        FROM pedidos
        WHERE caixa_id = ?
    """, (caixa_id,)).fetchone()["total"]

    total_reforcos = conn.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM caixa_movimentos
        WHERE caixa_id = ? AND tipo = 'reforco'
    """, (caixa_id,)).fetchone()["total"]

    total_sangrias = conn.execute("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM caixa_movimentos
        WHERE caixa_id = ? AND tipo = 'sangria'
    """, (caixa_id,)).fetchone()["total"]

    valor_inicial = money_float(caixa["valor_inicial"])
    total_vendas = money_float(total_vendas)
    total_reforcos = money_float(total_reforcos)
    total_sangrias = money_float(total_sangrias)

    valor_sistema = valor_inicial + total_vendas + total_reforcos - total_sangrias

    valor_informado = caixa["valor_final_informado"]

    if valor_informado is None:
        valor_informado = valor_sistema

    valor_informado = money_float(valor_informado)

    resumo = {
        "valor_inicial": valor_inicial,
        "total_vendas": total_vendas,
        "total_reforcos": total_reforcos,
        "total_sangrias": total_sangrias,
        "valor_sistema": valor_sistema,
        "valor_informado": valor_informado,
        "diferenca": valor_informado - valor_sistema
    }

    conn.close()

    return render_template(
        "cupom_caixa.html",
        caixa=dict(caixa),
        pedidos=[dict(item) for item in pedidos],
        movimentos=[dict(item) for item in movimentos],
        por_pagamento=[dict(item) for item in por_pagamento],
        resumo=resumo
    )


@app.route("/api/sessao", methods=["GET"])
@login_required_api
def api_sessao():
    return jsonify({
        "usuario": session.get("usuario"),
        "nome": session.get("nome"),
        "nivel": session.get("nivel")
    })


@app.route("/api/pizzas", methods=["GET"])
@login_required_api
def listar_pizzas():
    conn = get_db()
    pizzas = conn.execute("""
        SELECT *
        FROM pizzas
        ORDER BY CAST(codigo AS INTEGER), nome
    """).fetchall()
    conn.close()

    return jsonify([dict(pizza) for pizza in pizzas])


@app.route("/api/pizzas", methods=["POST"])
@login_required_api
def salvar_pizza():
    data = request.json or {}

    pizza_id = data.get("id")
    codigo = data.get("codigo", "").strip()
    nome = data.get("nome", "").strip()
    preco_broto = money_float(data.get("preco_broto"))
    preco_grande = money_float(data.get("preco_grande"))

    if not codigo or not nome:
        return jsonify({"erro": "Código e nome são obrigatórios."}), 400

    if preco_broto <= 0 or preco_grande <= 0:
        return jsonify({"erro": "Os preços precisam ser maiores que zero."}), 400

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
@login_required_api
def excluir_pizza(pizza_id):
    conn = get_db()
    conn.execute("DELETE FROM pizzas WHERE id = ?", (pizza_id,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/produtos", methods=["GET"])
@login_required_api
def listar_produtos():
    conn = get_db()
    produtos = conn.execute("""
        SELECT *
        FROM produtos
        ORDER BY tipo, nome
    """).fetchall()
    conn.close()

    return jsonify([dict(produto) for produto in produtos])


@app.route("/api/produtos", methods=["POST"])
@login_required_api
def salvar_produto():
    data = request.json or {}

    produto_id = data.get("id")
    tipo = data.get("tipo", "").strip()
    categoria = data.get("categoria", "").strip()
    nome = data.get("nome", "").strip()
    preco = money_float(data.get("preco"))

    if not tipo or not nome:
        return jsonify({"erro": "Tipo e nome são obrigatórios."}), 400

    if preco < 0:
        return jsonify({"erro": "Preço não pode ser negativo."}), 400

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
@login_required_api
def excluir_produto(produto_id):
    conn = get_db()
    conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/caixa/status", methods=["GET"])
@login_required_api
def caixa_status():
    conn = get_db()
    caixa = get_caixa_aberto(conn)

    if not caixa:
        conn.close()
        return jsonify({
            "aberto": False,
            "mensagem": "Nenhum caixa aberto."
        })

    valor_sistema = calcular_valor_caixa(conn, caixa["id"])

    movimentos = conn.execute("""
        SELECT *
        FROM caixa_movimentos
        WHERE caixa_id = ?
        ORDER BY id DESC
    """, (caixa["id"],)).fetchall()

    vendas = conn.execute("""
        SELECT COUNT(*) AS qtd, COALESCE(SUM(total), 0) AS total
        FROM pedidos
        WHERE caixa_id = ?
    """, (caixa["id"],)).fetchone()

    por_pagamento = conn.execute("""
        SELECT pagamento, COALESCE(SUM(total), 0) AS total
        FROM pedidos
        WHERE caixa_id = ?
        GROUP BY pagamento
        ORDER BY pagamento
    """, (caixa["id"],)).fetchall()

    caixa_dict = dict(caixa)
    caixa_dict["valor_sistema"] = valor_sistema
    caixa_dict["movimentos"] = [dict(item) for item in movimentos]
    caixa_dict["vendas_qtd"] = vendas["qtd"]
    caixa_dict["vendas_total"] = vendas["total"]
    caixa_dict["por_pagamento"] = [dict(item) for item in por_pagamento]

    conn.close()

    return jsonify({
        "aberto": True,
        "caixa": caixa_dict
    })


@app.route("/api/caixa/abrir", methods=["POST"])
@login_required_api
def abrir_caixa():
    data = request.json or {}
    valor_inicial = money_float(data.get("valor_inicial"))
    observacao = data.get("observacao", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    caixa = get_caixa_aberto(conn)

    if caixa:
        conn.close()
        return jsonify({"erro": "Já existe um caixa aberto."}), 400

    cursor.execute("""
        INSERT INTO caixas
        (status, valor_inicial, observacao, aberto_por, aberto_em)
        VALUES ('aberto', ?, ?, ?, ?)
    """, (
        valor_inicial,
        observacao,
        session.get("usuario"),
        agora_str()
    ))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/caixa/movimento", methods=["POST"])
@login_required_api
def caixa_movimento():
    data = request.json or {}

    tipo = data.get("tipo", "").strip()
    valor = money_float(data.get("valor"))
    descricao = data.get("descricao", "").strip()

    if tipo not in ["sangria", "reforco"]:
        return jsonify({"erro": "Tipo de movimento inválido."}), 400

    if valor <= 0:
        return jsonify({"erro": "Informe um valor maior que zero."}), 400

    if not descricao:
        descricao = "Sangria" if tipo == "sangria" else "Reforço de caixa"

    conn = get_db()
    cursor = conn.cursor()

    caixa = get_caixa_aberto(conn)

    if not caixa:
        conn.close()
        return jsonify({"erro": "Abra o caixa antes de registrar movimentos."}), 400

    cursor.execute("""
        INSERT INTO caixa_movimentos
        (caixa_id, tipo, descricao, valor, criado_em)
        VALUES (?, ?, ?, ?, ?)
    """, (
        caixa["id"],
        tipo,
        descricao,
        valor,
        agora_str()
    ))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/caixa/fechar", methods=["POST"])
@login_required_api
def fechar_caixa():
    data = request.json or {}

    valor_final_informado = money_float(data.get("valor_final_informado"))
    observacao = data.get("observacao", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    caixa = get_caixa_aberto(conn)

    if not caixa:
        conn.close()
        return jsonify({"erro": "Nenhum caixa aberto para fechar."}), 400

    valor_sistema = calcular_valor_caixa(conn, caixa["id"])
    caixa_id = caixa["id"]

    cursor.execute("""
        UPDATE caixas
        SET status = 'fechado',
            valor_final_informado = ?,
            valor_sistema = ?,
            observacao = ?,
            fechado_por = ?,
            fechado_em = ?
        WHERE id = ?
    """, (
        valor_final_informado,
        valor_sistema,
        observacao,
        session.get("usuario"),
        agora_str(),
        caixa_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "caixa_id": caixa_id,
        "valor_sistema": valor_sistema,
        "valor_informado": valor_final_informado,
        "diferenca": valor_final_informado - valor_sistema
    })


@app.route("/api/caixa/historico", methods=["GET"])
@login_required_api
def caixa_historico():
    conn = get_db()

    caixas = conn.execute("""
        SELECT *
        FROM caixas
        ORDER BY id DESC
        LIMIT 30
    """).fetchall()

    resultado = []

    for caixa in caixas:
        item = dict(caixa)

        vendas = conn.execute("""
            SELECT COUNT(*) AS qtd, COALESCE(SUM(total), 0) AS total
            FROM pedidos
            WHERE caixa_id = ?
        """, (caixa["id"],)).fetchone()

        item["vendas_qtd"] = vendas["qtd"]
        item["vendas_total"] = vendas["total"]

        resultado.append(item)

    conn.close()

    return jsonify(resultado)


@app.route("/api/pedidos", methods=["GET"])
@login_required_api
def listar_pedidos():
    conn = get_db()

    pedidos = conn.execute("""
        SELECT *
        FROM pedidos
        ORDER BY id DESC
    """).fetchall()

    resultado = []

    for pedido in pedidos:
        itens = conn.execute("""
            SELECT *
            FROM pedido_itens
            WHERE pedido_id = ?
            ORDER BY id
        """, (pedido["id"],)).fetchall()

        pedido_dict = dict(pedido)
        pedido_dict["itens"] = [dict(item) for item in itens]
        resultado.append(pedido_dict)

    conn.close()

    return jsonify(resultado)


@app.route("/api/pedidos", methods=["POST"])
@login_required_api
def criar_pedido():
    data = request.json or {}

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

    conn = get_db()
    cursor = conn.cursor()

    caixa = get_caixa_aberto(conn)

    if not caixa:
        conn.close()
        return jsonify({"erro": "Abra o caixa antes de finalizar vendas."}), 400

    total = sum(money_float(item.get("total")) for item in itens)
    criado_em = agora_str()

    cursor.execute("""
        INSERT INTO pedidos
        (tipo, cliente, telefone, endereco, mesa, pagamento, total, criado_em, caixa_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tipo,
        cliente,
        telefone,
        endereco,
        mesa,
        pagamento,
        total,
        criado_em,
        caixa["id"]
    ))

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

    return jsonify({
        "ok": True,
        "pedido_id": pedido_id
    })


@app.route("/api/comandas", methods=["GET"])
@login_required_api
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
@login_required_api
def adicionar_comanda():
    data = request.json or {}

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
        cursor.execute("""
            INSERT INTO comandas
            (mesa, status, pagamento, criado_em)
            VALUES (?, 'aberta', ?, ?)
        """, (
            mesa,
            pagamento,
            agora_str()
        ))

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
@login_required_api
def fechar_comanda(comanda_id):
    data = request.json or {}
    pagamento = data.get("pagamento", "")

    conn = get_db()
    cursor = conn.cursor()

    caixa = get_caixa_aberto(conn)

    if not caixa:
        conn.close()
        return jsonify({"erro": "Abra o caixa antes de fechar comandas."}), 400

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
    criado_em = agora_str()

    cursor.execute("""
        INSERT INTO pedidos
        (tipo, cliente, telefone, endereco, mesa, pagamento, total, criado_em, caixa_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Salão",
        f"Mesa {comanda['mesa']}",
        "",
        "",
        comanda["mesa"],
        pagamento or comanda["pagamento"] or "Não informado",
        total,
        criado_em,
        caixa["id"]
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
    """, (
        pagamento or comanda["pagamento"],
        comanda_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "pedido_id": pedido_id
    })


@app.route("/api/relatorio", methods=["GET"])
@login_required_api
def relatorio():
    conn = get_db()

    total_vendas_hoje = conn.execute("""
        SELECT COUNT(*) AS total
        FROM pedidos
        WHERE criado_em BETWEEN ? AND ?
    """, (hoje_inicio(), hoje_fim())).fetchone()["total"]

    faturamento_hoje = conn.execute("""
        SELECT COALESCE(SUM(total), 0) AS total
        FROM pedidos
        WHERE criado_em BETWEEN ? AND ?
    """, (hoje_inicio(), hoje_fim())).fetchone()["total"]

    total_vendas_geral = conn.execute("""
        SELECT COUNT(*) AS total
        FROM pedidos
    """).fetchone()["total"]

    faturamento_geral = conn.execute("""
        SELECT COALESCE(SUM(total), 0) AS total
        FROM pedidos
    """).fetchone()["total"]

    comandas_abertas = conn.execute("""
        SELECT COUNT(*) AS total
        FROM comandas
        WHERE status = 'aberta'
    """).fetchone()["total"]

    por_tipo_hoje = conn.execute("""
        SELECT tipo, COALESCE(SUM(total), 0) AS total
        FROM pedidos
        WHERE criado_em BETWEEN ? AND ?
        GROUP BY tipo
    """, (hoje_inicio(), hoje_fim())).fetchall()

    por_pagamento_hoje = conn.execute("""
        SELECT pagamento, COALESCE(SUM(total), 0) AS total
        FROM pedidos
        WHERE criado_em BETWEEN ? AND ?
        GROUP BY pagamento
    """, (hoje_inicio(), hoje_fim())).fetchall()

    caixa = get_caixa_aberto(conn)
    caixa_info = None

    if caixa:
        caixa_info = dict(caixa)
        caixa_info["valor_sistema"] = calcular_valor_caixa(conn, caixa["id"])

    conn.close()

    return jsonify({
        "total_vendas": total_vendas_hoje,
        "faturamento": faturamento_hoje,
        "total_vendas_geral": total_vendas_geral,
        "faturamento_geral": faturamento_geral,
        "comandas_abertas": comandas_abertas,
        "por_tipo": [dict(item) for item in por_tipo_hoje],
        "por_pagamento": [dict(item) for item in por_pagamento_hoje],
        "caixa_aberto": caixa_info
    })


@app.route("/api/backup", methods=["POST"])
@login_required_api
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
@login_required_page
def baixar_banco():
    return send_file(
        DB_PATH,
        as_attachment=True,
        download_name="pdv_pizzaria.db"
    )


@app.route("/api/sistema/zerar", methods=["POST"])
@login_required_api
def zerar_sistema():
    if session.get("nivel") != "admin":
        return jsonify({"erro": "Apenas administrador pode zerar o sistema."}), 403

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM pedido_itens")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM comanda_itens")
    cursor.execute("DELETE FROM comandas")
    cursor.execute("DELETE FROM caixa_movimentos")
    cursor.execute("DELETE FROM caixas")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM pizzas")

    conn.commit()
    conn.close()

    init_db()

    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )