from flask import Blueprint, render_template, request, redirect, url_for, session, send_from_directory

from config import USERS, BASE_DIR
from database import get_db, money_float, agora_str
from decorators import login_required_page


pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        BASE_DIR,
        "pizza.ico",
        mimetype="image/x-icon"
    )


@pages_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("usuario"):
            return redirect(url_for("pages.index"))
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

    return redirect(url_for("pages.index"))


@pages_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("pages.login"))


@pages_bp.route("/")
@login_required_page
def index():
    return render_template(
        "index.html",
        usuario=session.get("nome"),
        nivel=session.get("nivel")
    )


@pages_bp.route("/cupom/<int:pedido_id>")
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


@pages_bp.route("/cozinha/comanda/<int:comanda_id>")
@login_required_page
def cupom_cozinha_comanda(comanda_id):
    itens_param = request.args.get("itens", "").strip()
    observacao_envio = request.args.get("observacao", "").strip()

    item_ids = []

    if itens_param:
        for parte in itens_param.split(","):
            parte = parte.strip()

            if parte.isdigit():
                item_ids.append(int(parte))

    conn = get_db()

    comanda = conn.execute("""
        SELECT *
        FROM comandas
        WHERE id = ?
    """, (comanda_id,)).fetchone()

    if not comanda:
        conn.close()
        return "Comanda não encontrada.", 404

    if item_ids:
        placeholders = ",".join("?" for _ in item_ids)

        itens = conn.execute(f"""
            SELECT *
            FROM comanda_itens
            WHERE comanda_id = ?
              AND id IN ({placeholders})
            ORDER BY id
        """, [comanda_id] + item_ids).fetchall()
    else:
        itens = conn.execute("""
            SELECT *
            FROM comanda_itens
            WHERE comanda_id = ?
            ORDER BY id DESC
            LIMIT 10
        """, (comanda_id,)).fetchall()

        itens = list(reversed(itens))

    conn.close()

    return render_template(
        "cupom_cozinha.html",
        comanda=dict(comanda),
        itens=[dict(item) for item in itens],
        observacao_envio=observacao_envio,
        impresso_em=agora_str()
    )


@pages_bp.route("/caixa/cupom/<int:caixa_id>")
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