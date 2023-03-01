"""Flask application with embedded chatbot and analytics"""
from flask_bootstrap import Bootstrap
from flask import Flask, render_template

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'bdqVBWEsRebA4d@GiXm7'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analytics')
def user():
    return render_template('analytics.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
