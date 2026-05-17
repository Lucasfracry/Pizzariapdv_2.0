from flask import Blueprint, jsonify, request, session

from database import (
    get_db,
    money_float,
    agora_str,
    get_caixa_aberto,
    calcular_valor_caixa
)
from decorators import login_required_api


caixa_bp = Blueprint("caixa", __name__)


@caixa_bp.route("/api/caixa/status", methods=["GET"])
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


@caixa_bp.route("/api/caixa/abrir", methods=["POST"])
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


@caixa_bp.route("/api/caixa/movimento", methods=["POST"])
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


@caixa_bp.route("/api/caixa/fechar", methods=["POST"])
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


@caixa_bp.route("/api/caixa/historico", methods=["GET"])
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