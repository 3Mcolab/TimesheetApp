#home/views.py

from flask import render_template, request, Blueprint

home=Blueprint('home',__name__)

@home.route('/')
def index():
    return render_template('index.html')
