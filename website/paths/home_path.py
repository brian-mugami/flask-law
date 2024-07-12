from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

from website import UserModel
from website.models import CaseModel, CaseAttorneyModel, ClientModel

home_blp = Blueprint("home_blp", __name__, )


@home_blp.route("/")
@login_required
def home_page():
    user = UserModel.find_by_id(current_user.id)
    if not current_user.is_authenticated:
        return redirect(url_for('auth_blp.login'))
    if user.user_type == 'super_admin':
        cases = CaseModel.query.all()
    elif user.user_type != 'super_admin' and user.user_type != "client":
        cases = CaseModel.query.join(CaseAttorneyModel).filter(CaseAttorneyModel.user_id == user.id).all()
    elif user.user_type == 'client':
        client = ClientModel.find_by_email(user.email)
        print(client.id)
        cases = CaseModel.query.filter_by(client_id=client.id).all()
    else:
        return render_template("403.html", user=current_user)
    events = []
    print(len(cases))
    for case in cases:
        case_url = url_for('case_blp.get_case', id=case.id)
        if case.filed_date:
            events.append({
                "title": f"Filed: {case.case_number}",
                "start": case.filed_date.strftime("%Y-%m-%d"),
                "end": case.filed_date.strftime("%Y-%m-%d"),
                "color": "blue",
                "url": case_url
            })
        if case.court_date:
            events.append({
                "title": f"Court Date:  {case.case_number}",
                "start": case.court_date.strftime("%Y-%m-%d"),
                "end": case.court_date.strftime("%Y-%m-%d"),
                "color": "red",
                "url": case_url
            })
        if case.resolution_date:
            events.append({
                "title": f"Resolution:  {case.case_number}",
                "start": case.resolution_date.strftime("%Y-%m-%d"),
                "end": case.resolution_date.strftime("%Y-%m-%d"),
                "color": "green",
                "url": case_url
            })
        for hearing in case.court_hearings:
            events.append({
                "title": f"Hearing:  {case.case_number}",
                "start": hearing.hearing_date.strftime("%Y-%m-%d"),
                "end": hearing.hearing_date.strftime("%Y-%m-%d"),
                "color": "purple",
                "url": case_url
            })
            if hearing.next_hearing_date:
                events.append({
                    "title": f"Next Hearing:  {case.case_number}",
                    "start": hearing.next_hearing_date.strftime("%Y-%m-%d"),
                    "end": hearing.next_hearing_date.strftime("%Y-%m-%d"),
                    "color": "orange",
                    "url": case_url
                })

    return render_template("utils/home.html", user=current_user, events=events)
