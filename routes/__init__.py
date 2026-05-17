from routes.pages import pages_bp
from routes.cardapio import cardapio_bp
from routes.caixa import caixa_bp
from routes.pedidos import pedidos_bp
from routes.comandas import comandas_bp
from routes.relatorio import relatorio_bp
from routes.backup import backup_bp


def register_blueprints(app):
    app.register_blueprint(pages_bp)
    app.register_blueprint(cardapio_bp)
    app.register_blueprint(caixa_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(comandas_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(backup_bp)