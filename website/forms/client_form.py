from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.fields.datetime import DateField
from wtforms.validators import DataRequired, Email, Length


class CreateClientForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=80)])
    middle_name = StringField('Middle Name', validators=[Length(max=80)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=80)])
    phone_no = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    address = StringField('Address', validators=[DataRequired(), Length(max=200)])
    identification_no = StringField('Identification Number/Passport Number',
                                    validators=[DataRequired(), Length(max=200)])
    is_active = BooleanField("Is Active", default=True)
    is_archived = BooleanField("Is Archived", default=False)
    client_date = DateField("Client Date", default=datetime.utcnow())
    submit = SubmitField('Save')
