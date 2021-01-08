#users/views.py
from datetime import datetime
import time
from flask import render_template, url_for, flash, redirect, request, Blueprint,session,abort
from flask_login import login_user, current_user, logout_user, login_required
from TimesheetApp import db
from werkzeug.security import generate_password_hash,check_password_hash
from TimesheetApp.models import User, Message
from TimesheetApp.users.forms import LoginForm, UpdateAccountForm,UpdateProfileForm,MessageForm,ForgotForm,PasswordResetForm
#from TimesheetApp.users.picture_handler import add_profile_pic
######Mail Services###########
import uuid
from TimesheetApp.utilities.common import email
######Mail Services##########

users = Blueprint('users', __name__)

################LAST SEEN########################
###################DECORATOR####################
@users.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen=datetime.utcnow()
        db.session.commit()

##############LOGIN USER#################################
@users.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error=None
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user is None:
            if user.check_password(form.password.data) and user is not None:
                if user.user_status!='active' or user.email_confirmed!=True:
                    error="Unauthorized  Login: Check Email and Password"
                    return render_template('login.html', form=form,error=error)
                login_user(user,remember=form.remember_me.data)
                session['is_author']=user.is_author
                #After Verify the validity of username and password
                session.permanent = True
                next = request.args.get('next')
                if next == None or not next[0]=='/':
                    if session.get('is_author')!=False:
                        flash('You are successfully logged in', 'success')
                        next = url_for('adminDash.dash_admin')
                    else:
                        flash('You are successfully logged in', 'success')
                        next = url_for('employees.dashboard')
                return redirect(next)
            else:
                error="Unauthorized  Login: Check Email and Password"
                return render_template('login.html', form=form,error=error)
        else:
            error="Unauthorized  Login: Check Email and Password"
            return render_template('login.html', form=form,error=error)
    return render_template('login.html', form=form,error=error)

###############LOGOUT USER######################
@users.route("/logout")
def logout():
    logout_user()
    flash('You are now logged out', 'success')
    return redirect(url_for('users.login'))

###########Forget Password#######################
@users.route('/forgot', methods=['GET', 'POST'])
def forgot():
    error = None
    message = None
    form = ForgotForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            code = str(uuid.uuid4())
            user.password_reset_code=code
            db.session.commit()
            # email the user
            body_html = render_template('mail/user/password_reset.html', user=user)
            body_text = render_template('mail/user/password_reset.txt', user=user)
            email(user.email, "Password reset request", body_html, body_text)

        message = "You will receive a password reset email if your email is in our system"
    return render_template('users/forgot.html', form=form, error=error, message=message)
################Forget Password##############
################Password Reset Form#########
@users.route('/password_reset/<username>/<code>', methods=['GET', 'POST'])
def password_reset(username, code):
    message = None
    form = PasswordResetForm()
    user = User.query.filter_by(username=username).first_or_404()
    if not user or code != user.password_reset_code:
        abort(404)
    if request.method == 'POST':
        if form.validate_on_submit():
            user.password_hash=generate_password_hash(form.password.data)
            user.password_reset_code=''
            db.session.commit()
            return redirect(url_for('users.password_reset_complete'))
    return render_template('users/password_reset.html',form=form,message=message,
                                                    username=username,code=code
                            )
################Password Reset Form###########
@users.route('/password_reset_complete')
def password_reset_complete():
    return render_template('users/password_change_confirmed.html')
###########Password Reset Form################

########User Registration Confirmation##########
######Confirmation email from users for the registration########
@users.route('/confirm/<username>/<code>', methods=['GET', 'POST'])
def confirm(username, code):
    message = None
    form = PasswordResetForm()
    user = User.query.filter_by(username=username).first_or_404()
    if not user or code != user.confirmation_code:
        abort(404)
    if request.method == 'POST':
        if form.validate_on_submit():
            user.password_hash=generate_password_hash(form.password.data)
            user.email=user.confirmation_email
            user.email_confirmed=True
            user.confirmation_code=''
            db.session.commit()
            return redirect(url_for('users.register_confirm_complete'))
    return render_template('/users/confirm_register.html',message=message,form=form)

@users.route('/register_confirm_complete')
def register_confirm_complete():
    return render_template('users/register_confirm_complete.html')
########User Registration Confirmation##########

##########UPDATE USER PROFILE#################
@users.route("/profile_selection", methods=['GET', 'POST'])
@login_required
def profile_selection():
    import datetime
    form = UpdateProfileForm(request.form)
    error=None
    #if form.validate_on_submit():
    if request.method=='POST':
        current_user.firstname = form.firstname.data
        current_user.lastname = form.lastname.data
        current_user.position = form.position.data
        DOB_str=request.form.get('profile_DOB')
        if DOB_str=='' or form.firstname.data=='' or form.lastname.data=='':
            flash('Please Select Correct Format','danger')
            return redirect(url_for('users.profile_selection'))
        #DOB_user = datetime.datetime.strptime(DOB_str,'%Y-%m-%d')
        DOB_user = datetime.datetime.strptime(DOB_str,'%d/%m/%Y')
        ############UPDATING PROFILE OF USER ##################
        profile_update_user = User.query.filter_by(username=current_user.username).first()
        profile_update_user.firstname=form.firstname.data
        profile_update_user.lastname=form.lastname.data
        profile_update_user.position=form.position.data
        profile_update_user.birthday=DOB_user
        db.session.commit()
        flash('User profile has been successfully updated','success')
        return redirect(url_for('employees.dashboard'))
    if request.method == 'GET':
        form.firstname.data = current_user.firstname
        form.lastname.data = current_user.lastname
        form.position.data = current_user.position

    return render_template('/users/profile.html', form=form,error=error)

#######CHANGE PASSWORD #################
@users.route("/account_setting", methods=['GET','POST'])
@login_required
def account_setting():
    form = UpdateAccountForm()
    error=None
    if request.method=='POST':
        if form.validate_on_submit():
            user_dash = User.query.filter_by(username=current_user.username).first()
            user_dash.password_hash=generate_password_hash(form.password.data)
            db.session.commit()
            flash('Password has been changed successfully changed','success')
            return redirect(url_for('users.account_setting'))
    return render_template('/users/account.html',form=form,error=error)

##############MESSAGE SENDING #########################
@users.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body_message=form.message.data)
        db.session.add(msg)
        #user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash('Your message has been sent.')
        return "Thank you for sending message"
        #return redirect(url_for('main.user', username=recipient))
    return render_template('/users/send_message.html', title=('Send Message'),
                           form=form, recipient=recipient)

@users.route('/read_message')
@login_required
def read_messages():
    message=current_user.messages_received.order_by(Message.date.desc())
    return redirect(url_for('adminDash.dash_admin'))

@users.route('/dash_home')
@login_required
def dash_home():
    if session.get('is_author')!=False:
        return redirect(url_for('adminDash.dash_admin'))
    else:
        return redirect(url_for('employees.dashboard'))
