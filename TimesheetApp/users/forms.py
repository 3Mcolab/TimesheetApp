
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField,SubmitField,TextAreaField
from wtforms.validators import ValidationError, DataRequired,Email,EqualTo,Length
from flask_wtf.file import FileField, FileAllowed

from flask_login import current_user
from TimesheetApp.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me=BooleanField('Keep me sign in')
    submit = SubmitField('Log In')

class UpdateProfileForm(FlaskForm):
    firstname = StringField('First name', validators=[DataRequired()])
    lastname = StringField('Last name', validators=[DataRequired()])
    position = StringField('Position', validators=[DataRequired()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Profile')

class UpdateAccountForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('pass_confirm', message='Passwords Must Match!')])
    pass_confirm = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Update Password')

class MessageForm(FlaskForm):
    message = TextAreaField(('Message'), validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(('Submit'))

class ForgotForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class PasswordResetForm(FlaskForm):
        password = PasswordField('Password', validators=[DataRequired(), EqualTo('pass_confirm', message='Passwords Must Match!')])
        pass_confirm = PasswordField('Confirm password', validators=[DataRequired()])
