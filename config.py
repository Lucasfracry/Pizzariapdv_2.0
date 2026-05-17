import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pdv_pizzaria.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

SECRET_KEY = "troque-essa-chave-depois-pdv-pizzaria"

USERS = {
    "admin": {
        "senha": "1234",
        "nome": "Administrador",
        "nivel": "admin"
    },
    "operador": {
        "senha": "1234",
        "nome": "Operador",
        "nivel": "operador"
    }
}