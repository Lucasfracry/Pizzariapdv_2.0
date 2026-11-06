from flask import Blueprint, jsonify, request

from database import (
    get_db,
    money_float,
    agora_str,
    hoje_inicio,
    hoje_fim,
    get_caixa_aberto
)
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

    if not pagamento:
        return jsonify({"erro": "Forma de pagamento é obrigatória."}), 400

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

    status = data.get("status", "em_preparo")
    if status not in ["em_preparo", "pronto", "em_entrega", "finalizado", "cancelado"]:
        status = "em_preparo"

    pago = 1 if data.get("pago") else 0

    cursor.execute("""
        INSERT INTO pedidos
        (tipo, cliente, telefone, endereco, mesa, pagamento, observacao, total, criado_em, caixa_id, status, pago)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        caixa["id"],
        status,
        pago
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


@pedidos_bp.route("/api/pedidos/<int:pedido_id>", methods=["GET"])
@login_required_api
def obter_pedido(pedido_id):
    conn = get_db()
    pedido = conn.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()

    if not pedido:
        conn.close()
        return jsonify({"erro": "Pedido não encontrado."}), 404

    itens = conn.execute("""
        SELECT *
        FROM pedido_itens
        WHERE pedido_id = ?
        ORDER BY id
    """, (pedido_id,)).fetchall()

    pedido_dict = dict(pedido)
    pedido_dict["itens"] = [dict(item) for item in itens]
    conn.close()

    return jsonify(pedido_dict)


@pedidos_bp.route("/api/pedidos/<int:pedido_id>", methods=["DELETE"])
@login_required_api
def excluir_pedido(pedido_id):
    conn = get_db()
    cursor = conn.cursor()

    pedido = cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if not pedido:
        conn.close()
        return jsonify({"erro": "Pedido não encontrado."}), 404

    cursor.execute("DELETE FROM pedido_itens WHERE pedido_id = ?", (pedido_id,))
    cursor.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))

    conn.commit()
    conn.close()

    return jsonify({"ok": True, "mensagem": f"Pedido #{pedido_id} excluído com sucesso."})


@pedidos_bp.route("/api/pedidos/<int:pedido_id>", methods=["PUT"])
@login_required_api
def alterar_pedido(pedido_id):
    data = request.json or {}

    conn = get_db()
    cursor = conn.cursor()

    pedido = cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if not pedido:
        conn.close()
        return jsonify({"erro": "Pedido não encontrado."}), 404

    cliente = data.get("cliente", pedido["cliente"])
    telefone = data.get("telefone", pedido["telefone"])
    endereco = data.get("endereco", pedido["endereco"])
    mesa = data.get("mesa", pedido["mesa"])
    pagamento = data.get("pagamento", pedido["pagamento"])
    observacao = data.get("observacao", pedido["observacao"])
    status = data.get("status", pedido["status"] if "status" in pedido.keys() else "em_preparo")
    pago = 1 if data.get("pago", pedido["pago"] if "pago" in pedido.keys() else 0) else 0

    if not pagamento:
        conn.close()
        return jsonify({"erro": "Forma de pagamento não pode ficar em branco."}), 400

    itens = data.get("itens")

    if itens is not None:
        if not itens:
            conn.close()
            return jsonify({"erro": "O pedido deve ter pelo menos um item."}), 400

        total = sum(money_float(item.get("total", money_float(item.get("preco_unitario", 0)) * int(item.get("quantidade", 1)))) for item in itens)

        cursor.execute("""
            UPDATE pedidos
            SET cliente = ?, telefone = ?, endereco = ?, mesa = ?, pagamento = ?, observacao = ?, total = ?, status = ?, pago = ?
            WHERE id = ?
        """, (cliente, telefone, endereco, mesa, pagamento, observacao, total, status, pago, pedido_id))

        cursor.execute("DELETE FROM pedido_itens WHERE pedido_id = ?", (pedido_id,))
        for item in itens:
            quantidade = int(item.get("quantidade", 1))
            preco_unitario = money_float(item.get("preco_unitario", 0))
            item_total = money_float(item.get("total", preco_unitario * quantidade))
            cursor.execute("""
                INSERT INTO pedido_itens
                (pedido_id, descricao, quantidade, preco_unitario, total)
                VALUES (?, ?, ?, ?, ?)
            """, (
                pedido_id,
                item.get("descricao"),
                quantidade,
                preco_unitario,
                item_total
            ))
    else:
        cursor.execute("""
            UPDATE pedidos
            SET cliente = ?, telefone = ?, endereco = ?, mesa = ?, pagamento = ?, observacao = ?, status = ?, pago = ?
            WHERE id = ?
        """, (cliente, telefone, endereco, mesa, pagamento, observacao, status, pago, pedido_id))

    conn.commit()
    conn.close()

    return jsonify({"ok": True, "pedido_id": pedido_id})


@pedidos_bp.route("/api/pedidos/<int:pedido_id>/status", methods=["PATCH", "POST"])
@login_required_api
def alterar_status_pedido(pedido_id):
    data = request.json or {}
    novo_status = (data.get("status") or "").strip()

    status_permitidos = ["em_preparo", "pronto", "em_entrega", "finalizado", "cancelado"]
    if novo_status not in status_permitidos:
        return jsonify({"erro": f"Status inválido. Escolha entre: {', '.join(status_permitidos)}"}), 400

    conn = get_db()
    cursor = conn.cursor()

    pedido = cursor.execute("SELECT id FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if not pedido:
        conn.close()
        return jsonify({"erro": "Pedido não encontrado."}), 404

    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "pedido_id": pedido_id, "status": novo_status})


@pedidos_bp.route("/api/pedidos/<int:pedido_id>/pago", methods=["PATCH", "POST"])
@login_required_api
def alterar_pago_pedido(pedido_id):
    data = request.json or {}
    pago = 1 if data.get("pago") else 0

    conn = get_db()
    cursor = conn.cursor()

    pedido = cursor.execute("SELECT id FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if not pedido:
        conn.close()
        return jsonify({"erro": "Pedido não encontrado."}), 404

    cursor.execute("UPDATE pedidos SET pago = ? WHERE id = ?", (pago, pedido_id))
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "pedido_id": pedido_id, "pago": pago})


@pedidos_bp.route("/api/fila", methods=["GET"])
@login_required_api
def listar_fila():
    conn = get_db()

    # Pedidos ativos na fila feitos HOJE, por ordem de chegada (mais antigos primeiro: ASC)
    pedidos = conn.execute("""
        SELECT *
        FROM pedidos
        WHERE status IN ('em_preparo', 'pronto', 'em_entrega')
          AND criado_em BETWEEN ? AND ?
        ORDER BY id ASC
    """, (hoje_inicio(), hoje_fim())).fetchall()

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

