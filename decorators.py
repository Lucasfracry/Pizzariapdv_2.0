from functools import wraps

from flask import jsonify, redirect, session, url_for


def login_required_page(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return redirect(url_for("pages.login"))
        return func(*args, **kwargs)
    return wrapper


def login_required_api(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return jsonify({"erro": "Sessão expirada. Faça login novamente."}), 401
        return func(*args, **kwargs)
    return wrapper