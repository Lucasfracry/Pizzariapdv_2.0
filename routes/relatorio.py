from flask import Blueprint, jsonify

from database import (
    get_db,
    hoje_inicio,
    hoje_fim,
    get_caixa_aberto,
    calcular_valor_caixa
)
from decorators import login_required_api


relatorio_bp = Blueprint("relatorio", __name__)


@relatorio_bp.route("/api/relatorio", methods=["GET"])
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