import os
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///birthdays.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        # TODO: Add the user's entry into the database

        # 1. Obter dados do formulário
        name = request.form.get("name")
        month = request.form.get("month")
        day = request.form.get("day")

        # 2. Inserir os dados no banco de dados
        # (Usamos placeholders ? para segurança contra SQL Injection)
        db.execute("INSERT INTO birthdays (name, month, day) VALUES(?, ?, ?)", name, month, day)

        # 3. Redirecionar o usuário de volta para a página inicial (via GET)
        return redirect("/")

    else:

        # TODO: Display the entries in the database on index.html

        # 1. Consulte o banco de dados para todos os aniversários
        birthdays = db.execute("SELECT * FROM birthdays")

        # 2. Passe a lista de aniversários para o template
        return render_template("index.html", birthdays=birthdays)
