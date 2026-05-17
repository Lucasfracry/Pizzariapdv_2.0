from flask import Blueprint, jsonify, request, session

from database import get_db, money_float
from decorators import login_required_api


cardapio_bp = Blueprint("cardapio", __name__)


@cardapio_bp.route("/api/sessao", methods=["GET"])
@login_required_api
def api_sessao():
    return jsonify({
        "usuario": session.get("usuario"),
        "nome": session.get("nome"),
        "nivel": session.get("nivel")
    })


@cardapio_bp.route("/api/pizzas", methods=["GET"])
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


@cardapio_bp.route("/api/pizzas", methods=["POST"])
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


@cardapio_bp.route("/api/pizzas/<int:pizza_id>", methods=["DELETE"])
@login_required_api
def excluir_pizza(pizza_id):
    conn = get_db()
    conn.execute("DELETE FROM pizzas WHERE id = ?", (pizza_id,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@cardapio_bp.route("/api/produtos", methods=["GET"])
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


@cardapio_bp.route("/api/produtos", methods=["POST"])
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


@cardapio_bp.route("/api/produtos/<int:produto_id>", methods=["DELETE"])
@login_required_api
def excluir_produto(produto_id):
    conn = get_db()
    conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})