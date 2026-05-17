from flask import Blueprint, jsonify, request

from database import get_db, money_float, agora_str, get_caixa_aberto
from decorators import login_required_api


comandas_bp = Blueprint("comandas", __name__)


@comandas_bp.route("/api/comandas", methods=["GET"])
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


@comandas_bp.route("/api/comandas/adicionar", methods=["POST"])
@login_required_api
def adicionar_comanda():
    data = request.json or {}

    mesa = str(data.get("mesa", "")).strip()
    pagamento = data.get("pagamento", "")
    observacao = data.get("observacao", "").strip()
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

        observacao_antiga = comanda["observacao"] or ""
        observacao_final = observacao_antiga

        if observacao:
            if observacao_antiga:
                observacao_final = observacao_antiga + "\n" + observacao
            else:
                observacao_final = observacao

        cursor.execute("""
            UPDATE comandas
            SET pagamento = ?, observacao = ?
            WHERE id = ?
        """, (pagamento, observacao_final, comanda_id))
    else:
        cursor.execute("""
            INSERT INTO comandas
            (mesa, status, pagamento, observacao, criado_em)
            VALUES (?, 'aberta', ?, ?, ?)
        """, (
            mesa,
            pagamento,
            observacao,
            agora_str()
        ))

        comanda_id = cursor.lastrowid

    itens_ids = []

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

        itens_ids.append(cursor.lastrowid)

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "comanda_id": comanda_id,
        "mesa": mesa,
        "itens_ids": itens_ids
    })


@comandas_bp.route("/api/comandas/item/<int:item_id>", methods=["PUT"])
@login_required_api
def alterar_item_comanda(item_id):
    data = request.json or {}

    quantidade = int(data.get("quantidade", 0))

    if quantidade <= 0:
        return jsonify({"erro": "A quantidade precisa ser maior que zero."}), 400

    conn = get_db()
    cursor = conn.cursor()

    item = cursor.execute("""
        SELECT ci.*, c.status
        FROM comanda_itens ci
        INNER JOIN comandas c ON c.id = ci.comanda_id
        WHERE ci.id = ?
    """, (item_id,)).fetchone()

    if not item:
        conn.close()
        return jsonify({"erro": "Item da comanda não encontrado."}), 404

    if item["status"] != "aberta":
        conn.close()
        return jsonify({"erro": "Não é possível alterar item de comanda fechada."}), 400

    preco_unitario = money_float(item["preco_unitario"])
    total = preco_unitario * quantidade

    cursor.execute("""
        UPDATE comanda_itens
        SET quantidade = ?, total = ?
        WHERE id = ?
    """, (
        quantidade,
        total,
        item_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "item_id": item_id,
        "quantidade": quantidade,
        "preco_unitario": preco_unitario,
        "total": total
    })


@comandas_bp.route("/api/comandas/item/<int:item_id>", methods=["DELETE"])
@login_required_api
def excluir_item_comanda(item_id):
    conn = get_db()
    cursor = conn.cursor()

    item = cursor.execute("""
        SELECT ci.*, c.status, c.id AS comanda_id
        FROM comanda_itens ci
        INNER JOIN comandas c ON c.id = ci.comanda_id
        WHERE ci.id = ?
    """, (item_id,)).fetchone()

    if not item:
        conn.close()
        return jsonify({"erro": "Item da comanda não encontrado."}), 404

    if item["status"] != "aberta":
        conn.close()
        return jsonify({"erro": "Não é possível excluir item de comanda fechada."}), 400

    comanda_id = item["comanda_id"]

    cursor.execute("""
        DELETE FROM comanda_itens
        WHERE id = ?
    """, (item_id,))

    itens_restantes = cursor.execute("""
        SELECT COUNT(*) AS total
        FROM comanda_itens
        WHERE comanda_id = ?
    """, (comanda_id,)).fetchone()["total"]

    if itens_restantes == 0:
        cursor.execute("""
            DELETE FROM comandas
            WHERE id = ?
        """, (comanda_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "item_id": item_id,
        "comanda_id": comanda_id,
        "comanda_removida": itens_restantes == 0
    })


@comandas_bp.route("/api/comandas/<int:comanda_id>/fechar", methods=["POST"])
@login_required_api
def fechar_comanda(comanda_id):
    data = request.json or {}
    pagamento = data.get("pagamento", "")
    observacao_extra = data.get("observacao", "").strip()

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

    observacao_comanda = comanda["observacao"] or ""
    observacao_final = observacao_comanda

    if observacao_extra:
        if observacao_comanda:
            observacao_final = observacao_comanda + "\n" + observacao_extra
        else:
            observacao_final = observacao_extra

    total = sum(float(item["total"]) for item in itens)
    criado_em = agora_str()

    cursor.execute("""
        INSERT INTO pedidos
        (tipo, cliente, telefone, endereco, mesa, pagamento, observacao, total, criado_em, caixa_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Salão",
        f"Mesa {comanda['mesa']}",
        "",
        "",
        comanda["mesa"],
        pagamento or comanda["pagamento"] or "Não informado",
        observacao_final,
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