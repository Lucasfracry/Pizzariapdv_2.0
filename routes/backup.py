import os
import shutil
from datetime import datetime

from flask import Blueprint, jsonify, send_file, session

from config import BACKUP_DIR, DB_PATH
from database import get_db, init_db
from decorators import login_required_api, login_required_page


backup_bp = Blueprint("backup", __name__)


@backup_bp.route("/api/backup", methods=["POST"])
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


@backup_bp.route("/api/backup/download", methods=["GET"])
@login_required_page
def baixar_banco():
    return send_file(
        DB_PATH,
        as_attachment=True,
        download_name="pdv_pizzaria.db"
    )


@backup_bp.route("/api/sistema/zerar", methods=["POST"])
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