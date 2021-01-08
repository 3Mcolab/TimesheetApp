from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField,SubmitField,TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_wtf.file import FileField, FileAllowed

class AssetForm(FlaskForm):
    asset_add = StringField('Assets', validators=[DataRequired()])
    submit = SubmitField('Add')

class VendorForm(FlaskForm):
    vendor_add = StringField('Vendor', validators=[DataRequired()])
    submit = SubmitField('Add')

class ItemForm(FlaskForm):
    item_add = StringField('Item', validators=[DataRequired()])
    submit = SubmitField('Add')

class ConditionForm(FlaskForm):
    condition_add = StringField('Condition', validators=[DataRequired()])
    submit = SubmitField('Add')
