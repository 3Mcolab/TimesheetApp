
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField,SubmitField,TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
#from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from TimesheetApp.models import User

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(),Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('pass_confirm', message='Passwords Must Match!')])
    pass_confirm = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register!')

    def validate_email(self, email):
        user= User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email has been already registered!')

    def validate_username(self, username):
        user=User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username has been already taken!')

class ProjectForm(FlaskForm):
    project_add = StringField('Project', validators=[DataRequired()])
    job_add = StringField('Job No.', validators=[DataRequired()])
    allocate_project = FloatField('Allocated Hours',validators=[DataRequired(False)])
    submit = SubmitField('Add')

class TaskForm(FlaskForm):
    task_add = StringField('Task', validators=[DataRequired()])
    submit = SubmitField('Add')

class BirthDayForm(FlaskForm):
    daybirthrem = StringField('Enter Day', validators=[DataRequired()])
    submit = SubmitField('Add')

class LeaveRemForm(FlaskForm):
    dayleaverem = StringField('Enter Day', validators=[DataRequired()])
    submit = SubmitField('Add')

class InvoiceForm(FlaskForm):
    invoice_add = StringField('Accounting Code', validators=[DataRequired()])
    submit = SubmitField('Add')

class AllowanceForm(FlaskForm):
    allowance_add = StringField('Allowance Type', validators=[DataRequired()])
    allocate_rate = FloatField('Rate $',validators=[DataRequired(False)])
    submit = SubmitField('Add')

class ChangePasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(),Email()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('pass_confirm', message='Passwords Must Match!')])
    pass_confirm = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register!')
