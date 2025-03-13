import datetime
import os

import psycopg2
from psycopg2.extras import NamedTupleCursor
import validators
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)

@app.route("/")
def index():
    return render_template('/pages/index.html')

@app.post("/urls")
def post_url():
    data = request.form.to_dict()
    url = data["url"]
    today = datetime.datetime.now()
    error = validate_url(url)

    if error:
        flash(error["name"], 'error')
        return redirect(url_for('index'), 302)
    else:
        with conn.cursor() as curs:
            curs.execute("SELECT name FROM urls WHERE name =%s;", (url,))
            urlExist = curs.fetchone()
            if urlExist:
                flash('Url exists', 'error')
                return redirect(url_for('index'), 302)
            curs.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s);", (url, today))
            conn.commit()
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('all_urls'), 302)

@app.route('/urls')
def all_urls():
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute('SELECT * FROM urls ORDER BY id DESC')
        urls = curs.fetchall()
    return render_template('urls/index.html', urls=urls)

@app.route('/urls/<int:url_id>')
def show_url(url_id):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute("SELECT * FROM urls WHERE id = %s;", (url_id,))
        url = curs.fetchone()

        curs.execute("SELECT * FROM url_checks WHERE url_id = %s;", (url_id,))
        checks = curs.fetchall()
    return render_template('urls/show_url.html', url=url, checks=checks)

@app.post('/urls/<int:url_id>/checks')
def check_url(url_id):
    created_at = datetime.datetime.now()
    with conn.cursor() as curs:
        curs.execute("INSERT INTO url_checks (url_id, created_at) VALUES(%s, %s);", (url_id, created_at))
        conn.commit()
    flash('Страница успешно проверена', 'success')
    return redirect(url_for('show_url', url_id=url_id), 302) 

def validate_url(url):
    error = {}
    if not validators.url(url):
        error["name"] = 'Некорректный URL'
    elif len(url) > 255:
        error["name"] = 'Некорректный URL'
    else: 
        error = False
    return error
