from flask import Blueprint, render_template
from flask_login import current_user

home_blp = Blueprint("home_blp", __name__, )


@home_blp.route("/")
def home_page():
    return render_template("utils/calender.html",user=current_user)
