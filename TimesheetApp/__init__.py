#/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from datetime import timedelta
import pymysql
pymysql.install_as_MySQLdb()
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_uploads import configure_uploads
from extensions import uploaded_images
#from flask_uploads import UploadSet, configure_uploads, IMAGES
#import flask_whooshalchemy as whooshalchemy
from elasticsearch import Elasticsearch
from config import Config

db = SQLAlchemy()
migrate=Migrate()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
moment=Moment()
bootstrap = Bootstrap()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    configure_uploads(app, uploaded_images)

    from RyconElectricBlog.users.views import users
    app.register_blueprint(users)
    from RyconElectricBlog.home.views import home
    app.register_blueprint(home)
    from RyconElectricBlog.adminDash.views import adminDash
    app.register_blueprint(adminDash)
    from RyconElectricBlog.employees.views import employees
    app.register_blueprint(employees)
    from RyconElectricBlog.jobsafety.views import jobsafety
    app.register_blueprint(jobsafety)
    from RyconElectricBlog.barcode.views import barcode
    app.register_blueprint(barcode)
    from RyconElectricBlog.error_pages.handlers import error_pages
    app.register_blueprint(error_pages)

    db.init_app(app)
    migrate.init_app(app,db)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None
    return app
