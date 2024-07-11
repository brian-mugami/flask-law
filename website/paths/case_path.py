import os
import secrets
import traceback
from datetime import datetime

from flask import Blueprint, request, render_template, flash, url_for, redirect, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from .. import UserModel
from ..db import db
from ..forms import CreateCaseForm, AttToCaseForm, CaseDetailForm, CaseNoteForm, AttachmentForm, CourtHearingForm
from ..models import CaseModel, CaseAttorneyModel, CaseDetailModel, CaseNoteModel, CaseAttachmentModel, ClientModel, \
    CaseHearingModel

case_blp = Blueprint("case_blp", __name__, static_folder="static", template_folder="templates")
ALLOWED_EXTENSIONS = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'xlsm']
CASE_NOT_FOUND = "Case is not found."
CASE_CREATED_SUCCESSFULLY = "Case created successfully!"
CASE_CREATION_FAILED = "Case creation failed!!"
ASSIGN_SUCCESS = 'Attorneys assigned successfully.'
ASSIGN_FAILED = 'Failed to assign attorneys.'
CASE_DETAIL_CREATED = "Case details saved successfully"
CASE_DETAIL_NOT_FOUND = "Case does not have any details"
CASE_DETAIL_ERROR = "An error occurred while saving case details"
CASE_DETAIL_UPDATED_SUCCESS = "Case details updated successfully"
CASE_DETAIL_UPDATE_FAILED = "Case details update failed"
CASE_UPDATED_SUCCESSFULLY = "Case updated successfully."
CASE_UPDATE_FAILED = "Case update failed."
ATTACHMENT_SUCCESS = "Attachment uploaded successfully."
ATTACHMENT_FAIL = "Failed to upload attachment."""
HEARING_SUCCESS = "Hearing added successfully"
HEARING_FAIL = "Hearing update failed"


@case_blp.route("/edit_hearing/<int:hearing_id>", methods=["POST", "GET"])
@login_required
def edit_hearing(hearing_id):
    hearing = CaseHearingModel.find_by_id(hearing_id)
    case = CaseModel.find_by_id(hearing.case_id)
    form = CourtHearingForm(obj=hearing)
    if request.method == "POST":
        hearing.hearing_date = form.hearing_date.data
        hearing.next_hearing_date = form.next_hearing_date.data
        hearing.description = form.description.data
        hearing.details = form.details.data
        try:
            hearing.update_db()
            if form.next_hearing_date.data:
                case.court_date = form.next_hearing_date.data
                case.update_db()
            flash(HEARING_SUCCESS, "success")
            return redirect(url_for('case_blp.view_hearings', case_id=case.id))
        except Exception as e:
            traceback.print_exc()
            flash(HEARING_FAIL, category="error")
            db.session.rollback()
    return render_template("cases/add_hearing.html", form=form, case_id=hearing.case_id, case=case, user=current_user)


@case_blp.route("/case/<int:case_id>/hearings", methods=["GET"])
@login_required
def view_hearings(case_id):
    case = CaseModel.find_by_id(case_id)
    if not case:
        flash(CASE_NOT_FOUND, "error")
        return redirect(url_for('case_blp.all_cases'))
    page = request.args.get("page", 1, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = CaseHearingModel.query.filter_by(case_id=case_id).order_by(CaseHearingModel.hearing_date)

    if start_date and end_date:
        if start_date > end_date:
            flash("Start date cannot be after end date.", "error")
        else:
            query = query.filter(CaseHearingModel.hearing_date.between(start_date, end_date))

    hearings = query.paginate(page=page,per_page=10)
    return render_template("cases/view_hearings.html", case=case, hearings=hearings, user=current_user)


@case_blp.route("/add_hearing/<int:case_id>", methods=["POST", "GET"])
@login_required
def add_hearing(case_id):
    if not current_user.is_authenticated:
        return redirect(url_for('auth_blp.login'))
    form = CourtHearingForm()
    case = CaseModel.find_by_id(case_id)
    if request.method == "POST":
        hearing = CaseHearingModel(
            case_id=case_id,
            hearing_date=form.hearing_date.data,
            next_hearing_date=form.next_hearing_date.data,
            description=form.description.data,
            details=form.details.data,
            user_id=current_user.id
        )
        try:
            hearing.save_to_db()
            if form.next_hearing_date.data:
                case.court_date = form.next_hearing_date.data
                case.update_db()
            flash(HEARING_SUCCESS, "success")
            return redirect(url_for('case_blp.view_hearings', case_id=case_id))
        except Exception as e:
            traceback.print_exc()
            flash(HEARING_FAIL, category="error")
            db.session.rollback()
    return render_template("cases/add_hearing.html", form=form, case_id=case_id, user=current_user, case=case)


@case_blp.route("/mycase")
@login_required
def my_cases():
    page = request.args.get("page", 1, type=int)
    name_filter = request.args.get("nameFilter")
    base_query = CaseModel.query.join(CaseModel.attorneys).filter(UserModel.id == current_user.id).order_by(
        CaseModel.case_number, CaseModel.date_created.desc())

    if name_filter:
        search_query = f"%{name_filter}%"
        base_query = base_query.filter(
            or_(
                CaseModel.case_number.ilike(search_query),
            )
        )
    cases = base_query.paginate(page=page, per_page=10)
    return render_template("cases/cases.html", cases=cases, user=current_user)


@case_blp.route("/clientcase")
@login_required
def client_cases():
    page = request.args.get("page", 1, type=int)
    name_filter = request.args.get("nameFilter")
    user = UserModel.find_by_id(current_user.id)
    client = ClientModel.find_by_email(user.email)
    base_query = CaseModel.query.filter_by(client_id=client.id).order_by(CaseModel.case_number,
                                                                         CaseModel.date_created.desc())
    if name_filter:
        search_query = f"%{name_filter}%"
        base_query = base_query.filter(
            or_(
                CaseModel.case_number.ilike(search_query),
            )
        )
    cases = base_query.paginate(page=page, per_page=10)
    return render_template("cases/cases.html", cases=cases, user=current_user)


@case_blp.route("/view/detail/<int:id>", methods=["POST", "GET"])
@login_required
def view_case_detail(id):
    case_detail = CaseDetailModel.find_by_case_id(id)
    if not case_detail:
        flash(CASE_DETAIL_NOT_FOUND, category="error")
    return render_template("cases/case_detail.html", user=current_user, next=request.referrer, case_detail=case_detail)


@case_blp.route("/edit/detail/<int:id>", methods=["POST", "GET"])
@login_required
def edit_case_detail(id):
    case_detail = CaseDetailModel.find_by_id(id)
    if not case_detail:
        flash(CASE_DETAIL_NOT_FOUND, category="error")
    form = CaseDetailForm(obj=case_detail)
    if request.method == "POST":
        case_detail.judge_name = form.judge_name.data
        case_detail.court_type = form.court_type.data
        case_detail.court_description = form.court_description.data
        case_detail.court_location = form.court_location.data
        case_detail.case_judgment = form.case_judgment.data
        case_detail.case_outcome = form.case_outcome.data
        case_detail.assigned_prosecutor = form.assigned_prosecutor.data
        case_detail.evidence_details = form.evidence_details.data

        try:
            case_detail.update_db()
            case_detail.case.update_db()
            flash(CASE_DETAIL_UPDATED_SUCCESS, category="success")
            return redirect(url_for('case_blp.view_case_detail', id=id))
        except Exception as e:
            traceback.print_exc()
            flash(CASE_DETAIL_UPDATE_FAILED, category="error")
            db.session.rollback()
    return render_template("cases/edit_case_detail.html", user=current_user, next=request.referrer,
                           form=form)


@case_blp.route("/detail/<int:id>", methods=["POST", "GET"])
@login_required
def case_detail(id):
    if not current_user.is_authenticated:
        return redirect(url_for('auth_blp.login'))
    form = CaseDetailForm()
    case = CaseModel.find_by_id(id)
    if not case:
        flash(CASE_NOT_FOUND, category="error")
    if request.method == "POST":
        case_detail = CaseDetailModel(
            judge_name=form.judge_name.data,
            court_type=form.court_type.data,
            court_description=form.court_description.data,
            court_location=form.court_location.data,
            case_judgment=form.case_judgment.data,
            case_outcome=form.case_outcome.data,
            assigned_prosecutor=form.assigned_prosecutor.data,
            evidence_details=form.evidence_details.data,
            case_id=case.id,
            user_id=current_user.id
        )
        try:
            case_detail.save_to_db()
            case.update_db()
            flash(CASE_DETAIL_CREATED, category="success")
            return redirect(url_for('case_blp.get_case', id=case.id))
        except Exception as e:
            db.session.rollback()
            flash(CASE_DETAIL_ERROR, category="error")
    return render_template("cases/new_case_detail.html", form=form, user=current_user, next=request.referrer)


@case_blp.route("/new/<int:id>", methods=["POST", "GET"])
@login_required
def client_case(id):
    if not current_user.is_authenticated:
        return redirect(url_for('auth_blp.login'))
    form = CreateCaseForm()
    case_number = form.case_number.data
    title = form.title.data
    description = form.description.data
    status = form.status.data
    case_type = form.case_type.data
    case_description = form.case_description.data
    filed_date = form.filed_date.data
    court_date = form.court_date.data
    resolution_date = form.resolution_date.data
    resolution = form.resolution.data
    priority = form.priority.data
    user_id = current_user.id

    if request.method == "POST":
        new_case = CaseModel(
            case_number=case_number,
            title=title,
            description=description,
            status=status,
            case_type=case_type,
            case_description=case_description,
            filed_date=filed_date,
            court_date=court_date,
            resolution_date=resolution_date,
            resolution=resolution,
            priority=priority,
            client_id=id,
            user_id=user_id
        )
        try:
            new_case.save_to_db()
            flash(CASE_CREATED_SUCCESSFULLY, "success")
            return redirect(url_for('case_blp.get_case', id=new_case.id))
        except Exception as e:
            traceback.print_exc()
            flash(CASE_CREATION_FAILED, "error")

    return render_template("cases/new_client_case.html", form=form, user=current_user, next=request.referrer)


@case_blp.route("/new", methods=["POST", "GET"])
@login_required
def new_case():
    if not current_user.is_authenticated:
        return redirect(url_for('auth_blp.login'))
    form = CreateCaseForm()
    client = form.client.data
    case_number = form.case_number.data
    title = form.title.data
    description = form.description.data
    status = form.status.data
    case_type = form.case_type.data
    case_description = form.case_description.data
    filed_date = form.filed_date.data
    court_date = form.court_date.data
    resolution_date = form.resolution_date.data
    resolution = form.resolution.data
    priority = form.priority.data
    user_id = current_user.id

    if request.method == "POST":
        new_case = CaseModel(
            case_number=case_number,
            title=title,
            description=description,
            status=status,
            case_type=case_type,
            case_description=case_description,
            filed_date=filed_date,
            court_date=court_date,
            resolution_date=resolution_date,
            resolution=resolution,
            priority=priority,
            client_id=client.id,
            user_id=user_id
        )
        try:
            new_case.save_to_db()
            flash(CASE_CREATED_SUCCESSFULLY, "success")
            return redirect(url_for('case_blp.get_case', id=new_case.id))
        except Exception as e:
            traceback.print_exc()
            flash(CASE_CREATION_FAILED, "error")

    return render_template("cases/new_case.html", form=form, user=current_user, next=request.referrer)


@case_blp.route("/<int:id>/edit/case", methods=["POST", "GET"])
@login_required
def edit_case(id):
    case = CaseModel.find_by_id(id)
    if not case:
        flash(CASE_NOT_FOUND, "error")
        return redirect(url_for('case_blp.all_cases'))

    form = CreateCaseForm(obj=case)

    if request.method == "POST":
        case.case_number = form.case_number.data
        case.title = form.title.data
        case.description = form.description.data
        case.status = form.status.data
        case.case_type = form.case_type.data
        case.case_description = form.case_description.data
        case.filed_date = form.filed_date.data
        case.court_date = form.court_date.data
        case.resolution_date = form.resolution_date.data
        case.resolution = form.resolution.data
        case.priority = form.priority.data
        case.client_id = form.client.data.id
        try:
            case.update_db()
            flash(CASE_UPDATED_SUCCESSFULLY, "success")
            return redirect(url_for('case_blp.get_case', id=case.id))
        except Exception as e:
            traceback.print_exc()
            flash(CASE_UPDATE_FAILED, "error")

    return render_template("cases/edit_case.html", form=form, case=case, user=current_user, next=request.referrer)


@case_blp.route("/<int:id>/assign", methods=["POST", "GET"])
@login_required
def assign_cases(id):
    case = CaseModel.find_by_id(id)
    if not case:
        flash(CASE_NOT_FOUND, "error")
    form = AttToCaseForm(data={"attorneys": case.attorneys})
    if request.method == "POST":
        case.attorneys.clear()
        try:
            for att in form.attorneys.data:
                existing_attorney = CaseAttorneyModel.find_by_ids(user_id=att.id, case_id=case.id)
                if existing_attorney:
                    existing_attorney.delete_from_db()
                attorney = CaseAttorneyModel(case_id=case.id, user_id=att.id)
                case.update_db()
                attorney.save_to_db()
            flash(ASSIGN_SUCCESS, 'success')
            return redirect(url_for('case_blp.get_case', id=case.id))
        except Exception as e:
            traceback.print_exc()
            flash(ASSIGN_FAILED, 'error')

    return render_template("cases/assign_cases.html", form=form, user=current_user, next=request.referrer)


@case_blp.route("/")
@login_required
def all_cases():
    page = request.args.get("page", 1, type=int)
    name_filter = request.args.get("nameFilter")
    base_query = CaseModel.query.order_by(CaseModel.case_number, CaseModel.date_created.desc())

    if name_filter:
        search_query = f"%{name_filter}%"
        base_query = base_query.filter(
            or_(
                CaseModel.case_number.ilike(search_query),
            )
        )
    cases = base_query.paginate(page=page, per_page=10)
    return render_template("cases/cases.html", cases=cases, user=current_user)


@case_blp.route("/<int:id>")
@login_required
def get_case(id):
    case = CaseModel.find_by_id(id)
    if not case:
        flash(CASE_NOT_FOUND, category="error")
    count = CaseNoteModel.find_by_case_id(case.id).count()
    return render_template("cases/case_info.html", case=case, user=current_user, next=request.referrer, count=count)


@case_blp.route("/<int:id>/note", methods=["POST", "GET"])
@login_required
def add_note(id):
    case = CaseModel.find_by_id(id)
    if not case:
        flash(CASE_NOT_FOUND, "error")

    form = CaseNoteForm()
    note = form.note.data
    date = form.reference_date.data
    if request.method == "POST":
        new_note = CaseNoteModel(note=note, reference_date=date, user_id=current_user.id, case_id=case.id)
        try:
            new_note.save_to_db()
            case.update_db()
            flash(CASE_CREATED_SUCCESSFULLY, "success")
            return redirect(url_for('case_blp.view_notes', id=case.id))
        except Exception as e:
            traceback.print_exc()
            flash(CASE_CREATION_FAILED, "error")
    return render_template("cases/case_notes.html", form=form, user=current_user, next=request.referrer)


@case_blp.route("/<int:id>/notes")
@login_required
def view_notes(id):
    case = CaseModel.find_by_id(id)
    if not case:
        flash(CASE_NOT_FOUND, "error")
    page = request.args.get("page", 1, type=int)
    email_filter = request.args.get("emailFilter")
    base_query = CaseNoteModel.query.join(UserModel).filter(CaseNoteModel.case_id == id)

    if email_filter:
        base_query = base_query.filter(UserModel.email.ilike(f"%{email_filter}%"))

    notes = base_query.paginate(page=page, per_page=10)
    return render_template("cases/view_case_notes.html", notes=notes, case=case, user=current_user,
                           next=request.referrer)


@case_blp.route("/edit/<int:id>/notes", methods=["POST", "GET"])
@login_required
def edit_note(id):
    case = CaseNoteModel.find_by_id(id)
    if not case:
        flash(CASE_NOT_FOUND, "error")
    form = CaseNoteForm(obj=case)
    if request.method == "POST":
        case.note = form.note.data
        case.reference_date = form.reference_date.data
        try:
            case.update_db()
            case.case.update_db()
            flash(CASE_DETAIL_UPDATED_SUCCESS, "success")
            return redirect(url_for('case_blp.view_notes', id=case.case.id))
        except Exception as e:
            traceback.print_exc()
            flash(CASE_CREATION_FAILED, "error")

    return render_template("cases/case_notes.html", form=form, user=current_user, next=request.referrer)


@case_blp.route("/attachment/<int:id>", methods=["POST", "GET"])
@login_required
def case_attachment(id):
    case = CaseModel.find_by_id(id)
    if not case:
        flash(CASE_NOT_FOUND, "error")
        return redirect(url_for('case_blp.all_cases'))

    form = AttachmentForm()
    if request.method == "POST":
        file = form.file.data
        description = form.description.data
        filename = secure_filename(file.filename)
        if '.' in filename and filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
            flash('Invalid file type. Only PDF, Word, and Excel files are allowed.', 'error')
            return redirect(request.url)

        attachment_filename = secrets.token_hex(10) + os.path.splitext(filename)[1]

        case_dir = os.path.join(current_app.config['UPLOADED_ATTACHMENTS_DEST'], str(case.case_number))
        if not os.path.exists(case_dir):
            os.makedirs(case_dir)

        file_path = os.path.join(case_dir, attachment_filename)
        file.save(file_path)

        file_url = os.path.join('static', 'attachments', case.case_number, attachment_filename)

        new_attachment = CaseAttachmentModel(
            case_id=case.id,
            filename=filename,
            file_url=file_url,
            description=description,
            user_id=current_user.id,
            attachment_filename=attachment_filename
        )

        try:
            new_attachment.save_to_db()
            flash(ATTACHMENT_SUCCESS, "success")
            return redirect(url_for('case_blp.view_attachments', id=case.id))
        except Exception as e:
            traceback.print_exc()
            flash(ATTACHMENT_FAIL, "error")
    return render_template("cases/upload_attachment.html", form=form, case=case, user=current_user,
                           next=request.referrer)


@case_blp.route("/attachments/<int:id>", methods=["GET"])
@login_required
def view_attachments(id):
    case = CaseModel.find_by_id(id)
    if not case:
        flash(CASE_NOT_FOUND, "error")
        return redirect(url_for('case_blp.all_cases'))
    page = request.args.get("page", 1, type=int)
    desc_filter = request.args.get("description")
    base_query = CaseAttachmentModel.find_by_case_id(case.id)

    if desc_filter:
        base_query = base_query.filter(CaseAttachmentModel.description.ilike(f"%{desc_filter}%"))

    attachments = base_query.paginate(page=page, per_page=10)
    return render_template("cases/view_attachments.html", case=case, attachments=attachments, user=current_user)


@case_blp.route("/attachment/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_attachment(id):
    attachment = CaseAttachmentModel.find_by_id(id)
    if not attachment:
        flash("Attachment not found", "error")
        return redirect(url_for('case_blp.view_attachments', id=attachment.case_id))

    form = AttachmentForm(obj=attachment)
    if request.method == "POST":
        old_file_path = os.path.join(current_app.config['UPLOADED_ATTACHMENTS_DEST'], str(attachment.case.case_number),
                                     attachment.attachment_filename)
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

        file = form.file.data
        description = form.description.data
        filename = secure_filename(file.filename)
        attachment_filename = secrets.token_hex(10) + os.path.splitext(file.filename)[1]
        if filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
            flash('Invalid file type. Only PDF, Word, and Excel files are allowed.', 'error')
            return redirect(request.url)

        case_dir = os.path.join(current_app.config['UPLOADED_ATTACHMENTS_DEST'], str(attachment.case.case_number))
        if not os.path.exists(case_dir):
            os.makedirs(case_dir)

        file_path = os.path.join(case_dir, attachment_filename)
        file.save(file_path)

        attachment.filename = filename
        attachment.file_url = os.path.join('static', 'attachments', str(attachment.case.case_number),
                                           attachment_filename)
        attachment.description = description
        attachment.attachment_filename = attachment_filename
        attachment.uploaded_at = datetime.utcnow()
        try:
            attachment.update_db()
            attachment.case.update_db()
            flash(ATTACHMENT_SUCCESS, "success")
            return redirect(url_for('case_blp.view_attachments', id=attachment.case_id))
        except Exception as e:
            traceback.print_exc()
            flash(ATTACHMENT_FAIL, "error")

    return render_template("cases/upload_attachment.html", form=form, attachment=attachment, user=current_user,
                           next=request.referrer, case=attachment.case)
