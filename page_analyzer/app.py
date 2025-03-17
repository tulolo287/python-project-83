import datetime
import os

import psycopg2
import requests
import validators
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg2.extras import NamedTupleCursor

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")


@app.route("/")
def index():
    return render_template("/pages/index.html")


@app.post("/urls")
def post_url():
    data = request.form.to_dict()
    url = data["url"]
    today = datetime.datetime.now().date()
    error = validate_url(url)

    if error:
        flash(error["name"], "error")
        return redirect(url_for("index"), 422)
    else:
        conn = psycopg2.connect(DATABASE_URL)
        try:
            with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
                curs.execute("SELECT id, name FROM urls WHERE name =%s;", (url,))
                result = curs.fetchone()
                if result:
                    flash("Страница уже существует", "info")
                    return redirect(url_for("show_url", id=result.id), 302)
                curs.execute(
                    "INSERT INTO urls (name, created_at) VALUES (%s, %s);",
                    (url, today),
                )
                conn.commit()
        except psycopg2.Error as err:
            flash(err, "error")
            return redirect(url_for("index"), 422)
        finally:
            conn.close()
        flash("Страница успешно добавлена", "success")
        return redirect(url_for("all_urls"), 302)


@app.route("/urls")
def all_urls():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute("SELECT * FROM urls ORDER BY id DESC")
            urls = curs.fetchall()
    except psycopg2.Error as err:
        flash(err, "error")
        return redirect(url_for("index"), 422)
    finally:
        conn.close()
    return render_template("urls/index.html", urls=urls)


@app.route("/urls/<int:id>")
def show_url(id):
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute("SELECT * FROM urls WHERE id = %s;", (id,))
            url = curs.fetchone()

            curs.execute(
                """SELECT * FROM url_checks WHERE id = %s
                    ORDER BY id DESC;""",
                (id,),
            )
            checks = curs.fetchall()
    except psycopg2.Error as err:
        flash(err, "error")
        return redirect(url_for("show_url", id=id))
    finally:
        conn.close()
    return render_template("urls/show_url.html", url=url, checks=checks)


@app.post("/urls/<int:id>/checks")
def check_url(id):
    data = request.args.to_dict()
    created_at = datetime.datetime.now().date()

    try:
        res = requests.get(data["url_name"])
        res.raise_for_status()
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("show_url", id=id))

    status_code = res.status_code
    soup = BeautifulSoup(res.text, "html.parser")
    h1 = ""
    title = ""
    description = ""
    if soup.h1:
        h1 = str(soup.h1.string)
    if soup.title:
        title = str(soup.title.string)
    if soup.title:
        title = str(soup.title.string)
    if soup.find("meta", property="og:description"):
        description = soup.find("meta", property="og:description")
    description = description.get("content")

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as curs:
            curs.execute(
                """INSERT INTO url_checks
                (id, status_code, h1, title, description, created_at)
                VALUES(%s, %s, %s, %s, %s, %s);""",
                (id, status_code, h1, title, description, created_at),
            )
            conn.commit()
    except psycopg2.Error as err:
        flash(err, "error")
        return redirect(url_for("show_url", id=id))
    finally:
        conn.close()
    flash("Страница успешно проверена", "success")
    return redirect(url_for("show_url", id=id), 302)


def validate_url(url):
    error = {}
    if not validators.url(url):
        error["name"] = "Некорректный URL"
    elif len(url) > 255:
        error["name"] = "Некорректный URL"
    else:
        error = False
    return error
