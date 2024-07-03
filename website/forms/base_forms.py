from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length


class RoleForm(FlaskForm):
    name = StringField('Role Name', validators=[DataRequired(), Length(min=1, max=20)])
    description = TextAreaField('Description', validators=[Length(max=200)])
    is_active = BooleanField('Active')
    submit = SubmitField('Save')
