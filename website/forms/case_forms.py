from datetime import datetime

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired, Length, Optional
from wtforms_alchemy import QuerySelectField, QuerySelectMultipleField

from website import UserModel


class QuerySelectMultipleFieldsWithCheckboxes(QuerySelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


def non_client_users():
    return UserModel.query.filter(UserModel.user_type != 'client')


def active_clients():
    from website.models import ClientModel
    return ClientModel.query.filter_by(is_active=True).order_by(ClientModel.first_name)


class CreateCaseForm(FlaskForm):
    case_number = StringField('Case Number', validators=[DataRequired(), Length(max=80)])
    title = StringField('Title', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description')
    status = SelectField('Status', choices=[('open', 'Open'), ('closed', 'Closed'), ('pending', 'Pending')])
    case_type = SelectField('Case Type', choices=[
        ('Criminal', 'Criminal'), ('Civil', 'Civil'), ('Commercial', 'Commercial'),
        ('Administrative', 'Administrative'),
        ('Bankruptcy', 'Bankruptcy'), ('Environmental', 'Environmental'), ('Human Rights', 'Human Rights'),
        ('Immigration', 'Immigration'), ('Consumer Protection', 'Consumer Protection'), ('Tax', 'Tax'),
        ('Military', 'Military')
    ])
    case_description = TextAreaField('Case Description')
    filed_date = DateField('Filed Date', format='%Y-%m-%d', validators=[DataRequired()])
    court_date = DateField('Court Date', format='%Y-%m-%d', validators=[Optional()])
    resolution_date = DateField('Resolution Date', format='%Y-%m-%d', validators=[Optional()])
    resolution = StringField('Resolution', validators=[Optional(), Length(max=200)])
    priority = SelectField('Priority', choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')])
    client = QuerySelectField('Client', allow_blank=True, query_factory=active_clients, get_pk=lambda client: client.id)
    submit = SubmitField('Create Case')


class AttToCaseForm(FlaskForm):
    attorneys = QuerySelectMultipleFieldsWithCheckboxes('Attorneys', allow_blank=True, query_factory=non_client_users,
                                                        get_pk=lambda user: user.id)
    submit = SubmitField('Assign')


class CaseDetailForm(FlaskForm):
    judge_name = StringField('Judge Name', validators=[DataRequired()])
    court_type = SelectField('Court Type', choices=[
        ('supreme court of kenya', 'Supreme Court of Kenya'), ('court of appeal', 'Court of Appeal'),
        ('high court', 'High Court'),
        ('employment and labour relations court', 'Employment and Labour Relations Court'),
        ('environment and land court', 'Environment and Land Court'), ('magistrates court', 'Magistrates Court'),
        ('kadhi\'s court', 'Kadhi\'s Court'), ('courts martial', 'Courts Martial'), ('tribunal', 'Tribunal')
    ], validators=[DataRequired()])
    court_location = StringField('Court Location', validators=[Optional()])
    court_description = StringField('Court Description', validators=[Optional()])
    case_hearing_date = DateField('Case Hearing Date', format='%Y-%m-%d', validators=[Optional()])
    case_judgment = TextAreaField('Case Judgment', validators=[Optional()])
    case_outcome = StringField('Case Outcome', validators=[Optional()])
    assigned_prosecutor = StringField('Assigned Prosecutor', validators=[Optional()])
    evidence_details = TextAreaField('Evidence Details', validators=[Optional()])
    submit = SubmitField('Save Case Details')


class CaseNoteForm(FlaskForm):
    note = TextAreaField('Note', validators=[DataRequired()])
    reference_date = DateField('Reference Date', format='%Y-%m-%d', validators=[DataRequired()],
                               default=datetime.utcnow())
    submit = SubmitField('Submit')


class AttachmentForm(FlaskForm):
    description = StringField("Attachment Description", validators=[DataRequired()])
    file = FileField('File', validators=[FileRequired(),FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx'], 'PDF, Word, and Excel files only!')])
    submit = SubmitField('Upload')
