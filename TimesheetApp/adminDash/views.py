import datetime
import csv
from flask import render_template, url_for, flash, redirect, \
                  request, Blueprint,session,abort,\
                  send_file, Response,current_app
from flask_login import current_user,login_required
from io import BytesIO
import numpy as np
import random
from TimesheetApp.models import User,TimeSheetPost, LeavePost,InvoicePost,\
                                        Project_Add,Task_Add,Invoice_Add,Task_Schedule,Message,\
                                        BirthDay_Add,LeaveRem_Add,Public_Holiday,Allowance_Add,EnquiryPost
from TimesheetApp import db
from werkzeug.security import generate_password_hash,check_password_hash
from TimesheetApp.adminDash.forms import RegistrationForm,ProjectForm,TaskForm,InvoiceForm,\
                                                BirthDayForm,LeaveRemForm,AllowanceForm,ChangePasswordForm
from extensions import uploaded_images
from sqlalchemy import or_,and_
###Mail Services#########
import uuid
from TimesheetApp.utilities.common import email

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

adminDash = Blueprint('adminDash',__name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
##Initialization Default Values
clock_view_data={}
##########ADMIN DASHBOARD####################
@adminDash.route('/dash_admin')
@login_required
def dash_admin():
    if session.get('is_author')!=True:
        abort(403)
    #############Initialization###############
    count_clock=0
    count_leave=0
    count_invoice=0
    ######BIRTHDAY REMAINDER##############
    today_date=datetime.date.today()
    if current_user.birthday==None:
        message_card=''
    else:
        if(today_date.strftime('%m')==current_user.birthday.strftime('%m')) and  \
            (today_date.strftime('%d')==current_user.birthday.strftime('%d')):
            message_card='Happy Birthday !'
        else:
            message_card=''
    ###########Default Intialization#############
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    #############CLOCK POSTS#####################
    unique_userdash=[]
    unique_remainder=[]
    user_all_get=[]
    count_alluser=0
    start_clock=today_date- datetime.timedelta(7+idx_week)
    end_clock=today_date - datetime.timedelta(idx_week)
    #user_all=User.query.order_by(User.username).all()
    user_all=User.query.filter(User.user_status=='active').filter(User.is_author==False).order_by(User.username)
    for in_user in user_all:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        count_alluser=count_alluser+1
        user = User.query.filter_by(username=u_all).first_or_404()
        count_clock_in=0
        clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock \
                                        .between(start_clock,end_clock)).filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
        for check_clock in clock_post:
            count_clock_in=count_clock_in+1
        if count_clock_in==0:
            unique_userdash.append(user)
        if count_clock_in>0:
            count_clock=count_clock+1
    len_unique=len(unique_userdash)
    #############LEAVE POSTS#####################
    start_leave=today_date- datetime.timedelta(49+idx_week)
    end_leave=today_date + datetime.timedelta(365)
    leave_posts = LeavePost.query.filter(LeavePost.leave_from.between(start_leave,end_leave)) \
                                 .filter(LeavePost.user_request_leave=='request_approval')  \
                                 .filter(LeavePost.admin_request_leave=='').order_by(LeavePost.leave_from.asc())
    for check_leave in leave_posts:
        count_leave=count_leave+1
    #############INVOICE POSTS#####################
    start_invoice=today_date- datetime.timedelta(49+idx_week)
    end_invoice=today_date + datetime.timedelta(idx_week)
    invoice_posts=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_invoice,end_invoice)) \
                                   .filter(InvoicePost.user_request_invoice=='request_approval') \
                                   .filter(InvoicePost.admin_request_invoice=='').order_by(InvoicePost.invoice_from.asc())
    for check_invoice in invoice_posts:
        count_invoice=count_invoice+1
    ##############################################
    #############BIRTHDAY NOTICE REMAINDER#####################
    birth_day_init=BirthDay_Add.query.all()
    day_add_birth=15
    for init_birth in birth_day_init:
        day_add_birth=init_birth.daybirth
    user_bday_dash=[]
    user_dob_dash=[]
    today_date=datetime.date.today()
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date
    end_time=today_date + datetime.timedelta(day_add_birth)
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    for user_in in user_view:
        user_dob=user_in.birthday
        user_dob_init=user_dob.replace(today_date.year)
        if user_dob_init.date()>=start_time and user_dob_init.date()<=end_time:
            user_bday_dash.append(user_in.birthday)
            user_dob_dash.append(user_in.username)
    len_birthrem=len(user_bday_dash)
    #######################################################
    ###############LEAVE REQUEST REMAINDER################
    leave_day_init=LeaveRem_Add.query.all()
    day_add_leave=15
    for init_leave in leave_day_init:
        day_add_leave=init_leave.leaveDash
    user_start_leave=[]
    user_end_leave=[]
    user_leave_name=[]
    today_date=datetime.date.today()
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date
    end_time=today_date + datetime.timedelta(day_add_leave)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        leave_post = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
        for leave_init in leave_post:
            user_leave_name.append(leave_init.author.username)
            user_start_leave.append(leave_init.leave_from)
            user_end_leave.append(leave_init.leave_to)
    len_user_leave=len(user_leave_name)
    ##########################################################
    return render_template('admin/dash.html',message_card=message_card,len_user_leave=len_user_leave,
                                            user_leave_name=user_leave_name,user_start_leave=user_start_leave,
                                            user_end_leave=user_end_leave,user_bday_dash=user_bday_dash,
                                            user_dob_dash=user_dob_dash,len_birthrem=len_birthrem,len_unique=len_unique,
                                            count_clock=count_clock,count_alluser=count_alluser,count_leave=count_leave,
                                            count_invoice=count_invoice,unique_userdash=unique_userdash)

########### ADMIN REMAINDER TO THE DASHBOARD#####
@adminDash.route('/<username>/message_remainder',methods=['POST'])
@login_required
def message_remainder(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    if request.method=='POST':
        user_message_rm='Hi {}! Admin has flagged that you have not submitted your timesheet Please submit it.'.format(user.firstname)
        user_status_rm='unread' ##Message Unread
        user_flag_rm='checked'  ##Message Checked
        user_title_rm='Reminder: Time Entries Submission' ###Title
        msg = Message(author=current_user, recipient=user,
                        body_message=user_message_rm,
                        body_title=user_title_rm,
                        body_flag=user_flag_rm,
                        body_trans='timesheet',
                        body_id=int(0),
                        body_date=datetime.date.today(),
                        body_sheet='last_week',
                        body_status=user_status_rm)
        db.session.add(msg)
        db.session.commit()
        ######send email to user for verification###########
        message_email='Admin has flagged that you have not submitted your timesheet Please submit it'
        body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
        body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
        email(user.email,"Reminder: Time Entries Submission",body_html,body_text)
        ######send email to user for verification###########
        flash('You successfully send reminder to {}'.format(user.username),'danger')
    return redirect(url_for('adminDash.dash_admin'))
##################################################
#######USER REGISTER #################
@adminDash.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if session.get('is_author')!=True:
        abort(403)
    form = RegistrationForm()
    user_check=['User','Admin']
    if form.validate_on_submit():
        form_user_check=request.form.get('form_user_check')
        if form_user_check=='Admin':
            is_author_form=True
        else:
            is_author_form=False
        code=str(uuid.uuid4())
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data,
                    user_status='active',
                    is_author=is_author_form
                    )
        db.session.add(user)
        db.session.commit()
        profile_init=User.query.filter_by(username=form.username.data).first()
        profile_init.firstname=form.username.data
        profile_init.lastname=form.username.data
        profile_init.confirmation_email=form.email.data.lower()
        profile_init.confirmation_code=code
        profile_init.email_confirmed=False
        profile_init.permission_project=False
        db.session.commit()
        ######send email to user for verification###########
        user_init=User.query.filter_by(username=form.username.data).first()
        body_html=render_template('mail/user/register.html',user=user_init)
        body_text=render_template('mail/user/register.txt',user=user_init)
        email(user_init.email,"Welcome to Team",body_html,body_text)
        ######send email to user for verification###########
        flash('Account has been created!','success')
        return redirect(url_for('adminDash.dash_admin'))
    return render_template('admin/create_account.html', form=form,user_check=user_check)

@adminDash.route('/<username>/suspend_admin')
@login_required
def suspend_admin(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    user.user_status='suspend'
    db.session.commit()
    return redirect(url_for('adminDash.view_alluser'))

@adminDash.route('/<username>/resume_admin')
@login_required
def resume_admin(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    user.user_status='active'
    db.session.commit()
    return redirect(url_for('adminDash.view_alluser'))

@adminDash.route('/<username>/change_password_admin',methods=['POST','GET'])
@login_required
def change_password_admin(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    form = ChangePasswordForm(request.form)
    error=None
    if request.method=='POST':
        if form.validate_on_submit():
            if user.email!=form.email.data:
                flash('Cannot change password,invalid email address','danger')
                return redirect(url_for('adminDash.view_alluser'))
            user.email=form.email.data
            user.password_hash=generate_password_hash(form.password.data)
            db.session.commit()
            flash('Successfully change the password','success')
            return redirect(url_for('adminDash.view_alluser'))
    if request.method=='GET':
        form.email.data=user.email
    return render_template('admin/change_password.html',form=form,error=error)

#######VIEW All Users #################
@adminDash.route('/view_alluser')
@login_required
def view_alluser():
    if session.get('is_author')!=True:
        abort(403)
    user_all=User.query.order_by(User.username).all()
    count_all=0
    for post_ran in user_all:
        count_all=count_all+1
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('admin/view_alluser.html',user_all=user_all,color_all=color_all)

#######ADD PROJECT #################
@adminDash.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    if session.get('is_author')!=True:
        abort(403)
    form = ProjectForm()
    post_allowance=Allowance_Add.query.all()
    if form.validate_on_submit():
        project_init=Project_Add.query.filter_by(project_add=form.project_add.data).first()
        if project_init is not None:
            flash('Project has already been added! Add new Project!','danger')
            return redirect(url_for('adminDash.create_project'))
        allowance_type = request.form.getlist('allowance_type')
        if not allowance_type:
            allowance_init='default'
        else:
            allowance_init='-'.join(allowance_type)
        project_user = Project_Add(project_add=form.project_add.data,
                                   job_add=form.job_add.data,
                                   project_archieve='default',
                                   allowance_id=allowance_init,
                                   allocate_project=form.allocate_project.data)
        db.session.add(project_user)
        db.session.commit()
        flash('Project has been successfully created!','success')
        return redirect(url_for('adminDash.view_allproject'))
    return render_template('admin/create_project.html', form=form,allowance_all=post_allowance)
#######################################################
#######################################################
@adminDash.route('/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
    if session.get('is_author')!=True:
        abort(403)
    form = TaskForm()
    if form.validate_on_submit():
        task_init=Task_Add.query.filter_by(task_add=form.task_add.data).first()
        if task_init is not None:
            flash('Task has already been added! Add new Task!','danger')
            return redirect(url_for('adminDash.create_task'))
        task_user = Task_Add(task_add=form.task_add.data)
        db.session.add(task_user)
        db.session.commit()
        flash('Task has been successfully created!','success')
        return redirect(url_for('adminDash.view_task'))
    return render_template('admin/create_task.html', form=form)

#######VIEW TASK #################
@adminDash.route('/view_task')
@login_required
def view_task():
    if session.get('is_author')!=True:
        abort(403)
    task_all=Task_Add.query.all()
    return render_template('admin/view_task.html',task_all=task_all)

@adminDash.route('/<int:task_post_id>/delete_task',methods=['POST','GET'])
@login_required
def delete_task(task_post_id):
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        task_posts= Task_Add.query.get_or_404(task_post_id)
        db.session.delete(task_posts)
        db.session.commit()
        flash('Task has been deleted!','danger')
        return redirect(url_for('adminDash.view_task'))
    return redirect(url_for('adminDash.view_task'))

#######VIEW PROJECT #################
@adminDash.route('/view_allproject')
@login_required
def view_allproject():
    if session.get('is_author')!=True:
        abort(403)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    ########
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date - datetime.timedelta(730)
    end_time=today_date + datetime.timedelta(idx_week)
    ongoing_hr=[]
    overdue_hr=[]
    for project_init in project_all:
        cumu_all=0
        due_all=0
        project_delta=TimeSheetPost.query.filter(TimeSheetPost.project==project_init.project_add,TimeSheetPost \
                                        .day_clock.between(start_time,end_time)).filter(TimeSheetPost \
                                        .user_request_timesheet=='request_approval').order_by(TimeSheetPost.day_clock.asc())
        sum_HT=0
        sum_NT=0
        sum_DT=0
        sum_DTH=0
        for project_in in project_delta:
            sum_DTH = sum_DTH + project_in.OverTime_25
            sum_HT = sum_HT + project_in.OverTime_15
            sum_NT = sum_NT + project_in.NormalTime
            sum_DT = sum_DT + project_in.OverTime_2
        cumu_all=sum_HT+sum_NT+sum_DT+sum_DTH
        if project_init.allocate_project==None:
            cumu_all=cumu_all
            due_all=0
        elif project_init.allocate_project >=cumu_all:
            cumu_all=cumu_all
            due_all=project_init.allocate_project-cumu_all
        else:
            cumu_all=cumu_all
            due_all=project_init.allocate_project-cumu_all
        ongoing_hr.append(cumu_all)
        overdue_hr.append(due_all)
    return render_template('admin/view_projectall.html',project_all=project_all,
                                                        ongoing_hr=ongoing_hr,
                                                        overdue_hr=overdue_hr)

@adminDash.route('/view_allproject_selection',methods=['POST','GET'])
@login_required
def view_allproject_selection():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date - datetime.timedelta(730)
    end_time=today_date + datetime.timedelta(idx_week)
    ongoing_hr=[]
    overdue_hr=[]
    if request.method=='POST':
        project_chart=request.form.get('project_chart')
        if project_chart=='Alphabetic':
            project_all=Project_Add.query.filter(Project_Add.project_archieve=='default').order_by(Project_Add.project_add)
        elif project_chart=='Date Ascending Order':
            project_all=Project_Add.query.filter(Project_Add.project_archieve=='default').order_by(Project_Add.date.asc())
        else:
            project_all=Project_Add.query.filter(Project_Add.project_archieve=='default').order_by(Project_Add.date.desc())
        for project_init in project_all:
            cumu_all=0
            due_all=0
            project_delta=TimeSheetPost.query.filter(TimeSheetPost.project==project_init.project_add,TimeSheetPost.day_clock \
                                             .between(project_init.date,end_time)).filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                             .order_by(TimeSheetPost.day_clock.asc())
            sum_HT=0
            sum_NT=0
            sum_DT=0
            sum_DTH=0
            for project_in in project_delta:
                sum_DTH = sum_DTH + project_in.OverTime_25
                sum_HT = sum_HT + project_in.OverTime_15
                sum_NT = sum_NT + project_in.NormalTime
                sum_DT = sum_DT + project_in.OverTime_2
            cumu_all=sum_HT+sum_NT+sum_DT+sum_DTH
            if project_init.allocate_project==None:
                cumu_all=cumu_all
                due_all=0
            elif project_init.allocate_project >=cumu_all:
                cumu_all=cumu_all
                due_all=project_init.allocate_project-cumu_all
            else:
                cumu_all=cumu_all
                due_all=project_init.allocate_project-cumu_all
            ongoing_hr.append(cumu_all)
            overdue_hr.append(due_all)
        return render_template('admin/view_projectall.html',project_all=project_all,ongoing_hr=ongoing_hr,
                                                            overdue_hr=overdue_hr)
    return render_template('admin/view_projectall.html',project_all=project_all,ongoing_hr=ongoing_hr,
                                                        overdue_hr=overdue_hr)

########Search Project###################
@adminDash.route('/search_project_default')
@login_required
def search_project_default():
    if session.get('is_author')!=True:
        abort(403)
    query_in=request.args.get('query')
    page=request.args.get('page',1,type=int)
    project_all,total=Project_Add.search(query_in,page,current_app.config['POSTS_PER_PAGE'])
    count_post=0
    for post in project_all:
        count_post=count_post+1
    if count_post==0:
        project_all=Project_Add.query.all()
        flash('Search is not found','danger')
        return redirect(url_for('adminDash.view_allproject'))
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date - datetime.timedelta(730)
    end_time=today_date + datetime.timedelta(idx_week)
    ongoing_hr=[]
    overdue_hr=[]
    for project_init in project_all:
        cumu_all=0
        due_all=0
        project_delta=TimeSheetPost.query.filter(TimeSheetPost.project==project_init.project_add,TimeSheetPost.day_clock \
                                         .between(start_time,end_time)).filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                         .order_by(TimeSheetPost.day_clock.asc())
        sum_HT=0
        sum_NT=0
        sum_DT=0
        sum_DTH=0
        for project_in in project_delta:
            sum_DTH = sum_DTH + project_in.OverTime_25
            sum_HT = sum_HT + project_in.OverTime_15
            sum_NT = sum_NT + project_in.NormalTime
            sum_DT = sum_DT + project_in.OverTime_2
        cumu_all=sum_HT+sum_NT+sum_DT+sum_DTH
        if project_init.allocate_project==None:
            cumu_all=cumu_all
            due_all=0
        elif project_init.allocate_project >=cumu_all:
            cumu_all=cumu_all
            due_all=project_init.allocate_project-cumu_all
        else:
            cumu_all=cumu_all
            due_all=project_init.allocate_project-cumu_all
        ongoing_hr.append(cumu_all)
        overdue_hr.append(due_all)
    return render_template('admin/view_projectall.html',project_all=project_all,ongoing_hr=ongoing_hr,
                                                        overdue_hr=overdue_hr)
########View Archieve Project All###################
#######VIEW PROJECT #################
@adminDash.route('/<int:project_post_id>/view_ind_project')
@login_required
def view_ind_project(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    project_posts= Project_Add.query.get_or_404(project_post_id)
    #user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    user_all=User.query.order_by(User.username).all()
    #######Default Timesheet for the Project####
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    #start_time=today_date - datetime.timedelta(730)

    #####To know Initial Project Date###########
    clock_time=TimeSheetPost.query.filter(TimeSheetPost.project==project_posts.project_add).order_by(TimeSheetPost.date.asc())
    count_time=0
    for date_id in clock_time:
        count_time=count_time+1
        if count_time>=1 and count_time<2:
            start_time_init=date_id.date
    if count_time>=1:
        start_time_project=start_time_init
    else:
        start_time_project=today_date
    end_time=today_date + datetime.timedelta(idx_week)
    ################################################
    #######Task Project Display Views######
    H_All_T=[]
    Task_All_T=[]
    cumu_all_T=0
    task_post=Task_Add.query.order_by(Task_Add.task_add)
    for task_post_ind in task_post:
        clock_post_task_ind = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                 .filter(TimeSheetPost.project==project_posts.project_add) \
                                                 .filter(TimeSheetPost.task==task_post_ind.task_add) \
                                                 .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                 .order_by(TimeSheetPost.day_clock.asc())
        cumu_H_T=0
        sum_HT_T=0
        sum_NT_T=0
        sum_DT_T=0
        sum_DTH_T=0
        for task_in_clock in clock_post_task_ind:
            sum_DTH_T = sum_DTH_T + task_in_clock.OverTime_25
            sum_HT_T = sum_HT_T + task_in_clock.OverTime_15
            sum_NT_T = sum_NT_T + task_in_clock.NormalTime
            sum_DT_T = sum_DT_T + task_in_clock.OverTime_2
        cumu_H_T=sum_HT_T+sum_NT_T+sum_DT_T+sum_DTH_T
        cumu_all_T=cumu_all_T+cumu_H_T
        H_All_T.append(cumu_H_T)
        Task_All_T.append(task_post_ind.task_add)
    #######################################
    H_All=[]
    User_All=[]
    cumu_all=0
    for user_init in user_all:
        clock_post_ind = TimeSheetPost.query.filter(TimeSheetPost.author==user_init,TimeSheetPost.day_clock \
                                            .between(start_time,end_time)).filter(TimeSheetPost.project==project_posts.project_add) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval').order_by(TimeSheetPost.day_clock.asc())
        cumu_H=0
        sum_HT=0
        sum_NT=0
        sum_DT=0
        sum_DTH=0
        for project_in in clock_post_ind:
            sum_DTH = sum_DTH + project_in.OverTime_25
            sum_HT = sum_HT + project_in.OverTime_15
            sum_NT = sum_NT + project_in.NormalTime
            sum_DT = sum_DT + project_in.OverTime_2
        cumu_H=sum_HT+sum_NT+sum_DT+sum_DTH
        cumu_all=cumu_all+cumu_H
        H_All.append(cumu_H)
        User_All.append(user_init.username)
    return render_template('/admin/view_ind_project.html',H_All=H_All,H_All_T=H_All_T,Task_All_T=Task_All_T,
                                                        User_All=User_All,start_time=start_time_project,end_time=end_time,
                                                        project_posts=project_posts,Hour_All=cumu_all)
#######VIEW PROJECT #################
############Each Month Search########
@adminDash.route('/<int:project_post_id>/view_month_project',methods=['POST','GET'])
@login_required
def view_month_project(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    project_posts= Project_Add.query.get_or_404(project_post_id)
    user_all=User.query.order_by(User.username).all()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    year_now=today_date.year
    count_m=0
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='January':
            inx_month=1
        elif view_chart=='February':
            inx_month=2
        elif view_chart=='March':
            inx_month=3
        elif view_chart=='April':
            inx_month=4
        elif view_chart=='May':
            inx_month=5
        elif view_chart=='June':
            inx_month=6
        elif view_chart=='July':
            inx_month=7
        elif view_chart=='August':
            inx_month=8
        elif view_chart=='September':
            inx_month=9
        elif view_chart=='October':
            inx_month=10
        elif view_chart=='November':
            inx_month=11
        else:
            inx_month=12
        for month in range(1,13):
            count_m=count_m+1
            if count_m==inx_month:
                any_day=datetime.date(year_now, month, 1)
                next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
                end_time=next_month - datetime.timedelta(days=next_month.day)
                start_time=end_time.replace(day=1)
    if request.method=='GET':
        start_time=today_date - datetime.timedelta(730)
        end_time=today_date + datetime.timedelta(idx_week)
    #######Task Project Display Views######
    H_All_T=[]
    Task_All_T=[]
    cumu_all_T=0
    task_post=Task_Add.query.order_by(Task_Add.task_add)
    for task_post_ind in task_post:
        clock_post_task_ind = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                 .filter(TimeSheetPost.project==project_posts.project_add) \
                                                 .filter(TimeSheetPost.task==task_post_ind.task_add) \
                                                 .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                 .order_by(TimeSheetPost.day_clock.asc())
        cumu_H_T=0
        sum_HT_T=0
        sum_NT_T=0
        sum_DT_T=0
        sum_DTH_T=0
        for task_in_clock in clock_post_task_ind:
            sum_DTH_T = sum_DTH_T + task_in_clock.OverTime_25
            sum_HT_T = sum_HT_T + task_in_clock.OverTime_15
            sum_NT_T = sum_NT_T + task_in_clock.NormalTime
            sum_DT_T = sum_DT_T + task_in_clock.OverTime_2
        cumu_H_T=sum_HT_T+sum_NT_T+sum_DT_T+sum_DTH_T
        cumu_all_T=cumu_all_T+cumu_H_T
        H_All_T.append(cumu_H_T)
        Task_All_T.append(task_post_ind.task_add)
    #######################################
    H_All=[]
    User_All=[]
    cumu_all=0
    for user_init in user_all:
        clock_post_ind = TimeSheetPost.query.filter(TimeSheetPost.author==user_init,TimeSheetPost.day_clock \
                                            .between(start_time,end_time)).filter(TimeSheetPost.project==project_posts.project_add) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .order_by(TimeSheetPost.day_clock.asc())
        cumu_H=0
        sum_HT=0
        sum_NT=0
        sum_DT=0
        sum_DTH=0
        for project_in in clock_post_ind:
            sum_DTH = sum_DTH + project_in.OverTime_25
            sum_HT = sum_HT + project_in.OverTime_15
            sum_NT = sum_NT + project_in.NormalTime
            sum_DT = sum_DT + project_in.OverTime_2
        cumu_H=sum_HT+sum_NT+sum_DT+sum_DTH
        cumu_all=cumu_all+cumu_H
        H_All.append(cumu_H)
        User_All.append(user_init.username)
    return render_template('/admin/view_ind_project.html',H_All=H_All,H_All_T=H_All_T,Task_All_T=Task_All_T,
                                                        User_All=User_All,project_posts=project_posts,
                                                        start_time=start_time,end_time=end_time,Hour_All=cumu_all)
############Each Month Search########
@adminDash.route('/<int:project_post_id>/view_monthA_project',methods=['POST','GET'])
@login_required
def view_monthA_project(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    project_posts= Project_Add.query.get_or_404(project_post_id)
    user_all=User.query.order_by(User.username).all()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    year_now=today_date.year
    count_m=0
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='January':
            inx_month=1
        elif view_chart=='February':
            inx_month=2
        elif view_chart=='March':
            inx_month=3
        elif view_chart=='April':
            inx_month=4
        elif view_chart=='May':
            inx_month=5
        elif view_chart=='June':
            inx_month=6
        elif view_chart=='July':
            inx_month=7
        elif view_chart=='August':
            inx_month=8
        elif view_chart=='September':
            inx_month=9
        elif view_chart=='October':
            inx_month=10
        elif view_chart=='November':
            inx_month=11
        else:
            inx_month=12
        for month in range(1,13):
            count_m=count_m+1
            if count_m==inx_month:
                any_day=datetime.date(year_now, month, 1)
                next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
                end_time=next_month - datetime.timedelta(days=next_month.day)
                start_time=end_time.replace(day=1)
    if request.method=='GET':
        start_time=today_date - datetime.timedelta(730)
        end_time=today_date + datetime.timedelta(idx_week)
    H_All=[]
    User_All=[]
    cumu_all=0
    for user_init in user_all:
        clock_post_ind = TimeSheetPost.query.filter(TimeSheetPost.author==user_init,TimeSheetPost.day_clock \
                                            .between(start_time,end_time)).filter(TimeSheetPost.project==project_posts.project_add) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .order_by(TimeSheetPost.day_clock.asc())
        cumu_H=0
        sum_HT=0
        sum_NT=0
        sum_DT=0
        sum_DTH=0
        for project_in in clock_post_ind:
            sum_DTH = sum_DTH + project_in.OverTime_25
            sum_HT = sum_HT + project_in.OverTime_15
            sum_NT = sum_NT + project_in.NormalTime
            sum_DT = sum_DT + project_in.OverTime_2
        cumu_H=sum_HT+sum_NT+sum_DT+sum_DTH
        cumu_all=cumu_all+cumu_H
        H_All.append(cumu_H)
        User_All.append(user_init.username)
    return render_template('/admin/view_indA_project.html',H_All=H_All,User_All=User_All,
                                                           project_posts=project_posts,start_time=start_time,
                                                           end_time=end_time,Hour_All=cumu_all)
###########################################
@adminDash.route('/<int:project_post_id>/view_tab_project',methods=['POST','GET'])
@login_required
def view_tab_project(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    project_posts= Project_Add.query.get_or_404(project_post_id)
    user_view=User.query.order_by(User.username).all()
    #######Default Timesheet for the Project####
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    year_now=today_date.year
    if request.method=='POST':
        sheet_inx=request.form.get('view_chart')
        if sheet_inx=='This Month':
            month=today_date.month
            any_day=datetime.date(year_now, month, 1)
            next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
            end_time=next_month - datetime.timedelta(days=next_month.day)
            start_time=end_time.replace(day=1)
            end_day=end_time
        elif sheet_inx=='Last Month':
            now = datetime.datetime.now()
            last_month = now.month-1 if now.month > 1 else 12
            if now.month>1 and now.month<=12:
                last_year=now.year
            else:
                last_year= now.year -1
            any_day=datetime.date(last_year, last_month, 1)
            next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
            end_time=next_month - datetime.timedelta(days=next_month.day)
            start_time=end_time.replace(day=1)
            end_day=end_time
        elif sheet_inx=='This Year':
            year_now=today_date.year
            start_time=datetime.date(year_now, 1, 1)
            end_time=today_date + datetime.timedelta(idx_week)
            end_day=end_time
        elif sheet_inx=='Total':
            start_time=project_posts.date
            start_time=today_date- datetime.timedelta(49+idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
            end_day=end_time
        else:
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
            end_day=end_time
        unique_usersheet=[]
        user_all_get=[]
        for in_user in user_view:
            user_all_get.append(in_user.username)
        for u_all in user_all_get:
            user = User.query.filter_by(username=u_all).first_or_404()
            if sheet_inx=='Total':
                clock_ind=TimeSheetPost.query.filter(TimeSheetPost.author==user) \
                                             .filter(TimeSheetPost.project==project_posts.project_add) \
                                             .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                             .order_by(TimeSheetPost.day_clock.asc())
            else:
                clock_ind=TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock \
                                                .between(start_time,end_time)).filter(TimeSheetPost.project==project_posts.project_add) \
                                                .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                .order_by(TimeSheetPost.day_clock.asc())
            count_clock_in=0
            for check_clock in clock_ind:
                count_clock_in=count_clock_in+1
            if count_clock_in >0:
                unique_usersheet.append(user)
        len_usersheet=len(unique_usersheet)
        clock_post_ind = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                            .filter(TimeSheetPost.project==project_posts.project_add) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval')\
                                            .order_by(TimeSheetPost.day_clock.asc())
        return render_template('/admin/view_project_tabular.html',project_post_id=project_post_id,end_day=end_day,
                                                                    unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                    post_data=clock_post_ind,user_view=user_view,
                                                                    project=project_posts.project_add)
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=end_time
        unique_usersheet=[]
        user_all_get=[]
        for in_user in user_view:
            user_all_get.append(in_user.username)
        for u_all in user_all_get:
            user = User.query.filter_by(username=u_all).first_or_404()
            clock_ind=TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                            .filter(TimeSheetPost.project==project_posts.project_add) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .order_by(TimeSheetPost.day_clock.asc())
            count_clock_in=0
            for check_clock in clock_ind:
                count_clock_in=count_clock_in+1
            if count_clock_in >0:
                unique_usersheet.append(user)
        len_usersheet=len(unique_usersheet)
        clock_post_ind = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                            .filter(TimeSheetPost.project==project_posts.project_add) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .order_by(TimeSheetPost.day_clock.asc())
        return render_template('/admin/view_project_tabular.html',project_post_id=project_post_id,unique_usersheet=unique_usersheet,
                                                                len_usersheet=len_usersheet,end_day=end_day,post_data=clock_post_ind,
                                                                user_view=user_view,project=project_posts.project_add)
    return render_template('/admin/view_project_tabular.html',project_post_id=project_post_id,unique_usersheet=unique_usersheet,
                                                              len_usersheet=len_usersheet,end_day=end_day,post_data=clock_post_ind,
                                                              user_view=user_view,project=project_posts.project_add)
########View Archieve Project All###################
#######VIEW PROJECT #################
@adminDash.route('/view_archive_project')
@login_required
def view_archive_project():
    if session.get('is_author')!=True:
        abort(403)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='archive')
    ########
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date - datetime.timedelta(730)
    end_time=today_date + datetime.timedelta(idx_week)
    ongoing_hr=[]
    overdue_hr=[]
    for project_init in project_all:
        cumu_all=0
        due_all=0
        project_delta=TimeSheetPost.query.filter(TimeSheetPost.project==project_init.project_add,TimeSheetPost.day_clock \
                                            .between(start_time,end_time)).filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .order_by(TimeSheetPost.day_clock.asc())
        sum_HT=0
        sum_NT=0
        sum_DT=0
        sum_DTH=0
        for project_in in project_delta:
            sum_DTH = sum_DTH + project_in.OverTime_25
            sum_HT = sum_HT + project_in.OverTime_15
            sum_NT = sum_NT + project_in.NormalTime
            sum_DT = sum_DT + project_in.OverTime_2
        cumu_all=sum_HT+sum_NT+sum_DT+sum_DTH
        if project_init.allocate_project==None:
            cumu_all=cumu_all
            due_all=0
        elif project_init.allocate_project >=cumu_all:
            cumu_all=cumu_all
            due_all=project_init.allocate_project-cumu_all
        else:
            cumu_all=cumu_all
            due_all=project_init.allocate_project-cumu_all
        ongoing_hr.append(cumu_all)
        overdue_hr.append(due_all)
    return render_template('admin/view_archive_project.html',project_all=project_all,ongoing_hr=ongoing_hr,
                                                            overdue_hr=overdue_hr)
##########################################################
@adminDash.route('/search_archive_project')
@login_required
def search_archive_project():
    if session.get('is_author')!=True:
        abort(403)
    query_in=request.args.get('query')
    page=request.args.get('page',1,type=int)
    project_all,total=Project_Add.search(query_in,page,current_app.config['POSTS_PER_PAGE'])
    count_post=0
    for post in project_all:
        count_post=count_post+1
    if count_post==0:
        project_all=Project_Add.query.all()
        flash('Search is not found','danger')
        return redirect(url_for('adminDash.view_archive_project'))
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date - datetime.timedelta(730)
    end_time=today_date + datetime.timedelta(idx_week)
    ongoing_hr=[]
    overdue_hr=[]
    for project_init in project_all:
        cumu_all=0
        due_all=0
        project_delta=TimeSheetPost.query.filter(TimeSheetPost.project==project_init.project_add,TimeSheetPost.day_clock \
                                            .between(start_time,end_time)).filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .order_by(TimeSheetPost.day_clock.asc())
        sum_HT=0
        sum_NT=0
        sum_DT=0
        sum_DTH=0
        for project_in in project_delta:
            sum_DTH = sum_DTH + project_in.OverTime_25
            sum_HT = sum_HT + project_in.OverTime_15
            sum_NT = sum_NT + project_in.NormalTime
            sum_DT = sum_DT + project_in.OverTime_2
        cumu_all=sum_HT+sum_NT+sum_DT+sum_DTH
        if project_init.allocate_project==None:
            cumu_all=cumu_all
            due_all=0
        elif project_init.allocate_project >=cumu_all:
            cumu_all=cumu_all
            due_all=project_init.allocate_project-cumu_all
        else:
            cumu_all=cumu_all
            due_all=project_init.allocate_project-cumu_all
        ongoing_hr.append(cumu_all)
        overdue_hr.append(due_all)
    return render_template('admin/view_archive_project.html',project_all=project_all,ongoing_hr=ongoing_hr,
                                                            overdue_hr=overdue_hr)
######################################################
@adminDash.route('/<int:project_post_id>/view_indA_project')
@login_required
def view_indA_project(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    project_posts= Project_Add.query.get_or_404(project_post_id)
    user_all=User.query.order_by(User.username).all()
    #######Default Timesheet for the Project####
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date - datetime.timedelta(730)
    end_time=today_date + datetime.timedelta(idx_week)
    #####To know Initial Project Date###########
    clock_time=TimeSheetPost.query.filter(TimeSheetPost.project==project_posts.project_add).order_by(TimeSheetPost.date.asc())
    count_time=0
    for date_id in clock_time:
        count_time=count_time+1
        if count_time>=1 and count_time<2:
            start_time_init=date_id.date
    if count_time>=1:
        start_time_project=start_time_init
    else:
        start_time_project=today_date
    ################################################
    H_All=[]
    User_All=[]
    cumu_all=0
    for user_init in user_all:
        clock_post_ind = TimeSheetPost.query.filter(TimeSheetPost.author==user_init,TimeSheetPost.day_clock \
                                            .between(start_time,end_time)).filter(TimeSheetPost.project==project_posts.project_add) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .order_by(TimeSheetPost.day_clock.asc())
        cumu_H=0
        sum_HT=0
        sum_NT=0
        sum_DT=0
        sum_DTH=0
        for project_in in clock_post_ind:
            sum_DTH = sum_DTH + project_in.OverTime_25
            sum_HT = sum_HT + project_in.OverTime_15
            sum_NT = sum_NT + project_in.NormalTime
            sum_DT = sum_DT + project_in.OverTime_2
        cumu_H=sum_HT+sum_NT+sum_DT+sum_DTH
        cumu_all=cumu_all+cumu_H
        H_All.append(cumu_H)
        User_All.append(user_init.username)
    return render_template('/admin/view_indA_project.html',H_All=H_All,User_All=User_All,project_posts=project_posts,
                                                            start_time=start_time,end_time=end_time,Hour_All=cumu_all)
################################################################
@adminDash.route('/<int:project_post_id>/delete_project',methods=['POST','GET'])
@login_required
def delete_project(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        project_posts= Project_Add.query.get_or_404(project_post_id)
        db.session.delete(project_posts)
        db.session.commit()
        flash('Project has been deleted!','danger')
        return redirect(url_for('adminDash.view_allproject'))
    return redirect(url_for('adminDash.view_allproject'))

@adminDash.route('/<int:project_post_id>/archive_project')
@login_required
def archive_project(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    project_posts= Project_Add.query.get_or_404(project_post_id)
    project_posts.project_archieve='archive'
    db.session.commit()
    flash('Project has been successfully archived!','success')
    return redirect(url_for('adminDash.view_allproject'))
#######################################
@adminDash.route('/<int:project_post_id>/unarchive_project')
@login_required
def unarchive_project(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    project_posts= Project_Add.query.get_or_404(project_post_id)
    project_posts.project_archieve='default'
    db.session.commit()
    flash('Project has been successfully unarchived!','success')
    return redirect(url_for('adminDash.view_archive_project'))
#######DELETE PROJECT #################
@adminDash.route('/<int:project_post_id>/modify_project',methods=['POST','GET'])
@login_required
def modify_project(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    project_posts= Project_Add.query.get_or_404(project_post_id)
    return render_template('admin/modify_project.html',project_posts=project_posts)

@adminDash.route('/<int:project_post_id>/modify_project_selection', methods=['GET', 'POST'])
@login_required
def modify_project_selection(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        project_jobno=request.form.get('project_jobno')
        project_hour=request.form.get('project_hour')
        if project_hour=='':
            project_hour=float(0)
        project_posts= Project_Add.query.get_or_404(project_post_id)
        project_posts.job_add=project_jobno
        project_posts.allocate_project=project_hour
        db.session.commit()
        flash('Job no has been modifed!','success')
        return redirect(url_for('adminDash.view_allproject'))
    return render_template('admin/modify_project.html')
##########Archive Project Modification#########
@adminDash.route('/<int:project_post_id>/modify_archive_project')
@login_required
def modify_archive_project(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    project_posts= Project_Add.query.get_or_404(project_post_id)
    return render_template('admin/modify_archive_project.html',project_posts=project_posts)

@adminDash.route('/<int:project_post_id>/modify_archiveproject_selection', methods=['GET', 'POST'])
@login_required
def modify_archiveproject_selection(project_post_id):
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        project_jobno=request.form.get('project_jobno')
        project_hour=request.form.get('project_hour')
        if project_hour=='':
            project_hour=float(0)
        project_posts= Project_Add.query.get_or_404(project_post_id)
        project_posts.job_add=project_jobno
        project_posts.allocate_project=project_hour
        db.session.commit()
        flash('Project has been modifed!','success')
        return redirect(url_for('adminDash.view_archive_project'))
    return render_template('admin/modify_archive_project.html')
#######VIEW Invoice #################
@adminDash.route('/view_invoice')
@login_required
def view_invoice():
    if session.get('is_author')!=True:
        abort(403)
    invoice_all=Invoice_Add.query.all()
    return render_template('admin/view_invoice.html',invoice_all=invoice_all)

#######ADD INVOICE #################
@adminDash.route('/create_invoice', methods=['GET', 'POST'])
@login_required
def create_invoice():
    if session.get('is_author')!=True:
        abort(403)
    form = InvoiceForm()
    if form.validate_on_submit():
        invoice_init=Invoice_Add.query.filter_by(invoice_add=form.invoice_add.data).first()
        if invoice_init is not None:
            flash('Accounting code has already been added! Add new code!','danger')
            return redirect(url_for('adminDash.create_invoice'))
        invoice_user = Invoice_Add(invoice_add=form.invoice_add.data)
        db.session.add(invoice_user)
        db.session.commit()
        flash('Invoice has been successfully created!','success')
        return redirect(url_for('adminDash.view_invoice'))
    return render_template('admin/create_invoice.html', form=form)

@adminDash.route('/<int:invoice_post_id>/delete_invoice',methods=['POST','GET'])
@login_required
def delete_invoice(invoice_post_id):
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        invoice_posts= Invoice_Add.query.get_or_404(invoice_post_id)
        db.session.delete(invoice_posts)
        db.session.commit()
        flash('Invoice has been deleted!','danger')
        return redirect(url_for('adminDash.view_invoice'))
    return redirect(url_for('adminDash.view_invoice'))

@adminDash.route('/<username>/<sheet_inx>/timesheet_view_standardF',methods=['POST','GET'])
def timesheet_view_standardF(sheet_inx,username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    else:
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                    .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                    .order_by(TimeSheetPost.day_clock.asc())
    for clock_inflag_form in clock_post:
        clock_inflag_form.reject_flag=''
        clock_inflag_form.accept_flag=''
        db.session.commit()
    ######Approval##############
    clock_app = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock \
                                    .between(start_time,end_time)).filter(TimeSheetPost.user_status_timesheet=='Approved') \
                                    .order_by(TimeSheetPost.day_clock.asc())
    sum_HT=0
    sum_DTH=0
    sum_NT=0
    sum_LB=0
    sum_DT=0
    travel_dis=0
    sum_allowance=0
    for data_c in clock_app:
        sum_allowance=sum_allowance+data_c.meal_rate_day
        sum_DTH=sum_DTH+data_c.OverTime_25
        sum_HT=sum_HT+data_c.OverTime_15
        sum_NT=sum_NT+data_c.NormalTime
        sum_LB=sum_LB+data_c.Launch_Break
        sum_DT=sum_DT+data_c.OverTime_2
        if data_c.distance=='':
            travel_dis=travel_dis
        else:
            travel_dis=travel_dis+int(data_c.distance)
    ############Reimbursement################################
    invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from \
                                    .between(start_time,end_time)).filter(InvoicePost.user_status_invoice=='Approved') \
                                    .order_by(InvoicePost.invoice_from.asc())
    sum_invoice=0
    for invoice_in in invoice_post:
        sum_invoice=sum_invoice+invoice_in.invoice_Total
    ##########################################################
    if request.method=='POST':
        if request.form['submit_button']=='Approve':
            form_approve=request.form.getlist('selectedRow[]')
            form_reject=request.form.getlist('selectedItem_new[]')
            if form_approve==[]:
                flash('You have not selected any timesheets for approval','danger')
                return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
            if form_reject!=[]:
                flash('You cannot reject timesheets by Approval Selected buttom','danger')
                return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
            for init_form in form_approve:
                clock_posts_form = TimeSheetPost.query.get_or_404(int(init_form))
                clock_posts_form.accept_flag='checked'
                db.session.commit()
            ##################################################################
            clock_post_adj = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock \
                                                .between(start_time,end_time)).filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                .filter(TimeSheetPost.accept_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
            for clock_in in clock_post_adj:
                if clock_in.user_status_timesheet=='Rejected':
                    flash('You have already rejected timesheets','danger')
                    return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
            ########MESSAGE NOTIFICATION#################################
            count_check=0
            count_clock_in=0
            approved_date=[]
            clock_post_init = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                .filter(TimeSheetPost.accept_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
            ########### MESSAGE NOTIFICATION#########################
            for check_clock_init in clock_post_init:
                count_check=count_check+1
            for check_clock in clock_post_init:
                count_clock_in=count_clock_in+1
                if check_clock.user_status_timesheet=='Submited':
                    t_z=check_clock.day_clock
                    approved_date.append(t_z.strftime('%Y-%m-%d'))
            if count_clock_in>0 and approved_date !=[]:
                user_message_ap='Hi {}! Your timesheet on {} has been approved.'.format(user.firstname,approved_date)
                user_status_ap='unread'
                user_flag_ap=''
                user_title_ap='Time Entries Approval'
                msg = Message(author=current_user, recipient=user,
                                body_message=user_message_ap,
                                body_title=user_title_ap,
                                body_flag=user_flag_ap,
                                body_trans='timesheet',
                                body_id=int(0),
                                body_date=datetime.date.today(),
                                body_sheet=sheet_inx,
                                body_status=user_status_ap)
                db.session.add(msg)
                db.session.commit()
                ######send email to user for verification###########
                message_email='Your timesheet on {} has been approved'.format(approved_date)
                body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                email(user.email,"Time Entries Approval",body_html,body_text)
                ######send email to user for verification###########
            ##################################################################
            count_int=0
            clock_postR = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                .filter(TimeSheetPost.accept_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
            for clock_in in clock_postR:
                count_int=count_int+1
                if clock_in.user_status_timesheet!='Rejected':
                    clock_in.admin_request_timesheet='checked'
                    clock_in.user_status_timesheet='Approved'
                    clock_in.timesheet_flag=''
                    db.session.commit()
            if count_int==0:
                flash('You have not selected any timesheets','danger')
                return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
            else:
                flash('TimeSheet has been approved','success')
            #############Flag Timesheets#################
            ######Make default blank#####################
            clock_post_flag = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock \
                                                    .between(start_time,end_time)).order_by(TimeSheetPost.day_clock.asc())
            for clock_inflag in clock_post_flag:
                clock_inflag.accept_flag=''
                db.session.commit()
            return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
                ##################################################################
        if request.form['submit_button']=='Reject':
            form_approve=request.form.getlist('selectedRow[]')
            form_reject=request.form.getlist('selectedItem_new[]')
            if form_reject==[]:
                flash('You have not selected any timesheets for rejection','danger')
                return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
            if form_approve!=[]:
                flash('You cannot approved timesheets by Reject Selected buttom','danger')
                return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
            for init_form in form_reject:
                clock_posts_rej = TimeSheetPost.query.get_or_404(int(init_form))
                clock_posts_rej.reject_flag='checked'
                db.session.commit()
            ##################################################################
            clock_post_rej_form = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock \
                                                        .between(start_time,end_time)).filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                        .filter(TimeSheetPost.reject_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
            for clock_in in clock_post_rej_form:
                if clock_in.user_status_timesheet=='Approved':
                    flash('You have already approved timesheets','danger')
                    return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
            ##################################################################
            #########Message Notification############
            count_clock_in=0
            approved_date=[]
            clock_post_init = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                    .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                    .filter(TimeSheetPost.reject_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
            for check_clock in clock_post_init:
                if check_clock.user_status_timesheet=='Approved':
                    flash('Cannot be rejected, It has been approved already!!','danger')
                    return redirect(url_for('adminDash.timesheet_view_acceptflag',sheet_inx=sheet_inx))
                count_clock_in=count_clock_in+1
                if check_clock.user_status_timesheet=='Submited' and check_clock.reject_flag=='checked':
                    t_z=check_clock.day_clock
                    approved_date.append(t_z.strftime('%Y-%m-%d'))
            if count_clock_in>0 and approved_date !=[]:
                user_message_ap='Hi {}! Your timesheet on {} has been rejected.'.format(user.firstname,approved_date)
                user_status_ap='unread'
                user_flag_ap=''
                user_title_ap='Time Entries Rejected'
                msg = Message(author=current_user, recipient=user,
                                body_message=user_message_ap,
                                body_title=user_title_ap,
                                body_flag=user_flag_ap,
                                body_trans='timesheet',
                                body_sheet=sheet_inx,
                                body_id=int(0),
                                body_date=datetime.date.today(),
                                body_status=user_status_ap)
                db.session.add(msg)
                db.session.commit()
                ######send email to user for verification###########
                message_email='Your timesheet on {} has been rejected'.format(approved_date)
                body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                email(user.email,"Time Entries Rejected",body_html,body_text)
                ######send email to user for verification###########
        ##################################################################
            clock_post_td = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock \
                                                .between(start_time,end_time)).filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                .filter(TimeSheetPost.reject_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
            count_int=0
            for clock_in in clock_post_td:
                count_int=count_int+1
                if clock_in.user_status_timesheet!='Approved':
                    clock_in.timesheet_flag='checked'
                    clock_in.user_status_timesheet='Rejected'
                    db.session.commit()
            if count_int==0:
                flash('You have not selected any timesheets','danger')
                return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
            else:
                flash('TimeSheet is rejected','success')
            clock_post_flag = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)).order_by(TimeSheetPost.day_clock.asc())
            for clock_inflag in clock_post_flag:
                clock_inflag.reject_flag=''
                db.session.commit()
            return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
    return render_template('/admin/view_timesheet_standard.html',post_data=clock_post, inx_week=inx_week,sum_allowance=sum_allowance,
                                                                    sum_invoice=sum_invoice,travel_dis=travel_dis,user=user,
                                                                    user_all=user_all,sum_HT=sum_HT,sum_NT=sum_NT,sum_LB=sum_LB,
                                                                    sum_DT=sum_DT,sum_DTH=sum_DTH,end_time=end_day)

@adminDash.route("/<username>/<sheet_inx>/timesheet_ind_approval_acceptflag", methods=['POST'])
@login_required
def timesheet_ind_approval_acceptflag(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=start_time+datetime.timedelta(7)
            #end_time=today_date + datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
    ##################################################################
        clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .filter(TimeSheetPost.accept_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
        for clock_in in clock_post:
            if clock_in.user_status_timesheet=='Rejected':
                flash('You have already rejected timesheets','danger')
                return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
            if clock_in.user_status_timesheet=='Approved':
                flash('You have already approved timesheets','danger')
                return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
        ########MESSAGE NOTIFICATION#################################
        count_check=0
        count_clock_in=0
        approved_date=[]
        clock_post_init = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                .filter(TimeSheetPost.accept_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
        ########### MESSAGE NOTIFICATION#########################
        for check_clock_init in clock_post_init:
            count_check=count_check+1
        for check_clock in clock_post_init:
            count_clock_in=count_clock_in+1
            if check_clock.user_status_timesheet=='Submited':
                t_z=check_clock.day_clock
                approved_date.append(t_z.strftime('%Y-%m-%d'))
        if count_clock_in>0 and approved_date !=[]:
            user_message_ap='Hi {}! Your timesheet on {} has been approved.'.format(user.firstname,approved_date)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Time Entries Approval'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='timesheet',
                            body_id=int(0),
                            body_date=datetime.date.today(),
                            body_sheet=sheet_inx,
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your timesheet on {} has been approved'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Time Entries Approval",body_html,body_text)
            ######send email to user for verification###########
        ##################################################################
        count_int=0
        clock_postR = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .filter(TimeSheetPost.accept_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
        for clock_in in clock_postR:
            count_int=count_int+1
            if clock_in.user_status_timesheet!='Rejected':
                clock_in.admin_request_timesheet='checked'
                clock_in.user_status_timesheet='Approved'
                clock_in.timesheet_flag=''
                db.session.commit()
        if count_int==0:
            flash('You have not selected any timesheets','danger')
            return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
        else:
            flash('TimeSheet has been approved','success')
            #############Flag Timesheets#################
            ######Make default blank#####################
        clock_post_flag = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                .order_by(TimeSheetPost.day_clock.asc())
        for clock_inflag in clock_post_flag:
            clock_inflag.accept_flag=''
            db.session.commit()
        return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
#####DEFAULT DASHBOARD######################
@adminDash.route("/<username>/timesheet_view_standard",methods=['GET','POST'])
@login_required
def timesheet_view_standard(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='This Week':
            inx_week='this_week'
        elif view_chart=='This Month':
            inx_week='this_month'
        else:
            inx_week='last_week'
    if request.method=='GET':
        inx_week='last_week'
    return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=inx_week))

#########ADMIN TIMESHEET VIEW################
@adminDash.route("/<username>/<sheet_inx>/timesheet_view_standardF_xx")
@login_required
def timesheet_view_standardF_xx(sheet_inx,username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    else:
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
    ######Approval##############
    clock_app = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_status_timesheet=='Approved').order_by(TimeSheetPost.day_clock.asc())
    sum_HT=0
    sum_DTH=0
    sum_NT=0
    sum_LB=0
    sum_DT=0
    travel_dis=0
    sum_allowance=0
    for data_c in clock_app:
        sum_allowance=sum_allowance+data_c.meal_rate_day
        sum_DTH=sum_DTH+data_c.OverTime_25
        sum_HT=sum_HT+data_c.OverTime_15
        sum_NT=sum_NT+data_c.NormalTime
        sum_LB=sum_LB+data_c.Launch_Break
        sum_DT=sum_DT+data_c.OverTime_2
        if data_c.distance=='':
            travel_dis=travel_dis
        else:
            travel_dis=travel_dis+int(data_c.distance)
    ############Reimbursement################################
    invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                        .filter(InvoicePost.user_status_invoice=='Approved').order_by(InvoicePost.invoice_from.asc())
    sum_invoice=0
    for invoice_in in invoice_post:
        sum_invoice=sum_invoice+invoice_in.invoice_Total
    ##########################################################
    return render_template('/admin/view_timesheet_standard.html', post_data=clock_post, inx_week=inx_week,sum_allowance=sum_allowance,
                                                                    sum_invoice=sum_invoice,travel_dis=travel_dis,user=user,
                                                                    user_all=user_all,sum_HT=sum_HT,sum_NT=sum_NT,sum_LB=sum_LB,
                                                                    sum_DT=sum_DT,sum_DTH=sum_DTH,end_time=end_day)

#####DEFAULT DASHBOARD######################
@adminDash.route("/<username>/timesheet_view_standardnew",methods=['GET','POST'])
@login_required
def timesheet_view_standardnew(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    #user_all=User.query.all()
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='This Week':
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=today_date + datetime.timedelta(idx_week)
            end_time=start_time+datetime.timedelta(7)
            end_day=start_time+datetime.timedelta(6)
            inx_week='this_week'
        elif view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
            inx_week='this_month'
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
            inx_week='last_week'
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
    ########Clock Approval#####################
    clock_app = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                    .filter(TimeSheetPost.user_status_timesheet=='Approved').order_by(TimeSheetPost.day_clock.asc())
    sum_HT=0
    sum_DTH=0
    sum_NT=0
    sum_LB=0
    sum_DT=0
    travel_dis=0
    sum_allowance=0
    for data_c in clock_app:
        sum_allowance=sum_allowance+data_c.meal_rate_day
        sum_DTH=sum_DTH+data_c.OverTime_25
        sum_HT=sum_HT+data_c.OverTime_15
        sum_NT=sum_NT+data_c.NormalTime
        sum_LB=sum_LB+data_c.Launch_Break
        sum_DT=sum_DT+data_c.OverTime_2
        if data_c.distance=='':
            travel_dis=travel_dis
        else:
            travel_dis=travel_dis+int(data_c.distance)
    ############Reimbursement################################
    invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                    .filter(InvoicePost.user_status_invoice=='Approved').order_by(InvoicePost.invoice_from.asc())
    sum_invoice=0
    for invoice_in in invoice_post:
        sum_invoice=sum_invoice+invoice_in.invoice_Total
    ##########################################################
    return render_template('/admin/view_timesheet_standard.html', post_data=clock_post,inx_week=inx_week,sum_allowance=sum_allowance,
                                                                    sum_invoice=sum_invoice,travel_dis=travel_dis,user_all=user_all,
                                                                    user=user,sum_HT=sum_HT,sum_DTH=sum_DTH,sum_NT=sum_NT,sum_LB=sum_LB,
                                                                    sum_DT=sum_DT,end_time=end_day)

#####DEFAULT DASHBOARD######################
@adminDash.route("/<username>/<sheet_inx>/timesheet_view_standardF_daterange",methods=['GET','POST'])
@login_required
def timesheet_view_standardF_daterange(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    #user_all=User.query.all()
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        start_time_str=request.form.get('from_select')
        end_time_str=request.form.get('to_select')
        if start_time_str=='' or end_time_str=='':
            flash('Select the date range','danger')
            return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
        start_time = datetime.datetime.strptime(start_time_str,'%d/%m/%Y')
        end_time = datetime.datetime.strptime(end_time_str,'%d/%m/%Y')
        end_day=end_time
        if start_time>end_time:
            flash('Select the date range','danger')
            return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
        clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
        ########Clock Approval#####################
        clock_app = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_status_timesheet=='Approved').order_by(TimeSheetPost.day_clock.asc())
        sum_HT=0
        sum_DTH=0
        sum_NT=0
        sum_LB=0
        sum_DT=0
        travel_dis=0
        sum_allowance=0
        for data_c in clock_app:
            sum_allowance=sum_allowance+data_c.meal_rate_day
            sum_DTH=sum_DTH+data_c.OverTime_25
            sum_HT=sum_HT+data_c.OverTime_15
            sum_NT=sum_NT+data_c.NormalTime
            sum_LB=sum_LB+data_c.Launch_Break
            sum_DT=sum_DT+data_c.OverTime_2
            if data_c.distance=='':
                travel_dis=travel_dis
            else:
                travel_dis=travel_dis+int(data_c.distance)
        ############Reimbursement################################
        invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                            .filter(InvoicePost.user_status_invoice=='Approved').order_by(InvoicePost.invoice_from.asc())
        sum_invoice=0
        for invoice_in in invoice_post:
            sum_invoice=sum_invoice+invoice_in.invoice_Total
            ##########################################################
        return render_template('/admin/view_timesheet_standard.html', post_data=clock_post,inx_week=sheet_inx,sum_allowance=sum_allowance,
                                                                        sum_invoice=sum_invoice,travel_dis=travel_dis,user_all=user_all,
                                                                        user=user,sum_HT=sum_HT,sum_DTH=sum_DTH,sum_NT=sum_NT,sum_LB=sum_LB,
                                                                        sum_DT=sum_DT,end_time=end_day)
    return render_template('/admin/view_timesheet_standard.html', post_data=clock_post,inx_week=sheet_inx,sum_allowance=sum_allowance,
                                                                    sum_invoice=sum_invoice,travel_dis=travel_dis,user_all=user_all,
                                                                    user=user,sum_HT=sum_HT,sum_DTH=sum_DTH,sum_NT=sum_NT,sum_LB=sum_LB,
                                                                    sum_DT=sum_DT,end_time=end_day)

#########ADMIN TIMESHEET VIEW################
#########ADMIN TIMESHEET VIEW################
@adminDash.route("/<username>/<sheet_inx>/timesheet_csv_download",methods=['POST'])
def timesheet_csv_download (sheet_inx,username):
    user=User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        if sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=today_date + datetime.timedelta(idx_week)
            end_time=start_time+datetime.timedelta(7)
            end_day=start_time+datetime.timedelta(6)
        elif sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
        end_day=end_day.strftime('%d/%m/%Y')
        ##################################################
        clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
        clock_app = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_status_timesheet=='Approved') \
                                        .order_by(TimeSheetPost.day_clock.asc())
        sum_HT=0
        sum_HTD=0
        sum_NT=0
        sum_LB=0
        sum_DT=0
        travel_dis=0
        for data_c in clock_app:
            sum_HTD=sum_HTD+data_c.OverTime_25
            sum_HT=sum_HT+data_c.OverTime_15
            sum_NT=sum_NT+data_c.NormalTime
            sum_LB=sum_LB+data_c.Launch_Break
            sum_DT=sum_DT+data_c.OverTime_2
            if data_c.distance=='':
                travel_dis=travel_dis
            else:
                travel_dis=travel_dis+int(data_c.distance)
        ############Reimbursement################################
        invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                            .filter(InvoicePost.user_status_invoice=='Approved') \
                                            .order_by(InvoicePost.invoice_from.asc())
        sum_invoice=0
        for invoice_in in invoice_post:
            sum_invoice=sum_invoice+invoice_in.invoice_Total
        with open('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/timesheet_data.csv','w') as fp:
            data_init=csv.writer(fp)
            data_init.writerow(['Timesheet for:{}'.format(user.username)])
            data_init.writerow(['Week Ending:{}'.format(end_day)])
            data_init.writerow(['Date','Job No','Project','Task','Clock In','Clock Out','Normal Time','Over Time_Half', \
                                'Overtime_double','Lunch Break','Distance:kMs','User Status'])
            for cp_in in clock_post:
                data_init_post=[cp_in.day_clock.strftime('%d/%m/%Y'),cp_in.job_num,cp_in.project,cp_in.task,cp_in.clock_in.strftime('%H:%M'), \
                                cp_in.clock_out.strftime('%H:%M'),cp_in.NormalTime,cp_in.OverTime_15,cp_in.OverTime_2,cp_in.Launch_Break, \
                                cp_in.distance,cp_in.user_status_timesheet]
                data_init.writerow(data_init_post)
            data_f=['','','','','','',sum_NT,sum_HT,sum_DT,sum_LB,travel_dis]
            data_init.writerow(data_f)
            data_rem=['Reimbursement :${}'.format(sum_invoice)]
            data_init.writerow(data_rem)
        try:
            return send_file('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/timesheet_data.csv',
                            mimetype='text/csv',attachment_filename='timesheet_data.csv',as_attachment=True)
        except:
            flash('File not supported format','danger')
            return redirect(url_for('adminDash.timesheet_view_standardF',username=username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.timesheet_view_standardF',username=username,sheet_inx=sheet_inx))
############################################

#####DEFAULT DASHBOARD######################
@adminDash.route("/<sheet_inx>/timesheet_view",methods=['POST','GET'])
@login_required
def timesheet_view(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    else:
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    clock_view_data=TimeSheetPost.query.filter(TimeSheetPost.user_id).filter(TimeSheetPost.day_clock \
                                        .between(start_time,end_time)).filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
    for clock_inflag_form in clock_view_data:
        clock_inflag_form.reject_flag=''
        clock_inflag_form.accept_flag=''
        db.session.commit()
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        clock_ind=TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
        count_clock_in=0
        for check_clock in clock_ind:
            count_clock_in=count_clock_in+1
        if count_clock_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ########################################
    count_all=0
    for post_ran in clock_view_data:
        count_all=count_all+1
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    ##########################################################
    if request.method=='POST':
        #########Approval Process#################
        if request.form['submit_button']=='Approve':
            form_approve=request.form.getlist('selectedRow[]')
            form_reject=request.form.getlist('selectedItem_new[]')
            if form_approve==[]:
                flash('You have not selected any timesheets for approval','danger')
                return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
            if form_reject!=[]:
                flash('You cannot reject timesheets by Approval Selected buttom','danger')
                return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
            for init_form in form_approve:
                clock_posts_form = TimeSheetPost.query.get_or_404(int(init_form))
                clock_posts_form.accept_flag='checked'
                db.session.commit()
            #######################MESSAGE NOTIFICATION#################
            user_all_get_form_approve=[]
            user_all=User.query.filter(User.user_status=='active').order_by(User.username)
            for in_user in user_all:
                user_all_get_form_approve.append(in_user.username)
            ############################
            count_check=0
            ##################################################################
            clock_post_form_approve = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                            .filter(TimeSheetPost.accept_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
            for clock_in in clock_post_form_approve:
                if clock_in.user_status_timesheet=='Rejected':
                    flash('You have already rejected timesheets','danger')
                    return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
            #########################################
            ######Message Notification###############
            for u_all in user_all_get_form_approve:
                user = User.query.filter_by(username=u_all).first_or_404()
                count_clock_in=0
                approved_date=[]
                clock_post_init_form_approve = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                            .filter(TimeSheetPost.accept_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
                for check_clock in clock_post_init_form_approve:
                    count_clock_in=count_clock_in+1
                    if check_clock.user_status_timesheet=='Submited':
                        t_z=check_clock.day_clock
                        approved_date.append(t_z.strftime('%Y-%m-%d'))
                if count_clock_in>0 and approved_date !=[]:
                    user_message_ap='Hi {}! Your timesheet on {} has been approved.'.format(user.firstname,approved_date)
                    user_status_ap='unread'
                    user_flag_ap=''
                    user_title_ap='Time Entries Approval'
                    msg = Message(author=current_user, recipient=user,
                                    body_message=user_message_ap,
                                    body_title=user_title_ap,
                                    body_flag=user_flag_ap,
                                    body_trans='timesheet',
                                    body_id=int(0),
                                    body_date=datetime.date.today(),
                                    body_sheet=sheet_inx,
                                    body_status=user_status_ap)
                    db.session.add(msg)
                    db.session.commit()
                    ######send email to user for verification###########
                    message_email='Your timesheet on {} has been approved'.format(approved_date)
                    body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                    body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                    email(user.email,"Time Entries Approval",body_html,body_text)
                    ######send email to user for verification###########
            ########################################################
            count_int=0
            clock_post_form_approve_td = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                            .filter(TimeSheetPost.accept_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
            for clock_in in clock_post_form_approve_td:
                count_int=count_int+1
                if clock_in.user_status_timesheet!='Rejected':
                    clock_in.admin_request_timesheet='checked'
                    clock_in.user_status_timesheet='Approved'
                    clock_in.timesheet_flag=''
                    db.session.commit()
            if count_int==0:
                flash('You have not selected any timesheets','danger')
                return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
            else:
                flash('TimeSheet has been approved','success')
            #############Flag Timesheets#################
            ######Make default blank#####################
            clock_post_flag = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)).order_by(TimeSheetPost.day_clock.asc())
            for clock_inflag in clock_post_flag:
                clock_inflag.accept_flag=''
                db.session.commit()
            ################################################
            return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
        ########Reject Process###################
        if request.form['submit_button']=='Reject':
            form_approve=request.form.getlist('selectedRow[]')
            form_reject=request.form.getlist('selectedItem_new[]')
            if form_reject==[]:
                flash('You have not selected any timesheets for rejection','danger')
                return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
            if form_approve!=[]:
                flash('You cannot approved timesheets by Reject Selected buttom','danger')
                return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
            for init_form in form_reject:
                clock_posts_rej = TimeSheetPost.query.get_or_404(int(init_form))
                clock_posts_rej.reject_flag='checked'
                db.session.commit()
            ##################################################################
            #######################MESSAGE NOTIFICATION#################
            user_all_get_form_reject=[]
            user_all=User.query.filter(User.user_status=='active').order_by(User.username)
            for in_user in user_all:
                user_all_get_form_reject.append(in_user.username)
            ##################################################################
            clock_post_form_reject = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                        .filter(TimeSheetPost.reject_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
            for clock_in in clock_post_form_reject:
                if clock_in.user_status_timesheet=='Approved':
                    flash('You have already approved timesheets','danger')
                    return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
            ##################################################################
            count_check=0
            #####################MESSAGE NOTIFICATION#############
            for u_all in user_all_get_form_reject:
                user_form_reject = User.query.filter_by(username=u_all).first_or_404()
                count_clock_in=0
                approved_date=[]
                clock_post_init_form_reject = TimeSheetPost.query.filter(TimeSheetPost.author==user_form_reject,TimeSheetPost.day_clock \
                                                                    .between(start_time,end_time)).filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                                    .filter(TimeSheetPost.reject_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
                for check_clock in clock_post_init_form_reject:
                    if check_clock.user_status_timesheet=='Approved':
                        flash('Cannot be rejected, It has been approved already!!','danger')
                        return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
                    count_clock_in=count_clock_in+1
                    if check_clock.user_status_timesheet=='Submited' and check_clock.reject_flag=='checked':
                        t_z=check_clock.day_clock
                        approved_date.append(t_z.strftime('%Y-%m-%d'))
                if count_clock_in>0 and approved_date !=[]:
                    user_message_ap='Hi {}! Your timesheet on {} has been rejected.'.format(user.firstname,approved_date)
                    user_status_ap='unread'
                    user_flag_ap=''
                    user_title_ap='Time Entries Rejected'
                    msg = Message(author=current_user, recipient=user,
                                    body_message=user_message_ap,
                                    body_title=user_title_ap,
                                    body_flag=user_flag_ap,
                                    body_trans='timesheet',
                                    body_id=int(0),
                                    body_date=datetime.date.today(),
                                    body_sheet=sheet_inx,
                                    body_status=user_status_ap)
                    db.session.add(msg)
                    db.session.commit()
                    ######send email to user for verification###########
                    message_email='Your timesheet on {} has been rejected'.format(approved_date)
                    body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                    body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                    email(user.email,"Time Entries Rejected",body_html,body_text)
                    ######send email to user for verification###########
            ###############################################################
            clock_post_form_reject_td = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                            .filter(TimeSheetPost.reject_flag=='checked') \
                                                            .order_by(TimeSheetPost.day_clock.asc())
            count_int=0
            for clock_in in clock_post_form_reject_td:
                count_int=count_int+1
                if clock_in.user_status_timesheet!='Approved':
                    clock_in.timesheet_flag='checked'
                    clock_in.user_status_timesheet='Rejected'
                    db.session.commit()
            if count_int==0:
                flash('You have not selected any timesheets','danger')
                return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
            else:
                flash('TimeSheet is rejected','success')
            clock_post_flag_form_reject = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                                .order_by(TimeSheetPost.day_clock.asc())
            for clock_inflag in clock_post_flag_form_reject:
                clock_inflag.reject_flag=''
                db.session.commit()
            return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
    return render_template('/admin/timesheet_view_all.html',unique_usersheet=unique_usersheet,color_all=color_all,len_usersheet=len_usersheet,
                                                            end_time=end_day,inx_week=inx_week,post_data=clock_view_data,user_view=user_view)
#####ACTUAL DASHBOARD#################

#####DEFAULT DASHBOARD######################
@adminDash.route("/<sheet_inx>/timesheet_view_new")
@login_required
def timesheet_view_new(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    else:
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    clock_view_data=TimeSheetPost.query.filter(TimeSheetPost.user_id).filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        clock_ind=TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval').order_by(TimeSheetPost.day_clock.asc())
        count_clock_in=0
        for check_clock in clock_ind:
            count_clock_in=count_clock_in+1
        if count_clock_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ########################################
    count_all=0
    for post_ran in clock_view_data:
        count_all=count_all+1
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/admin/timesheet_view_all.html',unique_usersheet=unique_usersheet,color_all=color_all,
                                                            len_usersheet=len_usersheet,end_time=end_day,inx_week=inx_week,
                                                            post_data=clock_view_data,user_view=user_view)

@adminDash.route("/timesheet_view_all",methods=['GET','POST'])
@login_required
def timesheet_view_all():
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='Last Week':
            inx_week='last_week'
        elif view_chart=='This Month':
            inx_week='this_month'
        else:
            inx_week='this_week'
    if request.method=='GET':
        inx_week='last_week'
    return redirect(url_for('adminDash.timesheet_view',sheet_inx=inx_week))

#####ACTUAL DASHBOARD#################
@adminDash.route("/timesheet_view_all_old",methods=['GET','POST'])
@login_required
def timesheet_view_all_old():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='Last Week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
            inx_week='last_week'
        elif view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
            inx_week='this_month'
        else:
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=today_date + datetime.timedelta(idx_week)
            end_time=start_time+datetime.timedelta(7)
            end_day=start_time+datetime.timedelta(6)
            inx_week='this_week'
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    clock_view_data=TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
    #user_view=User.query.all()
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    unique_user=[]
    flag_timesheet=[]
    for in_view in clock_view_data:
        #unique_user.append(in_view.user_id)
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        clock_ind=TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock \
                                        .between(start_time,end_time)).filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
        count_clock_in=0
        for check_clock in clock_ind:
            count_clock_in=count_clock_in+1
            check_clock.accept_flag=''
            check_clock.reject_flag=''
            db.session.commit()
        if count_clock_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##############################
    count_all=0
    for post_ran in clock_view_data:
        count_all=count_all+1
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    ##################################################
    return render_template('/admin/timesheet_view_all.html',unique_usersheet=unique_usersheet,color_all=color_all,
                                                            len_usersheet=len_usersheet,end_time=end_day,inx_week=inx_week,
                                                            post_data=clock_view_data,user_view=user_view,view_unique=view_unique,
                                                            len_user=len_user,unique_user=unique_user)

######ACCEPT AND REJECT TIMESHEET FLAG#################
@adminDash.route("/<sheet_inx>/timesheet_view_acceptflag")
@login_required
def timesheet_view_acceptflag(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    else:
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    clock_view_data=TimeSheetPost.query.filter(TimeSheetPost.user_id).filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ##Finding Unique User
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        clock_ind=TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
        count_clock_in=0
        for check_clock in clock_ind:
            count_clock_in=count_clock_in+1
        if count_clock_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/timesheet_view_all_acceptflag.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                        end_time=end_day,inx_week=inx_week,post_data=clock_view_data,
                                                                        user_view=user_view)
#####ACTUAL DASHBOARD#################
@adminDash.route("/<sheet_inx>/timesheet_view_all_acceptflag",methods=['GET','POST'])
@login_required
def timesheet_view_all_acceptflag(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='This Week' or sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=start_time+datetime.timedelta(7)
            #end_time=today_date + datetime.timedelta(idx_week)
            end_day=start_time+datetime.timedelta(6)
            inx_week='this_week'
        elif view_chart=='This Month' or sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
            inx_week='this_month'
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
            inx_week='last_week'
    if request.method=='GET':
        if sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=today_date + datetime.timedelta(idx_week)
            end_time=start_time+datetime.timedelta(7)
            end_day=start_time+datetime.timedelta(6)
            inx_week='this_week'
        elif sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
            inx_week='this_month'
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
            inx_week='last_week'
    clock_view_data=TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
    #user_view=User.query.all()
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    unique_user=[]
    flag_timesheet=[]
    for in_view in clock_view_data:
        #unique_user.append(in_view.user_id)
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        clock_ind=TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
        count_clock_in=0
        for check_clock in clock_ind:
            count_clock_in=count_clock_in+1
        if count_clock_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/timesheet_view_all_acceptflag.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                        end_time=end_day,inx_week=inx_week,post_data=clock_view_data,
                                                                        user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                                        unique_user=unique_user)
#####################################################
######ACCEPT AND REJECT TIMESHEET FLAG#################
@adminDash.route("/<sheet_inx>/timesheet_view_acceptflagDash")
@login_required
def timesheet_view_acceptflagDash(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    else:
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    ##################Checked or Not################
    clock_ind=TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                    .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                    .order_by(TimeSheetPost.day_clock.asc())
    for clock_indD in clock_ind:
        if clock_indD.accept_flag=='checked':
            clock_indD.accept_flag=''
            db.session.commit()
        else:
            clock_indD.accept_flag='checked'
            db.session.commit()
    ##################################################
    return redirect(url_for('adminDash.timesheet_view',sheet_inx=inx_week))

#####Reject Timesheet Post Dash#####################
@adminDash.route("/<sheet_inx>/timesheet_view_rejectflagDash")
@login_required
def timesheet_view_rejectflagDash(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    else:
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    ##################Checked or Not################
    clock_ind=TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                    .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                    .order_by(TimeSheetPost.day_clock.asc())
    for clock_indD in clock_ind:
        if clock_indD.reject_flag=='checked':
            clock_indD.reject_flag=''
            db.session.commit()
        else:
            clock_indD.reject_flag='checked'
            db.session.commit()
    ##################################################
    return redirect(url_for('adminDash.timesheet_view',sheet_inx=inx_week))
#####ACTUAL DASHBOARD#################
@adminDash.route("/timesheet_view_all_acceptflagDash",methods=['GET','POST'])
@login_required
def timesheet_view_all_acceptflagDash():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='Last Week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
            inx_week='last_week'
        elif view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
            inx_week='this_month'
        else:
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=today_date + datetime.timedelta(idx_week)
            end_time=start_time+datetime.timedelta(7)
            end_day=start_time+datetime.timedelta(6)
            inx_week='this_week'
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    clock_view_data=TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
    #user_view=User.query.all()
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    unique_user=[]
    flag_timesheet=[]
    for in_view in clock_view_data:
        #unique_user.append(in_view.user_id)
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        clock_ind=TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .order_by(TimeSheetPost.day_clock.asc())
        count_clock_in=0
        for check_clock in clock_ind:
            count_clock_in=count_clock_in+1
            check_clock.accept_flag='checked'
            check_clock.reject_flag='checked'
            db.session.commit()
        if count_clock_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/timesheet_view_all_acceptflagDash.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                            end_time=end_day,inx_week=inx_week,post_data=clock_view_data,
                                                                            user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                                            unique_user=unique_user)
#####################################################
#########TIMESHEET APPROVAL FROM ADMIN###############
@adminDash.route("/<username>/<sheet_inx>/<int:clock_post_id>/acceptflag_user_clockpost", methods=['POST'])
@login_required
def acceptflag_user_clockpost(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    if request.method == 'POST':
        if clock_posts.accept_flag=='checked':
            clock_posts.accept_flag=''
            db.session.commit()
        else:
            clock_posts.accept_flag='checked'
            db.session.commit()
        return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))

@adminDash.route("/<username>/<sheet_inx>/<int:clock_post_id>/acceptflag_ind_clockpost", methods=['POST'])
@login_required
def acceptflag_ind_clockpost(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    if request.method == 'POST':
        if clock_posts.accept_flag=='checked':
            clock_posts.accept_flag=''
            db.session.commit()
        else:
            clock_posts.accept_flag='checked'
            db.session.commit()
        return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
###########TIMESHEET REJECT FLAG ######################
#########TIMESHEET APPROVAL FROM ADMIN###############
@adminDash.route("/<username>/<sheet_inx>/<int:clock_post_id>/rejectflag_user_clockpost", methods=['POST'])
@login_required
def rejectflag_user_clockpost(username,clock_post_id,sheet_inx):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    if request.method == 'POST':
        if clock_posts.reject_flag=='checked':
            clock_posts.reject_flag=''
            db.session.commit()
        else:
            clock_posts.reject_flag='checked'
            db.session.commit()
        return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))

@adminDash.route("/<username>/<sheet_inx>/<int:clock_post_id>/rejectflag_ind_clockpost", methods=['POST'])
@login_required
def rejectflag_ind_clockpost(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    if request.method == 'POST':
        if clock_posts.reject_flag=='checked':
            clock_posts.reject_flag=''
            db.session.commit()
        else:
            clock_posts.reject_flag='checked'
            db.session.commit()
        return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
######All Approval############
@adminDash.route("/<sheet_inx>/timesheet_admin_approval_acceptflag", methods=['POST'])
@login_required
def timesheet_admin_approval_acceptflag(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=start_time+datetime.timedelta(7)
            #end_time=today_date + datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
    #######################MESSAGE NOTIFICATION#################
    user_all_get=[]
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    for in_user in user_all:
        user_all_get.append(in_user.username)
    ############################
    count_check=0
    ##################################################################
    clock_post = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                    .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                    .filter(TimeSheetPost.accept_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
    for clock_in in clock_post:
        if clock_in.user_status_timesheet=='Rejected':
            flash('You have already rejected timesheets','danger')
            return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
        if clock_in.user_status_timesheet=='Approved':
            flash('You have already approved timesheets','danger')
            return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
    #########################################
    ######Message Notification###############
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        count_clock_in=0
        approved_date=[]
        clock_post_init = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                .filter(TimeSheetPost.accept_flag=='checked') \
                                                .order_by(TimeSheetPost.day_clock.asc())
        for check_clock in clock_post_init:
            count_clock_in=count_clock_in+1
            if check_clock.user_status_timesheet=='Submited':
                t_z=check_clock.day_clock
                approved_date.append(t_z.strftime('%Y-%m-%d'))
        if count_clock_in>0 and approved_date !=[]:
            user_message_ap='Hi {}! Your timesheet on {} has been approved.'.format(user.firstname,approved_date)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Time Entries Approval'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='timesheet',
                            body_id=int(0),
                            body_date=datetime.date.today(),
                            body_sheet=sheet_inx,
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your timesheet on {} has been approved'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Time Entries Approval",body_html,body_text)
            ######send email to user for verification###########
    ########################################################
    count_int=0
    clock_post = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .filter(TimeSheetPost.accept_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
    for clock_in in clock_post:
        count_int=count_int+1
        if clock_in.user_status_timesheet!='Rejected':
            clock_in.admin_request_timesheet='checked'
            clock_in.user_status_timesheet='Approved'
            clock_in.timesheet_flag=''
            db.session.commit()
    if count_int==0:
        flash('You have not selected any timesheets','danger')
        return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
    else:
        flash('TimeSheet has been approved','success')
    #############Flag Timesheets#################
    ######Make default blank#####################
    clock_post_flag = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                            .order_by(TimeSheetPost.day_clock.asc())
    for clock_inflag in clock_post_flag:
        clock_inflag.accept_flag=''
        db.session.commit()
    ################################################
    return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))

@adminDash.route("/<username>/<sheet_inx>/<int:clock_post_id>/acceptflag_ind_clockpostxx", methods=['POST'])
@login_required
def acceptflag_ind_clockpostxx(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    if request.method == 'POST':
        if clock_posts.accept_flag=='checked':
            clock_posts.accept_flag=''
            db.session.commit()
        else:
            clock_posts.accept_flag='checked'
            db.session.commit()
        return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))


######All Reject##########################################
@adminDash.route("/<sheet_inx>/timesheet_admin_rejectflag", methods=['POST'])
@login_required
def timesheet_admin_rejectflag(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=start_time+datetime.timedelta(7)
            #end_time=today_date + datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
    #######################MESSAGE NOTIFICATION#################
    user_all_get=[]
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    for in_user in user_all:
        user_all_get.append(in_user.username)
    ##################################################################
    clock_post = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                        .filter(TimeSheetPost.reject_flag=='checked') \
                                        .order_by(TimeSheetPost.day_clock.asc())
    for clock_in in clock_post:
        if clock_in.user_status_timesheet=='Approved':
            flash('You have already approved timesheets','danger')
            return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
        if clock_in.user_status_timesheet=='Rejected':
            flash('You have already rejected timesheets','danger')
            return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
    ##################################################################
    count_check=0
    #####################MESSAGE NOTIFICATION#############
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        count_clock_in=0
        approved_date=[]
        clock_post_init = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                .filter(TimeSheetPost.reject_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
        for check_clock in clock_post_init:
            if check_clock.user_status_timesheet=='Approved':
                flash('Cannot be rejected, It has been approved already!!','danger')
                return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
            count_clock_in=count_clock_in+1
            if check_clock.user_status_timesheet=='Submited' and check_clock.reject_flag=='checked':
                t_z=check_clock.day_clock
                approved_date.append(t_z.strftime('%Y-%m-%d'))
        if count_clock_in>0 and approved_date !=[]:
            user_message_ap='Hi {}! Your timesheet on {} has been rejected.'.format(user.firstname,approved_date)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Time Entries Rejected'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='timesheet',
                            body_id=int(0),
                            body_date=datetime.date.today(),
                            body_sheet=sheet_inx,
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your timesheet on {} has been rejected'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Time Entries Rejected",body_html,body_text)
            ######send email to user for verification###########
    ###############################################################
    clock_post = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                    .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                    .filter(TimeSheetPost.reject_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
    count_int=0
    for clock_in in clock_post:
        count_int=count_int+1
        if clock_in.user_status_timesheet!='Approved':
            clock_in.timesheet_flag='checked'
            clock_in.user_status_timesheet='Rejected'
            db.session.commit()
    if count_int==0:
        flash('You have not selected any timesheets','danger')
        return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
    else:
        flash('TimeSheet is rejected','success')
    clock_post_flag = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                            .order_by(TimeSheetPost.day_clock.asc())
    for clock_inflag in clock_post_flag:
        clock_inflag.reject_flag=''
        db.session.commit()
    return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
##########################################################
@adminDash.route("/<username>/<sheet_inx>/accept_ind_clockpost")
@login_required
def accept_ind_clockpost(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
    elif sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        #end_time=today_date + datetime.timedelta(idx_week)
    else:
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
    clock_post_init = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .order_by(TimeSheetPost.day_clock.asc())
    for clock_indD in clock_post_init:
        if clock_indD.accept_flag=='checked':
            clock_indD.accept_flag=''
            db.session.commit()
        else:
            clock_indD.accept_flag='checked'
            db.session.commit()
    return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))

##########################################################
@adminDash.route("/<username>/<sheet_inx>/reject_ind_clockpost")
@login_required
def reject_ind_clockpost(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
    elif sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        #end_time=today_date + datetime.timedelta(idx_week)
    else:
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
    clock_post_init = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .order_by(TimeSheetPost.day_clock.asc())
    for clock_indD in clock_post_init:
        if clock_indD.reject_flag=='checked':
            clock_indD.reject_flag=''
            db.session.commit()
        else:
            clock_indD.reject_flag='checked'
            db.session.commit()
    return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
############################################
@adminDash.route("/<username>/<sheet_inx>/timesheet_ind_rejectflag", methods=['POST'])
@login_required
def timesheet_ind_rejectflag(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=start_time+datetime.timedelta(7)
            #end_time=today_date + datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
        ##################################################################
        clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .filter(TimeSheetPost.reject_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
        for clock_in in clock_post:
            if clock_in.user_status_timesheet=='Approved':
                flash('You have already approved timesheets','danger')
                return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
            if clock_in.user_status_timesheet=='Rejected':
                flash('You have already rejected timesheets','danger')
                return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
        ##################################################################
        #########Message Notification############
        count_clock_in=0
        approved_date=[]
        clock_post_init = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                                .filter(TimeSheetPost.reject_flag=='checked') \
                                                .order_by(TimeSheetPost.day_clock.asc())
        for check_clock in clock_post_init:
            if check_clock.user_status_timesheet=='Approved':
                flash('Cannot be rejected, It has been approved already!!','danger')
                return redirect(url_for('adminDash.timesheet_view_acceptflag',sheet_inx=sheet_inx))
            count_clock_in=count_clock_in+1
            if check_clock.user_status_timesheet=='Submited' and check_clock.reject_flag=='checked':
                t_z=check_clock.day_clock
                approved_date.append(t_z.strftime('%Y-%m-%d'))
        if count_clock_in>0 and approved_date !=[]:
            user_message_ap='Hi {}! Your timesheet on {} has been rejected.'.format(user.firstname,approved_date)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Time Entries Rejected'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='timesheet',
                            body_sheet=sheet_inx,
                            body_id=int(0),
                            body_date=datetime.date.today(),
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your timesheet on {} has been rejected'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Time Entries Rejected",body_html,body_text)
            ######send email to user for verification###########
    ##################################################################
        clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time)) \
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval') \
                                            .filter(TimeSheetPost.reject_flag=='checked').order_by(TimeSheetPost.day_clock.asc())
        count_int=0
        for clock_in in clock_post:
            count_int=count_int+1
            if clock_in.user_status_timesheet!='Approved':
                clock_in.timesheet_flag='checked'
                clock_in.user_status_timesheet='Rejected'
                db.session.commit()
        if count_int==0:
            flash('You have not selected any timesheets','danger')
            return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
        else:
            flash('TimeSheet is rejected','success')
        clock_post_flag = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time)) \
                                                .order_by(TimeSheetPost.day_clock.asc())
        for clock_inflag in clock_post_flag:
            clock_inflag.reject_flag=''
            db.session.commit()
        return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username,sheet_inx=sheet_inx))
#########ADMIN LEAVE VIEW###############################
@adminDash.route("/<username>/<sheet_inx>/leave_view_standardF_away")
@login_required
def leave_view_standardF_away(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='last_year':
        start_time=today_date - datetime.timedelta(365)
        inx_week='last_year'
    elif sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        inx_week='default_week'
    end_time=today_date
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    leave_post=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_to.between(start_time,end_time)) \
                                .filter(LeavePost.user_status_leave=='Approved').order_by(LeavePost.leave_from.asc())
    return render_template('/admin/view_leave_standard_away.html', post_data=leave_post, inx_week=inx_week,user_all=user_all,
                                                                    user=user,end_time=end_time)
#########ADMIN TIMESHEET VIEW################
#####DEFAULT DASHBOARD######################
@adminDash.route("/<username>/leave_view_standard_away",methods=['GET','POST'])
@login_required
def leave_view_standard_away(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    #user_all=User.query.all()
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='Last Year':
            start_time=today_date - datetime.timedelta(365)
            inx_week='last_year'
        elif view_chart=='Last Week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            inx_week='last_week'
        elif view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            inx_week='this_month'
        elif view_chart=='This Week':
            start_time=today_date - datetime.timedelta(idx_week)
            inx_week='this_week'
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
            inx_week='default_week'
        end_time=today_date
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date
        inx_week='last_year'
    leave_post=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_to.between(start_time,end_time)) \
                                .filter(LeavePost.user_status_leave=='Approved').order_by(LeavePost.leave_from.asc())
    return render_template('/admin/view_leave_standard_away.html', post_data=leave_post,user_all=user_all, inx_week=inx_week,
                                                                    user=user,end_time=end_time)

#########TIMESHEET VIEW################
@adminDash.route("/<username>/<sheet_inx>/leave_csv_download_away",methods=['POST'])
def leave_csv_download_away (sheet_inx,username):
    user=User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        if sheet_inx=='last_year':
            start_time=today_date - datetime.timedelta(365)
            end_time=today_date
            end_day=today_date
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=today_date
            end_day=today_date
        elif sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date
            end_day=today_date
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date
            end_day=today_date
        end_day=end_day.strftime('%d/%m/%Y')
        leave_post=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_to.between(start_time,end_time)) \
                                    .filter(LeavePost.user_status_leave=='Approved').order_by(LeavePost.leave_from.asc())
        with open('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/leave_data.csv','w') as fp:
            data_init=csv.writer(fp)
            data_init.writerow(['Leave request for:{}'.format(user.username)])
            data_init.writerow(['Week Ending:{}'.format(end_day)])
            data_init.writerow(['Start Day','End Day','Total Days','Types','User Status'])
            for cp_in in leave_post:
                data_init_post=[cp_in.leave_from.strftime('%d/%m/%Y'),cp_in.leave_to.strftime('%d/%m/%Y'),cp_in.leave_days, \
                                cp_in.leave_type,cp_in.user_status_leave]
                data_init.writerow(data_init_post)
            data_f=['','','','','','']
            data_init.writerow(data_f)
        try:
            return send_file('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/leave_data.csv',
                            mimetype='text/csv',attachment_filename='leave_data.csv',as_attachment=True)
        except:
            flash('File not supported format','danger')
            return redirect(url_for('adminDash.leave_view_standardF_away',username=username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.leave_view_standardF_away',username=username,sheet_inx=sheet_inx))
############################################
######Submitted Status#####################
#########ADMIN LEAVE VIEW###############################
@adminDash.route("/<username>/<sheet_inx>/leave_view_standardF_submit",methods=['POST','GET'])
@login_required
def leave_view_standardF_submit(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='last_year':
        start_time=today_date - datetime.timedelta(365)
        inx_week='last_year'
    elif sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        inx_week='default_week'
    end_time=today_date + datetime.timedelta(365)
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    leave_post=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                .filter(or_(LeavePost.user_status_leave=='Submited',LeavePost.user_status_leave=='Rejected')) \
                                .order_by(LeavePost.leave_from.asc())
    for leave_inflag_form in leave_post:
        leave_inflag_form.reject_flag=''
        leave_inflag_form.accept_flag=''
        db.session.commit()
    ##########################################################
    if request.method=='POST':
        if request.form['submit_button']=='Approve':
            form_approve=request.form.getlist('selectedRow[]')
            form_reject=request.form.getlist('selectedItem_new[]')
            if form_approve==[]:
                flash('You have not selected any leave request for approval','danger')
                return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            if form_reject!=[]:
                flash('You cannot reject leave request by Approval Selected buttom','danger')
                return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            for init_form in form_approve:
                leave_posts_form = LeavePost.query.get_or_404(int(init_form))
                leave_posts_form.accept_flag='checked'
                db.session.commit()
            #####################
            leave_post_form_approve=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                                        .filter(or_(LeavePost.user_status_leave=='Submited',LeavePost.user_status_leave=='Rejected')) \
                                                        .filter(LeavePost.accept_flag=='checked').order_by(LeavePost.leave_from.asc())
            for leave_in in leave_post_form_approve:
                if leave_in.user_status_leave=='Rejected':
                    flash('You have already rejected leave request','danger')
                    return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            ########################################
            #leave_post_init = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)).filter(LeavePost.user_request_leave=='request_approval').filter(LeavePost.reject_flag=='checked').order_by(LeavePost.leave_from.asc())
            count_leave_in=0
            approved_date=[]
            leave_post_init=leave_post_form_approve
            #leave_post_init = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)).filter(LeavePost.user_request_leave=='request_approval').filter(LeavePost.accept_flag=='checked').order_by(LeavePost.leave_from.asc())
            for check_leave in leave_post_init:
                count_leave_in=count_leave_in+1
                if check_leave.user_status_leave=='Submited':
                    t_z=check_leave.leave_from
                    approved_date.append(t_z.strftime('%Y-%m-%d'))
            if count_leave_in>0 and approved_date !=[]:
                user_message_ap='Hi {}! Your leave request has been approved.'.format(user.firstname)
                user_status_ap='unread'
                user_flag_ap=''
                user_title_ap='Leave Request Approval'
                msg = Message(author=current_user, recipient=user,
                                body_message=user_message_ap,
                                body_title=user_title_ap,
                                body_flag=user_flag_ap,
                                body_trans='leave_request',
                                body_id=int(0),
                                body_date=datetime.date.today(),
                                body_sheet=sheet_inx,
                                body_status=user_status_ap)
                db.session.add(msg)
                db.session.commit()
                ######send email to user for verification###########
                message_email='Your leave request on {} has been approved'.format(approved_date)
                body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                email(user.email,"Leave Request Approval",body_html,body_text)
                ######send email to user for verification###########
            count_int=0
            leave_postR=leave_post_form_approve
            #leave_postR = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)).filter(LeavePost.user_request_leave=='request_approval').filter(LeavePost.accept_flag=='checked').order_by(LeavePost.leave_from.asc())
            for leave_in in leave_postR:
                count_int=count_int+1
                if leave_in.user_status_leave!='Rejected':
                    leave_in.admin_request_leave='checked'
                    leave_in.user_status_leave='Approved'
                    leave_in.leave_flag=''
                    db.session.commit()
                    ###################Timesheet Management Automatically########
                    start_lv=datetime.time()
                    end_lv=datetime.time()
                    start_lv=leave_in.leave_from.date()
                    end_lv=leave_in.leave_to.date()
                    delta = datetime.timedelta(days=1)
                    d_in=start_lv
                    inc_d=0
                    while d_in <=end_lv:
                        day_time=leave_in.leave_from+datetime.timedelta(inc_d)
                        inc_d=inc_d+1
                        inx_day=d_in.strftime('%A')
                        if(inx_day=='Saturday' or inx_day=='Sunday' or leave_in.leave_type=='Leave without Pay'):
                            clock_post_default = TimeSheetPost(day_clock=day_time,project=leave_in.leave_type,
                                                        comment='',clock_in=datetime.date.today(),
                                                        task=leave_in.leave_type,travel_choice='',
                                                        clock_out=datetime.date.today(),distance='',
                                                        OverTime_15=int(0),NormalTime=int(0),
                                                        OverTime_2=int(0),location='',OverTime_25=int(0),
                                                        Launch_Break=int(0),timesheet_status=False,
                                                        timesheet_flag='',user_request_timesheet='request_approval',
                                                        admin_request_timesheet='',user_status_timesheet='Approved',
                                                        meal_type='default',meal_rate_day=float(0),meal_allowance='no',
                                                        user_check_timesheet='',job_num='-',
                                                        remainder='',accept_flag='',
                                                        reject_flag='',user_id=leave_in.author.id)
                            db.session.add(clock_post_default)
                            db.session.commit()
                        else:
                            clock_post_default = TimeSheetPost(day_clock=day_time,project=leave_in.leave_type,
                                                        comment='',clock_in=datetime.date.today(),
                                                        task=leave_in.leave_type,travel_choice='',
                                                        clock_out=datetime.date.today(),distance='',
                                                        OverTime_15=int(0),NormalTime=int(8),
                                                        OverTime_2=int(0),location='',OverTime_25=int(0),
                                                        Launch_Break=int(0),timesheet_status=False,
                                                        timesheet_flag='',user_request_timesheet='request_approval',
                                                        admin_request_timesheet='',user_status_timesheet='Approved',
                                                        meal_type='default',meal_rate_day=float(0),meal_allowance='no',
                                                        user_check_timesheet='',job_num='-',
                                                        remainder='',accept_flag='',
                                                        reject_flag='',user_id=leave_in.author.id)
                            db.session.add(clock_post_default)
                            db.session.commit()
                        d_in = d_in + delta
            if count_int==0:
                flash('You have not selected any leave request','danger')
                return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            else:
                flash('Leave request has been approved','success')
                #############Flag Timesheets#################
                ######Make default blank#####################
            leave_post_flag_form_approve = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from \
                                                            .between(start_time,end_time)).order_by(LeavePost.leave_from.asc())
            for leave_inflag in leave_post_flag_form_approve:
                leave_inflag.accept_flag=''
                db.session.commit()
                return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        ##################################################################
        if request.form['submit_button']=='Reject':
            form_approve=request.form.getlist('selectedRow[]')
            form_reject=request.form.getlist('selectedItem_new[]')
            if form_reject==[]:
                flash('You have not selected any leave request for rejection','danger')
                return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            if form_approve!=[]:
                flash('You cannot approved leave request by Reject Selected buttom','danger')
                return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            for init_form in form_reject:
                leave_posts_rej = LeavePost.query.get_or_404(int(init_form))
                leave_posts_rej.reject_flag='checked'
                db.session.commit()
            leave_post_form_reject=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                                    .filter(or_(LeavePost.user_status_leave=='Submited',LeavePost.user_status_leave=='Rejected')) \
                                                    .filter(LeavePost.reject_flag=='checked').order_by(LeavePost.leave_from.asc())
            for leave_in in leave_post_form_reject:
                if leave_in.user_status_leave=='Approved':
                    flash('You have already approved leave request','danger')
                    return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            ##################################################################
            #########Message Notification############
            count_leave_in=0
            approved_date=[]
            leave_post_init=leave_post_form_reject
            #leave_post_init = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)).filter(LeavePost.user_request_leave=='request_approval').filter(LeavePost.reject_flag=='checked').order_by(LeavePost.leave_from.asc())
            for check_leave in leave_post_init:
                if check_leave.user_status_leave=='Approved':
                    flash('Cannot be rejected, It has been approved already!!','danger')
                    return redirect(url_for('adminDash.leave_view_acceptflag',sheet_inx=sheet_inx))
                count_leave_in=count_leave_in+1
                if check_leave.user_status_leave=='Submited' and check_leave.reject_flag=='checked':
                    t_z=check_leave.leave_from
                    approved_date.append(t_z.strftime('%Y-%m-%d'))
            if count_leave_in>0 and approved_date !=[]:
                user_message_ap='Hi {}! Your leave request on {} has been rejected.'.format(user.firstname,approved_date)
                user_status_ap='unread'
                user_flag_ap=''
                user_title_ap='Leave Request Rejected'
                msg = Message(author=current_user, recipient=user,
                                body_message=user_message_ap,
                                body_title=user_title_ap,
                                body_flag=user_flag_ap,
                                body_trans='leave_request',
                                body_id=int(0),###Qrcode ID
                                body_date=datetime.date.today(),
                                body_sheet=sheet_inx,
                                body_status=user_status_ap)
                db.session.add(msg)
                db.session.commit()
                ######send email to user for verification###########
                message_email='Your leave request on {} has been rejected'.format(approved_date)
                body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                email(user.email,"Leave Request Rejected",body_html,body_text)
                ######send email to user for verification###########
            #leave_post = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)).filter(LeavePost.user_request_leave=='request_approval').filter(LeavePost.reject_flag=='checked').order_by(LeavePost.leave_from.asc())
            count_int=0
            for leave_in in leave_post_form_reject:
                count_int=count_int+1
                if leave_in.user_status_leave!='Approved':
                    leave_in.timesheet_flag='checked'
                    leave_in.user_status_leave='Rejected'
                    db.session.commit()
            if count_int==0:
                flash('You have not selected any leave request','danger')
                return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            else:
                flash('Leave request is rejected','success')
            leave_post_flag_form_reject = LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                                            .order_by(LeavePost.leave_from.asc())
            for leave_inflag in leave_post_flag_form_reject:
                leave_inflag.reject_flag=''
                db.session.commit()
            return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
    return render_template('/admin/view_leave_standard_submit.html', post_data=leave_post, inx_week=inx_week,user_all=user_all,
                                                                        user=user,end_time=end_time)
#########ADMIN TIMESHEET VIEW################
#####DEFAULT DASHBOARD######################
@adminDash.route("/<username>/leave_view_standard_submit",methods=['GET','POST'])
@login_required
def leave_view_standard_submit(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='Last Year':
            inx_week='last_year'
        elif view_chart=='Last Week':
            inx_week='last_week'
        elif view_chart=='This Month':
            inx_week='this_month'
        elif view_chart=='This Week':
            inx_week='this_week'
        else:
            inx_week='default_week'
    if request.method=='GET':
        inx_week='last_year'
    return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=inx_week))

#########TIMESHEET VIEW################
@adminDash.route("/<username>/leave_view_standard_submit_new",methods=['GET','POST'])
@login_required
def leave_view_standard_submit_new(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    #user_all=User.query.all()
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='Last Year':
            start_time=today_date - datetime.timedelta(365)
            inx_week='last_year'
        elif view_chart=='Last Week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            inx_week='last_week'
        elif view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            inx_week='this_month'
        elif view_chart=='This Week':
            start_time=today_date - datetime.timedelta(idx_week)
            inx_week='this_week'
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
            inx_week='default_week'
        end_time=today_date + datetime.timedelta(365)
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(365)
        inx_week='last_year'
    leave_post=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                .filter(or_(LeavePost.user_status_leave=='Submited',LeavePost.user_status_leave=='Rejected')) \
                                .order_by(LeavePost.leave_from.asc())
    return render_template('/admin/view_leave_standard_submit.html', post_data=leave_post,user_all=user_all,
                                                                    inx_week=inx_week,user=user,end_time=end_time)

#########TIMESHEET VIEW################
@adminDash.route("/<username>/<sheet_inx>/leave_csv_download_submit")
def leave_csv_download_submit (sheet_inx,username):
    user=User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='last_year':
        start_time=today_date - datetime.timedelta(365)
        inx_week='last_year'
    elif sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        inx_week='default_week'
    end_time=today_date + datetime.timedelta(365)
    end_day=today_date + datetime.timedelta(365)
    end_day=end_day.strftime('%d/%m/%Y')
    ##################################################
    leave_post=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                .filter(or_(LeavePost.user_status_leave=='Submited',LeavePost.user_status_leave=='Rejected')) \
                                .order_by(LeavePost.leave_from.asc())
    with open('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/leave_data.csv','w') as fp:
        data_init=csv.writer(fp)
        data_init.writerow(['Leave request for:{}'.format(user.username)])
        data_init.writerow(['Week Ending:{}'.format(end_day)])
        data_init.writerow(['Start Day','End Day','Total Days','Types','User Status'])
        for cp_in in leave_post:
            data_init_post=[cp_in.leave_from.strftime('%d/%m/%Y'),cp_in.leave_to.strftime('%d/%m/%Y'),cp_in.leave_days, \
                            cp_in.leave_type,cp_in.user_status_leave]
            data_init.writerow(data_init_post)
        data_f=['','','','','','']
        data_init.writerow(data_f)
    try:
        return send_file('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/leave_data.csv',
                        mimetype='text/csv',attachment_filename='leave_data.csv',as_attachment=True)
    except:
        flash('File not supported format','danger')
        return redirect(url_for('adminDash.leave_view_standardF_submit',username=username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.leave_view_standardF_submit',username=username,sheet_inx=sheet_inx))
###########################################
@adminDash.route("/<username>/<sheet_inx>/leave_view_standardF_upcom")
@login_required
def leave_view_standardF_upcom(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='last_year':
        end_time=today_date + datetime.timedelta(365)
        inx_week='last_year'
    elif sheet_inx=='this_week':
        end_time=today_date + datetime.timedelta(idx_week)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        end_time=today_date+ datetime.timedelta(21+idx_week)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        end_time=today_date+ datetime.timedelta(7+idx_week)
        inx_week='last_week'
    else:
        end_time=today_date+ datetime.timedelta(49+idx_week)
        inx_week='default_week'
    start_time=today_date
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    leave_post=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_to.between(start_time,end_time)) \
                                .filter(LeavePost.user_status_leave=='Approved').order_by(LeavePost.leave_from.asc())
    return render_template('/admin/view_leave_standard_upcom.html', post_data=leave_post, inx_week=inx_week,user_all=user_all,
                                                                        user=user,end_time=end_time)
#########ADMIN TIMESHEET VIEW################
#####DEFAULT DASHBOARD######################
@adminDash.route("/<username>/leave_view_standard_upcom",methods=['GET','POST'])
@login_required
def leave_view_standard_upcom(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    #user_all=User.query.all()
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='Year':
            end_time=today_date + datetime.timedelta(365)
            inx_week='last_year'
        elif view_chart=='Fortnight':
            end_time=today_date + datetime.timedelta(7+idx_week)
            inx_week='last_week'
        elif view_chart=='Month':
            end_time=today_date + datetime.timedelta(21+idx_week)
            inx_week='this_month'
        elif view_chart=='Week':
            end_time=today_date + datetime.timedelta(idx_week)
            inx_week='this_week'
        else:
            end_time=today_date + datetime.timedelta(49+idx_week)
            inx_week='default_week'
        start_time=today_date
    if request.method=='GET':
        start_time=today_date
        end_time=today_date+ datetime.timedelta(49+idx_week)
        inx_week='last_year'
    leave_post=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_to.between(start_time,end_time)) \
                                .filter(LeavePost.user_status_leave=='Approved').order_by(LeavePost.leave_from.asc())
    return render_template('/admin/view_leave_standard_upcom.html', post_data=leave_post,user_all=user_all,
                                                                    inx_week=inx_week,user=user,end_time=end_time)

#########TIMESHEET VIEW################
@adminDash.route("/<username>/<sheet_inx>/leave_csv_download_upcom",methods=['POST'])
def leave_csv_download_upcom (sheet_inx,username):
    user=User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        if sheet_inx=='last_year':
            end_time=today_date + datetime.timedelta(365)
            end_day=today_date + datetime.timedelta(365)
        elif sheet_inx=='this_week':
            end_time=today_date + datetime.timedelta(idx_week)
            end_day=start_time+datetime.timedelta(6)
        elif sheet_inx=='this_month':

            end_time=today_date+ datetime.timedelta(21+idx_week)
            end_day=today_date - datetime.timedelta(idx_week+22)
        else:
            end_time=today_date+ datetime.timedelta(7+idx_week)
            end_day=today_date + datetime.timedelta(idx_week+8)
        end_day=end_day.strftime('%d/%m/%Y')
        start_time=today_date
        ##################################################
        leave_post=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_to.between(start_time,end_time)) \
                                    .filter(LeavePost.user_status_leave=='Approved').order_by(LeavePost.leave_from.asc())
        with open('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/leave_data.csv','w') as fp:
            data_init=csv.writer(fp)
            data_init.writerow(['Leave request for:{}'.format(user.username)])
            data_init.writerow(['Week Ending:{}'.format(end_day)])
            data_init.writerow(['Start Day','End Day','Total Days','Types','User Status'])
            for cp_in in leave_post:
                data_init_post=[cp_in.leave_from.strftime('%d/%m/%Y'),cp_in.leave_to.strftime('%d/%m/%Y'),cp_in.leave_days, \
                                cp_in.leave_type,cp_in.user_status_leave]
                data_init.writerow(data_init_post)
            data_f=['','','','','','']
            data_init.writerow(data_f)
        try:
            return send_file('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/leave_data.csv',
                            mimetype='text/csv',attachment_filename='leave_data.csv',as_attachment=True)
        except:
            flash('File not supported format','danger')
            return redirect(url_for('adminDash.leave_view_standardF_upcom',username=username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.leave_view_standardF_upcom',username=username,sheet_inx=sheet_inx))
################################

@adminDash.route('/<sheet_inx>/leave_view_new')
@login_required
def leave_view_new(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date- datetime.timedelta(49+idx_week)
    start_time_away=today_date- datetime.timedelta(14+idx_week)
    end_time=today_date + datetime.timedelta(365)
    end_time_away=today_date
    start_time_upcom=today_date
    post_submit=LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                .filter(or_(LeavePost.user_status_leave=='Submited',LeavePost.user_status_leave=='Rejected')) \
                                .order_by(LeavePost.leave_from.asc())
    post_away=LeavePost.query.filter(LeavePost.leave_to.between(start_time_away,end_time_away)) \
                                .filter(LeavePost.user_status_leave=='Approved')\
                                .order_by(LeavePost.leave_from.asc())
    post_upcom=LeavePost.query.filter(LeavePost.leave_to.between(start_time_upcom,end_time)).filter(LeavePost.user_status_leave=='Approved') \
                                .order_by(LeavePost.leave_from.asc())
    #############################
    count_all_1=0
    count_all_2=0
    count_all_3=0
    count_all=0
    for post_ran in post_submit:
        count_all_1=count_all_1+1
    for post_rand in post_away:
        count_all_2=count_all_2+1
    for post_randit in post_upcom:
        count_all_3=count_all_3+1
    count_all=count_all_1+count_all_2+count_all_3
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/admin/leave_view_all_new.html',post_submit=post_submit,post_upcom=post_upcom,
                                                            post_away=post_away,color_all=color_all,
                                                            sheet_inx=sheet_inx)

@adminDash.route('/<sheet_inx>/invoice_view_new_daterange',methods=['POST','GET'])
@login_required
def invoice_view_new_daterange(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        start_time_str=request.form.get('from_select')
        end_time_str=request.form.get('to_select')
        if start_time_str=='' or end_time_str=='':
            flash('Select the correct date range format','danger')
            return redirect(url_for('adminDash.invoice_view_new',sheet_inx=sheet_inx))
        start_time_paid = datetime.datetime.strptime(start_time_str,'%d/%m/%Y')
        end_time_paid = datetime.datetime.strptime(end_time_str,'%d/%m/%Y')
        if start_time_paid>end_time_paid:
            flash('Select the correct date range format','danger')
            return redirect(url_for('adminDash.invoice_view_new',sheet_inx=sheet_inx))
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        post_submit=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time)) \
                                        .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected')) \
                                        .order_by(InvoicePost.invoice_from.asc())
        post_paid=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time_paid,end_time_paid)) \
                                     .filter(InvoicePost.user_status_invoice=='Approved') \
                                     .order_by(InvoicePost.invoice_from.asc())
        #############################
        count_all_1=0
        count_all_2=0
        count_all=0
        for post_ran in post_submit:
            count_all_1=count_all_1+1
        for post_rand in post_paid:
            count_all_2=count_all_2+1
        count_all=count_all_1+count_all_2
        color_all=[]
        color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
        for random_count in range(count_all):
            color_r=random.choice(color_choice)
            color_all.append(color_r)
        return render_template('/admin/invoice_view_all_new.html',post_submit=post_submit,color_all=color_all,
                                                                    sheet_inx=sheet_inx,post_paid=post_paid)
    return render_template('/admin/invoice_view_all_new.html',post_submit=post_submit,color_all=color_all,
                                                                sheet_inx=sheet_inx,post_paid=post_paid)
#####DEFAULT DASHBOARD######################

#####DEFAULT DASHBOARD######################

@adminDash.route('/<sheet_inx>/leave_view_new_daterange',methods=['GET','POST'])
@login_required
def leave_view_new_daterange(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        start_time_str=request.form.get('from_select')
        end_time_str=request.form.get('to_select')
        if start_time_str=='' or end_time_str=='':
            flash('Select the date range','danger')
            return redirect(url_for('adminDash.leave_view_new',sheet_inx=sheet_inx))
        start_time_away = datetime.datetime.strptime(start_time_str,'%d/%m/%Y')
        end_time_away = datetime.datetime.strptime(end_time_str,'%d/%m/%Y')
        if start_time_away>end_time_away:
            flash('Select the date range','danger')
            return redirect(url_for('adminDash.leave_view_new',sheet_inx=sheet_inx))
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(365)
        start_time_upcom=today_date
        post_submit=LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(or_(LeavePost.user_status_leave=='Submited',LeavePost.user_status_leave=='Rejected')) \
                                    .order_by(LeavePost.leave_from.asc())
        post_away=LeavePost.query.filter(LeavePost.leave_to.between(start_time_away,end_time_away)) \
                                    .filter(LeavePost.user_status_leave=='Approved').order_by(LeavePost.leave_from.asc())
        post_upcom=LeavePost.query.filter(LeavePost.leave_to.between(start_time_upcom,end_time)) \
                                    .filter(LeavePost.user_status_leave=='Approved').order_by(LeavePost.leave_from.asc())
        #############################
        count_all_1=0
        count_all_2=0
        count_all_3=0
        count_all=0
        for post_ran in post_submit:
            count_all_1=count_all_1+1
        for post_rand in post_away:
            count_all_2=count_all_2+1
        for post_randit in post_upcom:
            count_all_3=count_all_3+1
        count_all=count_all_1+count_all_2+count_all_3
        color_all=[]
        color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
        for random_count in range(count_all):
            color_r=random.choice(color_choice)
            color_all.append(color_r)
        return render_template('/admin/leave_view_all_new.html',post_submit=post_submit,post_upcom=post_upcom,
                                                                post_away=post_away,color_all=color_all,
                                                                sheet_inx=sheet_inx)
    return render_template('/admin/leave_view_all_new.html',post_submit=post_submit,post_upcom=post_upcom,post_away=post_away,
                                                                color_all=color_all,sheet_inx=sheet_inx)

@adminDash.route('/<sheet_inx>/invoice_view_new')
@login_required
def invoice_view_new(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date- datetime.timedelta(49+idx_week)
    start_time_paid=today_date- datetime.timedelta(14+idx_week)
    end_time=today_date + datetime.timedelta(idx_week)
    post_submit=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time)) \
                                    .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected')) \
                                    .order_by(InvoicePost.invoice_from.asc())
    post_paid=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time_paid,end_time)) \
                                .filter(InvoicePost.user_status_invoice=='Approved') \
                                .order_by(InvoicePost.invoice_from.asc())
    #############################
    count_all_1=0
    count_all_2=0
    count_all=0
    for post_ran in post_submit:
        count_all_1=count_all_1+1
    for post_rand in post_paid:
        count_all_2=count_all_2+1
    count_all=count_all_1+count_all_2
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/admin/invoice_view_all_new.html',post_submit=post_submit,color_all=color_all,
                                                                sheet_inx=sheet_inx,post_paid=post_paid)
#####DEFAULT DASHBOARD######################
@adminDash.route("/<sheet_inx>/leave_view")
@login_required
def leave_view(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='last_year':
        start_time=today_date - datetime.timedelta(365)
        inx_week='last_year'
    elif sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        inx_week='default_week'
    end_time=today_date + datetime.timedelta(365)
    leave_view_data=LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                        .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    unique_user=[]
    for in_view in leave_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    #########################
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        leave_ind=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
        count_leave_in=0
        for check_leave in leave_ind:
            count_leave_in=count_leave_in+1
            db.session.commit()
        if count_leave_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/leave_view_all.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                        post_data=leave_view_data,inx_week=inx_week,end_time=end_time,
                                                        user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                        unique_user=unique_user)

#####ACTUAL LEAVE DASHBOARD#################
@adminDash.route("/leave_view_all",methods=['GET','POST'])
@login_required
def leave_view_all():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='Last Year':
            start_time=today_date - datetime.timedelta(365)
            inx_week='last_year'
        elif view_chart=='This Week':
            start_time=today_date - datetime.timedelta(idx_week)
            inx_week='this_week'
        elif view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            inx_week='this_month'
        elif view_chart=='Last Week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            inx_week='last_week'
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
            inx_week='default_week'
        end_time=today_date + datetime.timedelta(365)
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(365)
        inx_week='default_week'
    leave_view_data=LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(LeavePost.user_request_leave=='request_approval') \
                                    .order_by(LeavePost.leave_from.asc())
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ##Finding Unique User
    unique_user=[]
    for in_view in leave_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    #########################
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        leave_ind=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
        count_leave_in=0
        for check_leave in leave_ind:
            count_leave_in=count_leave_in+1
            check_leave.accept_flag=''
            check_leave.reject_flag=''
            db.session.commit()
        if count_leave_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/leave_view_all.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                            post_data=leave_view_data,inx_week=inx_week,end_time=end_time,
                                                            user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                            unique_user=unique_user)
######ACCEPT AND REJECT FLAG ##############
@adminDash.route("/leave_view_acceptflag")
@login_required
def leave_view_acceptflag():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date- datetime.timedelta(49+idx_week)
    end_time=today_date + datetime.timedelta(365)
    inx_week='last_year'
    leave_view_data=LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                        .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
    #user_view=User.query.all()
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ##Finding Unique User
    unique_user=[]
    for in_view in leave_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    #########################
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        leave_ind=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
        count_leave_in=0
        for check_leave in leave_ind:
            count_leave_in=count_leave_in+1
        if count_leave_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/leave_view_all_acceptflag.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                    post_data=leave_view_data,inx_week=inx_week,end_time=end_time,
                                                                    user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                                    unique_user=unique_user)

#####ACTUAL LEAVE DASHBOARD#################
@adminDash.route("/leave_view_all_acceptflag",methods=['GET','POST'])
@login_required
def leave_view_all_acceptflag():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='Last Year':
            start_time=today_date - datetime.timedelta(365)
            inx_week='last_year'
        elif view_chart=='Last Week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            inx_week='last_week'
        elif view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            inx_week='this_month'
        else:
            start_time=today_date - datetime.timedelta(idx_week)
            inx_week='this_week'
        end_time=today_date + datetime.timedelta(365)
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(365)
        inx_week='last_year'
    leave_view_data=LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
    #user_view=User.query.all()
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ##Finding Unique User
    unique_user=[]
    for in_view in leave_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    #########################
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        leave_ind=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
        count_leave_in=0
        for check_leave in leave_ind:
            count_leave_in=count_leave_in+1
        if count_leave_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/leave_view_all_acceptflag.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                    post_data=leave_view_data,inx_week=inx_week,end_time=end_time,
                                                                    user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                                    unique_user=unique_user)
##########################################
@adminDash.route("/<sheet_inx>/leave_view_acceptflagDash")
@login_required
def leave_view_acceptflagDash(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='last_year':
        start_time=today_date - datetime.timedelta(365)
    elif sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
    end_time=today_date + datetime.timedelta(365)
    leave_ind=LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                .filter(LeavePost.user_request_leave=='request_approval')\
                                .order_by(LeavePost.leave_from.asc())
    for leave_indD in leave_ind:
        if leave_indD.accept_flag=='checked':
            leave_indD.accept_flag=''
            db.session.commit()
        else:
            leave_indD.accept_flag='checked'
            db.session.commit()
    ##################################################
    return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))

##########################################
@adminDash.route("/<sheet_inx>/leave_view_rejectflagDash")
@login_required
def leave_view_rejectflagDash(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='last_year':
        start_time=today_date - datetime.timedelta(365)
    elif sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
    end_time=today_date + datetime.timedelta(365)
    leave_ind=LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
    for leave_indD in leave_ind:
        if leave_indD.reject_flag=='checked':
            leave_indD.reject_flag=''
            db.session.commit()
        else:
            leave_indD.reject_flag='checked'
            db.session.commit()
    ##################################################
    return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
    ##################Checked or Not################
#####ACTUAL LEAVE DASHBOARD#################
@adminDash.route("/leave_view_all_acceptflagDash",methods=['GET','POST'])
@login_required
def leave_view_all_acceptflagDash():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='Last Year':
            start_time=today_date - datetime.timedelta(365)
            inx_week='last_year'
        elif view_chart=='Last Week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            inx_week='last_week'
        elif view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            inx_week='this_month'
        else:
            start_time=today_date - datetime.timedelta(idx_week)
            inx_week='this_week'
        end_time=today_date + datetime.timedelta(365)
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(365)
        inx_week='last_year'
    leave_view_data=LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                        .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
    #user_view=User.query.all()
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ##Finding Unique User
    unique_user=[]
    for in_view in leave_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        leave_ind=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
        count_leave_in=0
        for check_leave in leave_ind:
            count_leave_in=count_leave_in+1
            check_leave.accept_flag='checked'
            check_leave.reject_flag='checked'
            db.session.commit()
        if count_leave_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/leave_view_all_acceptflagDash.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                        post_data=leave_view_data,inx_week=inx_week,end_time=end_time,
                                                                        user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                                        unique_user=unique_user)

#########TIMESHEET APPROVAL FROM ADMIN###############
@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/acceptflag_ind_leavepost")
@login_required
def acceptflag_ind_leavepost(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    if leave_posts.accept_flag=='checked':
        leave_posts.accept_flag=''
        db.session.commit()
    else:
        leave_posts.accept_flag='checked'
        db.session.commit()
    return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))

@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/acceptflag_user_leavepost", methods=['POST'])
@login_required
def acceptflag_user_leavepost(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    if request.method == 'POST':
        if leave_posts.accept_flag=='checked':
            leave_posts.accept_flag=''
            db.session.commit()
        else:
            leave_posts.accept_flag='checked'
            db.session.commit()
        return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.leave_view_acceptflag',sheet_inx=sheet_inx))
###########TIMESHEET REJECT FLAG ######################
#########TIMESHEET APPROVAL FROM ADMIN###############
@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/rejectflag_user_leavepost", methods=['POST'])
@login_required
def rejectflag_user_leavepost(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    if request.method == 'POST':
        if leave_posts.reject_flag=='checked':
            leave_posts.reject_flag=''
            db.session.commit()
        else:
            leave_posts.reject_flag='checked'
            db.session.commit()
        return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))

@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/rejectflag_ind_leavepost")
@login_required
def rejectflag_ind_leavepost(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    if leave_posts.reject_flag=='checked':
        leave_posts.reject_flag=''
        db.session.commit()
    else:
        leave_posts.reject_flag='checked'
        db.session.commit()
    return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))

@adminDash.route("/<sheet_inx>/leave_admin_approval_acceptflag", methods=['POST'])
@login_required
def leave_admin_approval_acceptflag(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='last_year':
            start_time=today_date - datetime.timedelta(365)
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
        elif sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(365)
    ##################################################################
        leave_post = LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                        .filter(LeavePost.user_request_leave=='request_approval') \
                                        .filter(LeavePost.accept_flag=='checked').order_by(LeavePost.leave_from.asc())
        for leave_in in leave_post:
            if leave_in.user_status_leave=='Rejected':
                flash('You have already rejected leave request','danger')
                return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
            if leave_in.user_status_leave=='Approved':
                flash('You have already approved leave request','danger')
                return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
    #########################################
    ######Message Notification###############
        user_all_get=[]
        user_all=User.query.filter(User.user_status=='active').order_by(User.username)
        for in_user in user_all:
            user_all_get.append(in_user.username)
    ###########################################
        for u_all in user_all_get:
            user = User.query.filter_by(username=u_all).first_or_404()
            count_leave_in=0
            approved_date=[]
            leave_post_init = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                                .filter(LeavePost.user_request_leave=='request_approval') \
                                                .filter(LeavePost.accept_flag=='checked').order_by(LeavePost.leave_from.asc())
            for check_leave in leave_post_init:
                count_leave_in=count_leave_in+1
                if check_leave.user_status_leave=='Submited':
                    t_z=check_leave.leave_from
                    approved_date.append(t_z.strftime('%Y-%m-%d'))
            if count_leave_in>0 and approved_date !=[]:
                user_message_ap='Hi {}! Your leave request has been approved.'.format(user.firstname)
                user_status_ap='unread'
                user_flag_ap=''
                user_title_ap='Leave Request Approval'
                msg = Message(author=current_user, recipient=user,
                                body_message=user_message_ap,
                                body_title=user_title_ap,
                                body_flag=user_flag_ap,
                                body_trans='leave_request',
                                body_id=int(0),
                                body_date=datetime.date.today(),
                                body_sheet=sheet_inx,
                                body_status=user_status_ap)
                db.session.add(msg)
                db.session.commit()
                ######send email to user for verification###########
                message_email='Your leave request on {} has been approved'.format(approved_date)
                body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                email(user.email,"Leave Request Approval",body_html,body_text)
                ######send email to user for verification###########
        count_int=0
        leave_post = LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                        .filter(LeavePost.user_request_leave=='request_approval') \
                                        .filter(LeavePost.accept_flag=='checked').order_by(LeavePost.leave_from.asc())
        for leave_in in leave_post:
            count_int=count_int+1
            if leave_in.user_status_leave!='Rejected':
                leave_in.admin_request_leave='checked'
                leave_in.user_status_leave='Approved'
                leave_in.leave_flag=''
                db.session.commit()
                ###################Timesheet Management Automatically########
                start_lv=datetime.time()
                end_lv=datetime.time()
                start_lv=leave_in.leave_from.date()
                end_lv=leave_in.leave_to.date()
                delta = datetime.timedelta(days=1)
                d_in=start_lv
                inc_d=0
                while d_in <=end_lv:
                    day_time=leave_in.leave_from+datetime.timedelta(inc_d)
                    inc_d=inc_d+1
                    inx_day=d_in.strftime('%A')
                    if(inx_day=='Saturday' or inx_day=='Sunday' or leave_in.leave_type=='Leave without Pay'):
                        clock_post_default = TimeSheetPost(day_clock=day_time,project=leave_in.leave_type,
                                                    comment='',clock_in=datetime.date.today(),
                                                    task=leave_in.leave_type,travel_choice='',
                                                    clock_out=datetime.date.today(),distance='',
                                                    OverTime_15=int(0),NormalTime=int(0),
                                                    OverTime_2=int(0),location='',OverTime_25=int(0),
                                                    Launch_Break=int(0),timesheet_status=False,
                                                    timesheet_flag='',user_request_timesheet='request_approval',
                                                    admin_request_timesheet='checked',user_status_timesheet='Approved',
                                                    meal_type='default',meal_rate_day=float(0),meal_allowance='no',
                                                    user_check_timesheet='checked',job_num='-',
                                                    remainder='',accept_flag='',
                                                    reject_flag='',user_id=leave_in.author.id)
                        db.session.add(clock_post_default)
                        db.session.commit()
                    else:
                        clock_post_default = TimeSheetPost(day_clock=day_time,project=leave_in.leave_type,
                                                    comment='',clock_in=datetime.date.today(),
                                                    task=leave_in.leave_type,travel_choice='',
                                                    clock_out=datetime.date.today(),distance='',
                                                    OverTime_15=int(0),NormalTime=int(8),
                                                    OverTime_2=int(0),location='',OverTime_25=int(0),
                                                    Launch_Break=int(0),timesheet_status=False,
                                                    timesheet_flag='',user_request_timesheet='request_approval',
                                                    admin_request_timesheet='checked',user_status_timesheet='Approved',
                                                    meal_type='default',meal_rate_day=float(0),meal_allowance='no',
                                                    user_check_timesheet='checked',job_num='-',
                                                    remainder='',accept_flag='',
                                                    reject_flag='',user_id=leave_in.author.id)
                        db.session.add(clock_post_default)
                        db.session.commit()
                    d_in = d_in + delta
                ##################################
        if count_int==0:
            flash('You have not selected any leave request','danger')
            return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
        else:
            flash('Leave request has been approved','success')
    #############Flag Timesheets#################
    ######Make default blank#####################
        leave_post_flag = LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)).order_by(LeavePost.leave_from.asc())
        for leave_inflag in leave_post_flag:
            leave_inflag.accept_flag=''
            db.session.commit()
        return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
       ##################################################################
    return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
################################################
@adminDash.route("/<username>/<sheet_inx>/leave_ind_approval_acceptflag", methods=['POST'])
@login_required
def leave_ind_approval_acceptflag(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user=User.query.filter_by(username=username).first_or_404()
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initializatio
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='last_year':
            start_time=today_date - datetime.timedelta(365)
            inx_week='last_year'
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            inx_week='this_week'
        elif sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            inx_week='this_month'
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            inx_week='last_week'
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
            inx_week='default_week'
        end_time=today_date + datetime.timedelta(365)
        #####################
        leave_post=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(or_(LeavePost.user_status_leave=='Submited',LeavePost.user_status_leave=='Rejected')) \
                                    .filter(LeavePost.accept_flag=='checked').order_by(LeavePost.leave_from.asc())
        for leave_in in leave_post:
            if leave_in.user_status_leave=='Rejected':
                flash('You have already rejected leave request','danger')
                return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            if leave_in.user_status_leave=='Approved':
                flash('You have already approved leave request','danger')
                return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        ########################################
        #leave_post_init = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)).filter(LeavePost.user_request_leave=='request_approval').filter(LeavePost.reject_flag=='checked').order_by(LeavePost.leave_from.asc())
        count_leave_in=0
        approved_date=[]
        leave_post_init=leave_post
        #leave_post_init = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)).filter(LeavePost.user_request_leave=='request_approval').filter(LeavePost.accept_flag=='checked').order_by(LeavePost.leave_from.asc())
        for check_leave in leave_post_init:
            count_leave_in=count_leave_in+1
            if check_leave.user_status_leave=='Submited':
                t_z=check_leave.leave_from
                approved_date.append(t_z.strftime('%Y-%m-%d'))
        if count_leave_in>0 and approved_date !=[]:
            user_message_ap='Hi {}! Your leave request has been approved.'.format(user.firstname)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Leave Request Approval'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='leave_request',
                            body_id=int(0),
                            body_date=datetime.date.today(),
                            body_sheet=sheet_inx,
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your leave request on {} has been approved'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Leave Request Approval",body_html,body_text)
            ######send email to user for verification###########
        count_int=0
        leave_postR=leave_post
        #leave_postR = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)).filter(LeavePost.user_request_leave=='request_approval').filter(LeavePost.accept_flag=='checked').order_by(LeavePost.leave_from.asc())
        for leave_in in leave_postR:
            count_int=count_int+1
            if leave_in.user_status_leave!='Rejected':
                leave_in.admin_request_leave='checked'
                leave_in.user_status_leave='Approved'
                leave_in.leave_flag=''
                db.session.commit()
                ###################Timesheet Management Automatically########
                start_lv=datetime.time()
                end_lv=datetime.time()
                start_lv=leave_in.leave_from.date()
                end_lv=leave_in.leave_to.date()
                delta = datetime.timedelta(days=1)
                d_in=start_lv
                inc_d=0
                while d_in <=end_lv:
                    day_time=leave_in.leave_from+datetime.timedelta(inc_d)
                    inc_d=inc_d+1
                    inx_day=d_in.strftime('%A')
                    if(inx_day=='Saturday' or inx_day=='Sunday' or leave_in.leave_type=='Leave without Pay'):
                        clock_post_default = TimeSheetPost(day_clock=day_time,project=leave_in.leave_type,
                                                    comment='',clock_in=datetime.date.today(),
                                                    task=leave_in.leave_type,travel_choice='',
                                                    clock_out=datetime.date.today(),distance='',
                                                    OverTime_15=int(0),NormalTime=int(0),
                                                    OverTime_2=int(0),location='',OverTime_25=int(0),
                                                    Launch_Break=int(0),timesheet_status=False,
                                                    timesheet_flag='',user_request_timesheet='request_approval',
                                                    admin_request_timesheet='',user_status_timesheet='Approved',
                                                    meal_type='default',meal_rate_day=float(0),meal_allowance='no',
                                                    user_check_timesheet='',job_num='-',
                                                    remainder='',accept_flag='',
                                                    reject_flag='',user_id=leave_in.author.id)
                        db.session.add(clock_post_default)
                        db.session.commit()
                    else:
                        clock_post_default = TimeSheetPost(day_clock=day_time,project=leave_in.leave_type,
                                                    comment='',clock_in=datetime.date.today(),
                                                    task=leave_in.leave_type,travel_choice='',
                                                    clock_out=datetime.date.today(),distance='',
                                                    OverTime_15=int(0),NormalTime=int(8),
                                                    OverTime_2=int(0),location='',OverTime_25=int(0),
                                                    Launch_Break=int(0),timesheet_status=False,
                                                    timesheet_flag='',user_request_timesheet='request_approval',
                                                    admin_request_timesheet='',user_status_timesheet='Approved',
                                                    meal_type='default',meal_rate_day=float(0),meal_allowance='no',
                                                    user_check_timesheet='',job_num='-',
                                                    remainder='',accept_flag='',
                                                    reject_flag='',user_id=leave_in.author.id)
                        db.session.add(clock_post_default)
                        db.session.commit()
                    d_in = d_in + delta
        if count_int==0:
            flash('You have not selected any leave request','danger')
            return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        else:
            flash('Leave request has been approved','success')
            #############Flag Timesheets#################
            ######Make default blank#####################
        leave_post_flag = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                            .order_by(LeavePost.leave_from.asc())
        for leave_inflag in leave_post_flag:
            leave_inflag.accept_flag=''
            db.session.commit()
            return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
######################################
@adminDash.route("/<username>/<sheet_inx>/accept_ind_leavepost")
@login_required
def accept_ind_leavepost(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initializatio
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='last_year':
        start_time=today_date - datetime.timedelta(365)
        inx_week='last_year'
    elif sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        inx_week='default_week'
    end_time=today_date + datetime.timedelta(365)
    leave_post_init=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(or_(LeavePost.user_status_leave=='Submited',LeavePost.user_status_leave=='Rejected')) \
                                    .order_by(LeavePost.leave_from.asc())
    for leave_indD in leave_post_init:
        if leave_indD.accept_flag=='checked':
            leave_indD.accept_flag=''
            db.session.commit()
        else:
            leave_indD.accept_flag='checked'
            db.session.commit()
    return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
###########Reject#######################################
######################################
@adminDash.route("/<username>/<sheet_inx>/reject_ind_leavepost")
@login_required
def reject_ind_leavepost(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initializatio
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='last_year':
        start_time=today_date - datetime.timedelta(365)
        inx_week='last_year'
    elif sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        inx_week='default_week'
    end_time=today_date + datetime.timedelta(365)
    leave_post_init=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                        .filter(or_(LeavePost.user_status_leave=='Submited',LeavePost.user_status_leave=='Rejected')) \
                                        .order_by(LeavePost.leave_from.asc())
    for leave_indD in leave_post_init:
        if leave_indD.reject_flag=='checked':
            leave_indD.reject_flag=''
            db.session.commit()
        else:
            leave_indD.reject_flag='checked'
            db.session.commit()
    return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
###########REJECT FLAG IND USER BY ADMIN################
@adminDash.route("/<username>/<sheet_inx>/leave_ind_rejectflag", methods=['POST'])
@login_required
def leave_ind_rejectflag(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user=User.query.filter_by(username=username).first_or_404()
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='last_year':
            start_time=today_date - datetime.timedelta(365)
            inx_week='last_year'
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            inx_week='this_week'
        elif sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            inx_week='this_month'
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            inx_week='last_week'
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
            inx_week='default_week'
        end_time=today_date + datetime.timedelta(365)
        leave_post=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(or_(LeavePost.user_status_leave=='Submited',LeavePost.user_status_leave=='Rejected')) \
                                    .filter(LeavePost.reject_flag=='checked').order_by(LeavePost.leave_from.asc())
        for leave_in in leave_post:
            if leave_in.user_status_leave=='Approved':
                flash('You have already approved leave request','danger')
                return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            if leave_in.user_status_leave=='Rejected':
                flash('You have already rejected leave request','danger')
                return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        ##################################################################
        #########Message Notification############
        count_leave_in=0
        approved_date=[]
        leave_post_init=leave_post
        #leave_post_init = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)).filter(LeavePost.user_request_leave=='request_approval').filter(LeavePost.reject_flag=='checked').order_by(LeavePost.leave_from.asc())
        for check_leave in leave_post_init:
            if check_leave.user_status_leave=='Approved':
                flash('Cannot be rejected, It has been approved already!!','danger')
                return redirect(url_for('adminDash.leave_view_acceptflag',sheet_inx=sheet_inx))
            count_leave_in=count_leave_in+1
            if check_leave.user_status_leave=='Submited' and check_leave.reject_flag=='checked':
                t_z=check_leave.leave_from
                approved_date.append(t_z.strftime('%Y-%m-%d'))
        if count_leave_in>0 and approved_date !=[]:
            user_message_ap='Hi {}! Your leave request on {} has been rejected.'.format(user.firstname,approved_date)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Leave Request Rejected'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='leave_request',
                            body_id=int(0),###Qrcode ID
                            body_date=datetime.date.today(),
                            body_sheet=sheet_inx,
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your leave request on {} has been rejected'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Leave Request Rejected",body_html,body_text)
            ######send email to user for verification###########
        #leave_post = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time)).filter(LeavePost.user_request_leave=='request_approval').filter(LeavePost.reject_flag=='checked').order_by(LeavePost.leave_from.asc())
        count_int=0
        for leave_in in leave_post:
            count_int=count_int+1
            if leave_in.user_status_leave!='Approved':
                leave_in.timesheet_flag='checked'
                leave_in.user_status_leave='Rejected'
                db.session.commit()
        if count_int==0:
            flash('You have not selected any leave request','danger')
            return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        else:
            flash('Leave request is rejected','success')
        leave_post_flag = LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)).order_by(LeavePost.leave_from.asc())
        for leave_inflag in leave_post_flag:
            leave_inflag.reject_flag=''
            db.session.commit()
        return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
###################################
@adminDash.route("/<sheet_inx>/leave_admin_rejectflag", methods=['POST'])
@login_required
def leave_admin_rejectflag(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='last_year':
            start_time=today_date - datetime.timedelta(365)
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
        elif sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(365)
    #######################MESSAGE NOTIFICATION#################
        user_all_get=[]
        user_all=User.query.filter(User.user_status=='active').order_by(User.username)
        for in_user in user_all:
            user_all_get.append(in_user.username)
    ######################################################
    ##################################################################
        leave_post = LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)) \
                                    .filter(LeavePost.user_request_leave=='request_approval') \
                                    .filter(LeavePost.reject_flag=='checked')\
                                    .order_by(LeavePost.leave_from.asc())
        for leave_in in leave_post:
            if leave_in.user_status_leave=='Approved':
                flash('You have already approved leave request','danger')
                return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
            if leave_in.user_status_leave=='Rejected':
                flash('You have already rejected leave request','danger')
                return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
    ##################################################################
        count_check=0
    #########################################################
        for u_all in user_all_get:
            user = User.query.filter_by(username=u_all).first_or_404()
            count_leave_in=0
            approved_date=[]
            leave_post_init = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time))\
                                                .filter(LeavePost.user_request_leave=='request_approval')\
                                                .filter(LeavePost.reject_flag=='checked').order_by(LeavePost.leave_from.asc())
            for check_leave in leave_post_init:
                count_leave_in=count_leave_in+1
                if check_leave.user_status_leave=='Approved':
                    flash('Cannot be rejected, It has been approved already!!','danger')
                    return redirect(url_for('adminDash.leave_view_acceptflag',sheet_inx=sheet_inx))
                if check_leave.user_status_leave=='Submited' and check_leave.reject_flag=='checked':
                    t_z=check_leave.leave_from
                    approved_date.append(t_z.strftime('%Y-%m-%d'))
            if count_leave_in>0 and approved_date !=[]:
                user_message_ap='Hi {}! Your leave request on {} has been rejected.'.format(user.firstname,approved_date)
                user_status_ap='unread'
                user_flag_ap=''
                user_title_ap='Leave Request Rejected'
                msg = Message(author=current_user, recipient=user,
                                body_message=user_message_ap,
                                body_title=user_title_ap,
                                body_flag=user_flag_ap,
                                body_trans='leave_request',
                                body_id=int(0),
                                body_date=datetime.date.today(),
                                body_sheet=sheet_inx,
                                body_status=user_status_ap)
                db.session.add(msg)
                db.session.commit()
                ######send email to user for verification###########
                message_email='Your leave request on {} has been rejected'.format(approved_date)
                body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                email(user.email,"Leave Request Rejected",body_html,body_text)
                ######send email to user for verification###########
        leave_post = LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)).filter(LeavePost.user_request_leave=='request_approval')\
                                        .filter(LeavePost.reject_flag=='checked').order_by(LeavePost.leave_from.asc())
        count_int=0
        for leave_in in leave_post:
            count_int=count_int+1
            if leave_in.user_status_leave!='Approved':
                leave_in.leave_flag='checked'
                leave_in.user_status_leave='Rejected'
                db.session.commit()
        if count_int==0:
            flash('You have not selected any leave request','danger')
            return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
        else:
            flash('Leave request is rejected','success')
        leave_post_flag = LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time)).order_by(LeavePost.leave_from.asc())
        for leave_inflag in leave_post_flag:
            leave_inflag.reject_flag=''
            db.session.commit()
        return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
    ##################################################################
    return redirect(url_for('adminDash.leave_view',sheet_inx))
#########ADMIN INVOICE VIEW################
#####DEFAULT DASHBOARD######################
@adminDash.route("/<sheet_inx>/invoice_view")
@login_required
def invoice_view(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        end_day=end_time
        inx_week='default_week'
    invoice_view_data=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time)) \
                                        .filter(InvoicePost.user_request_invoice=='request_approval') \
                                        .order_by(InvoicePost.invoice_from.asc())
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    unique_user=[]
    for in_view in invoice_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        invoice_ind=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                        .filter(InvoicePost.user_request_invoice=='request_approval') \
                                        .order_by(InvoicePost.invoice_from.asc())
        count_invoice_in=0
        for check_invoice in invoice_ind:
            count_invoice_in=count_invoice_in+1
        if count_invoice_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/invoice_view_all.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                            inx_week=inx_week,end_time=end_day,post_data=invoice_view_data,
                                                            user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                            unique_user=unique_user)

#########ADMIN REIMBURSEMENT VIEW################
@adminDash.route("/<username>/<sheet_inx>/invoice_view_standard_submit",methods=['GET','POST'])
@login_required
def invoice_view_standard_submit(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    #Default Initialization
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        end_day=end_time
        inx_week='default_week'
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    invoice_post=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                  .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected')) \
                                  .order_by(InvoicePost.invoice_from.asc())
    for invoice_inflag_form in invoice_post:
        invoice_inflag_form.reject_flag=''
        invoice_inflag_form.accept_flag=''
        db.session.commit()
    ##########################################################
    if request.method=='POST':
        if request.form['submit_button']=='Approve':
            form_approve=request.form.getlist('selectedRow[]')
            form_reject=request.form.getlist('selectedItem_new[]')
            if form_approve==[]:
                flash('You have not selected any reimbursement request for approval','danger')
                return redirect(url_for('adminDash.invoice_view_standard_submit',username=user.username,sheet_inx=sheet_inx))
            if form_reject!=[]:
                flash('You cannot reject reimbursement request by Approval Selected buttom','danger')
                return redirect(url_for('adminDash.invoice_view_standard_submit',username=user.username,sheet_inx=sheet_inx))
            for init_form in form_approve:
                invoice_posts_form = InvoicePost.query.get_or_404(int(init_form))
                invoice_posts_form.accept_flag='checked'
                db.session.commit()
            ##########Approval Process############
            invoice_post_form_approve = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                            .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                                            .filter(InvoicePost.accept_flag=='checked').order_by(InvoicePost.invoice_from.asc())
            for invoice_in in invoice_post_form_approve:
                if invoice_in.user_status_invoice=='Rejected':
                    flash('You have already rejected reimbursement request','danger')
                    return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
                if invoice_in.user_status_invoice=='Approved':
                    flash('You have already approved reimbursement request','danger')
                    return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            count_invoice_in=0
            approved_date=[]
            invoice_post_init_form_approve = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                                .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                                                .filter(InvoicePost.accept_flag=='checked').order_by(InvoicePost.invoice_from.asc())
            for check_invoice in invoice_post_init_form_approve:
                count_invoice_in=count_invoice_in+1
                if check_invoice.user_status_invoice=='Submited':
                    t_z=check_invoice.invoice_from
                    approved_date.append(t_z.strftime('%Y-%m-%d'))
            if count_invoice_in>0 and approved_date !=[]:
                user_message_ap='Hi {}! Your reimbursement request has been approved.'.format(user.firstname)
                user_status_ap='unread'
                user_flag_ap=''
                user_title_ap='Reimbursement Request Approval'
                msg = Message(author=current_user, recipient=user,
                                body_message=user_message_ap,
                                body_title=user_title_ap,
                                body_flag=user_flag_ap,
                                body_trans='invoice_request',
                                body_id=int(0),
                                body_date=datetime.date.today(),
                                body_sheet=sheet_inx,
                                body_status=user_status_ap)
                db.session.add(msg)
                db.session.commit()
                ######send email to user for verification###########
                message_email='Your reimbursement request on {} has been rejected'.format(approved_date)
                body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                email(user.email,"Reimbursement Request Approval",body_html,body_text)
                ######send email to user for verification###########
             ##################################################################
            count_int=0
            invoice_postR_form_approve = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                                .filter(InvoicePost.accept_flag=='checked').order_by(InvoicePost.invoice_from.asc())
            for invoice_in in invoice_postR_form_approve:
                count_int=count_int+1
                if invoice_in.user_status_invoice!='Rejected':
                    invoice_in.admin_request_invoice='checked'
                    invoice_in.user_status_invoice='Approved'
                    invoice_in.invoice_flag=''
                    db.session.commit()
            if count_int==0:
                flash('You have not selected any reimbursement request','danger')
                return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            else:
                flash('Reimbursement request has been approved','success')
                #############Flag Timesheets#################
                ######Make default blank#####################
            invoice_post_flag_form_approve = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                                .order_by(InvoicePost.invoice_from.asc())
            for invoice_inflag in invoice_post_flag_form_approve:
                invoice_inflag.accept_flag=''
                db.session.commit()
            return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        ##########Reject POST Form##################
        if request.form['submit_button']=='Reject':
            form_approve=request.form.getlist('selectedRow[]')
            form_reject=request.form.getlist('selectedItem_new[]')
            if form_reject==[]:
                flash('You have not selected any reimbursement request for rejection','danger')
                return redirect(url_for('adminDash.invoice_view_standard_submit',username=user.username,sheet_inx=sheet_inx))
            if form_approve!=[]:
                flash('You cannot approved reimbursement request by Reject Selected buttom','danger')
                return redirect(url_for('adminDash.invoice_view_standard_submit',username=user.username,sheet_inx=sheet_inx))
            for init_form in form_reject:
                invoice_posts_rej = InvoicePost.query.get_or_404(int(init_form))
                invoice_posts_rej.reject_flag='checked'
                db.session.commit()
            invoice_post_form_reject = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                                .filter(InvoicePost.reject_flag=='checked').order_by(InvoicePost.invoice_from.asc())
            for invoice_in in invoice_post_form_reject:
                if invoice_in.user_status_invoice=='Approved':
                    flash('You have already approved reimbursement request','danger')
                    return redirect(url_for('adminDash.invoice_view_standard_submit',username=user.username,sheet_inx=sheet_inx))
                if invoice_in.user_status_invoice=='Rejected':
                    flash('You have already rejected reimbursement request','danger')
                    return redirect(url_for('adminDash.invoice_view_standard_submit',username=user.username,sheet_inx=sheet_inx))
            ##################################################################
            ##########################################
            count_invoice_in=0
            approved_date=[]
            invoice_post_init_form_reject = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                                .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                                                .filter(InvoicePost.reject_flag=='checked').order_by(InvoicePost.invoice_from.asc())
            for check_invoice in invoice_post_init_form_reject:
                count_invoice_in=count_invoice_in+1
                if check_invoice.user_status_invoice=='Approved':
                    flash('Cannot be rejected, It has been approved already!!','danger')
                    return redirect(url_for('adminDash.invoice_view_standard_submit',username=user.username,sheet_inx=sheet_inx))
                if check_invoice.user_status_invoice=='Submited' and check_invoice.reject_flag=='checked':
                    t_z=check_invoice.invoice_from
                    approved_date.append(t_z.strftime('%Y-%m-%d'))
            if count_invoice_in>0 and approved_date !=[]:
                user_message_ap='Hi {}! Your reimbursement request on {} has been rejected.'.format(user.firstname,approved_date)
                user_status_ap='unread'
                user_flag_ap=''
                user_title_ap='Reimbursement Request Rejected'
                msg = Message(author=current_user, recipient=user,
                                body_message=user_message_ap,
                                body_title=user_title_ap,
                                body_flag=user_flag_ap,
                                body_trans='invoice_request',
                                body_id=int(0),
                                body_date=datetime.date.today(),
                                body_sheet=sheet_inx,
                                body_status=user_status_ap)
                db.session.add(msg)
                db.session.commit()
                ######send email to user for verification###########
                message_email='Your reimbursement request on {} has been rejected'.format(approved_date)
                body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                email(user.email,"Reimbursement Request Rejected",body_html,body_text)
                ######send email to user for verification###########
            ##################################################################
            invoice_post_form_reject = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                                .filter(InvoicePost.reject_flag=='checked').order_by(InvoicePost.invoice_from.asc())
            count_int=0
            for invoice_in in invoice_post_form_reject:
                count_int=count_int+1
                if invoice_in.user_status_invoice!='Approved':
                    invoice_in.invoice_flag='checked'
                    invoice_in.user_status_invoice='Rejected'
                    db.session.commit()
            if count_int==0:
                flash('You have not selected any reimbursement request','danger')
                return redirect(url_for('adminDash.invoice_view_standard_submit',username=user.username,sheet_inx=sheet_inx))
            else:
                flash('Reimbursement request is rejected','success')
            invoice_post_flag_form_reject = InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time)).order_by(InvoicePost.invoice_from.asc())
            for invoice_inflag in invoice_post_flag_form_reject:
                invoice_inflag.reject_flag=''
                db.session.commit()
            return redirect(url_for('adminDash.invoice_view_standard_submit',username=user.username,sheet_inx=sheet_inx))
    return render_template('/admin/view_invoice_standard_submit.html', post_data=invoice_post, user=user,user_all=user_all,
                                                                        inx_week=inx_week,end_time=end_day)
#########ADMIN TIMESHEET VIEW################

#########ADMIN REIMBURSEMENT VIEW################
@adminDash.route("/<username>/<sheet_inx>/invoice_view_standard_submit_old")
@login_required
def invoice_view_standard_submit_old(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    #Default Initialization
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        end_day=end_time
        inx_week='default_week'
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    invoice_post=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                    .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected')) \
                                    .order_by(InvoicePost.invoice_from.asc())
    return render_template('/admin/view_invoice_standard_submit.html', post_data=invoice_post, user=user,user_all=user_all,
                                                                        inx_week=inx_week,end_time=end_day)
#########ADMIN TIMESHEET VIEW################
@adminDash.route("/<username>/invoice_view_standardF_submit",methods=['GET','POST'])
@login_required
def invoice_view_standardF_submit(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='This Month':
            inx_week='this_month'
        elif view_chart=='Last Week':
            inx_week='last_week'
        elif view_chart=='This Week':
            inx_week='this_week'
        else:
            inx_week='default_week'
    if request.method=='GET':
        inx_week='default_week'
    return redirect(url_for('adminDash.invoice_view_standard_submit',username=user.username,sheet_inx=inx_week))

@adminDash.route("/<username>/<sheet_inx>/invoice_view_standardF_submit_check")
@login_required
def invoice_view_standardF_submit_check(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
    elif sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        end_day=end_time
    invoice_post=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                    .filter(InvoicePost.user_request_invoice=='request_approval')\
                                    .order_by(InvoicePost.invoice_from.asc())
    return render_template('/admin/view_invoice_standard_submit_check.html', post_data=invoice_post,user_all=user_all, user=user,
                                                                            inx_week='default',end_time=end_day)
#########ADMIN TIMESHEET VIEW################

#########ADMIN TIMESHEET VIEW################
@adminDash.route("/<username>/<sheet_inx>/invoice_csv_download_submit")
def invoice_csv_download_submit (sheet_inx,username):
    user=User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        #end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        end_day=end_time
        inx_week='default_week'
    end_day=end_day.strftime('%d/%m/%Y')
    ##################################################
    invoice_post=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                    .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                    .order_by(InvoicePost.invoice_from.asc())
    with open('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/invoice_data.csv','w') as fp:
        data_init=csv.writer(fp)
        data_init.writerow(['Reimbursement request for:{}'.format(user.username)])
        data_init.writerow(['Week Ending:{}'.format(end_day)])
        data_init.writerow(['Date','Supplier','Type','Total Amount($)','Status'])
        for cp_in in invoice_post:
            data_init_post=[cp_in.invoice_from.strftime('%d/%m/%Y'),cp_in.invoice_supplier,cp_in.invoice_category,cp_in.invoice_Total,\
                            cp_in.user_status_invoice]
            data_init.writerow(data_init_post)
        data_f=['','','','','','']
        data_init.writerow(data_f)
    try:
        return send_file('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/invoice_data.csv',
                        mimetype='text/csv',attachment_filename='invoice_data.csv',as_attachment=True)
    except:
        flash('File not supported format','danger')
        return redirect(url_for('adminDash.invoice_view_standardF_submit',username=username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.invoice_view_standardF_submit',username=username,sheet_inx=sheet_inx))
############################################
@adminDash.route("/<username>/<sheet_inx>/invoice_view_standard_paid")
@login_required
def invoice_view_standard_paid(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    #Default Initialization
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        #end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        end_day=end_time
        inx_week='default_week'
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    invoice_post=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                    .filter(InvoicePost.user_status_invoice=='Approved').order_by(InvoicePost.invoice_from.asc())
    return render_template('/admin/view_invoice_standard_paid.html', post_data=invoice_post, user=user,user_all=user_all,
                                                                        inx_week=inx_week,end_time=end_day)
#########ADMIN TIMESHEET VIEW################
@adminDash.route("/<username>/invoice_view_standardF_paid",methods=['GET','POST'])
@login_required
def invoice_view_standardF_paid(username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
            inx_week='this_month'
        elif view_chart=='Last Week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
            inx_week='last_week'
        elif view_chart=='This Week':
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
            end_day=start_time+datetime.timedelta(6)
            #end_time=start_time+datetime.timedelta(7)
            inx_week='this_week'
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
            end_day=end_time
            inx_week='default_week'
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date
        end_day=end_time
        inx_week='default_week'
    invoice_post=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                    .filter(InvoicePost.user_status_invoice=='Approved')\
                                    .order_by(InvoicePost.invoice_from.asc())
    return render_template('/admin/view_invoice_standard_paid.html', post_data=invoice_post,user_all=user_all,
                                                                        user=user,inx_week=inx_week,end_time=end_day)

#########ADMIN TIMESHEET VIEW################
@adminDash.route("/<username>/<sheet_inx>/invoice_csv_download_paid",methods=['POST'])
def invoice_csv_download_paid (sheet_inx,username):
    user=User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        if sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
            #end_time=start_time+datetime.timedelta(7)
            end_day=start_time+datetime.timedelta(6)
        elif sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
        end_day=end_day.strftime('%d/%m/%Y')
        ##################################################
        invoice_post=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_status_invoice=='Approved').order_by(InvoicePost.invoice_from.asc())
        with open('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/invoice_data.csv','w') as fp:
            data_init=csv.writer(fp)
            data_init.writerow(['Reimbursement request for:{}'.format(user.username)])
            data_init.writerow(['Week Ending:{}'.format(end_day)])
            data_init.writerow(['Date','Supplier','Type','Total Amount($)','Status'])
            for cp_in in invoice_post:
                data_init_post=[cp_in.invoice_from.strftime('%d/%m/%Y'),cp_in.invoice_supplier,cp_in.invoice_category,\
                                cp_in.invoice_Total,cp_in.user_status_invoice]
                data_init.writerow(data_init_post)
            data_f=['','','','','','']
            data_init.writerow(data_f)
        try:
            return send_file('/home/ubuntu/TimesheetApp/TimesheetApp/static/img/invoice_data.csv',
                            mimetype='text/csv',attachment_filename='invoice_data.csv',as_attachment=True)
        except:
            flash('File not supported format','danger')
            return redirect(url_for('adminDash.invoice_view_standardF_paid',username=username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.invoice_view_standardF_paid',username=username,sheet_inx=sheet_inx))
#####ACTUAL LEAVE DASHBOARD#################
@adminDash.route("/invoice_view_all",methods=['GET','POST'])
@login_required
def invoice_view_all():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
            inx_week='this_month'
        elif view_chart=='Last Week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
            inx_week='last_week'
        else:
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
            #end_time=start_time+datetime.timedelta(7)
            end_day=start_time+datetime.timedelta(6)
            inx_week='this_week'
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date
        end_day=end_time
        inx_week='default'
    invoice_view_data=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time)) \
                                            .filter(InvoicePost.user_request_invoice=='request_approval') \
                                            .order_by(InvoicePost.invoice_from.asc())
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ##Finding Unique User
    unique_user=[]
    for in_view in invoice_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    #########################
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        invoice_ind=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                        .filter(InvoicePost.user_request_invoice=='request_approval').order_by(InvoicePost.invoice_from.asc())
        count_invoice_in=0
        for check_invoice in invoice_ind:
            count_invoice_in=count_invoice_in+1
            check_invoice.accept_flag=''
            check_invoice.reject_flag=''
            db.session.commit()
        if count_invoice_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/invoice_view_all.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                            inx_week=inx_week,end_time=end_day,post_data=invoice_view_data,
                                                            user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                            unique_user=unique_user)
#######INVOICE ACCEPT AND REJECT FLAG#############
#####DEFAULT DASHBOARD######################
@adminDash.route("/<sheet_inx>/invoice_view_acceptflagDash")
@login_required
def invoice_view_acceptflagDash(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        #end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date
        end_day=end_time
        inx_week='default_week'
    ##################Checked or Not################
    invoice_ind=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time)) \
                                    .filter(InvoicePost.user_request_invoice=='request_approval')\
                                    .order_by(InvoicePost.invoice_from.asc())
    for invoice_indD in invoice_ind:
        if invoice_indD.accept_flag=='checked':
            invoice_indD.accept_flag=''
            db.session.commit()
        else:
            invoice_indD.accept_flag='checked'
            db.session.commit()
    ##################################################
    return redirect(url_for('adminDash.invoice_view',sheet_inx=inx_week))

@adminDash.route("/<sheet_inx>/invoice_view_rejectflagDash")
@login_required
def invoice_view_rejectflagDash(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        #end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date
        end_day=end_time
        inx_week='default_week'
    ##################Checked or Not################
    invoice_ind=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time))\
                                    .filter(InvoicePost.user_request_invoice=='request_approval')\
                                    .order_by(InvoicePost.invoice_from.asc())
    for invoice_indD in invoice_ind:
        if invoice_indD.reject_flag=='checked':
            invoice_indD.reject_flag=''
            db.session.commit()
        else:
            invoice_indD.reject_flag='checked'
            db.session.commit()
    ##################################################
    return redirect(url_for('adminDash.invoice_view',sheet_inx=inx_week))

@adminDash.route("/invoice_view_approveflag")
@login_required
def invoice_view_approveflag():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date- datetime.timedelta(49+idx_week)
    end_time=today_date
    end_day=end_time
    inx_week='default'
    #clock_view_data=TimeSheetPost.query.filter((TimeSheetPost.day_clock.between(start_time,end_time)),TimeSheetPost.day_clock.desc())
    invoice_view_data=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_request_invoice=='request_approval')\
                                        .order_by(InvoicePost.invoice_from.asc())
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    unique_user=[]
    for in_view in invoice_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        invoice_ind=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_request_invoice=='request_approval')\
                                        .order_by(InvoicePost.invoice_from.asc())
        count_invoice_in=0
        for check_invoice in invoice_ind:
            count_invoice_in=count_invoice_in+1
        if count_invoice_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    return render_template('/admin/invoice_view_all_acceptflag.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                    inx_week=inx_week,end_time=end_day,post_data=invoice_view_data,
                                                                    user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                                    unique_user=unique_user)

@adminDash.route("/invoice_view_all_approveflag",methods=['GET','POST'])
@login_required
def invoice_view_all_approveflag():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
            inx_week='this_month'
        elif view_chart=='Last Week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
            inx_week='last_week'
        else:
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
            #end_time=start_time+datetime.timedelta(7)
            end_day=start_time+datetime.timedelta(6)
            inx_week='this_week'
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date
        end_day=end_time
        inx_week='default'
    invoice_view_data=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_request_invoice=='request_approval')\
                                        .order_by(InvoicePost.invoice_from.asc())
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ##Finding Unique User
    unique_user=[]
    for in_view in invoice_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        invoice_ind=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_request_invoice=='request_approval')\
                                        .order_by(InvoicePost.invoice_from.asc())
        count_invoice_in=0
        for check_invoice in invoice_ind:
            count_invoice_in=count_invoice_in+1
        if count_invoice_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    return render_template('/admin/invoice_view_all_acceptflag.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                    inx_week=inx_week,end_time=end_day,post_data=invoice_view_data,
                                                                    user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                                    unique_user=unique_user)

#####DEFAULT DASHBOARD######################
@adminDash.route("/invoice_view_approveflagDash")
@login_required
def invoice_view_approveflagDash():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date- datetime.timedelta(49+idx_week)
    end_time=today_date
    end_day=end_time
    inx_week='default'
    #clock_view_data=TimeSheetPost.query.filter((TimeSheetPost.day_clock.between(start_time,end_time)),TimeSheetPost.day_clock.desc())
    invoice_view_data=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_request_invoice=='request_approval')\
                                        .order_by(InvoicePost.invoice_from.asc())
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    unique_user=[]
    for in_view in invoice_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        invoice_ind=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_request_invoice=='request_approval').order_by(InvoicePost.invoice_from.asc())
        count_invoice_in=0
        for check_invoice in invoice_ind:
            count_invoice_in=count_invoice_in+1
            check_invoice.accept_flag='checked'
            check_invoice.reject_flag='checked'
            db.session.commit()
        if count_invoice_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    return render_template('/admin/invoice_view_all_acceptflagDash.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                            inx_week=inx_week,end_time=end_day,post_data=invoice_view_data,
                                                                            user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                                            unique_user=unique_user)

@adminDash.route("/invoice_view_all_approveflagDash",methods=['GET','POST'])
@login_required
def invoice_view_all_approveflagDash():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='This Month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
            inx_week='this_month'
        elif view_chart=='Last Week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
            inx_week='last_week'
        else:
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=today_date + datetime.timedelta(idx_week)
            end_time=start_time+datetime.timedelta(7)
            end_day=start_time+datetime.timedelta(6)
            inx_week='this_week'
    if request.method=='GET':
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date
        end_day=end_time
        inx_week='default'
    invoice_view_data=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_request_invoice=='request_approval')\
                                        .order_by(InvoicePost.invoice_from.asc())
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ##Finding Unique User
    unique_user=[]
    for in_view in invoice_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        invoice_ind=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time)) \
                                        .filter(InvoicePost.user_request_invoice=='request_approval') \
                                        .order_by(InvoicePost.invoice_from.asc())
        count_invoice_in=0
        for check_invoice in invoice_ind:
            count_invoice_in=count_invoice_in+1
            check_invoice.accept_flag='checked'
            check_invoice.reject_flag='checked'
            db.session.commit()
        if count_invoice_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    return render_template('/admin/invoice_view_all_acceptflagDash.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                        inx_week=inx_week,end_time=end_day,post_data=invoice_view_data,
                                                                        user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                                        unique_user=unique_user)

#########INVOICE APPROVAL FROM ADMIN###############
@adminDash.route("/<username>/<int:invoice_post_id>/<sheet_inx>/acceptflag_user_invoicepost", methods=['POST'])
@login_required
def acceptflag_user_invoicepost(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    if request.method == 'POST':
        if invoice_posts.accept_flag=='checked':
            invoice_posts.accept_flag=''
            db.session.commit()
        else:
            invoice_posts.accept_flag='checked'
            db.session.commit()
        return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))

@adminDash.route("/<username>/<int:invoice_post_id>/<sheet_inx>/acceptflag_ind_invoicepost")
@login_required
def acceptflag_ind_invoicepost(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    if invoice_posts.accept_flag=='checked':
        invoice_posts.accept_flag=''
        db.session.commit()
    else:
        invoice_posts.accept_flag='checked'
        db.session.commit()
    return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
###########TIMESHEET REJECT FLAG ######################
@adminDash.route("/<username>/<int:invoice_post_id>/<sheet_inx>/rejectflag_ind_invoicepost")
@login_required
def rejectflag_ind_invoicepost(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    if invoice_posts.reject_flag=='checked':
        invoice_posts.reject_flag=''
        db.session.commit()
    else:
        invoice_posts.reject_flag='checked'
        db.session.commit()
    return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
#####################################################
@adminDash.route("/<username>/<int:invoice_post_id>/<sheet_inx>/rejectflag_user_invoicepost", methods=['POST'])
@login_required
def rejectflag_user_invoicepost(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    if request.method == 'POST':
        if invoice_posts.reject_flag=='checked':
            invoice_posts.reject_flag=''
            db.session.commit()
        else:
            invoice_posts.reject_flag='checked'
            db.session.commit()
        return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))

#######All Approval############
@adminDash.route("/<sheet_inx>/invoice_admin_approval_acceptflag", methods=['POST'])
@login_required
def invoice_admin_approval_acceptflag(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=start_time+datetime.timedelta(7)
            end_time=today_date + datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
    #######################MESSAGE NOTIFICATION#################
        user_all_get=[]
        user_all=User.query.filter(User.user_status=='active').order_by(User.username)
        for in_user in user_all:
            user_all_get.append(in_user.username)
    ######################################################
        invoice_post = InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time)) \
                                        .filter(InvoicePost.user_request_invoice=='request_approval') \
                                        .filter(InvoicePost.accept_flag=='checked')\
                                        .order_by(InvoicePost.invoice_from.asc())
        for invoice_in in invoice_post:
            if invoice_in.user_status_invoice=='Rejected':
                flash('You have already rejected reimbursement request','danger')
                return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
            if invoice_in.user_status_invoice=='Approved':
                flash('You have already approved reimbursement request','danger')
                return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
    #########################################
    ###############################################
        count_check=0
        for u_all in user_all_get:
            user = User.query.filter_by(username=u_all).first_or_404()
            count_invoice_in=0
            approved_date=[]
            invoice_post_init = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                    .filter(InvoicePost.user_request_invoice=='request_approval')\
                                                    .filter(InvoicePost.accept_flag=='checked').order_by(InvoicePost.invoice_from.asc())
            for check_invoice in invoice_post_init:
                count_invoice_in=count_invoice_in+1
                if check_invoice.user_status_invoice=='Submited':
                    t_z=check_invoice.invoice_from
                    approved_date.append(t_z.strftime('%Y-%m-%d'))
            if count_invoice_in>0 and approved_date !=[]:
                user_message_ap='Hi {}! Your reimbursement request has been approved.'.format(user.firstname)
                user_status_ap='unread'
                user_flag_ap=''
                user_title_ap='Reimbursement Request Approval'
                msg = Message(author=current_user, recipient=user,
                                body_message=user_message_ap,
                                body_title=user_title_ap,
                                body_flag=user_flag_ap,
                                body_trans='invoice_request',
                                body_id=int(0),
                                body_date=datetime.date.today(),
                                body_sheet=sheet_inx,
                                body_status=user_status_ap)
                db.session.add(msg)
                db.session.commit()
                ######send email to user for verification###########
                message_email='Your reimbursement request on {} has been approved'.format(approved_date)
                body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                email(user.email,"Reimbursement Request Approval",body_html,body_text)
                ######send email to user for verification###########
        count_int=0
        invoice_post = InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time))\
                                            .filter(InvoicePost.user_request_invoice=='request_approval')\
                                            .filter(InvoicePost.accept_flag=='checked').order_by(InvoicePost.invoice_from.asc())
        for invoice_in in invoice_post:
            count_int=count_int+1
            if invoice_in.user_status_invoice!='Rejected':
                invoice_in.admin_request_invoice='checked'
                invoice_in.user_status_invoice='Approved'
                invoice_in.invoice_flag=''
                db.session.commit()
        if count_int==0:
            flash('You have not selected any reimbursement request','danger')
            return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
        else:
            flash('TimeSheet has been approved','success')
        #############Flag Timesheets#################
        ######Make default blank#####################
        invoice_post_flag = InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time))\
                                                .order_by(InvoicePost.invoice_from.asc())
        for invoice_inflag in invoice_post_flag:
            invoice_inflag.accept_flag=''
            db.session.commit()
        return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
#######Individual Approval############
@adminDash.route("/<username>/<sheet_inx>/invoice_ind_approval_acceptflag", methods=['POST'])
@login_required
def invoice_ind_approval_acceptflag(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=start_time+datetime.timedelta(7)
            end_time=today_date + datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
##################################################################
        invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                            .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                            .filter(InvoicePost.accept_flag=='checked').order_by(InvoicePost.invoice_from.asc())
        for invoice_in in invoice_post:
            if invoice_in.user_status_invoice=='Rejected':
                flash('You have already rejected reimbursement request','danger')
                return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            if invoice_in.user_status_invoice=='Approved':
                flash('You have already approved reimbursement request','danger')
                return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        count_invoice_in=0
        approved_date=[]
        invoice_post_init = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                                .filter(InvoicePost.accept_flag=='checked').order_by(InvoicePost.invoice_from.asc())
        for check_invoice in invoice_post_init:
            count_invoice_in=count_invoice_in+1
            if check_invoice.user_status_invoice=='Submited':
                t_z=check_invoice.invoice_from
                approved_date.append(t_z.strftime('%Y-%m-%d'))
        if count_invoice_in>0 and approved_date !=[]:
            user_message_ap='Hi {}! Your reimbursement request has been approved.'.format(user.firstname)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Reimbursement Request Approval'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='invoice_request',
                            body_id=int(0),
                            body_date=datetime.date.today(),
                            body_sheet=sheet_inx,
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your reimbursement request on {} has been approved'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Reimbursement Request Approval",body_html,body_text)
            ######send email to user for verification###########
         ##################################################################
        count_int=0
        invoice_postR = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                            .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                            .filter(InvoicePost.accept_flag=='checked').order_by(InvoicePost.invoice_from.asc())
        for invoice_in in invoice_postR:
            count_int=count_int+1
            if invoice_in.user_status_invoice!='Rejected':
                invoice_in.admin_request_invoice='checked'
                invoice_in.user_status_invoice='Approved'
                invoice_in.invoice_flag=''
                db.session.commit()
        if count_int==0:
            flash('You have not selected any reimbursement request','danger')
            return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        else:
            flash('Reimbursement request has been approved','success')
            #############Flag Timesheets#################
            ######Make default blank#####################
        invoice_post_flag = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                .order_by(InvoicePost.invoice_from.asc())
        for invoice_inflag in invoice_post_flag:
            invoice_inflag.accept_flag=''
            db.session.commit()
        return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
#######Approve or Reject All Selection##########
@adminDash.route("/<username>/<sheet_inx>/accept_ind_invoicepost")
@login_required
def accept_ind_invoicepost(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        #end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        end_day=end_time
        inx_week='default_week'
    invoice_post_init=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                        .order_by(InvoicePost.invoice_from.asc())
    for invoice_indD in invoice_post_init:
        if invoice_indD.accept_flag=='checked':
            invoice_indD.accept_flag=''
            db.session.commit()
        else:
            invoice_indD.accept_flag='checked'
            db.session.commit()
    return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))

##########################################################
@adminDash.route("/<username>/<sheet_inx>/reject_ind_invoicepost")
@login_required
def reject_ind_invoicepost(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        #end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        end_day=end_time
        inx_week='default_week'
    invoice_post_init=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                        .order_by(InvoicePost.invoice_from.asc())
    for invoice_indD in invoice_post_init:
        if invoice_indD.reject_flag=='checked':
            invoice_indD.reject_flag=''
            db.session.commit()
        else:
            invoice_indD.reject_flag='checked'
            db.session.commit()
    return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))

######Individual Reject############
@adminDash.route("/<username>/<sheet_inx>/invoice_ind_rejectflag", methods=['POST'])
@login_required
def invoice_ind_rejectflag(username,sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=start_time+datetime.timedelta(7)
            end_time=today_date + datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
        ##################################################################
        invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                            .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                            .filter(InvoicePost.reject_flag=='checked').order_by(InvoicePost.invoice_from.asc())
        for invoice_in in invoice_post:
            if invoice_in.user_status_invoice=='Approved':
                flash('You have already approved reimbursement request','danger')
                return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            if invoice_in.user_status_invoice=='Rejected':
                flash('You have already rejected reimbursement request','danger')
                return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        ##################################################################
        ##########################################
        count_invoice_in=0
        approved_date=[]
        invoice_post_init = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                                .filter(InvoicePost.reject_flag=='checked').order_by(InvoicePost.invoice_from.asc())
        for check_invoice in invoice_post_init:
            count_invoice_in=count_invoice_in+1
            if check_invoice.user_status_invoice=='Approved':
                flash('Cannot be rejected, It has been approved already!!','danger')
                return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
            if check_invoice.user_status_invoice=='Submited' and check_invoice.reject_flag=='checked':
                t_z=check_invoice.invoice_from
                approved_date.append(t_z.strftime('%Y-%m-%d'))
        if count_invoice_in>0 and approved_date !=[]:
            user_message_ap='Hi {}! Your reimbursement request on {} has been rejected.'.format(user.firstname,approved_date)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Reimbursement Request Rejected'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='invoice_request',
                            body_id=int(0),
                            body_date=datetime.date.today(),
                            body_sheet=sheet_inx,
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your reimbursement on {} has been rejected'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Reimbursement Request Rejected",body_html,body_text)
            ######send email to user for verification###########
        ##################################################################
        invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                            .filter(or_(InvoicePost.user_status_invoice=='Submited',InvoicePost.user_status_invoice=='Rejected'))\
                                            .filter(InvoicePost.reject_flag=='checked').order_by(InvoicePost.invoice_from.asc())
        count_int=0
        for invoice_in in invoice_post:
            count_int=count_int+1
            if invoice_in.user_status_invoice!='Approved':
                invoice_in.invoice_flag='checked'
                invoice_in.user_status_invoice='Rejected'
                db.session.commit()
        if count_int==0:
            flash('You have not selected any reimbursement request','danger')
            return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        else:
            flash('Reimbursement request is rejected','success')
        invoice_post_flag = InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time)).order_by(InvoicePost.invoice_from.asc())
        for invoice_inflag in invoice_post_flag:
            invoice_inflag.reject_flag=''
            db.session.commit()
        return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
##########################################################
######All Reject############
@adminDash.route("/<sheet_inx>/invoice_admin_rejectflag", methods=['POST'])
@login_required
def invoice_admin_rejectflag(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=start_time+datetime.timedelta(7)
            end_time=today_date + datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
    #######################MESSAGE NOTIFICATION#################
        user_all_get=[]
        user_all=User.query.filter(User.user_status=='active').order_by(User.username)
        for in_user in user_all:
            user_all_get.append(in_user.username)
    ######################################################
    ##################################################################
        invoice_post = InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_request_invoice=='request_approval')\
                                        .filter(InvoicePost.reject_flag=='checked').order_by(InvoicePost.invoice_from.asc())
        for invoice_in in invoice_post:
            if invoice_in.user_status_invoice=='Approved':
                flash('You have already approved reimbursement request','danger')
                return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
            if invoice_in.user_status_invoice=='Rejected':
                flash('You have already rejected reimbursement request','danger')
                return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
    ##################################################################
        ##################################
        count_check=0
        for u_all in user_all_get:
            user = User.query.filter_by(username=u_all).first_or_404()
            count_invoice_in=0
            approved_date=[]
            invoice_post_init = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                                    .filter(InvoicePost.user_request_invoice=='request_approval')\
                                                    .filter(InvoicePost.reject_flag=='checked').order_by(InvoicePost.invoice_from.asc())
            for check_invoice in invoice_post_init:
                count_invoice_in=count_invoice_in+1
                if check_invoice.user_status_invoice=='Approved':
                    flash('Cannot be rejected, It has been approved already!!','danger')
                    return redirect(url_for('adminDash.invoice_view_approveflag',sheet_inx=sheet_inx))
                if check_invoice.user_status_invoice=='Submited' and check_invoice.reject_flag=='checked':
                    t_z=check_invoice.invoice_from
                    approved_date.append(t_z.strftime('%Y-%m-%d'))
            if count_invoice_in>0 and approved_date !=[]:
                user_message_ap='Hi {}! Your reimbursement request on {} has been rejected.'.format(user.firstname,approved_date)
                user_status_ap='unread'
                user_flag_ap=''
                user_title_ap='Reimbursement Request Rejected'
                msg = Message(author=current_user, recipient=user,
                                body_message=user_message_ap,
                                body_title=user_title_ap,
                                body_flag=user_flag_ap,
                                body_trans='invoice_request',
                                body_id=int(0),
                                body_date=datetime.date.today(),
                                body_sheet=sheet_inx,
                                body_status=user_status_ap)
                db.session.add(msg)
                db.session.commit()
                ######send email to user for verification###########
                message_email='Your reimbursement request on {} has been rejected'.format(approved_date)
                body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
                body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
                email(user.email,"Reimbursement Request Rejected",body_html,body_text)
                ######send email to user for verification###########
        invoice_post = InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time))\
                                            .filter(InvoicePost.user_request_invoice=='request_approval')\
                                            .filter(InvoicePost.reject_flag=='checked').order_by(InvoicePost.invoice_from.asc())
        count_int=0
        for invoice_in in invoice_post:
            count_int=count_int+1
            if invoice_in.user_status_invoice!='Approved':
                invoice_in.invoice_flag='checked'
                invoice_in.user_status_invoice='Rejected'
                db.session.commit()
        if count_int==0:
            flash('You have not selected any reimbursement request','danger')
            return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
        else:
            flash('Reimbursement request is rejected','success')
        invoice_post_flag = InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time)).order_by(InvoicePost.invoice_from.asc())
        for invoice_inflag in invoice_post_flag:
            invoice_inflag.reject_flag=''
            db.session.commit()
        return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.invoice_view',sheet_inx=sheet_inx))
##########################################################

######################################
###########LEAVE DOWNLOAD#############
@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/leave_download")
@login_required
def leave_download(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    file_data_leave=LeavePost.query.get_or_404(leave_post_id)
    try:
        return send_file((file_data_leave.imgsrc),attachment_filename=file_data_leave.image,as_attachment=True)
    except:
        flash('No attachment or file not supported format','danger')
        return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
#######Leave Download to leave_view_all_new.html#################
@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/leave_download_new")
@login_required
def leave_download_new(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    file_data_leave=LeavePost.query.get_or_404(leave_post_id)
    try:
        return send_file((file_data_leave.imgsrc),attachment_filename=file_data_leave.image,as_attachment=True)
    except:
        flash('No attachment or file not supported format','danger')
        return redirect(url_for('adminDash.leave_view_new',sheet_inx=sheet_inx))
###########INVOICE DOWNLOAD#############
@adminDash.route("/<username>/<sheet_inx>/<int:invoice_post_id>/invoice_download")
@login_required
def invoice_download(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    file_data_invoice=InvoicePost.query.get_or_404(invoice_post_id)
    try:
        return send_file((file_data_invoice.imgsrc),attachment_filename=file_data_invoice.image,as_attachment=True)
    except:
        flash('No attachment or file not supported format','danger')
        return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))

#########TIMESHEET APPROVAL FROM ADMIN###############
@adminDash.route("/<username>/<int:clock_post_id>/approval_user_clockpost", methods=['POST'])
@login_required
def approval_user_clockpost(username,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    if request.method == 'POST':
        def_val='test'
    #clock_posts.timesheet_status=True
    clock_posts.timesheet_flag='checked'
    db.session.commit()
    flash('TimeSheet has been approved','success')
    return redirect(url_for('adminDash.timesheet_view',sheet_inx='default_inx'))

#########LEAVE APPROVAL FROM ADMIN###############
@adminDash.route("/<username>/<int:leave_post_id>/approval_user_leavepost", methods=['POST'])
@login_required
def approval_user_leavepost(username,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    leave_posts.leave_status=True
    leave_posts.leave_flag='checked'
    db.session.commit()
    flash('Leave request has been approved','success')
    return redirect(url_for('adminDash.leave_view'))

#########INVOICE APPROVAL FROM ADMIN###############
@adminDash.route("/<username>/<int:invoice_post_id>/approval_user_invoicepost", methods=['POST'])
@login_required
def approval_user_invoicepost(username,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    invoice_posts.invoice_status=True
    invoice_posts.invoice_flag='checked'
    db.session.commit()
    flash('Invoice request has been approved','success')
    return redirect(url_for('adminDash.invoice_view'))

#########TIMESHEET REJECT FROM ADMIN###############
@adminDash.route("/<username>/<sheet_inx>/<int:clock_post_id>/reject_user_clockpost", methods=['POST'])
@login_required
def reject_user_clockpost(username,sheet_inx,clock_post_id):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    ####################################################
    if request.method=='POST':
        user_message_ap=request.form.get('txt_message')
        if user_message_ap=='':
            flash('Please type the reason for rejection','danger')
            return redirect(url_for('adminDash.modify_user_clockpostDash',username=user.username,
                                                                       sheet_inx=sheet_inx,
                                                                       clock_post_id=clock_posts.id))
        user_message_ck='Hi {}!Your timesheet on {} has been deleted, please resubmit or contact admin.'.format(user.firstname,clock_posts.day_clock.date())
        user_status_ck="unread"
        user_status_flag=''
        user_title_ck="Timesheets Deleted"
        msg = Message(author=current_user, recipient=user,
                    body_message=user_message_ck,
                    body_flag=user_status_flag,
                    body_title=user_title_ck,
                    body_trans='timesheet',
                    body_id=int(0),
                    body_date=datetime.date.today(),
                    body_sheet=sheet_inx,
                    body_status=user_status_ck)
        db.session.add(msg)
        db.session.commit()
        ######send email to user for verification###########
        message_email='Your timesheet on {} has been been deleted. {}'.format(clock_posts.day_clock.date().strftime('%d/%m/%Y'),user_message_ap)
        body_subject='Timesheets Deleted {}'.format(clock_posts.day_clock.date().strftime('%d/%m/%Y'))
        body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
        body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
        email(user.email,body_subject,body_html,body_text)
        ######send email to user for verification###########
        ####################################################
        db.session.delete(clock_posts)
        db.session.commit()
        flash('TimeSheet has been Deleted','danger')
        return redirect(url_for('adminDash.timesheet_view',username=user.username,sheet_inx=sheet_inx))

#########LEAVE REJECT FROM ADMIN###############
@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/reject_user_leavepost", methods=['POST'])
@login_required
def reject_user_leavepost(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    if request.method=='POST':
        user_message_ap=request.form.get('txt_message')
        if user_message_ap=='':
            flash('Please type the reason for rejection','danger')
            return redirect(url_for('adminDash.modify_user_leavepostDash',username=user.username,
                                                                       sheet_inx=sheet_inx,
                                                                       leave_post_id=leave_posts.id))
        ####################################################
        user_message_ck='Hi {}!Your leave request on {} has been deleted, please resubmit or contact admin.'.format(user.firstname,leave_posts.leave_from.date())
        user_status_ck="unread"
        user_status_flag=''
        user_title_ck="Leave Request Deleted"
        msg = Message(author=current_user, recipient=user,
                    body_message=user_message_ck,
                    body_flag=user_status_flag,
                    body_title=user_title_ck,
                    body_trans='leave_request',
                    body_id=int(0),
                    body_date=datetime.date.today(),
                    body_sheet=sheet_inx,
                    body_status=user_status_ck)
        db.session.add(msg)
        db.session.commit()
        ######send email to user for verification###########
        message_email='Your leave request on {} has been been deleted. {}'.format(leave_posts.leave_from.date().strftime('%d/%m/%Y'),user_message_ap)
        body_subject='Leave Request Deleted on {}'.format(leave_posts.leave_from.date().strftime('%d/%m/%Y'))
        body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
        body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
        email(user.email,body_subject,body_html,body_text)
        ######send email to user for verification###########
        ####################################################
        db.session.delete(leave_posts)
        db.session.commit()
        flash('Leave request has been Deleted','danger')
        return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))


#########REIMBURSEMENT REJECT FROM ADMIN###############
@adminDash.route("/<username>/<sheet_inx>/<int:invoice_post_id>/reject_user_invoicepost", methods=['POST'])
@login_required
def reject_user_invoicepost(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    ####################################################
    if request.method=='POST':
        user_message_ap=request.form.get('txt_message')
        if user_message_ap=='':
            flash('Please type the reason for rejection','danger')
            return redirect(url_for('adminDash.modify_user_invoicepostDash',username=user.username,
                                                                       sheet_inx=sheet_inx,
                                                                       invoice_post_id=invoice_posts.id))
            ####################################################
        user_message_ck='Hi {}!Your reimbursement request on {} has been deleted, please resubmit or contact admin.'.format(user.firstname,invoice_posts.invoice_from.date())
        user_status_ck="unread"
        user_status_flag=''
        user_title_ck="Reimbursement Request Deleted"
        msg = Message(author=current_user, recipient=user,
                    body_message=user_message_ck,
                    body_flag=user_status_flag,
                    body_title=user_title_ck,
                    body_trans='invoice_request',
                    body_id=int(0),
                    body_date=datetime.date.today(),
                    body_sheet=sheet_inx,
                    body_status=user_status_ck)
        db.session.add(msg)
        db.session.commit()
        ######send email to user for verification###########
        message_email='Your reimbursement request on {} has been been deleted. {}'.format(invoice_posts.invoice_from.date().strftime('%d/%m/%Y'),user_message_ap)
        body_subject='Reimbursement Request Deleted on {}'.format(invoice_posts.invoice_from.date().strftime('%d/%m/%Y'))
        body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
        body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
        email(user.email,body_subject,body_html,body_text)
        ######send email to user for verification###########
        ####################################################
        db.session.delete(invoice_posts)
        db.session.commit()
        flash('Reimbursement request has been Deleted','danger')
        return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
#######USER MODE RECTIFY###############
###########TIMESHEETS##################
@adminDash.route("/<username>/<sheet_inx>/<int:clock_post_id>/modify_user_clockpostDash",methods=['GET','POST'])
@login_required
def modify_user_clockpostDash(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    task_all=Task_Add.query.all()
    return render_template('/admin/modify_user_clockpost.html',project_all=project_all,sheet_inx=sheet_inx,task_all=task_all,
                                                                post_data=clock_posts,username=user.username)
#####################TIMESHEET MODIFY FROM ADMIN##############
@adminDash.route("/<username>/<sheet_inx>/<int:clock_post_id>/modify_user_clockpost", methods=['GET','POST'])
@login_required
def modify_user_clockpost(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        #Default Values
        OverTime_15=0
        OverTime_25=0
        OverTime_2=0
        NormalTime=0
        Launch_Break=0
        day_clock_str=request.form.get('clockinout_fromD')
        clock_in_str=request.form.get('clockinout_fromT')
        clock_out_str=request.form.get('clockinout_toT')
        project=request.form.get('clockinout_project')
        task=request.form.get('clockinout_site')
        if day_clock_str=='':
            flash('Please Select Format Correctly','danger')
            return redirect(url_for('adminDash.modify_user_clockpost_error',clock_post_id=clock_post_id,username=user.username,
                                                                            sheet_inx=sheet_inx))
        clock_in_strF= day_clock_str + clock_in_str
        clock_out_strF= day_clock_str + clock_out_str

        day_clock = datetime.datetime.strptime(day_clock_str,'%d/%m/%Y')
        clock_in = datetime.datetime.strptime(clock_in_strF,'%d/%m/%Y%H:%M')
        clock_out = datetime.datetime.strptime(clock_out_strF,'%d/%m/%Y%H:%M')
        #print(day_clock,clock_in,clock_out)
        #Hour Calculation of Employer
        time_dev=(clock_out-clock_in)/60
        hour_check,min_check= divmod(time_dev.seconds, 3600)
        hour_day=round((hour_check+float(min_check/60)),1)
        #######Check if Clockout time is not supported#############
        if(hour_day>24):
            flash('Please select properly Check Out Time','danger')
            return redirect(url_for('adminDash.modify_user_clockpost_error',clock_post_id=clock_post_id,username=user.username,sheet_inx=sheet_inx))
        #######Modification#####Inorder to Modify Existing One########
        clock_posts_init = TimeSheetPost.query.get_or_404(clock_post_id)
        clock_posts_init.day_clock=day_clock+datetime.timedelta(365)
        db.session.commit()
        ############################################################
        #Default Initialization
        time_query=TimeSheetPost.query.filter(TimeSheetPost.day_clock==day_clock).filter(TimeSheetPost.user_id==user.id)
        hour_day_repeat=0
        Launch_Break_repeat=0
        NormalTime_repeat=0
        OverTime_15_repeat=0
        OverTime_25_repeat=0
        for time_init_query in time_query:
            if (clock_in>time_init_query.clock_in and clock_out<time_init_query.clock_out):
                flash('Checkin and Checkout time is overlapping','danger')
                clock_posts_init = TimeSheetPost.query.get_or_404(clock_post_id)
                clock_posts_init.day_clock=day_clock
                db.session.commit()
                return redirect(url_for('adminDash.modify_user_clockpost_error',clock_post_id=clock_post_id,username=user.username,sheet_inx=sheet_inx))
            if (clock_out>time_init_query.clock_in and clock_in<time_init_query.clock_out):
                flash('Checkin and Checkout time is overlapping','danger')
                clock_posts_init = TimeSheetPost.query.get_or_404(clock_post_id)
                clock_posts_init.day_clock=day_clock
                db.session.commit()
                return redirect(url_for('adminDash.modify_user_clockpost_error',clock_post_id=clock_post_id,username=user.username,sheet_inx=sheet_inx))
            time_dev2=(time_init_query.clock_out-time_init_query.clock_in)/60
            hour_check2,min_check2= divmod(time_dev2.seconds, 3600)
            hour_day2=round((hour_check2+float(min_check2/60)),1)
            hour_day_repeat=hour_day_repeat+hour_day2
            Launch_Break_repeat=Launch_Break_repeat+time_init_query.Launch_Break
            OverTime_15_repeat=OverTime_15_repeat+time_init_query.OverTime_15
            OverTime_25_repeat=OverTime_25_repeat+time_init_query.OverTime_25
            NormalTime_repeat=NormalTime_repeat+time_init_query.NormalTime
        hour_day_main=hour_day
        hour_day=hour_day_main+ hour_day_repeat
        ################PUBLIC HOLIDAY###########################
        count_hol=0
        holiday_post_init=Public_Holiday.query.filter(Public_Holiday.day_clock==day_clock)
        for post_initm in holiday_post_init:
            count_hol=count_hol+1
        if count_hol>=1:
            if  hour_day<=6:
                NormalTime=0
                Launch_Break=0
                OverTime_15=0
                OverTime_2=0
                OverTime_25=round(hour_day_main-Launch_Break,1)
            else:
                NormalTime=0
                if Launch_Break_repeat==0:
                    Launch_Break=0.5
                else:
                    Launch_Break=0
                OverTime_15=0
                OverTime_2=0
                OverTime_25=round(hour_day_main-Launch_Break,1)
            clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
            clock_posts.day_clock=day_clock
            clock_posts.project=project
            clock_posts.task=task
            clock_posts.clock_in=clock_in
            clock_posts.clock_out=clock_out
            clock_posts.NormalTime=NormalTime
            clock_posts.OverTime_15=OverTime_15
            clock_posts.OverTime_2=OverTime_2
            clock_posts.OverTime_25=OverTime_25
            clock_posts.Launch_Break=Launch_Break
            db.session.commit()
            flash('TimeSheet has been Modified','success')
            return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
        ###########################################
        if day_clock.strftime("%A")=='Saturday':
            if hour_day <=2:
                NormalTime=0
                Launch_Break=0
                OverTime_15=round(hour_day_main,1)
                OverTime_2=0
                OverTime_25=0
            elif hour_day>2 and hour_day<=6:
                NormalTime=0
                OverTime_25=0
                Launch_Break=0
                if OverTime_15_repeat==2:
                    OverTime_15=0
                else:
                    OverTime_15=2
                OverTime_2=round(abs(hour_day_main-OverTime_15-Launch_Break),1)
            else:
                NormalTime=0
                OverTime_25=0
                if Launch_Break_repeat==0:
                    Launch_Break=0.5
                else:
                    Launch_Break=0
                if OverTime_15_repeat==2:
                    OverTime_15=0
                else:
                    OverTime_15=2
                OverTime_2=round(abs(hour_day_main-OverTime_15-Launch_Break),1)
        elif day_clock.strftime("%A")=='Sunday':
            if  hour_day<=6:
                NormalTime=0
                OverTime_25=0
                Launch_Break=0
                OverTime_15=0
                OverTime_2=round(hour_day_main-Launch_Break,1)
            else:
                NormalTime=0
                OverTime_25=0
                if Launch_Break_repeat==0:
                    Launch_Break=0.5
                else:
                    Launch_Break=0
                OverTime_15=0
                OverTime_2=round(hour_day_main-Launch_Break,1)
        else:
            if hour_day<=6:
                Launch_Break=0
                OverTime_15=0
                OverTime_25=0
                OverTime_2=0
                NormalTime=round(hour_day_main-Launch_Break,1)
            elif hour_day>6 and hour_day<=8.5:
                if Launch_Break_repeat==0:
                    Launch_Break=0.5
                else:
                    Launch_Break=0
                OverTime_15=0
                OverTime_2=0
                OverTime_25=0
                NormalTime=round(hour_day_main-Launch_Break,1)
            elif hour_day >8.5 and hour_day <=10:
                if Launch_Break_repeat==0:
                    Launch_Break=0.5
                else:
                    Launch_Break=0
                if NormalTime_repeat!=0:
                    NormalTime=round(abs(8-NormalTime_repeat),1)
                else:
                    NormalTime=8
                OverTime_25=0
                OverTime_15=round(abs(round(hour_day_main,1)-Launch_Break-NormalTime),1)
                OverTime_2=0
            else:
                if Launch_Break_repeat==0:
                    Launch_Break=0.5
                else:
                    Launch_Break=0
                if NormalTime_repeat!=0:
                    NormalTime=round(abs(8-NormalTime_repeat),1)
                else:
                    NormalTime=8
                if OverTime_15_repeat!=0:
                    OverTime_15=0
                else:
                    OverTime_15=2
                OverTime_25=0
                OverTime_2=round(abs(round(hour_day_main,1)-Launch_Break-OverTime_15-NormalTime),1)
        clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
        clock_posts.day_clock=day_clock
        clock_posts.project=project
        clock_posts.task=task
        clock_posts.clock_in=clock_in
        clock_posts.clock_out=clock_out
        clock_posts.NormalTime=NormalTime
        clock_posts.OverTime_15=OverTime_15
        clock_posts.OverTime_25=OverTime_25
        clock_posts.OverTime_2=OverTime_2
        clock_posts.Launch_Break=Launch_Break
        db.session.commit()
        flash('TimeSheet has been Modified','success')
        return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
    return render_template('/admin/modify_user_clockpost.html',post_data=clock_posts,username=user.username,sheet_inx=sheet_inx)
#######USER MODE RECTIFY TIMESHEETS###############
@adminDash.route("/<username>/<sheet_inx>/<int:clock_post_id>/modify_user_clockpost_error",methods=['GET','POST'])
@login_required
def modify_user_clockpost_error(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    #print(clock_post_id)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    task_all=Task_Add.query.all()
    #print(clock_posts)
    return render_template('/admin/modify_user_clockpost.html',project_all=project_all,sheet_inx=sheet_inx,task_all=task_all,
                                                                post_data=clock_posts,username=user.username)
#######USER MODE RECTIFY###############
###########LEAVE##################
@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/modify_user_leavepostDash")
@login_required
def modify_user_leavepostDash(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
            abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    return render_template('/admin/modify_user_leavepost.html',post_data=leave_posts,sheet_inx=sheet_inx,
                                                                username=user.username)
#####################LEAVE MODIFY FROM ADMIN##############
@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/modify_user_leavepost", methods=['GET','POST'])
@login_required
def modify_user_leavepost(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        #Default Values
        leave_from_str=request.form.get('leave_from')
        leave_to_str=request.form.get('leave_to')
        leave_type=request.form.get('leave_type')
        if (leave_from_str=='') or (leave_to_str=='') or (leave_type=='Choose...'):
            flash('Please Select Format Correctly','danger')
            return redirect(url_for('adminDash.modify_user_leavepost_error',leave_post_id=leave_post_id,sheet_inx=sheet_inx,username=user.username))
        leave_from = datetime.datetime.strptime(leave_from_str,'%d/%m/%Y')
        leave_to = datetime.datetime.strptime(leave_to_str,'%d/%m/%Y')
        leave_days_total = (leave_to -leave_from) + datetime.timedelta(1)
        leave_days=leave_days_total.days
        if leave_days<0:
            flash('End Day of leave cannot be ahead than Start Day of leave','danger')
            return redirect(url_for('adminDash.modify_user_leavepost_error',leave_post_id=leave_post_id,sheet_inx=sheet_inx,username=user.username))
        leave_posts = LeavePost.query.get_or_404(leave_post_id)
        leave_posts.leave_from=leave_from
        leave_posts.leave_to=leave_to
        leave_posts.leave_days=leave_days
        leave_posts.leave_type=leave_type
        db.session.commit()
        flash('Leave request has been Modified','success')
        return redirect(url_for('adminDash.leave_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
    return render_template('/admin/modify_user_leavepost.html',post_data=leave_posts,sheet_inx=sheet_inx,username=user.username)
#######USER MODE RECTIFY LEAVE###############
@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/modify_user_leavepost_error",methods=['GET','POST'])
@login_required
def modify_user_leavepost_error(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    return render_template('/admin/modify_user_leavepost.html',post_data=leave_posts,sheet_inx=sheet_inx,username=user.username)

#######USER MODE RECTIFY###############
###########INVOICE##################
@adminDash.route("/<username>/<sheet_inx>/<int:invoice_post_id>/modify_user_invoicepostDash")
@login_required
def modify_user_invoicepostDash(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    invoice_all=Invoice_Add.query.all()
    return render_template('/admin/modify_user_invoicepost.html',username=user.username,sheet_inx=sheet_inx,post_data=invoice_posts,
                                                                    invoice_all=invoice_all)
#####################LEAVE MODIFY FROM ADMIN##############
@adminDash.route("/<username>/<sheet_inx>/<int:invoice_post_id>/modify_user_invoicepost", methods=['GET','POST'])
@login_required
def modify_user_invoicepost(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        #Default Values
        invoice_date_str=request.form.get('invoice_date')
        invoice_supplier=request.form.get('invoice_supplier')
        invoice_Total=request.form.get('invoice_Total')
        invoice_category=request.form.get('invoice_category')
        if (invoice_date_str=='') or (invoice_category=='Choose...'):
            flash('Please Select Format Correctly','danger')
            invoice_all=Invoice_Add.query.all()
            return redirect(url_for('adminDash.modify_user_invoicepost_error',username=user.username,sheet_inx=sheet_inx,
                                                                                invoice_post_id=invoice_post_id,invoice_all=invoice_all))
        invoice_from = datetime.datetime.strptime(invoice_date_str,'%d/%m/%Y')
        invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
        invoice_posts.invoice_from=invoice_from
        invoice_posts.invoice_supplier=invoice_supplier
        invoice_posts.invoice_Total=invoice_Total
        invoice_posts.invoice_category=invoice_category
        db.session.commit()
        flash('Reimbursement request has been Modified','success')
        return redirect(url_for('adminDash.invoice_view_standardF_submit',username=user.username,sheet_inx=sheet_inx))
        #return redirect(url_for('adminDash.invoice_view_new',sheet_inx=sheet_inx))
    return render_template('/admin/modify_user_invoicepost.html',username=user.username,post_data=invoice_posts,sheet_inx=sheet_inx)
#######USER MODE RECTIFY LEAVE###############
@adminDash.route("/<username>/<sheet_inx>/<int:invoice_post_id>/modify_user_invoicepost_error",methods=['GET','POST'])
@login_required
def modify_user_invoicepost_error(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    invoice_all=Invoice_Add.query.all()
    return render_template('/admin/modify_user_invoicepost.html',username=user.username,sheet_inx=sheet_inx,post_data=invoice_posts,
                                                                    invoice_all=invoice_all)
################TIMESHEETS VIEW OF INDIVIDUAL USER#####################
##############TIMESHEETS APPROVAL FROM ADMIN#############################
#########TIMESHEET APPROVAL FROM ADMIN###############
@adminDash.route("/<username>/<int:clock_post_id>/approval_ind_clockpost", methods=['POST'])
@login_required
def approval_ind_clockpost(username,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    if request.method == 'POST':
        clock_posts.admin_request_timesheet='checked'
        db.session.commit()
        return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username))
    return redirect(url_for('adminDash.timesheet_view_standardF',username=user.username))

################USER SEND REQUEST FOR APPROVAL#################################
################TIMESHEET#############
#######Individual Approval############
@adminDash.route("/<username>/<sheet_inx>/timesheet_admin_approval", methods=['POST'])
@login_required
def timesheet_admin_approval(username,sheet_inx):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
        else:
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
        clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time))\
                                            .filter(TimeSheetPost.user_request_timesheet=='request_approval')\
                                            .order_by(TimeSheetPost.day_clock.asc())
        approved_date=[]
        for clock_in in clock_post:
            if clock_in.user_status_timesheet=='Submited':
                t_z=clock_in.day_clock
                approved_date.append(t_z.strftime('%Y-%m-%d'))
            if clock_in.user_status_timesheet!='Rejected':
                clock_in.admin_request_timesheet='checked'
                clock_in.user_status_timesheet='Approved'
                clock_in.timesheet_flag=''
                db.session.commit()
        ################################################
        if approved_date !=[]:
            user_message_ap='Hi {}! Your timesheet on {} has been approved.'.format(user.firstname,approved_date)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Time Entries Approval'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='timesheet',
                            body_id=int(0),
                            body_date=datetime.date.today(),
                            body_sheet=sheet_inx,
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your timesheet on {} has been approved'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Time Entries Approval",body_html,body_text)
            ######send email to user for verification###########
        ################################################
        flash('TimeSheet has been approved','success')
        return redirect(url_for('adminDash.timesheet_view_standard',username=username))
    return redirect(url_for('adminDash.timesheet_view_standard',username=username))
####################################################################################

#######All Approval############
@adminDash.route("/<sheet_inx>/timesheet_admin_approval_all", methods=['POST'])
@login_required
def timesheet_admin_approval_all(sheet_inx):
    if session.get('is_author')!=True:
        abort(403)
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
        else:
            start_time=today_date - datetime.timedelta(idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
    #######################MESSAGE NOTIFICATION#################
    user_all_get=[]
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    for in_user in user_all:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        count_clock_in=0
        approved_date=[]
        clock_post_init = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time))\
                                                .filter(TimeSheetPost.user_request_timesheet=='request_approval')\
                                                .order_by(TimeSheetPost.day_clock.asc())
        for check_clock in clock_post_init:
            count_clock_in=count_clock_in+1
            if check_clock.user_status_timesheet=='Submited':
                t_z=check_clock.day_clock
                approved_date.append(t_z.strftime('%Y-%m-%d'))
        if count_clock_in>0 and approved_date !=[]:
            user_message_ap='Hi {}! Your timesheet on {} has been approved.'.format(user.firstname,approved_date)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Time Entries Approval'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='timesheet',
                            body_id=int(0),
                            body_date=datetime.date.today(),
                            body_sheet=sheet_inx,
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your timesheet on {} has been approved'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Time Entries Approval",body_html,body_text)
            ######send email to user for verification###########
       ##################################################################
    clock_post = TimeSheetPost.query.filter(TimeSheetPost.day_clock.between(start_time,end_time))\
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval')\
                                        .order_by(TimeSheetPost.day_clock.asc())
    for clock_in in clock_post:
        if clock_in.user_status_timesheet!='Rejected':
            clock_in.admin_request_timesheet='checked'
            clock_in.user_status_timesheet='Approved'
            clock_in.timesheet_flag=''
            db.session.commit()
    flash('TimeSheet has been approved','success')
    return redirect(url_for('adminDash.timesheet_view',sheet_inx=sheet_inx))
####################################################################################

################USER SEND REQUEST FOR APPROVAL#################################
################LEAVE#############
#######Individual Approval############
@adminDash.route("/<username>/<sheet_inx>/leave_admin_approval", methods=['POST'])
@login_required
def leave_admin_approval(username,sheet_inx):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='last_year':
            start_time=today_date - datetime.timedelta(365)
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
        elif sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
        else:
            start_time=today_date - datetime.timedelta(idx_week)
        end_time=today_date + datetime.timedelta(365)
        leave_post = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time))\
                                        .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
        approved_date=[]
        for leave_in in leave_post:
            if leave_in.user_status_leave=='Submited':
                t_z=leave_in.leave_from
                approved_date.append(t_z.strftime('%Y-%m-%d'))
                t_z1=leave_in.leave_to
                approved_date.append(t_z1.strftime('%Y-%m-%d'))
            if leave_in.user_status_leave!='Rejected':
                leave_in.admin_request_leave='checked'
                leave_in.user_status_leave='Approved'
                leave_in.leave_flag=''
                db.session.commit()
                ###################Timesheet Management Automatically########
                start_lv=datetime.time()
                end_lv=datetime.time()
                start_lv=leave_in.leave_from.date()
                end_lv=leave_in.leave_to.date()
                delta = datetime.timedelta(days=1)
                d_in=start_lv
                inc_d=0
                while d_in <=end_lv:
                    day_time=leave_in.leave_from+datetime.timedelta(inc_d)
                    inc_d=inc_d+1
                    inx_day=d_in.strftime('%A')
                    if(inx_day=='Saturday' or inx_day=='Sunday' or leave_in.leave_type=='Leave without Pay'):
                        clock_post_default = TimeSheetPost(day_clock=day_time,project=leave_in.leave_type,
                                                    comment='',clock_in=datetime.date.today(),
                                                    task=leave_in.leave_type,travel_choice='',
                                                    clock_out=datetime.date.today(),distance='',
                                                    OverTime_15=int(0),NormalTime=int(0),
                                                    OverTime_2=int(0),location='',OverTime_25=int(0),
                                                    Launch_Break=int(0),timesheet_status=False,
                                                    timesheet_flag='',user_request_timesheet='request_approval',
                                                    admin_request_timesheet='',user_status_timesheet='Approved',
                                                    meal_type='default',meal_rate_day=float(0),meal_allowance='no',
                                                    user_check_timesheet='',job_num='-',
                                                    remainder='',accept_flag='',
                                                    reject_flag='',user_id=leave_in.author.id)
                        db.session.add(clock_post_default)
                        db.session.commit()
                    else:
                        clock_post_default = TimeSheetPost(day_clock=day_time,project=leave_in.leave_type,
                                                    comment='',clock_in=datetime.date.today(),
                                                    task=leave_in.leave_type,travel_choice='',
                                                    clock_out=datetime.date.today(),distance='',
                                                    OverTime_15=int(0),NormalTime=int(8),
                                                    OverTime_2=int(0),location='',OverTime_25=int(0),
                                                    Launch_Break=int(0),timesheet_status=False,
                                                    timesheet_flag='',user_request_timesheet='request_approval',
                                                    admin_request_timesheet='',user_status_timesheet='Approved',
                                                    meal_type='default',meal_rate_day=float(0),meal_allowance='no',
                                                    user_check_timesheet='',job_num='-',
                                                    remainder='',accept_flag='',
                                                    reject_flag='',user_id=leave_in.author.id)
                        db.session.add(clock_post_default)
                        db.session.commit()
                    d_in = d_in + delta
                ##################################
        ###############MESSAGE SENDING TO USERS###############
        if approved_date !=[]:
            user_message_ap='Hi {}! Your leave request has been approved.'.format(user.firstname)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Leave Request Approval'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='leave_request',
                            body_id=int(0),
                            body_date=datetime.date.today(),
                            body_sheet=sheet_inx,
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your leave request on {} has been approved'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Leave Request Approval",body_html,body_text)
            ######send email to user for verification###########
        ################################################
        flash('Leave request has been approved','success')
        return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
    return redirect(url_for('adminDash.leave_view',sheet_inx=sheet_inx))
####################################################################################

################LEAVE#############
#######Individual Approval############
@adminDash.route("/<username>/<sheet_inx>/invoice_admin_approval", methods=['POST'])
@login_required
def invoice_admin_approval(username,sheet_inx):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    ##########################################################
    if request.method=='POST':
        today_date=datetime.date.today()
        idx_week=(today_date.weekday()+1)%7
        #Default Initialization
        start_time=datetime.time()
        end_time=datetime.time()
        if sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
        elif sheet_inx=='last_week':
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=start_time+datetime.timedelta(7)
            end_time=today_date + datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(49+idx_week)
            end_time=today_date + datetime.timedelta(idx_week)
        invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                            .filter(InvoicePost.user_request_invoice=='request_approval')\
                                            .order_by(InvoicePost.invoice_from.asc())
        approved_date=[]
        for invoice_in in invoice_post:
            if invoice_in.user_status_invoice=='Submited':
                t_z=invoice_in.invoice_from
                approved_date.append(t_z.strftime('%Y-%m-%d'))
            if invoice_in.user_status_invoice!='Rejected':
                invoice_in.admin_request_invoice='checked'
                invoice_in.user_status_invoice='Approved'
                invoice_in.invoice_flag=''
                db.session.commit()
        ###############MESSAGE SENDING TO USERS###############
        if approved_date !=[]:
            user_message_ap='Hi {}! Your reimbursement request on {} has been approved.'.format(user.firstname,approved_date)
            user_status_ap='unread'
            user_flag_ap=''
            user_title_ap='Reimbursement Request Approval'
            msg = Message(author=current_user, recipient=user,
                            body_message=user_message_ap,
                            body_title=user_title_ap,
                            body_flag=user_flag_ap,
                            body_trans='invoice_request',
                            body_id=int(0),
                            body_date=datetime.date.today(),
                            body_sheet=sheet_inx,
                            body_status=user_status_ap)
            db.session.add(msg)
            db.session.commit()
            ######send email to user for verification###########
            message_email='Your reimbursement request on {} has been approved'.format(approved_date)
            body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
            body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
            email(user.email,"Reimbursement Request Approval",body_html,body_text)
            ######send email to user for verification###########
        ################################################
        flash('Invoice request has been approved','success')
        return redirect(url_for('adminDash.invoice_view_standard',username=username))
    return redirect(url_for('adminDash.invoice_view_standard',username=username))
####################################################################################
###################REJECT CLOCKPOST###########################
#########TIMESHEET APPROVAL FROM ADMIN###############
@adminDash.route("/<username>/<sheet_inx>/<int:clock_post_id>/reject_userpost_clock", methods=['POST'])
@login_required
def reject_userpost_clock(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    if clock_posts.user_status_timesheet=='Approved':
        flash('Cannot be rejected, It has been approved already!!','danger')
        return redirect(url_for('adminDash.timesheet_rejectbutton',inx_week_reject=sheet_inx))
    if clock_posts.timesheet_flag=='checked':
        clock_posts.timesheet_flag=''
        clock_posts.user_status_timesheet='Submited'
    else:
        clock_posts.timesheet_flag='checked'
        clock_posts.user_status_timesheet='Rejected'
    db.session.commit()
    ################################################
    user_message_rp='Hi {}! Your timesheet on {} has been rejected, please contact admin or resubmit.'.format(user.firstname,clock_posts.day_clock.date())
    user_status_rp='unread'
    user_flag_rp=''
    user_title_rp='Time Entries Rejected'
    msg = Message(author=current_user, recipient=user,
                    body_message=user_message_rp,
                    body_title=user_title_rp,
                    body_flag=user_flag_rp,
                    body_trans='timesheet',
                    body_id=int(0),
                    body_date=datetime.date.today(),
                    body_sheet=sheet_inx,
                    body_status=user_status_rp)
    db.session.add(msg)
    db.session.commit()
    ######send email to user for verification###########
    message_email='Your timesheet on {} has been rejected, please contact admin or resubmit'.format(clock_posts.day_clock.date())
    body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
    body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
    email(user.email,"Time Entries Rejected",body_html,body_text)
    ######send email to user for verification###########
    ################################################
    return redirect(url_for('adminDash.timesheet_rejectbutton',inx_week_reject=sheet_inx))

#########REJECT TIMESHEET INDIVIDUAL###############
@adminDash.route("/<username>/<sheet_inx>/<int:clock_post_id>/reject_ind_userpost_clock", methods=['POST'])
@login_required
def reject_ind_userpost_clock(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    if clock_posts.user_status_timesheet=='Approved':
        flash('Cannot be rejected, It has been approved already!!','danger')
        return redirect(url_for('adminDash.timesheet_view_standardF_rejectbutton',sheet_inx=sheet_inx,username=user.username))
    if clock_posts.timesheet_flag=='checked':
        clock_posts.timesheet_flag=''
        clock_posts.user_status_timesheet='Submited'
    else:
        clock_posts.timesheet_flag='checked'
        clock_posts.user_status_timesheet='Rejected'
    db.session.commit()
    ##################MESSAGE ######################
    ################################################
    user_message_rp='Hi {}! Your timesheet on {} has been rejected, please contact admin or resubmit.'.format(user.firstname,clock_posts.day_clock.date())
    user_status_rp='unread'
    user_flag_rp=''
    user_title_rp='Time Entries Rejected'
    msg = Message(author=current_user, recipient=user,
                    body_message=user_message_rp,
                    body_title=user_title_rp,
                    body_flag=user_flag_rp,
                    body_trans='timesheet',
                    body_id=int(0),
                    body_date=datetime.date.today(),
                    body_sheet=sheet_inx,
                    body_status=user_status_rp)
    db.session.add(msg)
    db.session.commit()
    ######send email to user for verification###########
    message_email='Your timesheet on {} has been rejected, please contact admin or resubmit'.format(clock_posts.day_clock.date())
    body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
    body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
    email(user.email,"Time Entries Rejected",body_html,body_text)
    ######send email to user for verification###########
    ################################################
    return redirect(url_for('adminDash.timesheet_view_standardF_rejectbutton',sheet_inx=sheet_inx,username=user.username))

#########ADMIN TIMESHEET VIEW################
@adminDash.route("/<username>/<sheet_inx>/timesheet_view_standardF_rejectbutton")
@login_required
def timesheet_view_standardF_rejectbutton(sheet_inx,username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    inx_week_reject=sheet_inx
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if inx_week_reject=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    elif inx_week_reject=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    else:
        start_time=today_date - datetime.timedelta(idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        #end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time))\
                                        .filter(TimeSheetPost.user_request_timesheet=='request_approval')\
                                        .order_by(TimeSheetPost.day_clock.asc())
    return render_template('/admin/view_timesheet_standard_reject.html', post_data=clock_post, inx_week=inx_week,user=user,
                                                                            user_all=user_all,end_time=end_day)
##########################################################################
################LEAVE REQUEST REJECT FROM ADMIN###########################
@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/reject_userpost_leave", methods=['POST'])
@login_required
def reject_userpost_leave(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    if leave_posts.user_status_leave=='Approved':
        flash('Cannot be rejected, It has been approved already!!','danger')
        return redirect(url_for('adminDash.leave_rejectbutton',inx_week_reject=sheet_inx))
    if leave_posts.leave_flag=='checked':
        leave_posts.leave_flag=''
        leave_posts.user_status_leave='Submited'
    else:
        leave_posts.leave_flag='checked'
        leave_posts.user_status_leave='Rejected'
    db.session.commit()
    ################################################
    user_message_rp='Hi {}! Your {} leave request from {} till {} has been rejected, please contact admin or resubmit.'\
                        .format(user.firstname,leave_posts.leave_type,leave_posts.leave_from.date(),leave_posts.leave_to.date())
    user_status_rp='unread'
    user_flag_rp=''
    user_title_rp='Leave Request Rejected'
    msg = Message(author=current_user, recipient=user,
                    body_message=user_message_rp,
                    body_title=user_title_rp,
                    body_flag=user_flag_rp,
                    body_trans='leave_request',
                    body_id=int(0),
                    body_date=datetime.date.today(),
                    body_sheet=sheet_inx,
                    body_status=user_status_rp)
    db.session.add(msg)
    db.session.commit()
    ######send email to user for verification###########
    message_email='Your {} leave request from {} till {} has been rejected, please contact admin or resubmit'\
                    .format(leave_posts.leave_type,leave_posts.leave_from.date(),leave_posts.leave_to.date())
    body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
    body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
    email(user.email,"Leave Request Rejected",body_html,body_text)
    ######send email to user for verification###########
    ################################################
    return redirect(url_for('adminDash.leave_rejectbutton',inx_week_reject=sheet_inx))

@adminDash.route("/<username>/<sheet_inx>/<int:leave_post_id>/reject_ind_userpost_leave", methods=['POST'])
@login_required
def reject_ind_userpost_leave(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    if leave_posts.user_status_leave=='Approved':
        flash('Cannot be rejected, It has been approved already!!','danger')
        return redirect(url_for('adminDash.leave_view_standardF_rejectbutton',sheet_inx=sheet_inx,username=user.username))
    if leave_posts.leave_flag=='checked':
        leave_posts.leave_flag=''
        leave_posts.user_status_leave='Submited'
    else:
        leave_posts.leave_flag='checked'
        leave_posts.user_status_leave='Rejected'
    db.session.commit()
    ################################################
    user_message_rp='Hi {}! Your {} leave request from {} till {} has been rejected, please contact admin or resubmit.'\
                        .format(user.firstname,leave_posts.leave_type,leave_posts.leave_from.date(),leave_posts.leave_to.date())
    user_status_rp='unread'
    user_flag_rp=''
    user_title_rp='Leave Request Rejected'
    msg = Message(author=current_user, recipient=user,
                    body_message=user_message_rp,
                    body_title=user_title_rp,
                    body_flag=user_flag_rp,
                    body_trans='leave_request',
                    body_id=int(0),
                    body_date=datetime.date.today(),
                    body_sheet=sheet_inx,
                    body_status=user_status_rp)
    db.session.add(msg)
    db.session.commit()
    ######send email to user for verification###########
    message_email='Your {} leave request from {} till {} has been rejected, please contact admin or resubmit'\
                    .format(leave_posts.leave_type,leave_posts.leave_from.date(),leave_posts.leave_to.date())
    body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
    body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
    email(user.email,"Leave Request Rejected",body_html,body_text)
    ######send email to user for verification###########
    ################################################
    return redirect(url_for('adminDash.leave_view_standardF_rejectbutton',sheet_inx=sheet_inx,username=user.username))

@adminDash.route("/<inx_week_reject>/leave_rejectbutton")
@login_required
def leave_rejectbutton(inx_week_reject):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if inx_week_reject=='last_year':
        start_time=today_date - datetime.timedelta(365)
        inx_week='last_year'
    elif inx_week_reject=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        inx_week='last_week'
    elif inx_week_reject=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        inx_week='this_month'
    else:
        start_time=today_date - datetime.timedelta(idx_week)
        inx_week='this_week'
    end_time=today_date + datetime.timedelta(365)
    leave_view_data=LeavePost.query.filter(LeavePost.leave_from.between(start_time,end_time))\
                                    .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
    #user_view=User.query.all()
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ##Finding Unique User
    unique_user=[]
    for in_view in leave_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    #########################
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        leave_ind=LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time))\
                                    .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
        count_leave_in=0
        for check_leave in leave_ind:
            count_leave_in=count_leave_in+1
        if count_leave_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/leave_view_all_reject.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,post_data=leave_view_data,
                                                                inx_week=inx_week,end_time=end_time,user_view=user_view,view_unique=view_unique,
                                                                len_user=len_user,unique_user=unique_user)

@adminDash.route("/<username>/<sheet_inx>/leave_view_standardF_rejectbutton")
@login_required
def leave_view_standardF_rejectbutton(sheet_inx,username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    inx_week_reject=sheet_inx
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if inx_week_reject=='last_year':
        start_time=today_date - datetime.timedelta(365)
        inx_week='last_year'
    elif inx_week_reject=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        inx_week='last_week'
    elif inx_week_reject=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        inx_week='this_month'
    else:
        start_time=today_date - datetime.timedelta(idx_week)
        inx_week='this_week'
    end_time=today_date + datetime.timedelta(365)
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    leave_post = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time))\
                                    .filter(LeavePost.user_request_leave=='request_approval').order_by(LeavePost.leave_from.asc())
    return render_template('/admin/view_leave_standard_reject.html', post_data=leave_post, inx_week=inx_week,user_all=user_all,
                                                                        user=user,end_time=end_time)
################################################################################
#########ADMIN INVOICE VIEW REJECT ################
################INVOICE REQUEST REJECT FROM ADMIN###########################
@adminDash.route("/<username>/<sheet_inx>/<int:invoice_post_id>/reject_userpost_invoice", methods=['POST'])
@login_required
def reject_userpost_invoice(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    if invoice_posts.user_status_invoice=='Approved':
        flash('Cannot be rejected, It has been approved already!!','danger')
        return redirect(url_for('adminDash.invoice_rejectbutton',inx_week_reject=sheet_inx))
    if invoice_posts.invoice_flag=='checked':
        invoice_posts.invoice_flag=''
        invoice_posts.user_status_invoice='Submited'
    else:
        invoice_posts.invoice_flag='checked'
        invoice_posts.user_status_invoice='Rejected'
    db.session.commit()
    ################################################
    user_message_rp='Hi {}! Your reimbursement from {} on {} has been rejected, please contact admin or resubmit.'\
                        .format(user.firstname,invoice_posts.invoice_supplier,invoice_posts.invoice_from.date())
    user_status_rp='unread'
    user_flag_rp=''
    user_title_rp='Reimbursement Request Rejected'
    msg = Message(author=current_user, recipient=user,
                    body_message=user_message_rp,
                    body_title=user_title_rp,
                    body_flag=user_flag_rp,
                    body_trans='invoice_request',
                    body_date=datetime.date.today(),
                    body_id=int(0),
                    body_sheet=sheet_inx,
                    body_status=user_status_rp)
    db.session.add(msg)
    db.session.commit()
    ######send email to user for verification###########
    message_email='Your reimbursement from {} on {} has been rejected, please contact admin or resubmit'\
                    .format(invoice_posts.invoice_supplier,invoice_posts.invoice_from.date())
    body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
    body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
    email(user.email,"Reimbursement Request Rejected",body_html,body_text)
    ######send email to user for verification###########
    ################################################
    return redirect(url_for('adminDash.invoice_rejectbutton',inx_week_reject=sheet_inx))

@adminDash.route("/<username>/<sheet_inx>/<int:invoice_post_id>/reject_ind_userpost_invoice", methods=['POST'])
@login_required
def reject_ind_userpost_invoice(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    if invoice_posts.user_status_invoice=='Approved':
        flash('Cannot be rejected, It has been approved already!!','danger')
        return redirect(url_for('adminDash.invoice_view_standardF_rejectbutton',sheet_inx=sheet_inx,username=user.username))
    if invoice_posts.invoice_flag=='checked':
        invoice_posts.invoice_flag=''
        invoice_posts.user_status_invoice='Submited'
    else:
        invoice_posts.invoice_flag='checked'
        invoice_posts.user_status_invoice='Rejected'
    db.session.commit()
    ################################################
    user_message_rp='Hi {}! Your reimbursement from {} on {} has been rejected, please contact admin or resubmit.'\
                        .format(user.firstname,invoice_posts.invoice_supplier,invoice_posts.invoice_from.date())
    user_status_rp='unread'
    user_flag_rp=''
    user_title_rp='Reimbursement Request Rejected'
    msg = Message(author=current_user, recipient=user,
                    body_message=user_message_rp,
                    body_title=user_title_rp,
                    body_flag=user_flag_rp,
                    body_trans='invoice_request',
                    body_id=int(0),
                    body_date=datetime.date.today(),
                    body_sheet=sheet_inx,
                    body_status=user_status_rp)
    db.session.add(msg)
    db.session.commit()
    ######send email to user for verification###########
    message_email='Your reimbursement from {} on {} has been rejected, please contact admin or resubmit'\
                    .format(invoice_posts.invoice_supplier,invoice_posts.invoice_from.date())
    body_html=render_template('mail/user/reminder.html',user=user,message_email=message_email)
    body_text=render_template('mail/user/reminder.txt',user=user,message_email=message_email)
    email(user.email,"Reimbursement Request Rejected",body_html,body_text)
    ######send email to user for verification###########
    ################################################
    return redirect(url_for('adminDash.invoice_view_standardF_rejectbutton',sheet_inx=sheet_inx,username=user.username))

@adminDash.route("/<inx_week_reject>/invoice_rejectbutton")
@login_required
def invoice_rejectbutton(inx_week_reject):
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if inx_week_reject=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif inx_week_reject=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    elif inx_week_reject=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=start_time+datetime.timedelta(7)
        end_time=today_date + datetime.timedelta(idx_week)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date
        end_day=end_time
        inx_week='default'
    invoice_view_data=InvoicePost.query.filter(InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_request_invoice=='request_approval').order_by(InvoicePost.invoice_from.asc())
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    ##Finding Unique User
    unique_user=[]
    for in_view in invoice_view_data:
        unique_user.append(in_view.user_id)
    view_unique=np.unique(unique_user)
    len_user=len(view_unique)
    #########################
    ############UNIQUE USER IDENTIFIER###############
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        invoice_ind=InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_request_invoice=='request_approval').order_by(InvoicePost.invoice_from.asc())
        count_invoice_in=0
        for check_invoice in invoice_ind:
            count_invoice_in=count_invoice_in+1
        if count_invoice_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##################################################
    return render_template('/admin/invoice_view_all_reject.html',unique_usersheet=unique_usersheet,len_usersheet=len_usersheet,
                                                                    inx_week=inx_week,end_time=end_day,post_data=invoice_view_data,
                                                                    user_view=user_view,view_unique=view_unique,len_user=len_user,
                                                                    unique_user=unique_user)

@adminDash.route("/<username>/<sheet_inx>/invoice_view_standardF_rejectbutton")
@login_required
def invoice_view_standardF_rejectbutton(sheet_inx,username):
    if session.get('is_author')!=True:
        abort(403)
    user = User.query.filter_by(username=username).first_or_404()
    inx_week_reject=sheet_inx
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if inx_week_reject=='this_month':
        start_time=today_date- datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif inx_week_reject=='last_week':
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    elif inx_week_reject=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        #end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        inx_week='this_week'
    else:
        start_time=today_date- datetime.timedelta(49+idx_week)
        end_time=today_date
        end_day=end_time
        inx_week='default'
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                        .filter(InvoicePost.user_request_invoice=='request_approval')\
                                        .order_by(InvoicePost.invoice_from.asc())
    return render_template('/admin/view_invoice_standard_reject.html', post_data=invoice_post, user=user,user_all=user_all,
                                                                        inx_week=inx_week,end_time=end_day)
################################################################################
###Setting for Public Holiday###
@adminDash.route('/public_holiday',methods=['GET','POST'])
@login_required
def public_holiday():
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        sch_day_strF=request.form.get('pub_day')
        hday_type=request.form.get('holiday_type')
        user_all_get=[]
        user_view=User.query.filter(User.user_status=='active').order_by(User.username)
        for in_user in user_view:
            user_all_get.append(in_user.username)
        if sch_day_strF=='':
            flash('Please Select Format Correctly','danger')
            return redirect(url_for('adminDash.public_holiday'))
        sch_day_strF=sch_day_strF.split(",") #Converting to list
        for date_init in range(len(sch_day_strF)):
            sch_day_strF_init=sch_day_strF[date_init]
            sch_day_strF_init=sch_day_strF_init.lstrip()
            sch_day = datetime.datetime.strptime(sch_day_strF_init,'%d/%m/%Y')
            count_hol=0
            holiday_post_init=Public_Holiday.query.filter(Public_Holiday.day_clock==sch_day)
            for post_init in holiday_post_init:
                count_hol=count_hol+1
            if count_hol==0:
                holiday_post=Public_Holiday(day_clock=sch_day,holiday_type=hday_type)
                db.session.add(holiday_post)
                db.session.commit()
                for user_init in user_all_get:
                    user = User.query.filter_by(username=user_init).first_or_404()
                    if sch_day.strftime("%A")!='Saturday' and sch_day.strftime("%A")!='Sunday':
                        clock_post_default = TimeSheetPost(day_clock=sch_day,project=hday_type,
                                                            comment='',clock_in=datetime.date.today(),
                                                            task=hday_type,travel_choice='',
                                                            clock_out=datetime.date.today(),distance='',
                                                            OverTime_15=int(0),NormalTime=int(8),
                                                            OverTime_2=int(0),location='',OverTime_25=int(0),
                                                            Launch_Break=int(0),timesheet_status=False,
                                                            timesheet_flag='',user_request_timesheet='request_approval',
                                                            admin_request_timesheet='',user_status_timesheet='Approved',
                                                            meal_type='default',meal_rate_day=float(0),meal_allowance='no',
                                                            user_check_timesheet='',job_num='-',
                                                            remainder='',accept_flag='',
                                                            reject_flag='',user_id=user.id)
                        db.session.add(clock_post_default)
                        db.session.commit()
            else:
                flash('Duplicate Public Holiday','danger')
                return redirect(url_for('adminDash.public_holiday'))
        return redirect(url_for('adminDash.dash_admin'))
    return render_template('admin/public_holiday.html')

@adminDash.route('/view_publicHoliday')
@login_required
def view_publicHoliday():
    if session.get('is_author')!=True:
        abort(403)
    post_data=Public_Holiday.query.order_by(Public_Holiday.day_clock.asc())
    return render_template('admin/view_publicHoliday.html',holiday_all=post_data)

@adminDash.route('/<int:post_id>/delte_holiday')
@login_required
def delte_holiday(post_id):
    if session.get('is_author')!=True:
        abort(403)
    #######TimeSheetPost Remove#####
    post_data=Public_Holiday.query.get_or_404(post_id)
    timesheetpost_init=TimeSheetPost.query.filter(TimeSheetPost.day_clock==post_data.day_clock,TimeSheetPost.project==post_data.holiday_type)
    for post_init in timesheetpost_init:
        db.session.delete(post_init)
        db.session.commit()
    db.session.delete(post_data)
    db.session.commit()
    return redirect(url_for('adminDash.view_publicHoliday'))

@adminDash.route("/<int:post_id>/modify_holiday")
@login_required
def modify_holiday(post_id):
    post_data=Public_Holiday.query.get_or_404(post_id)
    return render_template('/admin/modify_holiday.html',post_data=post_data)

@adminDash.route("/<int:post_id>/modify_holiday_selection",methods=['GET','POST'])
@login_required
def modify_holiday_selection(post_id):
    if session.get('is_author')!=True:
        abort(403)
    post_data=Public_Holiday.query.get_or_404(post_id)
    if request.method=='POST':
        type_hold=request.form.get('holiday_type')
        hol_day_str=request.form.get('hol_day')
        if type_hold=='' or hol_day_str=='':
            flash('Cannot be blank','danger')
            return redirect(url_for('adminDash.modify_holiday',post_id=post_id))
        hol_day_f = datetime.datetime.strptime(hol_day_str,'%d/%m/%Y')
        ###########Timesheets Delete and Modify According to It#######
        timesheetpost_init=TimeSheetPost.query.filter(TimeSheetPost.day_clock==post_data.day_clock,TimeSheetPost.project==post_data.holiday_type,\
                                                        TimeSheetPost.task==post_data.holiday_type)
        for post_init in timesheetpost_init:
            db.session.delete(post_init)
            db.session.commit()
        ###########################
        count_hol=0
        holiday_post_init=Public_Holiday.query.filter(Public_Holiday.day_clock==hol_day_f)
        for post_initm in holiday_post_init:
            count_hol=count_hol+1
        if count_hol>=1:
            flash('Duplicate Public Holiday Modification','danger')
            return redirect(url_for('adminDash.modify_holiday',post_id=post_id))
        user_all_get=[]
        user_view=User.query.filter(User.user_status=='active').order_by(User.username)
        for in_user in user_view:
            user_all_get.append(in_user.username)
        for user_init in user_all_get:
            user = User.query.filter_by(username=user_init).first_or_404()
            if hol_day_f.strftime("%A")!='Saturday' and hol_day_f.strftime("%A")!='Sunday':
                clock_post_default = TimeSheetPost(day_clock=hol_day_f,project=type_hold,
                                                    comment='',clock_in=datetime.date.today(),
                                                    task=type_hold,travel_choice='',
                                                    clock_out=datetime.date.today(),distance='',
                                                    OverTime_15=int(0),NormalTime=int(8),
                                                    OverTime_2=int(0),location='',OverTime_25=int(0),
                                                    Launch_Break=int(0),timesheet_status=False,
                                                    timesheet_flag='',user_request_timesheet='request_approval',
                                                    admin_request_timesheet='',user_status_timesheet='Approved',
                                                    meal_type='default',meal_rate_day=float(0),meal_allowance='no',
                                                    user_check_timesheet='',job_num='-',
                                                    remainder='',accept_flag='',
                                                    reject_flag='',user_id=user.id)
                db.session.add(clock_post_default)
                db.session.commit()
        #############################################################
        post_data.day_clock=hol_day_f
        post_data.holiday_type=type_hold
        db.session.commit()
        return redirect(url_for('adminDash.view_publicHoliday'))
    return redirect(url_for('adminDash.view_publicHoliday'))
########TASK SCHEDULE##############
@adminDash.route('/task_schedule')
@login_required
def task_schedule():
    if session.get('is_author')!=True:
        abort(403)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    return render_template('admin/task_schedule.html',project_all=project_all,user_all=user_all)

@adminDash.route('/task_schedule_selection',methods=['POST'])
@login_required
def task_schedule_selection():
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        ##Reading Arguments from Users
        sch_project=request.form.get('sch_project')
        sch_users=request.form.getlist('sch_users')
        sch_day_strF=request.form.get('sch_day')
        sch_from_strF=request.form.get('sch_from')
        sch_to_strF=request.form.get('sch_to')
        sch_comment=request.form.get('sch_comment')
        if (sch_users=='') or (sch_day_strF=='') or(sch_from_strF=='') or(sch_to_strF=='') or (sch_project=='Choose...'):
            flash('Please Select Format Correctly','danger')
            return redirect(url_for('adminDash.task_schedule'))
        sch_day_strF=sch_day_strF.split(",") #Converting to list
        for user_init in range(len(sch_users)):
            for date_init in range(len(sch_day_strF)):
                sch_day_strF_init=sch_day_strF[date_init]
                sch_day_strF_init=sch_day_strF_init.lstrip() ##Removing space in loop
                sch_from_strF_init2= sch_day_strF_init + sch_from_strF
                sch_to_strF_init2= sch_day_strF_init + sch_to_strF
                sch_from = datetime.datetime.strptime(sch_from_strF_init2,'%d/%m/%Y%H:%M')
                sch_to = datetime.datetime.strptime(sch_to_strF_init2,'%d/%m/%Y%H:%M')
                sch_day = datetime.datetime.strptime(sch_day_strF_init,'%d/%m/%Y')
                user_to=sch_users[user_init]
                user = User.query.filter_by(username=user_to).first_or_404()
                task_assign=Task_Schedule(author=current_user,recipient=user,
                                          sch_day=sch_day,sch_from=sch_from,
                                          sch_to=sch_to,sch_project=sch_project,
                                          sch_comment=sch_comment)
                db.session.add(task_assign)
                db.session.commit()
        flash('Thank you for submission','success')
        return redirect(url_for('adminDash.task_schedule'))
    return render_template('admin/task_schedule.html')

########Event Schedule#######################################
########TASK SCHEDULE##############
@adminDash.route('/event_schedule')
@login_required
def event_schedule():
    if session.get('is_author')!=True:
        abort(403)
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    return render_template('admin/event_schedule.html',user_all=user_all)

@adminDash.route('/event_schedule_selection',methods=['POST'])
@login_required
def event_schedule_selection():
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        ##Reading Arguments from Users
        sch_project=request.form.get('event_project')
        sch_users=request.form.getlist('event_users')
        sch_day_strF=request.form.get('event_day')
        sch_from_strF=request.form.get('event_from')
        sch_to_strF=request.form.get('event_to')
        sch_comment=request.form.get('event_comment')
        if (sch_users=='') or (sch_day_strF=='') or(sch_from_strF=='') or(sch_to_strF==''):
            flash('Please Select Format Correctly','danger')
            return redirect(url_for('adminDash.event_schedule'))
        sch_day_strF=sch_day_strF.split(",") #Converting to list
        for user_init in range(len(sch_users)):
            for date_init in range(len(sch_day_strF)):
                sch_day_strF_init=sch_day_strF[date_init]
                sch_day_strF_init=sch_day_strF_init.lstrip() ##Removing space in loop
                sch_from_strF_init2= sch_day_strF_init + sch_from_strF
                sch_to_strF_init2= sch_day_strF_init + sch_to_strF
                sch_from = datetime.datetime.strptime(sch_from_strF_init2,'%d/%m/%Y%H:%M')
                sch_to = datetime.datetime.strptime(sch_to_strF_init2,'%d/%m/%Y%H:%M')
                sch_day = datetime.datetime.strptime(sch_day_strF_init,'%d/%m/%Y')
                user_to=sch_users[user_init]
                user = User.query.filter_by(username=user_to).first_or_404()
                task_assign=Task_Schedule(author=current_user,recipient=user,
                                          sch_day=sch_day,sch_from=sch_from,
                                          sch_to=sch_to,sch_project=sch_project,
                                          sch_comment=sch_comment)
                db.session.add(task_assign)
                db.session.commit()
        flash('Thank you for submission','success')
        return redirect(url_for('adminDash.admin_task_view'))
    return render_template('admin/event_schedule.html')
################View Task Schedule Calendar View#############
@adminDash.route("/admin_task_view")
@login_required
def admin_task_view():
    if session.get('is_author')!=True:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    start_time=today_date
    end_time=start_time+datetime.timedelta(1)
    ##Finding Unique User
    schedule_post=Task_Schedule.query.filter(Task_Schedule.sch_day.between(start_time,end_time))
    user_view=User.query.filter(User.user_status=='active').order_by(User.username)
    unique_usersheet=[]
    user_all_get=[]
    for in_user in user_view:
        user_all_get.append(in_user.username)
    user_count_all=0
    for u_all in user_all_get:
        user = User.query.filter_by(username=u_all).first_or_404()
        user_count_all=user_count_all+1
        schedule_post_ind = Task_Schedule.query.filter(Task_Schedule.recipient==user,Task_Schedule.sch_day.between(start_time,end_time))
        count_task_in=0
        for check_task in schedule_post_ind:
            count_task_in=count_task_in+1
        if count_task_in >0:
            unique_usersheet.append(user)
    len_usersheet=len(unique_usersheet)
    ##########################################################
    ###############Task SCHEDULE################
    overall_sch={}
    week_taskall={}
    end_day=start_time+datetime.timedelta(6)
    delta = datetime.timedelta(days=1)
    for sch_all in user_all_get:
        user = User.query.filter_by(username=sch_all).first_or_404()
        d_in=start_time
        week_taskall[user.username]={'user_name':user.username}
        overall_sch[user.username]={'user_name':user.username}
        schedule_post = Task_Schedule.query.filter(Task_Schedule.recipient==user,Task_Schedule.sch_day \
                                            .between(start_time,end_day)).order_by(Task_Schedule.sch_day.asc())
        day_inc=0
        day_week=[]
        week_task={}
        while d_in <= end_day:
            day_inc=day_inc+1
            inx_day=d_in.strftime('%A')
            count_din=0
            for sch_task in schedule_post:
                d_check=sch_task.sch_day
                if d_check.date()==d_in:
                    nw_task=sch_task.sch_project
                    nw_comment=sch_task.sch_comment
                    nw_start=sch_task.sch_from.strftime('%H:%M')
                    nw_end=sch_task.sch_to.strftime('%H:%M')
                    nw_id=int(sch_task.id)
            if count_din==0:
                    append_empty=''
                    nw_task=append_empty
                    nw_comment=append_empty
                    nw_start=append_empty
                    nw_end=append_empty
                    nw_id=int(0)
            day_week.append(d_in)
            week_task[d_in]={'day_week':d_in,'tk_project':nw_task,'tk_comment':nw_comment,
                                     'tk_start':nw_start,'tk_end':nw_end,'tk_id':nw_id}
            d_in = d_in + delta
        week_taskall[user.username].update(week_task)
    color_all=[]
    color_choice=['red','blue','green','pink','orange','brown','purple']
    for random_count in range(2*user_count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template("/admin/task_schedule_view.html",week_taskall=week_taskall,color_all=color_all,overall_sch=overall_sch,
                                                            week_task=week_task,day_week=day_week,schedule_post=schedule_post,
                                                            start_time=start_time,unique_usersheet=unique_usersheet,
                                                            len_usersheet=len_usersheet)

@adminDash.route("/admin_task_selection",methods=['GET','POST'])
@login_required
def admin_task_selection():
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        task_date_str=request.form.get('task_date')
        task_date=datetime.datetime.strptime(task_date_str,'%d/%m/%Y')
        #task_date = datetime.datetime.strptime(task_date_str,'%Y-%m-%d')
        start_time=datetime.time()
        start_time=task_date
        end_time=start_time
        ##Finding Unique User
        schedule_post=Task_Schedule.query.filter(Task_Schedule.sch_day.between(start_time,end_time))
        user_view=User.query.filter(User.user_status=='active').order_by(User.username)
        unique_usersheet=[]
        user_all_get=[]
        for in_user in user_view:
            user_all_get.append(in_user.username)
        user_count_all=0
        for u_all in user_all_get:
            user = User.query.filter_by(username=u_all).first_or_404()
            user_count_all=user_count_all+1
            schedule_post_ind = Task_Schedule.query.filter(Task_Schedule.recipient==user,Task_Schedule.sch_day.between(start_time,end_time))
            count_task_in=0
            for check_task in schedule_post_ind:
                count_task_in=count_task_in+1
            if count_task_in >0:
                unique_usersheet.append(user)
        len_usersheet=len(unique_usersheet)
        color_all=[]
        color_choice=['red','blue','green','pink','orange','brown','purple']
        for random_count in range(2*user_count_all):
            color_r=random.choice(color_choice)
            color_all.append(color_r)
        return render_template("/admin/task_schedule_view.html",schedule_post=schedule_post,color_all=color_all,start_time=start_time,
                                                                unique_usersheet=unique_usersheet,len_usersheet=len_usersheet)
    return redirect(url_for('adminDash.admin_task_view'))
################Task Weekly View#########################
@adminDash.route("/weekly_view_task")
@login_required
def weekly_view_task():
    if session.get('is_author')!=True:
        abort(403)
    #Default Initialization
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    start_time=today_date - datetime.timedelta(idx_week)
    end_time=today_date + datetime.timedelta(idx_week)
    user_all_get=[]
    overall_timesheet={}
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    for in_user in user_all:
        user_all_get.append(in_user.username)
    week_taskall={}
    end_day=start_time+datetime.timedelta(6)
    delta = datetime.timedelta(days=1)
    count_color=0
    for sch_all in user_all_get:
        user = User.query.filter_by(username=sch_all).first_or_404()
        d_in=start_time
        week_taskall[user.username]={'user_name':user.username}
        schedule_post = Task_Schedule.query.filter(Task_Schedule.recipient==user,Task_Schedule.sch_day.between(start_time,end_day))\
                                            .order_by(Task_Schedule.sch_day.asc())
        day_inc=0
        day_week=[]
        week_task={}
        while d_in <= end_day:
            day_inc=day_inc+1

            inx_day=d_in.strftime('%A')
            count_din=0
            for sch_task in schedule_post:
                d_check=sch_task.sch_day
                if d_check.date()==d_in:
                    count_din=count_din+1
                    count_color=count_color+1
                    nw_task=sch_task.sch_project
                    nw_comment=sch_task.sch_comment
                    nw_start=sch_task.sch_from.strftime('%H:%M')
                    nw_end=sch_task.sch_to.strftime('%H:%M')
                    nw_id=int(sch_task.id)
            if count_din==0:
                    append_empty=''
                    nw_task=append_empty
                    nw_comment=append_empty
                    nw_start=append_empty
                    nw_end=append_empty
                    nw_id=int(0)
            day_week.append(d_in)
            week_task[d_in]={'day_week':d_in,'tk_project':nw_task,'tk_comment':nw_comment,
                                     'tk_start':nw_start,'tk_end':nw_end,'tk_id':nw_id}
            d_in = d_in + delta
        week_taskall[user.username].update(week_task)
    color_all=[]
    color_choice=['red','blue','green','pink','orange','brown','purple']
    for random_count in range(count_color):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template("/admin/viewtask_weekly.html",day_week=day_week,color_all=color_all,start_time=start_time,
                                                            end_time=end_day,week_taskall=week_taskall)
##########Delete Task#########################
@adminDash.route("/<int:post_task_id>/<username>/ind_task_delete")
@login_required
def ind_task_delete(username,post_task_id):
    if session.get('is_author')!=True:
        abort(403)
    schedule_post= Task_Schedule.query.get_or_404(post_task_id)
    user = User.query.filter_by(username=username).first_or_404()
    db.session.delete(schedule_post)
    db.session.commit()
    return redirect(url_for('adminDash.admin_task_view'))
###########Task Modification#########################
@adminDash.route("/<int:post_task_id>/<username>/ind_task_modify")
@login_required
def ind_task_modify(username,post_task_id):
    if session.get('is_author')!=True:
        abort(403)
    schedule_post= Task_Schedule.query.get_or_404(post_task_id)
    user = User.query.filter_by(username=username).first_or_404()
    start_time=schedule_post.sch_day
    end_day=start_time+datetime.timedelta(1)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    #schedule_post = Task_Schedule.query.filter(Task_Schedule.recipient==user,Task_Schedule.sch_day.between(start_time,end_day)).order_by(Task_Schedule.sch_day.asc())
    return render_template('/admin/modify_ind_task.html',post_data=schedule_post,project_all=project_all,username=user.username)

@adminDash.route("/<int:post_task_id>/<username>/ind_task_modify_selection",methods=['POST'])
@login_required
def ind_task_modify_selection(username,post_task_id):
    if session.get('is_author')!=True:
        abort(403)
    schedule_post= Task_Schedule.query.get_or_404(post_task_id)
    user = User.query.filter_by(username=username).first_or_404()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    if request.method=='POST':
        task_fromD_str=request.form.get('task_fromD')
        task_fromT_str=request.form.get('task_fromT')
        task_toT_str=request.form.get('task_toT')
        project=request.form.get('task_project')
        comment=request.form.get('sch_comment')
        if task_fromD_str=='':
            flash('Please Select Format Correctly','danger')
            return render_template('/admin/modify_ind_task.html',post_data=schedule_post,project_all=project_all,username=user.username)
        task_strF_from= task_fromD_str + task_fromT_str
        task_strF_to= task_fromD_str + task_toT_str
        day_task = datetime.datetime.strptime(task_fromD_str,'%d/%m/%Y')
        task_inT = datetime.datetime.strptime(task_strF_from,'%d/%m/%Y%H:%M')
        task_outT = datetime.datetime.strptime(task_strF_to,'%d/%m/%Y%H:%M')
        #######################Modify Task Schedule####################
        if project=='':
            schedule_post.sch_project=schedule_post.sch_project
        else:
            schedule_post.sch_project=project
        schedule_post.recipient_id=schedule_post.recipient_id
        schedule_post.sch_day=day_task
        schedule_post.sch_from=task_inT
        schedule_post.sch_to=task_outT
        schedule_post.sch_comment=comment
        db.session.commit()
        ######Email Service##################################
        if project=='':
            project_email=schedule_post.sch_project
        else:
            project_email=project
        body_subject='Job Modification {}'.format(day_task.strftime('%d/%m/%Y'))
        body_html=render_template('mail/user/modify_task.html',user=user,project=project_email,
                                                                time_in=task_inT,time_out=task_outT,
                                                                comment=comment,day=day_task)
        body_text=render_template('mail/user/modify_task.txt',user=user,project=project_email,
                                                              time_in=task_inT,time_out=task_outT,
                                                              comment=comment,day=day_task)
        email(user.email,body_subject,body_html,body_text)
        #######Email Service#################################
        return redirect(url_for('adminDash.admin_task_view'))
    return redirect(url_for('adminDash.admin_task_view'))
##############################################################
################Task Increment or Decrement Weekly View#########
@adminDash.route("/weekly_view_task_inc",methods=['POST','GET'])
@login_required
def weekly_view_task_inc():
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        task_date_str=request.form.get('task_date')
        task_date = datetime.datetime.strptime(task_date_str,'%d/%m/%Y')
        check_email=request.form.get('check_email')
        #task_date = datetime.datetime.strptime(task_date_str,'%Y-%m-%d')
        idx_week=(task_date.weekday()+1)%7
        start_time=datetime.time()
        end_time=datetime.time()
        start_time=task_date - datetime.timedelta(idx_week)
        #end_time=task_date + datetime.timedelta(idx_week)
        end_day=start_time+datetime.timedelta(6)
        end_time=start_time+datetime.timedelta(7)
        user_all_get=[]
        project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
        user_all=User.query.filter(User.user_status=='active').order_by(User.username)
        for in_user in user_all:
            user_all_get.append(in_user.username)
        week_taskall={}
        delta = datetime.timedelta(days=1)
        count_color=0
        for sch_all in user_all_get:
            week_taskall_email={}
            user = User.query.filter_by(username=sch_all).first_or_404()
            d_in=start_time
            week_taskall[user.username]={'user_name':user.username}
            week_taskall_email[user.username]={'user_name':user.username}
            schedule_post = Task_Schedule.query.filter(Task_Schedule.recipient==user,Task_Schedule.sch_day.between(start_time,end_time))\
                                                .order_by(Task_Schedule.sch_day.asc())
            ####count_for_email#####
            count_email=0
            for sch_post_in in schedule_post:
                count_email=count_email+1
            ######################
            day_inc=0
            day_week=[]
            week_task={}
            while d_in <= end_day:
                day_inc=day_inc+1
                inx_day=d_in.strftime('%A')
                count_din=0
                for sch_task in schedule_post:
                    d_check=sch_task.sch_day
                    #if d_check.date()==d_in:
                    if d_check==d_in:
                        count_din=count_din+1
                        count_color=count_color+1
                        nw_task=sch_task.sch_project
                        nw_comment=sch_task.sch_comment
                        nw_start=sch_task.sch_from.strftime('%H:%M')
                        nw_end=sch_task.sch_to.strftime('%H:%M')
                        nw_id=int(sch_task.id)
                if count_din==0:
                        append_empty=''
                        nw_task=append_empty
                        nw_comment=append_empty
                        nw_start=append_empty
                        nw_end=append_empty
                        nw_id=int(0)
                day_week.append(d_in)
                week_task[d_in]={'day_week':d_in.strftime('%d/%m/%Y'),'day_week_nw':d_in.strftime('%A'),'tk_project':nw_task,'tk_comment':nw_comment,
                                         'tk_start':nw_start,'tk_end':nw_end,'tk_id':nw_id}
                d_in = d_in + delta
            week_taskall[user.username].update(week_task)
            week_taskall_email[user.username].update(week_task)
            ################Email Service###################
            color_all_email=[]
            color_choice_email=['red','blue','green','pink','orange','brown','purple']
            for random_count in range(count_color):
                color_r_email=random.choice(color_choice_email)
                color_all_email.append(color_r_email)
            if check_email=='checked' and count_email >=1:
                body_subject='Weekly Task Schedule: {} - {}'.format(start_time.strftime('%d/%m/%Y'),end_time.strftime('%d/%m/%Y'))
                body_html=render_template('mail/user/weekly_task.html',user=user,week_taskall=week_taskall_email,
                                                                        day_week=day_week,color_all=color_all_email)
                body_text=render_template('mail/user/weekly_task.txt',user=user,week_taskall=week_taskall_email,
                                                                        day_week=day_week,color_all=color_all_email)
                email(user.email,body_subject,body_html,body_text)
            ###############Email Service####################
        color_all=[]
        color_choice=['red','blue','green','pink','orange','brown','purple']
        for random_count in range(count_color):
            color_r=random.choice(color_choice)
            color_all.append(color_r)
        return render_template("/admin/viewtask_weekly.html",day_week=day_week,color_all=color_all,week_taskall=week_taskall)
    return redirect(url_for('adminDash.weekly_view_task'))
    #return render_template("/admin/viewtask_weekly.html",day_week=day_week,color_all=color_all,week_taskall=week_taskall)
#########################################################
#####Admin Modification##################################
@adminDash.route("/<username>/modify_userall_view")
@login_required
def modify_userall_view(username):
    if session.get('is_author')!=True:
        abort(403)
    user=User.query.filter_by(username=username).first_or_404()
    return render_template('/admin/modify_user_all.html',post_data=user)

@adminDash.route("/<username>/modify_userall",methods=['GET','POST'])
@login_required
def modify_userall(username):
    if session.get('is_author')!=True:
        abort(403)
    user=User.query.filter_by(username=username).first_or_404()
    if request.method=='POST':
        firstname_user=request.form.get('firstname_user')
        #username_user=request.form.get('username_user')
        lastname_user=request.form.get('lastname_user')
        position_user=request.form.get('position_user')
        dob_user_str=request.form.get('dob_user')
        dob_user = datetime.datetime.strptime(dob_user_str,'%d/%m/%Y')
        user.firstname=firstname_user
        #user.username=username_user
        user.lastname=lastname_user
        user.position=position_user
        user.birthday=dob_user
        db.session.commit()
        return redirect(url_for('adminDash.view_alluser'))
    return redirect(url_for('adminDash.view_alluser'))
#############################################################
############Reminder###############
@adminDash.route('/birthday_remainder', methods=['GET', 'POST'])
@login_required
def birthday_remainder():
    if session.get('is_author')!=True:
        abort(403)
    form = BirthDayForm()
    if form.validate_on_submit():
        birth_init_all=BirthDay_Add.query.all()
        for birth_init in birth_init_all:
            if birth_init is not None:
                birth_init.daybirth=form.daybirthrem.data
                db.session.commit()
                flash('Birthday reminder days has been successfully created!','success')
                return redirect(url_for('adminDash.dash_admin'))
        birthrem_user = BirthDay_Add(daybirth=form.daybirthrem.data)
        db.session.add(birthrem_user)
        db.session.commit()
        flash('Birthday reminder days has been successfully created!','success')
        return redirect(url_for('adminDash.dash_admin'))
    return render_template('admin/add_birthday.html', form=form)
################################################################
#########################LEAVE REMAINDER DAYS#############################
@adminDash.route('/leave_remainder', methods=['GET', 'POST'])
@login_required
def leave_remainder():
    if session.get('is_author')!=True:
        abort(403)
    form = LeaveRemForm()
    if form.validate_on_submit():
        leave_init_all=LeaveRem_Add.query.all()
        for leave_init in leave_init_all:
            if leave_init is not None:
                leave_init.leaveDash=form.dayleaverem.data
                db.session.commit()
                flash('Leave request reminder days has been successfully created!','success')
                return redirect(url_for('adminDash.dash_admin'))
        leaverem_user = LeaveRem_Add(leaveDash=form.dayleaverem.data)
        db.session.add(leaverem_user)
        db.session.commit()
        flash('Leave request reminder days has been successfully created!','success')
        return redirect(url_for('adminDash.dash_admin'))
    return render_template('admin/leave_notification.html', form=form)

#########Allowance All Types#################
@adminDash.route('/create_allowance', methods=['GET', 'POST'])
@login_required
def create_allowance():
    if session.get('is_author')!=True:
        abort(403)
    form = AllowanceForm()
    unit_allowance=['hour','day','week']
    if form.validate_on_submit():
        allowance_init=Allowance_Add.query.filter_by(allowance_add=form.allowance_add.data).first()
        if allowance_init is not None:
            flash('Allowance has already been added! Add new Allowance Category!','danger')
            return redirect(url_for('adminDash.create_allowance'))
        allowance_unit_init = request.form.get('allowance_unit')
        allowance_user = Allowance_Add(allowance_add=form.allowance_add.data,
                                       allocate_rate=form.allocate_rate.data,
                                       allocate_unit=allowance_unit_init)
        db.session.add(allowance_user)
        db.session.commit()
        flash('Allowance has been successfully created!','success')
        return redirect(url_for('adminDash.view_allowance'))
    return render_template('admin/create_allowance.html', form=form,unit_allowance=unit_allowance)

@adminDash.route('/view_allowance')
@login_required
def view_allowance():
    if session.get('is_author')!=True:
        abort(403)
    post_data=Allowance_Add.query.all()
    return render_template('admin/view_allowance.html',post_data=post_data)

@adminDash.route('/<int:post_allowance_id>/delete_allowance')
@login_required
def delete_allowance(post_allowance_id):
    if session.get('is_author')!=True:
        abort(403)
    allowance_post= Allowance_Add.query.get_or_404(post_allowance_id)
    db.session.delete(allowance_post)
    db.session.commit()
    return redirect(url_for('adminDash.view_allowance'))

@adminDash.route('/<int:post_allowance_id>/modify_allowance')
@login_required
def modify_allowance(post_allowance_id):
    if session.get('is_author')!=True:
        abort(403)
    unit_allowance=['hour','day','week']
    allowance_posts= Allowance_Add.query.get_or_404(post_allowance_id)
    return render_template('admin/modify_allowance.html',allowance_posts=allowance_posts,unit_allowance=unit_allowance)

@adminDash.route('/<int:post_allowance_id>/modify_allowance_selection', methods=['GET', 'POST'])
@login_required
def modify_allowance_selection(post_allowance_id):
    if session.get('is_author')!=True:
        abort(403)
    if request.method=='POST':
        allowance_add=request.form.get('allowance_add')
        allocate_rate=request.form.get('allocate_rate')
        allowance_unit_init = request.form.get('allowance_unit')
        if allocate_rate=='':
            allocate_rate=float(0)
        allowance_posts= Allowance_Add.query.get_or_404(post_allowance_id)
        allowance_posts.allowance_add=allowance_add
        allowance_posts.allocate_rate=allocate_rate
        allowance_posts.allocate_unit=allowance_unit_init
        db.session.commit()
        flash('Allowance has been modifed!','success')
        return redirect(url_for('adminDash.view_allowance'))
    return render_template('admin/modify_allowance.html')
###############################################################################
#####Error Report Enquiry#########
@adminDash.route('/enquiry_post_admin',methods=['GET','POST'])
@login_required
def enquiry_post_admin():
    if session.get('is_author')!=True:
        abort(403)
    user_all=User.query.filter(and_(User.is_author==True,User.user_status=='active'))
    if request.method=='POST':
        request_type=request.form.get('request_type')
        summary=request.form.get('summary')
        details=request.form.get('details')
        receipt_user=request.form.getlist('receipt_user')
        if receipt_user==[]:
            flash('Please select email address','danger')
            return redirect(url_for('adminDash.enquiry_post_admin'))
        if request_type=='Choose...':
            flash('Please select request type','danger')
            return redirect(url_for('adminDash.enquiry_post_admin'))
        if 'inputFile' not in request.files:
            flash('Please upload the image','danger')
            return redirect(url_for('adminDash.enquiry_post_admin'))
        try:
            image=request.files['inputFile']
            filename=None
        except:
            image=None
            filename=None
        if image and allowed_file(image.filename):
            filename=uploaded_images.save(image)
        else:
            filename=None
        ##########Save in Database###########
        code=str(uuid.uuid4())
        enquiry_post=EnquiryPost(image=filename,request_type=request_type,
                                 summary=summary,details=details,
                                 receipt_email=code,user_id=current_user.id)
        db.session.add(enquiry_post)
        db.session.commit()
        #######Email Services###############
        enquiry_post_user=EnquiryPost.query.filter_by(receipt_email=code).first()
        for user_init in range(len(receipt_user)):
            user_to=receipt_user[user_init]
            user=User.query.filter_by(email=user_to).first_or_404()
            body_subject='{}:{}'.format(request_type,summary)
            body_html=render_template('mail/user/enquiry.html',user=user,message=summary,post_id=enquiry_post_user.id)
            body_text=render_template('mail/user/enquiry.txt',user=user,message=summary,post_id=enquiry_post_user.id)
            email(user.email,body_subject,body_html,body_text)
        flash('You have successfully send the error report','success')
        return redirect(url_for('adminDash.view_enquiry'))
    return render_template('/admin/enquiry_post_admin.html',user_all=user_all)

@adminDash.route('/<int:post_id>/download_enquiry')
@login_required
def download_enquiry(post_id):
    if session.get('is_author')!=True:
        abort(403)
    file_data=EnquiryPost.query.get_or_404(post_id)
    try:
        return send_file((file_data.imgsrc),mimetype='application/octet-stream',attachment_filename=file_data.image,as_attachment=True)
    except:
        flash('No attachment or file not supported format','danger')
        return redirect(url_for('adminDash.dash_admin'))

@adminDash.route('/view_enquiry')
@login_required
def view_enquiry():
    if session.get('is_author')!=True:
        abort(403)
    post_data=EnquiryPost.query.all()
    return render_template('/admin/view_enquiry.html',post_data=post_data)

@adminDash.route('/<int:post_id>/delete_enquiry')
@login_required
def delete_enquiry(post_id):
    if session.get('is_author')!=True:
        abort(403)
    post_data=EnquiryPost.query.get_or_404(post_id)
    db.session.delete(post_data)
    db.session.commit()
    flash('Enquiry has been deleted','danger')
    return redirect(url_for('adminDash.view_enquiry'))

#######Project Permissions#################
@adminDash.route('/project_permission',methods=['GET','POST'])
@login_required
def project_permission():
    if session.get('is_author')!=True:
        abort(403)
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    permission_default=['access','deny']
    if request.method=='POST':
        permission_user=request.form.get('permission_form')
        project_users=request.form.getlist('project_users')
        if project_users==[]:
            flash('Please select users to grant permission','danger')
            return redirect(url_for('adminDash.project_permission'))
        for user_init in range(len(project_users)):
            user_to=project_users[user_init]
            user=User.query.filter_by(username=user_to).first_or_404()
            if permission_user=='access':
                user.permission_project=True
            else:
                user.permission_project=False
            db.session.commit()
        return redirect(url_for('adminDash.view_alluser'))
    return render_template('admin/project_permission.html',user_all=user_all,permission=permission_default)
