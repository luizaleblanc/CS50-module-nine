import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    user_id = session["user_id"]

    # 1. Obter o portfólio do usuário (agrupando ações)
    portfolio = db.execute(
        "SELECT symbol, SUM(shares) AS total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0",
        user_id
    )

    # 2. Obter o dinheiro (cash) atual do usuário
    cash_rows = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    cash = cash_rows[0]["cash"]

    # 3. Preparar o total geral (começa com o dinheiro)
    grand_total = cash

    # 4. Iterar sobre o portfólio para adicionar preços atuais e valores totais
    for stock in portfolio:
        current_data = lookup(stock["symbol"])
        # Handle possible lookup failure (e.g., if API is down or mock data is missing)
        if current_data:
            stock["price"] = current_data["price"]
            stock["total_value"] = stock["total_shares"] * stock["price"]
            grand_total += stock["total_value"]
        else:
            # Handle cases where lookup might fail (though less likely with our mock/Alpha Vantage)
            stock["price"] = 0.0
            stock["total_value"] = 0.0


    # 5. Renderizar o template com todos os dados
    return render_template("index.html", stocks=portfolio, cash=cash, grand_total=grand_total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # Se o usuário enviou o formulário (POST)
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares_str = request.form.get("shares")

        # 1. Validação: Checa se os campos foram preenchidos
        if not symbol:
            return apology("must provide symbol", 400)
        elif not shares_str:
            return apology("must provide number of shares", 400)

        # 2. Validação: Checa se 'shares' é um número inteiro positivo
        if not shares_str.isdigit() or int(shares_str) <= 0:
            return apology("shares must be a positive integer", 400)

        shares = int(shares_str)

        # 3. Validação: Chama o lookup
        stock = lookup(symbol)
        if stock is None:
            return apology("invalid symbol", 400)

        # 4. Lógica de Compra:
        price = stock["price"]
        cost = price * shares

        # Pega o dinheiro do usuário no banco de dados
        user_cash_rows = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        user_cash = user_cash_rows[0]["cash"]

        # 5. Validação: Checa se o usuário pode pagar
        if user_cash < cost:
            return apology("can't afford", 400)

        # 6. Executa a transação
        # Subtrai o dinheiro do usuário
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", cost, session["user_id"])
        
        # Adiciona a compra na tabela de transações
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
                   session["user_id"], stock["symbol"], shares, price)

        # Feedback e redirecionamento
        flash("Bought!")
        return redirect("/")

    # Se o usuário acessou a rota via GET (clicando no link)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    user_id = session["user_id"]

    # 1. Busca todas as transações do usuário, ordenadas da mais recente para a mais antiga
    transactions = db.execute(
        "SELECT symbol, shares, price, timestamp FROM transactions WHERE user_id = ? ORDER BY timestamp DESC",
        user_id
    )

    # 2. Renderiza a página de histórico, passando os dados das transações
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # Se o usuário enviou o formulário (POST)
    if request.method == "POST":
        symbol = request.form.get("symbol")

        # 1. Validação: Checa se o símbolo foi enviado
        if not symbol:
            return apology("must provide symbol", 400)

        # 2. Chama a função lookup (que editamos)
        stock = lookup(symbol)

        # 3. Validação: Checa se o lookup retornou um símbolo válido
        if stock is None:
            return apology("invalid symbol", 400)

        # 4. Sucesso: Mostra a página 'quoted.html' com os dados
        return render_template("quoted.html", stock=stock)

    # Se o usuário acessou a rota via GET (clicando no link)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Limpa a sessão antiga
    session.clear()

    # Se o método for POST (usuário enviou o formulário)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # 1. Validação: Checa se os campos estão preenchidos
        if not username:
            return apology("must provide username", 400)
        elif not password:
            return apology("must provide password", 400)
        elif not confirmation:
            return apology("must confirm password", 400)

        # 2. Validação: Checa se as senhas batem
        if password != confirmation:
            return apology("passwords do not match", 400)

        # 3. Gera o hash da senha
        hash = generate_password_hash(password)

        # 4. Tenta inserir o usuário no banco de dados
        try:
            # db.execute vai falhar se o username já existir (por causa do UNIQUE INDEX)
            new_user_id = db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
        except ValueError:
            # Se falhar, é porque o username já existe
            return apology("username already exists", 400)

        # 5. Loga o usuário automaticamente após o registro
        session["user_id"] = new_user_id

        # Redireciona para a página inicial
        flash("Registered successfully!") # Feedback opcional
        return redirect("/")

    # Se o método for GET (usuário apenas clicou no link para registrar)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    
    user_id = session["user_id"]

    # Se o usuário enviou o formulário (POST)
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares_to_sell_str = request.form.get("shares")

        # 1. Validação: Checa se os campos foram preenchidos
        if not symbol:
            return apology("must provide symbol", 400)
        elif not shares_to_sell_str:
            return apology("must provide number of shares", 400)

        # 2. Validação: Checa se 'shares' é um número inteiro positivo
        if not shares_to_sell_str.isdigit() or int(shares_to_sell_str) <= 0:
            return apology("shares must be a positive integer", 400)

        shares_to_sell = int(shares_to_sell_str)

        # 3. Validação: Checa se o usuário possui ações suficientes
        rows = db.execute(
            "SELECT SUM(shares) AS total_shares FROM transactions WHERE user_id = ? AND symbol = ? GROUP BY symbol",
            user_id, symbol
        )
        
        if len(rows) != 1:
            return apology("symbol not owned", 400)

        shares_owned = rows[0]["total_shares"]
        
        if shares_to_sell > shares_owned:
            return apology("not enough shares", 400)

        # 4. Executa a Venda
        stock = lookup(symbol)
        sale_value = shares_to_sell * stock["price"]

        # Adiciona o dinheiro da venda ao usuário
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", sale_value, user_id)
        
        # Registra a transação (com número negativo de ações)
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
                   user_id, stock["symbol"], -shares_to_sell, stock["price"])

        # Feedback e redirecionamento
        flash("Sold!")
        return redirect("/")

    # Se o usuário acessou a rota via GET (clicando no link)
    else:
        # Busca quais ações o usuário possui para popular o dropdown
        stocks_owned = db.execute(
            "SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0",
            user_id
        )
        # Renderiza o template de venda, passando a lista de ações
        return render_template("sell.html", stocks=stocks_owned)