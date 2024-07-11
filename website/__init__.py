from flask import Flask, render_template
from flask_cors import CORS
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_uploads import configure_uploads

from .db import db
from .models import UserModel
from .photos import photos, attachments

migrate = Migrate()
cors = CORS()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_pyfile("default_config.py")
    db.init_app(app)

    migrate.init_app(app=app, db=db)
    cors.init_app(app, resources={r"*": {"origins": "*"}})
    login_manager.init_app(app)
    configure_uploads(app, photos)
    configure_uploads(app, attachments)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(id):
        return UserModel.query.get(int(id))

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html', user=current_user), 404

    @app.errorhandler(403)
    def page_not_found(e):
        return render_template('403.html', user=current_user), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html', user=current_user), 500

    from .paths import home_blp, auth_blp, client_blp, case_blp
    app.register_blueprint(home_blp)
    app.register_blueprint(auth_blp, url_prefix="/auth")
    app.register_blueprint(client_blp, url_prefix="/client")
    app.register_blueprint(case_blp, url_prefix="/case")
    return app
