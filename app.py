from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

APP_DB = "pdv.db"

app = Flask(__name__)
app.secret_key = "troque-essa-chave-por-uma-bem-grande"

# -----------------------
# DB helpers
# -----------------------
def db():
    conn = sqlite3.connect(APP_DB)
    conn.row_factory = sqlite3.Row
    return conn

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def init_db():
    conn = db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin'
    );
    """)

    # CASH SESSIONS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cash_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opened_at TEXT NOT NULL,
        closed_at TEXT,
        opening_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'open'
    );
    """)

    # PIZZAS (1 pizza com 2 preços)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pizzas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        price_broto REAL NOT NULL DEFAULT 0,
        price_grande REAL NOT NULL DEFAULT 0
    );
    """)

    # PRODUCTS (adicional | borda | bebida)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,                 -- adicional | borda | bebida
        name TEXT NOT NULL,
        price REAL NOT NULL DEFAULT 0,
        drink_type TEXT                     -- refrigerante | vinho | cerveja (apenas se kind=bebida)
    );
    """)

    # SALES + ITEMS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cash_session_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,

        sale_type TEXT NOT NULL,            -- delivery | balcao | mesa
        customer_name TEXT,
        address TEXT,
        phone TEXT,
        table_number TEXT,

        payment_method TEXT NOT NULL,       -- dinheiro | cartao | pix
        total REAL NOT NULL DEFAULT 0,

        FOREIGN KEY(cash_session_id) REFERENCES cash_sessions(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sale_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        qty INTEGER NOT NULL DEFAULT 1,
        unit_price REAL NOT NULL DEFAULT 0,
        total_price REAL NOT NULL DEFAULT 0,
        FOREIGN KEY(sale_id) REFERENCES sales(id)
    );
    """)

    # MESAS ABERTAS (COMANDAS)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS table_tabs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cash_session_id INTEGER NOT NULL,
        table_number TEXT NOT NULL,
        opened_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open',
        FOREIGN KEY(cash_session_id) REFERENCES cash_sessions(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS table_tab_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tab_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        qty INTEGER NOT NULL DEFAULT 1,
        unit_price REAL NOT NULL DEFAULT 0,
        total_price REAL NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY(tab_id) REFERENCES table_tabs(id)
    );
    """)

    # Seed admin
    cur.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users(username, password_hash, role) VALUES(?,?,?)",
            ("admin", generate_password_hash("123"), "admin")
        )

    # Seed "Sem borda"
    cur.execute("SELECT id FROM products WHERE kind='borda' AND name=?", ("Sem borda",))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO products(kind, name, price) VALUES(?,?,?)", ("borda", "Sem borda", 0.0))

    conn.commit()
    conn.close()

def get_open_cash_session():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cash_sessions WHERE status='open' ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

# -----------------------
# Mesa (comanda) helpers
# -----------------------
def get_or_create_tab(cash_session_id: int, table_number: str):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM table_tabs
        WHERE cash_session_id=? AND table_number=? AND status='open'
        LIMIT 1
    """, (cash_session_id, table_number))
    tab = cur.fetchone()

    if not tab:
        cur.execute("""
            INSERT INTO table_tabs(cash_session_id, table_number, opened_at, status)
            VALUES(?,?,?, 'open')
        """, (cash_session_id, table_number, now_str()))
        conn.commit()
        tab_id = cur.lastrowid
        cur.execute("SELECT * FROM table_tabs WHERE id=?", (tab_id,))
        tab = cur.fetchone()

    conn.close()
    return tab

def get_open_tabs_with_items(cash_session_id: int):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM table_tabs
        WHERE cash_session_id=? AND status='open'
        ORDER BY CAST(table_number AS INTEGER), table_number
    """, (cash_session_id,))
    tabs = cur.fetchall()

    enriched = []
    for t in tabs:
        cur.execute("""
            SELECT * FROM table_tab_items
            WHERE tab_id=?
            ORDER BY id DESC
        """, (t["id"],))
        items = cur.fetchall()

        total = 0.0
        for it in items:
            total += float(it["total_price"])

        enriched.append({
            "id": t["id"],
            "table_number": t["table_number"],
            "opened_at": t["opened_at"],
            "items": items,
            "total": round(total, 2)
        })

    conn.close()
    return enriched

# -----------------------
# Carrinho (sessão)
# -----------------------
def cart_get():
    return session.get("cart", [])

def cart_set(items):
    session["cart"] = items

def cart_clear():
    session["cart"] = []

def cart_total(items):
    return round(sum(i["total_price"] for i in items), 2)

def pizza_price_for_size(pizza_row, size: str) -> float:
    size = (size or "").lower()
    if size == "grande":
        return float(pizza_row["price_grande"])
    return float(pizza_row["price_broto"])

# -----------------------
# Auth
# -----------------------
@app.route("/", methods=["GET", "POST"])
def login():
    init_db()
    if request.method == "POST":
        username = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        u = cur.fetchone()
        conn.close()

        if u and check_password_hash(u["password_hash"], senha):
            session["user_id"] = u["id"]
            session["username"] = u["username"]
            session["role"] = u["role"]
            return redirect(url_for("caixa"))

        flash("Usuário ou senha inválidos.")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -----------------------
# Caixa
# -----------------------
@app.route("/caixa")
@login_required
def caixa():
    open_cash = get_open_cash_session()
    return render_template("caixa.html", open_cash=open_cash)

@app.route("/abrir_caixa", methods=["POST"])
@login_required
def abrir_caixa():
    open_cash = get_open_cash_session()
    if open_cash:
        flash("Já existe um caixa aberto.")
        return redirect(url_for("caixa"))

    valor = request.form.get("valor", "0").replace(",", ".")
    try:
        opening_amount = float(valor)
    except:
        opening_amount = 0.0

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO cash_sessions(opened_at, opening_amount, status) VALUES(?,?, 'open')",
        (now_str(), opening_amount)
    )
    conn.commit()
    conn.close()

    flash("Caixa aberto com sucesso.")
    return redirect(url_for("caixa"))

@app.route("/fechar_caixa", methods=["POST"])
@login_required
def fechar_caixa():
    open_cash = get_open_cash_session()
    if not open_cash:
        flash("Não há caixa aberto para fechar.")
        return redirect(url_for("caixa"))

    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE cash_sessions SET closed_at=?, status='closed' WHERE id=?", (now_str(), open_cash["id"]))
    conn.commit()
    conn.close()

    flash("Caixa fechado com sucesso.")
    return redirect(url_for("historico"))

# -----------------------
# Cadastro
# -----------------------
@app.route("/cadastro")
@login_required
def cadastro():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM pizzas ORDER BY name")
    pizzas = cur.fetchall()

    cur.execute("SELECT * FROM products WHERE kind='adicional' ORDER BY name")
    adicionais = cur.fetchall()

    cur.execute("SELECT * FROM products WHERE kind='borda' ORDER BY name")
    bordas = cur.fetchall()

    cur.execute("SELECT * FROM products WHERE kind='bebida' ORDER BY drink_type, name")
    bebidas = cur.fetchall()

    conn.close()
    return render_template("cadastro.html", pizzas=pizzas, adicionais=adicionais, bordas=bordas, bebidas=bebidas)

@app.route("/cadastro/pizza", methods=["POST"])
@login_required
def cadastrar_pizza():
    name = request.form.get("name", "").strip()
    broto = request.form.get("price_broto", "0").replace(",", ".")
    grande = request.form.get("price_grande", "0").replace(",", ".")

    if not name:
        flash("Nome da pizza é obrigatório.")
        return redirect(url_for("cadastro"))

    try:
        broto_f = float(broto)
    except:
        broto_f = 0.0

    try:
        grande_f = float(grande)
    except:
        grande_f = 0.0

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM pizzas WHERE name=?", (name,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE pizzas SET price_broto=?, price_grande=? WHERE id=?", (broto_f, grande_f, row["id"]))
    else:
        cur.execute("INSERT INTO pizzas(name, price_broto, price_grande) VALUES(?,?,?)", (name, broto_f, grande_f))

    conn.commit()
    conn.close()
    flash("Pizza salva (Broto e Grande).")
    return redirect(url_for("cadastro"))

@app.route("/cadastro/adicional", methods=["POST"])
@login_required
def cadastrar_adicional():
    name = request.form.get("name", "").strip()
    price = request.form.get("price", "0").replace(",", ".")
    if not name:
        flash("Nome do adicional é obrigatório.")
        return redirect(url_for("cadastro"))
    try:
        price_f = float(price)
    except:
        price_f = 0.0
    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO products(kind, name, price) VALUES('adicional', ?, ?)", (name, price_f))
    conn.commit()
    conn.close()
    flash("Adicional cadastrado.")
    return redirect(url_for("cadastro"))

@app.route("/cadastro/borda", methods=["POST"])
@login_required
def cadastrar_borda():
    name = request.form.get("name", "").strip()
    price = request.form.get("price", "0").replace(",", ".")
    if not name:
        flash("Nome da borda é obrigatório.")
        return redirect(url_for("cadastro"))
    try:
        price_f = float(price)
    except:
        price_f = 0.0
    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO products(kind, name, price) VALUES('borda', ?, ?)", (name, price_f))
    conn.commit()
    conn.close()
    flash("Borda cadastrada.")
    return redirect(url_for("cadastro"))

@app.route("/cadastro/bebida", methods=["POST"])
@login_required
def cadastrar_bebida():
    name = request.form.get("name", "").strip()
    drink_type = request.form.get("drink_type", "refrigerante").strip().lower()
    price = request.form.get("price", "0").replace(",", ".")
    if not name:
        flash("Nome da bebida é obrigatório.")
        return redirect(url_for("cadastro"))
    if drink_type not in ("refrigerante", "vinho", "cerveja"):
        drink_type = "refrigerante"
    try:
        price_f = float(price)
    except:
        price_f = 0.0
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products(kind, name, price, drink_type) VALUES('bebida', ?, ?, ?)",
        (name, price_f, drink_type)
    )
    conn.commit()
    conn.close()
    flash("Bebida cadastrada.")
    return redirect(url_for("cadastro"))

@app.route("/pizza/<int:pid>/delete", methods=["POST"])
@login_required
def delete_pizza(pid: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM pizzas WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    flash("Pizza removida.")
    return redirect(url_for("cadastro"))

@app.route("/produto/<int:pid>/delete", methods=["POST"])
@login_required
def delete_product(pid: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    flash("Produto removido.")
    return redirect(url_for("cadastro"))

# -----------------------
# PDV
# -----------------------
@app.route("/pdv")
@login_required
def pdv():
    open_cash = get_open_cash_session()

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM pizzas ORDER BY name")
    pizzas = cur.fetchall()

    cur.execute("SELECT * FROM products WHERE kind='bebida' ORDER BY drink_type, name")
    bebidas = cur.fetchall()

    cur.execute("SELECT * FROM products WHERE kind='borda' ORDER BY name")
    bordas = cur.fetchall()

    cur.execute("SELECT * FROM products WHERE kind='adicional' ORDER BY name")
    adicionais = cur.fetchall()

    conn.close()

    items = cart_get()
    total = cart_total(items)

    open_tabs = []
    if open_cash:
        open_tabs = get_open_tabs_with_items(open_cash["id"])

    return render_template(
        "pdv.html",
        open_cash=open_cash,
        pizzas=pizzas,
        bebidas=bebidas,
        bordas=bordas,
        adicionais=adicionais,
        cart_items=items,
        cart_total=total,
        open_tabs=open_tabs
    )

@app.route("/pdv/add_pizza", methods=["POST"])
@login_required
def pdv_add_pizza():
    if not get_open_cash_session():
        flash("Abra o caixa para usar o PDV.")
        return redirect(url_for("pdv"))

    mode = request.form.get("mode", "inteira")  # inteira | meio
    size = request.form.get("size", "broto")    # broto | grande

    pizza_id_1 = request.form.get("pizza_id_1")
    pizza_id_2 = request.form.get("pizza_id_2")  # só no meio a meio

    borda_id = request.form.get("borda_id")
    adicionais_ids = request.form.getlist("adicionais_ids")
    qty_raw = request.form.get("qty", "1")

    try:
        qty = int(qty_raw)
        if qty < 1:
            qty = 1
    except:
        qty = 1

    if size not in ("broto", "grande"):
        size = "broto"

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM pizzas WHERE id=?", (pizza_id_1,))
    p1 = cur.fetchone()
    if not p1:
        conn.close()
        flash("Pizza inválida.")
        return redirect(url_for("pdv"))

    p2 = None
    if mode == "meio":
        cur.execute("SELECT * FROM pizzas WHERE id=?", (pizza_id_2,))
        p2 = cur.fetchone()
        if not p2:
            conn.close()
            flash("Selecione a 2ª metade.")
            return redirect(url_for("pdv"))

    cur.execute("SELECT * FROM products WHERE id=? AND kind='borda'", (borda_id,))
    borda = cur.fetchone()
    if not borda:
        cur.execute("SELECT * FROM products WHERE kind='borda' AND name='Sem borda' LIMIT 1")
        borda = cur.fetchone()

    adicionais = []
    if adicionais_ids:
        qmarks = ",".join(["?"] * len(adicionais_ids))
        cur.execute(f"SELECT * FROM products WHERE kind='adicional' AND id IN ({qmarks})", tuple(adicionais_ids))
        adicionais = cur.fetchall()

    conn.close()

    base_1 = pizza_price_for_size(p1, size)
    if mode == "meio":
        base_2 = pizza_price_for_size(p2, size)
        base_price = max(base_1, base_2)   # regra: cobra o maior sabor
    else:
        base_price = base_1

    borda_price = float(borda["price"]) if borda else 0.0
    adicionais_price = sum(float(a["price"]) for a in adicionais)

    unit_price = round(base_price + borda_price + adicionais_price, 2)
    total_price = round(unit_price * qty, 2)

    if mode == "meio":
        desc_main = f"Pizza Meio a Meio ({size}): {p1['name']} + {p2['name']}"
    else:
        desc_main = f"Pizza ({size}): {p1['name']}"

    desc_parts = [desc_main]
    if borda and borda["name"] != "Sem borda":
        desc_parts.append(f"Borda: {borda['name']}")
    if adicionais:
        desc_parts.append("Adicionais: " + ", ".join(a["name"] for a in adicionais))

    description = " | ".join(desc_parts)

    items = cart_get()
    items.append({
        "description": description,
        "qty": qty,
        "unit_price": unit_price,
        "total_price": total_price
    })
    cart_set(items)

    flash("Pizza adicionada ao pedido.")
    return redirect(url_for("pdv"))

@app.route("/pdv/add_bebida", methods=["POST"])
@login_required
def pdv_add_bebida():
    if not get_open_cash_session():
        flash("Abra o caixa para usar o PDV.")
        return redirect(url_for("pdv"))

    bebida_id = request.form.get("bebida_id")
    qty_raw = request.form.get("qty", "1")
    try:
        qty = int(qty_raw)
        if qty < 1:
            qty = 1
    except:
        qty = 1

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id=? AND kind='bebida'", (bebida_id,))
    bebida = cur.fetchone()
    conn.close()

    if not bebida:
        flash("Bebida inválida.")
        return redirect(url_for("pdv"))

    unit_price = float(bebida["price"])
    total_price = round(unit_price * qty, 2)
    description = f"Bebida: {bebida['name']} ({bebida['drink_type']})"

    items = cart_get()
    items.append({
        "description": description,
        "qty": qty,
        "unit_price": unit_price,
        "total_price": total_price
    })
    cart_set(items)

    flash("Bebida adicionada ao pedido.")
    return redirect(url_for("pdv"))

@app.route("/pdv/remove_item/<int:index>", methods=["POST"])
@login_required
def pdv_remove_item(index: int):
    items = cart_get()
    if 0 <= index < len(items):
        items.pop(index)
        cart_set(items)
        flash("Item removido.")
    return redirect(url_for("pdv"))

@app.route("/pdv/cancelar", methods=["POST"])
@login_required
def pdv_cancelar():
    cart_clear()
    flash("Pedido cancelado.")
    return redirect(url_for("pdv"))

@app.route("/pdv/finalizar", methods=["POST"])
@login_required
def pdv_finalizar():
    open_cash = get_open_cash_session()
    if not open_cash:
        flash("Abra o caixa para finalizar.")
        return redirect(url_for("pdv"))

    sale_type = request.form.get("sale_type", "balcao").lower()
    payment_method = request.form.get("payment_method", "dinheiro").lower()

    customer_name = request.form.get("customer_name", "").strip()
    address = request.form.get("address", "").strip()
    phone = request.form.get("phone", "").strip()
    table_number = request.form.get("table_number", "").strip()

    if payment_method not in ("dinheiro", "cartao", "pix"):
        payment_method = "dinheiro"

    items = cart_get()

    # DELIVERY
    if sale_type == "delivery":
        if not (customer_name and address and phone):
            flash("Delivery exige Nome, Endereço e Telefone.")
            return redirect(url_for("pdv"))
        if not items:
            flash("Carrinho vazio.")
            return redirect(url_for("pdv"))

        total = cart_total(items)

        conn = db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sales(
                cash_session_id, created_at,
                sale_type, customer_name, address, phone, table_number,
                payment_method, total
            ) VALUES(?,?,?,?,?,?,?,?,?)
        """, (
            open_cash["id"], now_str(),
            "delivery", customer_name, address, phone, "",
            payment_method, total
        ))
        sale_id = cur.lastrowid

        for it in items:
            cur.execute("""
                INSERT INTO sale_items(sale_id, description, qty, unit_price, total_price)
                VALUES(?,?,?,?,?)
            """, (sale_id, it["description"], it["qty"], it["unit_price"], it["total_price"]))

        conn.commit()
        conn.close()

        cart_clear()
        flash(f"Delivery finalizado! Total R$ {total:.2f}")
        return redirect(url_for("pdv"))

    # BALCÃO
    if sale_type == "balcao":
        if not customer_name:
            flash("Balcão exige Nome.")
            return redirect(url_for("pdv"))
        if not items:
            flash("Carrinho vazio.")
            return redirect(url_for("pdv"))

        total = cart_total(items)

        conn = db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sales(
                cash_session_id, created_at,
                sale_type, customer_name, address, phone, table_number,
                payment_method, total
            ) VALUES(?,?,?,?,?,?,?,?,?)
        """, (
            open_cash["id"], now_str(),
            "balcao", customer_name, "", "", "",
            payment_method, total
        ))
        sale_id = cur.lastrowid

        for it in items:
            cur.execute("""
                INSERT INTO sale_items(sale_id, description, qty, unit_price, total_price)
                VALUES(?,?,?,?,?)
            """, (sale_id, it["description"], it["qty"], it["unit_price"], it["total_price"]))

        conn.commit()
        conn.close()

        cart_clear()
        flash(f"Balcão finalizado! Total R$ {total:.2f}")
        return redirect(url_for("pdv"))

    # MESA (COMANDA)
    if sale_type == "mesa":
        if not table_number:
            flash("Mesa exige Número da mesa.")
            return redirect(url_for("pdv"))

        mesa_action = request.form.get("mesa_action", "add")  # add | close

        # ADD: joga carrinho na mesa
        if mesa_action == "add":
            if not items:
                flash("Carrinho vazio (nada para adicionar na mesa).")
                return redirect(url_for("pdv"))

            tab = get_or_create_tab(open_cash["id"], table_number)

            conn = db()
            cur = conn.cursor()
            for it in items:
                cur.execute("""
                    INSERT INTO table_tab_items(tab_id, description, qty, unit_price, total_price, created_at)
                    VALUES(?,?,?,?,?,?)
                """, (tab["id"], it["description"], it["qty"], it["unit_price"], it["total_price"], now_str()))
            conn.commit()
            conn.close()

            cart_clear()
            flash(f"Itens adicionados na Mesa {table_number}.")
            return redirect(url_for("pdv"))

        # CLOSE: fecha mesa e gera venda
        if mesa_action == "close":
            conn = db()
            cur = conn.cursor()

            cur.execute("""
                SELECT * FROM table_tabs
                WHERE cash_session_id=? AND table_number=? AND status='open'
                LIMIT 1
            """, (open_cash["id"], table_number))
            tab = cur.fetchone()

            if not tab:
                conn.close()
                flash(f"Não existe comanda aberta na Mesa {table_number}.")
                return redirect(url_for("pdv"))

            # adiciona carrinho também se tiver
            if items:
                for it in items:
                    cur.execute("""
                        INSERT INTO table_tab_items(tab_id, description, qty, unit_price, total_price, created_at)
                        VALUES(?,?,?,?,?,?)
                    """, (tab["id"], it["description"], it["qty"], it["unit_price"], it["total_price"], now_str()))
                cart_clear()

            cur.execute("SELECT * FROM table_tab_items WHERE tab_id=?", (tab["id"],))
            tab_items = cur.fetchall()

            if not tab_items:
                conn.close()
                flash("Mesa sem itens para fechar.")
                return redirect(url_for("pdv"))

            total = round(sum(float(x["total_price"]) for x in tab_items), 2)

            cur.execute("""
                INSERT INTO sales(
                    cash_session_id, created_at,
                    sale_type, customer_name, address, phone, table_number,
                    payment_method, total
                ) VALUES(?,?,?,?,?,?,?,?,?)
            """, (
                open_cash["id"], now_str(),
                "mesa", "", "", "", table_number,
                payment_method, total
            ))
            sale_id = cur.lastrowid

            for it in tab_items:
                cur.execute("""
                    INSERT INTO sale_items(sale_id, description, qty, unit_price, total_price)
                    VALUES(?,?,?,?,?)
                """, (sale_id, it["description"], it["qty"], it["unit_price"], it["total_price"]))

            # fecha tab e limpa itens
            cur.execute("UPDATE table_tabs SET status='closed' WHERE id=?", (tab["id"],))
            cur.execute("DELETE FROM table_tab_items WHERE tab_id=?", (tab["id"],))

            conn.commit()
            conn.close()

            flash(f"Mesa {table_number} fechada! Total R$ {total:.2f}")
            return redirect(url_for("pdv"))

    flash("Tipo de venda inválido.")
    return redirect(url_for("pdv"))

# -----------------------
# Histórico do Caixa
# -----------------------
@app.route("/historico")
@login_required
def historico():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM cash_sessions ORDER BY id DESC")
    sessions = cur.fetchall()

    enriched = []
    for cs in sessions:
        cs_id = cs["id"]
        cur.execute("""
            SELECT payment_method, COALESCE(SUM(total),0) as total
            FROM sales
            WHERE cash_session_id=?
            GROUP BY payment_method
        """, (cs_id,))
        rows = cur.fetchall()

        totals = {"dinheiro": 0.0, "cartao": 0.0, "pix": 0.0}
        for r in rows:
            totals[r["payment_method"]] = float(r["total"])

        total_geral = round(totals["dinheiro"] + totals["cartao"] + totals["pix"], 2)

        enriched.append({
            "id": cs_id,
            "opened_at": cs["opened_at"],
            "closed_at": cs["closed_at"],
            "opening_amount": float(cs["opening_amount"]),
            "status": cs["status"],
            "dinheiro": round(totals["dinheiro"], 2),
            "cartao": round(totals["cartao"], 2),
            "pix": round(totals["pix"], 2),
            "total_geral": total_geral
        })

    conn.close()
    return render_template("historico.html", sessions=enriched)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)