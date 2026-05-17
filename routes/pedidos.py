from flask import Blueprint, jsonify, request

from database import get_db, money_float, agora_str, get_caixa_aberto
from decorators import login_required_api


pedidos_bp = Blueprint("pedidos", __name__)


@pedidos_bp.route("/api/pedidos", methods=["GET"])
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


@pedidos_bp.route("/api/pedidos", methods=["POST"])
@login_required_api
def criar_pedido():
    data = request.json or {}

    tipo = data.get("tipo")
    cliente = data.get("cliente", "")
    telefone = data.get("telefone", "")
    endereco = data.get("endereco", "")
    mesa = data.get("mesa", "")
    pagamento = data.get("pagamento", "")
    observacao = data.get("observacao", "")
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
        (tipo, cliente, telefone, endereco, mesa, pagamento, observacao, total, criado_em, caixa_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tipo,
        cliente,
        telefone,
        endereco,
        mesa,
        pagamento,
        observacao,
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