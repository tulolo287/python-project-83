import datetime
import os

import psycopg2
import requests
import validators
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg2.extras import NamedTupleCursor

from page_analyzer.utils.index import get_parsed_url

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
    parsed_url = get_parsed_url(url)
    today = datetime.datetime.now().date()
    error = validate_url(url)

    if error:
        flash(error["name"], "error")
        return render_template("/pages/index.html"), 422
    else:
        conn = psycopg2.connect(DATABASE_URL)
        try:
            with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
                curs.execute(
                    """SELECT id, name FROM urls WHERE name =%s;""",
                    (parsed_url,),
                )
                url_exist = curs.fetchone()
                if url_exist:
                    flash("Страница уже существует", "info")
                    return redirect(url_for("show_url", id=url_exist.id), 302)
                curs.execute(
                    """INSERT INTO urls (name, created_at) VALUES (%s, %s)
                    RETURNING id;""",
                    (parsed_url, today),
                )
                id = curs.fetchone()[0]
                conn.commit()
        except psycopg2.Error as err:
            flash(err, "error")
            return redirect(url_for("index"), 422)
        finally:
            conn.close()
        flash("Страница успешно добавлена", "success")
        return redirect(url_for("show_url", id=id), 302)


@app.route("/urls")
def all_urls():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute("""
            SELECT url.id, url.name, ch.created_at AS last_check,
            ch.status_code FROM urls url
            LEFT JOIN url_checks ch ON url.id = ch.url_id
            WHERE ch.url_id IS NULL
            OR ch.id = (SELECT MAX(ch.id) FROM url_checks ch
            WHERE ch.url_id = url.id)
            ORDER BY url.id DESC
            """)

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
                """SELECT * FROM url_checks WHERE url_id = %s
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
    url = request.args.to_dict()["url"]
    h1 = ""
    title = ""
    description = ""
    created_at = datetime.datetime.now().date()

    response = requests.get(url)
    if response.status_code != 200:
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("show_url", id=id))
    else:
        status_code = response.status_code
        soup = BeautifulSoup(response.text, "html.parser")

        if soup.h1:
            h1 = str(soup.h1.string)
        if soup.title:
            title = str(soup.title.string)
        if soup.title:
            title = str(soup.title.string)
        if soup.find("meta", attrs={"name": "description"}):
            description = soup.find("meta", attrs={"name": "description"})
            description = description.get("content", "")

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as curs:
            curs.execute(
                """INSERT INTO url_checks
                (url_id, status_code, h1, title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s);""",
                (id, status_code, h1, title, description, created_at),
            )
            conn.commit()

    except psycopg2.Error as err:
        print(err)
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("show_url", id=id))
    finally:
        conn.close()
    flash("Страница успешно проверена", "success")
    return redirect(url_for("show_url", id=id))


def validate_url(url):
    error = {}
    if not validators.url(url):
        error["name"] = "Некорректный URL"
    elif len(url) > 255:
        error["name"] = "Некорректный URL"
    else:
        error = False
    return error
