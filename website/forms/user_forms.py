from datetime import datetime

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.fields.datetime import DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

from ..models import UserModel


class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=80)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_no = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=200)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    date_registered = DateField("Date Registered", default=datetime.utcnow(), validators=[DataRequired(), ])
    user_type = SelectField('User Type',
                            choices=[('admin', 'Admin'), ('super_admin', 'Super Admin'),
                                     ('advocate', 'Advocate'), ('associate', 'Associate'), ('secretary', 'Secretary'),
                                     ('intern', 'Intern'),
                                     ('lawyer', 'Lawyer'), ('client', 'Client'), ],
                            validators=[DataRequired()])
    image = FileField('User Image',
                      validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images Only Please')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = UserModel.find_by_email(email.data)
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

    def validate_phone_no(self, phone_no):
        user = UserModel.query.filter_by(phone_no=phone_no.data).first()
        if user:
            raise ValidationError('That phone number is already in use. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=80)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_no = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    date_registered = DateField("Date Registered", default=datetime.utcnow(), validators=[DataRequired(), ])
    password = PasswordField("Password", )
    image = FileField('User Image',
                      validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images Only Please')])
    user_type = SelectField('User Type', choices=[
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin'),
        ('advocate', 'Advocate'),
        ('associate', 'Associate'),
        ('intern', 'Intern'),
        ('client', 'Client'),
    ], validators=[DataRequired()])
    is_active = BooleanField("Is Active")
    submit = SubmitField('Save Changes')
