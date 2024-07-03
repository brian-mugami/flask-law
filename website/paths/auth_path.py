import secrets
import traceback
from datetime import datetime

import werkzeug
from flask import Blueprint, redirect, url_for, request, flash, render_template, make_response
from flask_login import current_user, login_user, login_required, logout_user
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from sqlalchemy.exc import IntegrityError

from website.forms import RegistrationForm, LoginForm, UpdateProfileForm
from ..db import db
from ..libs.send_email import MailgunException
from ..models import UserModel, ConfirmationModel
from ..photos import photos

auth_blp = Blueprint("auth_blp", __name__, static_folder="static", template_folder="templates")

USER_EMAIL_EXISTS = "An account with this email already exists."
USER_PHONE_EXISTS = "An account with this phone number already exists."
PASSWORD_MISMATCH_ERROR = "Passwords do not match."
USER_CREATED_SUCCESS = "User created successfully. Please check your email to confirm registration."
NAME_EXISTS = "A user with this name already exists."
SERVER_ERROR = "An internal server error occurred. Please try again."
EMAIL_ERROR = "An error occurred while sending the confirmation email. Please try again later."
CONFIRMATION_NOT_FOUND = "Confirmation link not found."
CONFIRMATION_EXPIRED = "Confirmation link has expired."
CONFIRMATION_CONFIRMED = "Email already confirmed."
CONFIRMATION_SUCCESS = "Email confirmed successfully."
USER_NOT_FOUND = "User not found."
RESEND_SUCCESS = "Confirmation email resent successfully."
RESEND_FAILED = "Failed to resend confirmation email."
INVALID_PASSWORD = "Invalid password. Please try again."
LOGIN_SUCCESS = "Logged in successfully."
LOGOUT_SUCCESS = "Logged out successfully."
NOT_ALLOWED_CREATION = "You are not allowed to create a new user."
USER_UPDATED_SUCCESS = "User details updated successfully."
INTEGRITY_ERROR = "Please check your email or phone number"
ACCOUNT_INACTIVE = "Account is inactive. Please contact support."
NOT_CONFIRMED_ERROR = "This email is not confirmed"
EMAIL_SENT = "Password reset instructions sent to your email."
EMAIL_NOT_SENT = "Failed to send password reset email. Please try again later."
PASSWORD_CHANGE_SUCCESS = "Password Changed Successfully.Please wait as we redirect you to our website"
WRONG_PASSWORD_COMBO = "Passwords must match"


@auth_blp.route("/register/user/law/admin", methods=["POST", "GET"])
def register_admin():
    if current_user.is_authenticated:
        return redirect(url_for('home_blp.home_page'))
    form = RegistrationForm()
    email = form.email.data
    phone_no = form.phone_no.data
    last_name = form.last_name.data
    first_name = form.first_name.data
    pass1 = form.password.data
    pass2 = form.confirm_password.data
    image = form.image.data
    if request.method == "POST":
        if UserModel.find_by_email(email):
            flash(USER_EMAIL_EXISTS, category="error")
        if UserModel.find_by_phone_no(phone_no):
            flash(USER_PHONE_EXISTS, category="error")
        if pass1 != pass2:
            flash(PASSWORD_MISMATCH_ERROR, category="error")
        image = photos.save(image, name=secrets.token_hex(10) + ".")
        user = UserModel(email=email, phone_no=phone_no, user_type="super_admin", last_name=last_name,
                         first_name=first_name, password=pbkdf2_sha256.hash(pass1), date_registered=datetime.utcnow(),
                         image=image)
        try:
            user.save_to_db()
            confirmation = ConfirmationModel(user.id)
            confirmation.save_to_db()
            user.send_email()
            flash(USER_CREATED_SUCCESS, "success")
        except IntegrityError as e:
            db.session.rollback()
            if "users_first_name_last_name_key" in str(e.orig):
                flash(NAME_EXISTS, category="error")
            else:
                flash(SERVER_ERROR, category="error")
        except MailgunException as e:
            user.delete_from_db()
            traceback.print_exc()
            flash(EMAIL_ERROR, category="error")
        except Exception as e:
            user.delete_from_db()
            traceback.print_exc()
            flash(SERVER_ERROR, category="error")
    return render_template("auth/register.html", form=form, user=current_user)


@auth_blp.route("/confirmation/<string:confirm_id>")
def confirmation(confirm_id):
    confirmation = ConfirmationModel.find_by_id(confirm_id)
    if not confirmation:
        flash(CONFIRMATION_NOT_FOUND, "error")

    if confirmation.expired:
        flash(CONFIRMATION_EXPIRED, "error")

    if confirmation.confirmed:
        flash(CONFIRMATION_CONFIRMED, "success")

    confirmation.confirmed = True
    confirmation.save_to_db()
    headers = {"Content-Type": "text/html"}
    return make_response(
        render_template("auth/confirmation.html", email=confirmation.user.email,
                        confirmation_id=confirmation.id), 200,
        headers)


@auth_blp.route("/confirmation/<int:user_id>", methods=["POST", "GET"])
def reconfirmation(user_id):
    user = UserModel.find_by_id(user_id)
    if not user:
        flash(USER_NOT_FOUND, "error")

    try:
        confirmation = user.most_recent_confirmation
        if confirmation:
            if confirmation.confirmed:
                flash(CONFIRMATION_CONFIRMED, "error")
            confirmation.force_to_expire()
            new_confirmation = ConfirmationModel(user_id)
            new_confirmation.save_to_db()
            user.send_email()
            return {"message": RESEND_SUCCESS}, 201

    except MailgunException as e:
        flash(str(e), "error")
    except:
        traceback.print_exc()
        flash(RESEND_FAILED, "error")


@auth_blp.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home_blp.home_page'))
    form = LoginForm()
    if request.method == "POST":
        email = form.email.data
        password = form.password.data
        remember = form.remember.data

        user = UserModel.find_by_email(email)
        if not user:
            flash(USER_NOT_FOUND, "error")
        elif not user.check_pwd(password):
            flash(INVALID_PASSWORD, "error")
        elif not user.is_active:
            flash(ACCOUNT_INACTIVE, "error")
        else:
            confirmation = user.most_recent_confirmation
            if confirmation and confirmation.confirmed:
                login_user(user, remember=remember)
                user.last_login = datetime.utcnow()
                user.update_db()
                flash(LOGIN_SUCCESS, "success")
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home_blp.home_page'))
            else:
                flash(NOT_CONFIRMED_ERROR, category="error")
    return render_template("auth/login.html", form=form, user=current_user)


@auth_blp.route("/logout")
@login_required
def logout():
    logout_user()
    flash(LOGOUT_SUCCESS, category="success")
    return redirect(url_for("auth_blp.login"))


@auth_blp.route("/edituser/<int:id>", methods=["POST", "GET"])
@login_required
def edit_user(id):
    user = UserModel.query.get(id)
    if not user:
        flash(USER_NOT_FOUND, category="error")
        return redirect(url_for('home_blp.home_page'))
    form = UpdateProfileForm(obj=user)
    if request.method == 'POST' and form.validate_on_submit():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.email = form.email.data
        user.phone_no = form.phone_no.data
        user.user_type = form.user_type.data
        user.is_active = form.is_active.data
        user.date_registered = form.date_registered.data
        if form.password.data:
            user.password = pbkdf2_sha256.hash(form.password.data)
        if form.image.data and isinstance(form.image.data, werkzeug.datastructures.FileStorage):
            try:
                image = photos.save(form.image.data, name=secrets.token_hex(10) + ".")
                user.image = image
            except Exception as e:
                flash(f"Error saving image: {str(e)}", category="error")
                return render_template("auth/edit_user.html", form=form, user=user)
        try:
            user.update_db()
            flash(USER_UPDATED_SUCCESS, category="success")
            return redirect(url_for('auth_blp.user_info', id=user.id))
        except IntegrityError as e:
            db.session.rollback()
            if "users_first_name_last_name_key" in str(e.orig):
                flash(NAME_EXISTS, category="error")
            else:
                flash(INTEGRITY_ERROR, category="error")
        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            flash(SERVER_ERROR, category="error")

    return render_template("auth/edit_user.html", form=form, user=current_user)


@auth_blp.route("/new-user", methods=["POST", "GET"])
@login_required
def new_user():
    if current_user.user_type != "super_admin":
        flash(NOT_ALLOWED_CREATION, category="error")
        return redirect(url_for('home_blp.home_page'))
    form = RegistrationForm()
    first_name = form.first_name.data
    last_name = form.last_name.data
    email = form.email.data
    user_type = form.user_type.data
    date_registered = form.date_registered.data
    phone_no = form.phone_no.data
    pass1 = form.password.data
    pass2 = form.confirm_password.data
    image = form.image.data

    if request.method == "POST":
        if UserModel.find_by_email(email):
            flash(USER_EMAIL_EXISTS, category="error")
        if UserModel.find_by_phone_no(phone_no):
            flash(USER_PHONE_EXISTS, category="error")
        if pass1 != pass2:
            flash(PASSWORD_MISMATCH_ERROR, category="error")
        image = photos.save(image, name=secrets.token_hex(10) + ".")
        user = UserModel(email=email, phone_no=phone_no, user_type=user_type, last_name=last_name,
                         first_name=first_name, password=pbkdf2_sha256.hash(pass1), date_registered=date_registered,
                         image=image)
        try:
            user.save_to_db()
            confirmation = ConfirmationModel(user.id)
            confirmation.save_to_db()
            user.send_email()
            flash(USER_CREATED_SUCCESS, "success")
        except IntegrityError as e:
            db.session.rollback()
            if "users_first_name_last_name_key" in str(e.orig):
                flash(NAME_EXISTS, category="error")
            else:
                flash(SERVER_ERROR, category="error")
        except MailgunException as e:
            user.delete_from_db()
            traceback.print_exc()
            flash(EMAIL_ERROR, category="error")
        except Exception as e:
            user.delete_from_db()
            traceback.print_exc()
            flash(SERVER_ERROR, category="error")
    return render_template("auth/new_user.html", form=form, user=current_user)


@auth_blp.route("/users")
@login_required
def all_users():
    page = request.args.get("page", 1, type=int)
    item_filter = request.args.get("emailFilter")
    base_query = UserModel.query.order_by(UserModel.first_name, UserModel.last_name, UserModel.creation_date.asc())

    if item_filter:
        base_query = base_query.filter(UserModel.email.icontains(item_filter))
    users = base_query.paginate(page=page, per_page=10)
    return render_template("auth/all_users.html", users=users, user=current_user)


@auth_blp.route("/<int:id>")
@login_required
def user_info(id):
    user = UserModel.find_by_id(id)
    if not user:
        flash(USER_NOT_FOUND, category="error")
    return render_template("auth/user_info.html", user_info=user, user=current_user)


@auth_blp.route("/reset-password", methods=["POST", "GET"])
def reset():
    if request.method == "POST":
        email = request.form.get("email")
        user = UserModel.find_by_email(email)
        if not user:
            flash(USER_NOT_FOUND, category="error")

        confirmation = user.most_recent_confirmation
        if not confirmation.confirmed:
            flash(message=NOT_CONFIRMED_ERROR, category="error")
        else:
            try:
                user.send_pass_reset_email()
                flash(EMAIL_SENT, "success")
            except MailgunException as e:
                traceback.print_exc()
                flash(EMAIL_NOT_SENT, "error")
            except Exception as e:
                traceback.print_exc()
                flash(SERVER_ERROR, "error")
    return render_template("auth/reset_pass.html", user=current_user)


@auth_blp.route("/reset-password/<int:id>", methods=["POST", "GET"])
def reset_pass(id):
    if request.method == "POST":
        user = UserModel.find_by_id(id)
        if not user:
            flash(message=USER_NOT_FOUND, category="error")

        pass_1 = request.form.get("password_1")
        pass_2 = request.form.get("password_2")

        if pass_1 != pass_2:
            flash(message=WRONG_PASSWORD_COMBO, category="error")
            return render_template("auth/change_password.html")
        else:
            user.password = pbkdf2_sha256.hash(pass_1)
            user.update_db()
            flash(message=PASSWORD_CHANGE_SUCCESS, category="success")
            return redirect(url_for("auth_blp.login"))
    return render_template("auth/change_password.html")
