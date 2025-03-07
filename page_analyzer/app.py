import datetime
import os

import psycopg2
import validators
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)


@app.route("/")
def index():
    return render_template('/pages/index.html')


@app.post("/urls")
def get_url():
    data = request.form.to_dict()
    url = data["url"]
    today = datetime.date.today()
    isValid = validators.url(url)
    if isValid:
        curs = conn.cursor() 
        sql = f"INSERT INTO urls (name, created_at) VALUES ('{url}', '{today}')"
        curs.execute(sql)
        conn.commit()
        return redirect('/urls', 302)
    else:
        return redirect('/', 302)


@app.route('/urls')
def all_urls():
    with conn.cursor() as curs:
        curs.execute('SELECT * FROM urls')
        urls = curs.fetchall()
    return render_template('urls/index.html', urls=urls)


@validators.utils.validator
def validate_url(url):
    return validators.url(url)
