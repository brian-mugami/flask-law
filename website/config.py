import os

from dotenv import load_dotenv

load_dotenv(".env", verbose=True)
DEBUG = False
basedir = os.path.abspath(os.path.dirname(__file__))
UPLOADED_PHOTOS_DEST = os.path.join(basedir, "static/uploads")
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE1")
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get("APP_SECRET_KEY")
PROPAGATE_EXCEPTIONS = True
