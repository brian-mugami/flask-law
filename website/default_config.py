import os

from dotenv import load_dotenv

load_dotenv(".env", verbose=True)
DEBUG = True
basedir = os.path.abspath(os.path.dirname(__file__))
UPLOADED_PHOTOS_DEST = os.path.join(basedir, "static/uploads")
UPLOADED_ATTACHMENTS_DEST = os.path.join(basedir, "static/attachments")
base_dir = os.path.abspath(os.path.dirname(__file__))
URI = "sqlite:///" + os.path.join(base_dir, "database.db")
load_dotenv(".env", verbose=True)
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE", URI)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get("APP_SECRET_KEY")
PROPAGATE_EXCEPTIONS = True
