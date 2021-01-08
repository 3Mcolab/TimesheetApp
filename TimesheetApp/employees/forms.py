from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField,SubmitField,TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
#from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from TimesheetApp.models import User

class Project_UserForm(FlaskForm):
    project_add = StringField('Project', validators=[DataRequired()])
    job_add = StringField('Job No.', validators=[DataRequired()])
    allocate_project = FloatField('Allocated Hours',validators=[DataRequired(False)])
    submit = SubmitField('Add')
