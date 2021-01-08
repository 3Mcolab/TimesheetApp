import os
from datetime import timedelta
from dotenv import load_dotenv
import pymysql
pymysql.install_as_MySQLdb()

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config():
    SECRET_KEY = 'WXRTYWISYS'
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///'+os.path.join(basedir,'app_v27.db')
    SQLALCHEMY_DATABASE_URI = 'mysql://mydbrev:TimesheetAPP#@mydb.cjtun0czhcnb.ap-southeast-2.rds.amazonaws.com/appdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME=  timedelta(minutes=30)   ####Session Expires in xx minutes
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    POSTS_PER_PAGE = 25
    UPLOADED_IMAGES_DEST = '/home/ubuntu/TimesheetApp/TimesheetApp/static/img'
    UPLOADED_IMAGES_URL = '/home/ubuntu/TimesheetApp/TimesheetApp/static/img/'
    HOSTNAME='https://xyz.com.au'
    POSTS_PER_PAGE = 25
