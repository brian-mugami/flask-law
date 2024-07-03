import traceback

from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from ..db import db
from ..forms import CreateClientForm
from ..models import ClientModel

client_blp = Blueprint("client_blp", __name__, static_folder="static", template_folder="templates")

CLIENT_NOT_FOUND = "Client not found!"
CLIENT_EMAIL_EXISTS = "Client with this email already exists."
CLIENT_PHONE_EXISTS = "Client with this phone number already exists."
CLIENT_IDENTIFICATION_EXISTS = "Client with this identification number already exists."
CREATED_SUCCESSFULLY = "Client created successfully."
INTEGRITY_ERROR = "Integrity error occurred, Please check the details and ensure no duplicates."
SERVER_ERROR = "Server error occurred."
CLIENT_UPDATED_SUCCESS = "Client Updated Successfully"


@client_blp.route("/")
@login_required
def get_clients():
    page = request.args.get("page", 1, type=int)
    name_filter = request.args.get("nameFilter")
    base_query = ClientModel.query.order_by(ClientModel.first_name, ClientModel.last_name,
                                            ClientModel.date_created.asc())

    if name_filter:
        search_query = f"%{name_filter}%"
        base_query = base_query.filter(
            or_(
                ClientModel.first_name.ilike(search_query),
                ClientModel.middle_name.ilike(search_query),
                ClientModel.last_name.ilike(search_query),
                ClientModel.email.ilike(search_query)
            )
        )
    clients = base_query.paginate(page=page, per_page=10)
    return render_template("clients/clients.html", clients=clients, user=current_user)


@client_blp.route("/<int:id>")
@login_required
def get_client(id):
    client = ClientModel.find_by_id(id)
    if not client:
        flash(CLIENT_NOT_FOUND, category="error")
    return render_template("clients/client_info.html", client=client, user=current_user)


@client_blp.route("edit/<int:id>", methods=["POST", "GET"])
@login_required
def edit_client(id):
    client = ClientModel.find_by_id(id)
    if not client:
        flash(CLIENT_NOT_FOUND, category="error")
    form = CreateClientForm(obj=client)
    if request.method == "POST" and form.validate_on_submit():
        client.first_name = form.first_name.data
        client.middle_name = form.middle_name.data
        client.last_name = form.last_name.data
        client.email = form.email.data
        client.phone_no = form.phone_no.data
        client.address = form.address.data
        client.client_date = form.client_date.data
        client.is_archived = form.is_archived.data
        client.identification_no = form.identification_no.data
        client.is_active = form.is_active.data
        try:
            client.update_db()
            flash(CLIENT_UPDATED_SUCCESS, category="success")
            return redirect(url_for('client_blp.get_client', id=client.id))
        except IntegrityError as e:
            db.session.rollback()
            flash(INTEGRITY_ERROR, category="error")
        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            flash(SERVER_ERROR, category="error")

    return render_template("clients/edit_client.html", client=client, user=current_user, form=form)


@client_blp.route("/new", methods=["POST", "GET"])
@login_required
def new_client():
    user_id = current_user.id
    form = CreateClientForm()
    if request.method == 'POST' and form.validate_on_submit():
        if ClientModel.find_by_email(form.email.data):
            flash(CLIENT_EMAIL_EXISTS, "error")
        if ClientModel.find_by_phone(form.phone_no.data):
            flash(CLIENT_PHONE_EXISTS, "error")
        if ClientModel.find_by_identification(form.identification_no.data):
            flash(CLIENT_IDENTIFICATION_EXISTS, "error")
        new_client = ClientModel(
            first_name=form.first_name.data,
            middle_name=form.middle_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_no=form.phone_no.data,
            address=form.address.data,
            identification_no=form.identification_no.data,
            is_active=form.is_active.data,
            client_date=form.client_date.data,
            user_id=user_id
        )
        try:
            new_client.save_to_db()
            flash(CREATED_SUCCESSFULLY, category="success")
            return redirect(url_for("client_blp.get_clients"))
        except IntegrityError as e:
            db.session.rollback()
            flash(INTEGRITY_ERROR, category="error")
        except Exception as e:
            new_client.delete_from_db()
            traceback.print_exc()
            flash(SERVER_ERROR, category="error")
    return render_template("clients/new_client.html", user=current_user, form=form, next=request.referrer)
