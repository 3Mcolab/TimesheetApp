import datetime
import os
import time
import random
from flask import render_template,url_for,flash, redirect,request,\
                    Blueprint,abort,session,send_file,current_app
from flask_login import current_user,login_required
from io import BytesIO
from werkzeug.utils import secure_filename
#from TimesheetApp import db,uploaded_images
from TimesheetApp import db
from TimesheetApp.models import User,TimeSheetPost,LeavePost,InvoicePost,\
                                        Project_Add,Task_Add,Invoice_Add,Task_Schedule,Message,Public_Holiday,\
                                        Allowance_Add,BarcodePost,Remainder_Barcode,Remainder_Itemcondition,\
                                        EnquiryPost
from TimesheetApp.employees.forms import Project_UserForm
from extensions import uploaded_images
from sqlalchemy import and_
###Mail Services#########
import uuid
from TimesheetApp.utilities.common import email

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

employees = Blueprint('employees',__name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#####DASHBOARD##############
@employees.route('/dashboard')
@login_required
def dashboard():
    today_date=datetime.date.today()
    if current_user.birthday==None:
        message_card=''
    else:
        if(today_date.strftime('%m')==current_user.birthday.strftime('%m')) and (today_date.strftime('%d')==current_user.birthday.strftime('%d')):
            message_card='Happy Birthday !'
        else:
            message_card=''
    ##########Qrcode Notification to Users#########
    post_rem=Remainder_Barcode.query.order_by(Remainder_Barcode.date.asc())
    for post_in in post_rem:
        post_qrcode=BarcodePost.query.get(post_in.remainder_id)
        if post_qrcode !=None:
            requested_user=User.query.filter_by(username=post_in.remainder_user).first()
            if post_in.remainder_status=='approve' and requested_user==current_user and today_date >=post_in.remainder_date.date():
                user_message_ap='Hi {}! Have you received the {} with serial number {}.Report the condition'.format(current_user.firstname,
                                                                                                                    post_qrcode.item_add,
                                                                                                                    post_qrcode.item_serial_num)
                user_status_ap='unread'
                user_flag_ap=''
                user_title_ap='Report the condition of {}'.format(post_qrcode.item_serial_num)
                msg = Message(author=current_user, recipient=current_user,
                                body_message=user_message_ap,
                                body_title=user_title_ap,
                                body_flag=user_flag_ap,
                                body_trans='inventory_request_ack',
                                body_date=post_in.remainder_date,
                                body_id=post_qrcode.id,
                                body_sheet='default',
                                body_status=user_status_ap)
                db.session.add(msg)
                db.session.commit()
                ######send email to user for verification###########
                rem_post_email=Remainder_Barcode.query.filter(and_(Remainder_Barcode.remainder_id==post_qrcode.id,\
                                                                                Remainder_Barcode.remainder_date==post_in.remainder_date)).first()
                message_email='Have you received the {} with serial number {}.Report the condition'.format(post_qrcode.item_add,\
                                                                                                            post_qrcode.item_serial_num)
                body_html=render_template('mail/user/inventory_report_reminder.html',user=current_user,message_email=message_email,
                                                                                        post_rem_id=rem_post_email.id,post_id=post_qrcode.id)
                body_text=render_template('mail/user/inventory_report_reminder.txt',user=current_user,message_email=message_email,
                                                                                    post_rem_id=rem_post_email.id,post_id=post_qrcode.id)
                body_title='Report the condition of {}'.format(post_qrcode.item_serial_num)
                email(current_user.email,body_title,body_html,body_text)
                ######send email to user for verification###########
    #########DASHBOARD NOTIFICATION################
    page = request.args.get('page', 1, type=int)
    message_post=current_user.messages_received.order_by(Message.date.desc()).paginate(page=page, per_page=15)
    ################################################
    return render_template('users/dash.html',message_card=message_card,message_post=message_post)
########TIMESHEETS OF EMPLOYEES##############
@employees.route('/clockinout')
@login_required
def clockinout():
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    task_all=Task_Add.query.all()
    return render_template('users/clockinout.html',task_all=task_all,project_all=project_all)

@employees.route('/clockinout_selection',methods=['GET','POST'])
@login_required
def clockinout_selection():
    if request.method=='POST':
        OverTime_15=0
        OverTime_25=0
        OverTime_2=0
        NormalTime=0
        Launch_Break=0
        hour_day=0
        ##Reading Arguments from Users
        day_clock_str=request.form.get('clockinout_fromD')
        clock_in_str=request.form.get('clockinout_fromT')
        clock_out_str=request.form.get('clockinout_toT')
        project=request.form.get('clockinout_project')
        task=request.form.get('clockinout_site')
        travel_choice=request.form.get('clockinout_travelch')
        meal_choice=request.form.get('meal_allowance')
        distance=request.form.get('clockinout_distance')
        location=request.form.get('clockinout_location')
        comment=request.form.get('clockinout_comment')

        user_id=current_user.id
        if (day_clock_str=='') or (project=='Choose...') or (task=='Choose...'):
            flash('Please Select Format Correctly','danger')
            return redirect(url_for('employees.clockinout'))
        ##Conversion from String to Format
        clock_in_strF= day_clock_str + clock_in_str
        clock_out_strF= day_clock_str + clock_out_str
        day_clock = datetime.datetime.strptime(day_clock_str,'%d/%m/%Y')
        clock_in = datetime.datetime.strptime(clock_in_strF,'%d/%m/%Y%H:%M')
        clock_out = datetime.datetime.strptime(clock_out_strF,'%d/%m/%Y%H:%M')
        ############Check same repetition and interval#################
        ###Hour Calculation of Employees
        time_dev=(clock_out-clock_in)/60
        hour_check,min_check= divmod(time_dev.seconds, 3600)
        hour_day=round((hour_check+float(min_check/60)),1)
        #######Check if Clockout time is not supported#############
        if(hour_day>24):
            flash('Please select properly Check Out Time','danger')
            return redirect(url_for('employees.clockinout'))
        #Default Initialization
        time_query=TimeSheetPost.query.filter(TimeSheetPost.day_clock==day_clock)\
                                            .filter(TimeSheetPost.user_id==current_user.id)
        hour_day_repeat=0
        Launch_Break_repeat=0
        NormalTime_repeat=0
        OverTime_15_repeat=0
        OverTime_25_repeat=0
        for time_init_query in time_query:
            if (clock_in>time_init_query.clock_in and clock_out<time_init_query.clock_out):
                flash('Checkin and Checkout time is overlapping','danger')
                return redirect(url_for('employees.clockinout'))
            if (clock_out>time_init_query.clock_in and clock_in<time_init_query.clock_out):
                flash('Checkin and Checkout time is overlapping','danger')
                return redirect(url_for('employees.clockinout'))
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
        #######MEAL ALLOWANCE####################################
        project_posts= Project_Add.query.filter(Project_Add.project_add==project)
        for allowance_init in project_posts:
            id_project=allowance_init.id
        project_query=Project_Add.query.get_or_404(id_project)
        if project_query.allowance_id=='default' and meal_choice=='no':
            meal_rate_day=float(0)
        elif project_query.allowance_id=='default' and meal_choice=='yes':
            meal_rate_day=float(0)
        elif project_query.allowance_id!='default' and meal_choice=='yes':
            allowance_list=project_query.allowance_id
            aw_all=allowance_list.split('-')
            meal_rate_day=0
            for aws_loop in aw_all:
                allowance_posts= Allowance_Add.query.filter(Allowance_Add.allowance_add==aws_loop)
                for aw_init in allowance_posts:
                    id_aws_ind=aw_init.id
                allowance_ind=Allowance_Add.query.get_or_404(id_aws_ind)
                if allowance_ind.allocate_unit=='hour':
                    meal_rate_day=round(meal_rate_day+(allowance_ind.allocate_rate*hour_day_main),1)
                elif allowance_ind.allocate_unit=='week':
                    meal_rate_day=round(meal_rate_day+(allowance_ind.allocate_rate/5),1)
                else:
                    meal_rate_day=round(meal_rate_day+allowance_ind.allocate_rate,1)
        else:
            meal_rate_day=float(0)
        meal_type=project_query.allowance_id
        #############################################################################
        count_hol=0
        holiday_post_init=Public_Holiday.query.filter(Public_Holiday.day_clock==day_clock)
        for post_initm in holiday_post_init:
            count_hol=count_hol+1
            id_post_holiday=post_initm.id
        if count_hol>=1:
            post_data_hol=Public_Holiday.query.get_or_404(id_post_holiday)
            timesheetpost_init=TimeSheetPost.query.filter(TimeSheetPost.day_clock==post_data_hol.day_clock,\
                                                            TimeSheetPost.project==post_data_hol.holiday_type,\
                                                            TimeSheetPost.task==post_data_hol.holiday_type)
            for post_init in timesheetpost_init:
                db.session.delete(post_init)
                db.session.commit()
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
            project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
            for project_init in project_all:
                if project_init.project_add==project:
                    job_add_clock=project_init.job_add
            clock_post = TimeSheetPost(day_clock=day_clock,project=project,
                                        comment=comment,clock_in=clock_in,
                                        task=task,travel_choice=travel_choice,
                                        clock_out=clock_out,distance=distance,
                                        OverTime_15=OverTime_15,NormalTime=NormalTime,
                                        OverTime_2=OverTime_2,location=location,
                                        Launch_Break=Launch_Break,timesheet_status=False,
                                        timesheet_flag='',user_request_timesheet='',
                                        admin_request_timesheet='',user_status_timesheet='Posted',
                                        user_check_timesheet='',job_num=job_add_clock,
                                        remainder='',accept_flag='',OverTime_25=OverTime_25,
                                        meal_type=meal_type,meal_rate_day=meal_rate_day,meal_allowance=meal_choice,
                                        reject_flag='',user_id=user_id)
            db.session.add(clock_post)
            db.session.commit()
            flash('Thank you for submission','success')
            return redirect(url_for('employees.timesheet_userlogin',username=current_user.username,sheet_inx='default_week'))
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
                Launch_Break=0
                OverTime_25=0
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
                OverTime_25=0
                OverTime_15=0
                OverTime_2=0
                NormalTime=round(hour_day_main-Launch_Break,1)
            elif hour_day>6 and hour_day<=8.5:
                if Launch_Break_repeat==0:
                    Launch_Break=0.5
                else:
                    Launch_Break=0
                OverTime_15=0
                OverTime_25=0
                OverTime_2=0
                NormalTime=round((hour_day_main-Launch_Break),1)
            elif hour_day >8.5 and hour_day <=10:
                if Launch_Break_repeat==0:
                    Launch_Break=0.5
                else:
                    Launch_Break=0
                if NormalTime_repeat!=0:
                    NormalTime=round(abs(8-NormalTime_repeat),1)
                else:
                    NormalTime=8
                OverTime_15=round(abs(round(hour_day_main,1)-Launch_Break-NormalTime),1)
                OverTime_2=0
                OverTime_25=0
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
        ###############################################
        project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
        for project_init in project_all:
            if project_init.project_add==project:
                job_add_clock=project_init.job_add
        ###############################################
        clock_post = TimeSheetPost(day_clock=day_clock,project=project,
                                    comment=comment,clock_in=clock_in,
                                    task=task,travel_choice=travel_choice,
                                    clock_out=clock_out,distance=distance,
                                    OverTime_15=OverTime_15,NormalTime=NormalTime,
                                    OverTime_2=OverTime_2,location=location,
                                    Launch_Break=Launch_Break,timesheet_status=False,
                                    timesheet_flag='',user_request_timesheet='',
                                    admin_request_timesheet='',user_status_timesheet='Posted',
                                    user_check_timesheet='',job_num=job_add_clock,
                                    remainder='',accept_flag='',OverTime_25=OverTime_25,
                                    meal_type=meal_type,meal_rate_day=meal_rate_day,meal_allowance=meal_choice,
                                    reject_flag='',user_id=user_id)
        db.session.add(clock_post)
        db.session.commit()
        flash('Thank you for submission','success')
        return redirect(url_for('employees.timesheet_userlogin',username=current_user.username,sheet_inx='default_week'))
    return render_template('users/clockinout.html')
########LEAVE OF EMPLOYEES##############
@employees.route('/leave')
@login_required
def leave():
    return render_template('users/leave.html')

@employees.route('/leave_selection',methods=['GET','POST'])
@login_required
def leave_selection():
    if request.method=='POST':
        ##Reading Arguments from Users
        leave_from_str=request.form.get('leave_from')
        leave_to_str=request.form.get('leave_to')
        leave_type=request.form.get('leave_type')
        leave_note=request.form.get('leave_note')
        user_id=current_user.id
        if (leave_from_str=='') or (leave_to_str=='') or (leave_type=='Choose...'):
            flash('Please Select Format Correctly','danger')
            return redirect(url_for('employees.leave'))
        ##########Handling Files#####################
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
        ##############Handling File################
        leave_from = datetime.datetime.strptime(leave_from_str,'%d/%m/%Y')
        leave_to = datetime.datetime.strptime(leave_to_str,'%d/%m/%Y')
        leave_days_total = (leave_to -leave_from) + datetime.timedelta(1)
        leave_days=leave_days_total.days
        if leave_days<0:
            flash('End Day of leave cannot be ahead than Start Day of leave','danger')
            return redirect(url_for('employees.leave'))
        leave_post = LeavePost(leave_from=leave_from,leave_to=leave_to,
                                leave_type=leave_type,leave_note=leave_note,
                                leave_days=leave_days,image=filename,
                                leave_status=False,leave_flag='',
                                user_request_leave='request_approval',
                                user_status_leave='Submited',
                                accept_flag='',reject_flag='',
                                user_check_leave='',admin_request_leave='',
                                user_id=user_id
                                )
        db.session.add(leave_post)
        db.session.commit()
        flash('Thank you for submission','success')
        return redirect(url_for('employees.leave_userlogin',username=current_user.username,sheet_inx='default_week'))
    return render_template('users/leave.html')

########LEAVE OF EMPLOYEES##############
@employees.route('/invoice')
@login_required
def invoice():
    invoice_all=Invoice_Add.query.all()
    return render_template('users/invoice.html',invoice_all=invoice_all)

@employees.route('/invoice_selection',methods=['GET','POST'])
@login_required
def invoice_selection():
    if request.method=='POST':
        ##Reading Arguments from Users
        invoice_date_str=request.form.get('invoice_date')
        invoice_supplier=request.form.get('invoice_supplier')
        invoice_Total=request.form.get('invoice_Total')
        invoice_category=request.form.get('invoice_category')
        invoice_description=request.form.get('invoice_description')
        user_id=current_user.id
        ####Handling File#############
        if 'inputFile' not in request.files:
            flash('Please Select Format Correctly','danger')
            return redirect(url_for('employees.invoice'))
        #size_file=request.files['inputFile'].read()
        #if size_file>=BytesIO(4*1024*1024):
        #    flash('File size too large. Only support upto 3MB')
        #    return redirect(url_for('employees.invoice'))
        ######################################
        if (invoice_date_str=='') or (invoice_category=='Choose...'):
            flash('Please Select Format Correctly','danger')
            return redirect(url_for('employees.invoice'))
        ####Handling Files#####
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
        ##############Handling File################
        invoice_from = datetime.datetime.strptime(invoice_date_str,'%d/%m/%Y')
        invoice_post = InvoicePost(invoice_from=invoice_from,invoice_supplier=invoice_supplier,
                                invoice_Total=invoice_Total,invoice_category=invoice_category,
                                invoice_description=invoice_description,image=filename,
                                invoice_status=False,invoice_flag='',
                                user_request_invoice='request_approval',admin_request_invoice='',
                                user_status_invoice='Submited',user_check_invoice='',
                                accept_flag='',reject_flag='',
                                admin_reject_flag='checked',admin_approve_flag='checked',
                                user_id=user_id
                                )
        db.session.add(invoice_post)
        db.session.commit()
        flash('Thank you for submission','success')
        return redirect(url_for('employees.invoice_userlogin',username=current_user.username,sheet_inx='default_week'))
    return render_template('users/invoice.html')
##########USER TIMESHEET VIEW############
########DEFAULT POST#####################
@employees.route("/<sheet_inx>/timesheet_userlogin/<username>")
@login_required
def timesheet_userlogin(sheet_inx,username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    #Default Initialization
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time + datetime.timedelta(7)
        end_day=start_time + datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date - datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    else:
        start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock\
                                    .between(start_time,end_time)).order_by(TimeSheetPost.day_clock.asc())
    sum_HT=0
    sum_NT=0
    sum_LB=0
    sum_DT=0
    sum_DTH=0
    for data_c in clock_post:
        sum_DTH=sum_DTH+data_c.OverTime_25
        sum_HT=sum_HT+data_c.OverTime_15
        sum_NT=sum_NT+data_c.NormalTime
        sum_LB=sum_LB+data_c.Launch_Break
        sum_DT=sum_DT+data_c.OverTime_2
    return render_template('/users/user_timesheet_standard.html', post_data=clock_post,inx_week=inx_week,sum_DTH=sum_DTH,
                                                                    sum_HT=sum_HT,sum_NT=sum_NT,sum_LB=sum_LB,
                                                                    sum_DT=sum_DT,end_time=end_day)

############POST BY SELECTION#################
@employees.route("/timesheet_userdash/<username>",methods=['GET','POST'])
@login_required
def timesheet_userdash(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='This Month':
            inx_week='this_month'
        elif view_chart=='This Week':
            inx_week='this_week'
        else:
            inx_week='last_week'
    if request.method=='GET':
        inx_week='last_week'
    return redirect(url_for('employees.timesheet_userlogin',username=user.username,sheet_inx=inx_week))


@employees.route("/timesheet_userdash_old/<username>",methods=['GET','POST'])
@login_required
def timesheet_userdash_old(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        #print(view_chart)
        if view_chart=='This Month':
            start_time=today_date - datetime.timedelta(21+idx_week)
            end_time=today_date - datetime.timedelta(idx_week+7)
            end_day=today_date - datetime.timedelta(idx_week+8)
            inx_week='this_month'
        elif view_chart=='This Week':
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=today_date + datetime.timedelta(idx_week)
            end_time=start_time + datetime.timedelta(7)
            end_day=start_time + datetime.timedelta(6)
            inx_week='this_week'
        else:
            start_time=today_date - datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
            inx_week='last_week'
        clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time))\
                                            .order_by(TimeSheetPost.day_clock.asc())
        sum_HT=0
        sum_NT=0
        sum_LB=0
        sum_DT=0
        sum_DTH=0
        for data_c in clock_post:
            sum_DTH=sum_DTH+data_c.OverTime_25
            sum_HT=sum_HT+data_c.OverTime_15
            sum_NT=sum_NT+data_c.NormalTime
            sum_LB=sum_LB+data_c.Launch_Break
            sum_DT=sum_DT+data_c.OverTime_2
            #print(sum_HT,sum_NT,sum_LB,sum_DT)
        return render_template('/users/user_timesheet_standard.html', post_data=clock_post,inx_week=inx_week,sum_DTH=sum_DTH,
                                                                        sum_HT=sum_HT,sum_NT=sum_NT,sum_LB=sum_LB,
                                                                        sum_DT=sum_DT,end_time=end_day)
    return render_template('/users/user_timesheet_standard.html', post_data=clock_post,inx_week=inx_week,sum_DTH=sum_DTH,
                                                                    sum_HT=sum_HT,sum_NT=sum_NT,sum_LB=sum_LB,
                                                                    sum_DT=sum_DT,end_time=end_day)
##########USER LEAVE VIEW############
########DEFAULT POST#####################
@employees.route("/<sheet_inx>/leave_userlogin/<username>")
@login_required
def leave_userlogin(sheet_inx,username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
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
    leave_post = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time))\
                                    .order_by(LeavePost.leave_from.asc())
    return render_template('/users/user_leave_standard.html', inx_week=inx_week,post_data=leave_post,end_time=end_time)

############POST BY SELECTION#################
@employees.route("/leave_userdash/<username>",methods=['GET','POST'])
@login_required
def leave_userdash(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    today_date=datetime.date.today()
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='Last Year':
            inx_week='last_year'
        elif view_chart=='Last Week':
            inx_week='last_week'
        elif view_chart=='This Month':
            inx_week='this_month'
        else:
            inx_week='this_week'
    if request.method=='GET':
        inx_week='last_week'
    return redirect(url_for('employees.leave_userlogin',username=user.username,sheet_inx=inx_week))

@employees.route("/leave_userdash_old/<username>",methods=['GET','POST'])
@login_required
def leave_userdash_old(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
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
        leave_post = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time))\
                                        .order_by(LeavePost.leave_from.asc())
        return render_template('/users/user_leave_standard.html', inx_week=inx_week,post_data=leave_post,end_time=end_time)
    return render_template('/users/user_leave_standard.html', inx_week=inx_week,post_data=leave_post,end_time=end_time)

##########USER INVOICE VIEW############
########DEFAULT POST#####################
@employees.route("/<sheet_inx>/invoice_userlogin/<username>")
@login_required
def invoice_userlogin(sheet_inx,username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    #Default Initialization
    start_time=datetime.time()
    end_time=datetime.time()
    if sheet_inx=='this_week':
        start_time=today_date - datetime.timedelta(idx_week)
        #end_time=today_date + datetime.timedelta(idx_week)
        end_time=start_time + datetime.timedelta(7)
        end_day=start_time + datetime.timedelta(6)
        inx_week='this_week'
    elif sheet_inx=='this_month':
        start_time=today_date - datetime.timedelta(21+idx_week)
        end_time=today_date - datetime.timedelta(idx_week+7)
        end_day=today_date - datetime.timedelta(idx_week+8)
        inx_week='this_month'
    elif sheet_inx=='last_week':
        start_time=today_date - datetime.timedelta(7+idx_week)
        end_time=today_date - datetime.timedelta(idx_week)
        end_day=today_date - datetime.timedelta(idx_week+1)
        inx_week='last_week'
    else:
        start_time=today_date - datetime.timedelta(49+idx_week)
        end_time=today_date + datetime.timedelta(idx_week)
        end_day=end_time
        inx_week='default_week'
    invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                        .order_by(InvoicePost.invoice_from.asc())
    return render_template('/users/user_invoice_standard.html', inx_week=inx_week,post_data=invoice_post,end_time=end_day)

############POST BY SELECTION#################
@employees.route("/invoice_userdash/<username>",methods=['GET','POST'])
@login_required
def invoice_userdash(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    if request.method=='POST':
        view_chart=request.form.get('view_chart')
        if view_chart=='This Month':
            inx_week='this_month'
        elif view_chart=='This Week':
            inx_week='this_week'
        else:
            inx_week='last_week'
    if request.method=='GET':
        inx_week='last_week'
    return redirect(url_for('employees.invoice_userlogin',username=user.username,sheet_inx=inx_week))

@employees.route("/invoice_userdash_old/<username>",methods=['GET','POST'])
@login_required
def invoice_userdash_old(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
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
        elif view_chart=='This Week':
            start_time=today_date - datetime.timedelta(idx_week)
            #end_time=today_date + datetime.timedelta(idx_week)
            end_time=start_time + datetime.timedelta(7)
            end_day=start_time + datetime.timedelta(6)
            inx_week='this_week'
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
            end_day=today_date - datetime.timedelta(idx_week+1)
            inx_week='last_week'
        invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                            .order_by(InvoicePost.invoice_from.asc())
        return render_template('/users/user_invoice_standard.html', inx_week=inx_week,post_data=invoice_post,end_time=end_day)
    return render_template('/users/user_invoice_standard.html', inx_week=inx_week,post_data=invoice_post,end_time=end_day)

##########Modify/Delete#############################
#######USER MODE RECTIFY###############
###########TIMESHEETS##################
#########TIMESHEET REJECT FROM ADMIN###############
@employees.route("/<username>/<sheet_inx>/<int:clock_post_id>/reject_user_clockpostD", methods=['POST'])
@login_required
def reject_user_clockpostD(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    ############CANNOT MODIFY OR DELETE TIMESHEETS#################
    #if clock_posts.user_status_timesheet=='Approved' or clock_posts.user_status_timesheet=='Submited':
    if clock_posts.user_status_timesheet=='Approved':
        flash('You cannot modify or delete timesheet once submitted','danger')
        return redirect(url_for('employees.timesheet_userlogin',username=user.username,sheet_inx=sheet_inx))
    ##############################################################
    db.session.delete(clock_posts)
    db.session.commit()
    flash('TimeSheet has been Deleted','danger')
    return redirect(url_for('employees.timesheet_userlogin',username=user.username,sheet_inx=sheet_inx))
#############Modify############################################
@employees.route("/<username>/<sheet_inx>/<int:clock_post_id>/modify_user_clockpostDashD",methods=['GET','POST'])
@login_required
def modify_user_clockpostDashD(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    #################CANNOT MODIFY OR DELETE ##################
    #if clock_posts.user_status_timesheet=='Approved' or clock_posts.user_status_timesheet=='Submited':
    if clock_posts.user_status_timesheet=='Approved':
        flash('You cannot modify or delete timesheet once submitted','danger')
        return redirect(url_for('employees.timesheet_userlogin',username=user.username,sheet_inx=sheet_inx))
    ##########################################################
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    task_all=Task_Add.query.all()
    return render_template('/users/modify_user_clockpostD1.html',post_data=clock_posts,sheet_inx=sheet_inx,
                                                                    project_all=project_all,task_all=task_all)
#####################TIMESHEET MODIFY FROM ADMIN##############
@employees.route("/<username>/<sheet_inx>/<int:clock_post_id>/modify_user_clockpostD", methods=['GET','POST'])
@login_required
def modify_user_clockpostD(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    clock_posts_init = TimeSheetPost.query.get_or_404(clock_post_id)
    ############CANNOT MODIFY OR DELETE##################
    #if clock_posts_init.user_status_timesheet=='Approved' or clock_posts_init.user_status_timesheet=='Submited':
    if clock_posts_init.user_status_timesheet=='Approved':
        flash('You cannot modify or delete timesheet once submitted','danger')
        return redirect(url_for('employees.timesheet_userlogin',username=user.username,sheet_inx=sheet_inx))
    #####################################################
    if request.method=='POST':
        #Default Values
        OverTime_15=0
        OverTime_25=0
        OverTime_2=0
        NormalTime=0
        Launch_Break=0
        hour_day=0
        day_clock_str=request.form.get('clockinout_fromD')
        clock_in_str=request.form.get('clockinout_fromT')
        clock_out_str=request.form.get('clockinout_toT')
        project=request.form.get('clockinout_project')
        task=request.form.get('clockinout_site')
        if day_clock_str=='':
            flash('Please Select Format Correctly','danger')
            return redirect(url_for('employees.modify_user_clockpost_errorD',sheet_inx=sheet_inx,clock_post_id=clock_post_id,username=username))
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
            return redirect(url_for('employees.modify_user_clockpost_errorD',clock_post_id=clock_post_id,sheet_inx=sheet_inx,username=username))
        #Default Initialization
        #######Modification#####Inorder to Modify Existing One########
        clock_posts_init.day_clock=day_clock+datetime.timedelta(365)
        db.session.commit()
        ############################################################
        #Default Initialization
        time_query=TimeSheetPost.query.filter(TimeSheetPost.day_clock==day_clock).filter(TimeSheetPost.user_id==current_user.id)
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
                return redirect(url_for('employees.modify_user_clockpost_errorD',clock_post_id=clock_post_id,sheet_inx=sheet_inx,username=username))
            if (clock_out>time_init_query.clock_in and clock_in<time_init_query.clock_out):
                flash('Checkin and Checkout time is overlapping','danger')
                clock_posts_init = TimeSheetPost.query.get_or_404(clock_post_id)
                clock_posts_init.day_clock=day_clock
                db.session.commit()
                return redirect(url_for('employees.modify_user_clockpost_errorD',clock_post_id=clock_post_id,sheet_inx=sheet_inx,username=username))
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
            clock_posts.Launch_Break=Launch_Break
            db.session.commit()
            flash('TimeSheet has been Modified','success')
            return redirect(url_for('employees.timesheet_userlogin',username=username,sheet_inx=sheet_inx))
        ###########################################
        if day_clock.strftime("%A")=='Saturday':
            if hour_day <=2:
                NormalTime=0
                Launch_Break=0
                OverTime_15=hour_day_main
                OverTime_2=0
                OverTime_25=0
            elif hour_day>2 and hour_day<=6:
                NormalTime=0
                Launch_Break=0
                OverTime_25=0
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
                Launch_Break=0
                OverTime_15=0
                OverTime_25=0
                OverTime_2=round(hour_day_main-Launch_Break,1)
            else:
                NormalTime=0
                if Launch_Break_repeat==0:
                    Launch_Break=0.5
                else:
                    Launch_Break=0
                OverTime_15=0
                OverTime_25=0
                OverTime_2=round(hour_day_main-Launch_Break,1)
        else:
            if hour_day<=6:
                Launch_Break=0
                OverTime_15=0
                OverTime_2=0
                OverTime_25=0
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
                OverTime_15=round(abs(round(hour_day_main,1)-Launch_Break-NormalTime),1)
                OverTime_2=0
                OverTime_25=0
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
        clock_posts.OverTime_2=OverTime_2
        clock_posts.Launch_Break=Launch_Break
        db.session.commit()
        flash('TimeSheet has been Modified','success')
        return redirect(url_for('employees.timesheet_userlogin',username=username,sheet_inx=sheet_inx))
    return render_template('/users/modify_user_clockpostD1.html',post_data=clock_posts,username=username,sheet_inx=sheet_inx)
#######USER MODE RECTIFY TIMESHEETS###############
@employees.route("/<username>/<sheet_inx>/<int:clock_post_id>/modify_user_clockpost_errorD",methods=['GET','POST'])
@login_required
def modify_user_clockpost_errorD(username,sheet_inx,clock_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    clock_posts = TimeSheetPost.query.get_or_404(clock_post_id)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    task_all=Task_Add.query.all()
    ##################CANNOT MODIFY OR DELETE #######################
    #if clock_posts.user_status_timesheet=='Approved' or clock_posts.user_status_timesheet=='Submited':
    if clock_posts.user_status_timesheet=='Approved':
        flash('You cannot modify or delete timesheet once submitted','danger')
        return redirect(url_for('employees.timesheet_userlogin',username=user.username,sheet_inx=sheet_inx))
    ################################################################
    return render_template('/users/modify_user_clockpostD1.html',post_data=clock_posts,project_all=project_all,task_all=task_all,sheet_inx=sheet_inx)

###########LEAVE DOWNLOAD#############
@employees.route("/<username>/<sheet_inx>/<int:leave_post_id>/leave_downloadD",methods=['POST'])
@login_required
def leave_downloadD(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    file_data_leave=LeavePost.query.get_or_404(leave_post_id)
    try:
        return send_file((file_data_leave.imgsrc),mimetype='application/octet-stream',attachment_filename=file_data_leave.image,as_attachment=True)
    except:
        flash('No attachment or file not supported format','danger')
        return redirect(url_for('employees.leave_userlogin',username=username,sheet_inx=sheet_inx))
#########LEAVE REJECT FROM ADMIN###############
@employees.route("/<username>/<sheet_inx>/<int:leave_post_id>/reject_user_leavepostD", methods=['POST'])
@login_required
def reject_user_leavepostD(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    #################CANNOT MODIFY OR DELETE ##################
    if leave_posts.user_status_leave=='Approved':
        flash('You cannot modify or delete leave request once approved','danger')
        return redirect(url_for('employees.leave_userlogin',username=user.username,sheet_inx=sheet_inx))
    ##########################################################
    db.session.delete(leave_posts)
    db.session.commit()
    flash('Leave request has been Deleted','danger')
    return redirect(url_for('employees.leave_userlogin',username=username,sheet_inx=sheet_inx))

#######USER MODE RECTIFY###############
###########LEAVE##################
@employees.route("/<username>/<sheet_inx>/<int:leave_post_id>/modify_user_leavepostDashD",methods=['GET','POST'])
@login_required
def modify_user_leavepostDashD(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    #################CANNOT MODIFY OR DELETE ##################
    if leave_posts.user_status_leave=='Approved':
        flash('You cannot modify or delete leave request once approved','danger')
        return redirect(url_for('employees.leave_userlogin',username=user.username,sheet_inx=sheet_inx))
    return render_template('/users/modify_user_leavepostD1.html',post_data=leave_posts,username=username,sheet_inx=sheet_inx)
#####################LEAVE MODIFY FROM ADMIN##############
@employees.route("/<username>/<sheet_inx>/<int:leave_post_id>/modify_user_leavepostD", methods=['GET','POST'])
@login_required
def modify_user_leavepostD(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    #################CANNOT MODIFY OR DELETE ##################
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    if leave_posts.user_status_leave=='Approved':
        flash('You cannot modify or delete leave request once approved','danger')
        return redirect(url_for('employees.leave_userlogin',username=user.username,sheet_inx=sheet_inx))
    ##########################################################
    if request.method=='POST':
        #Default Values
        leave_from_str=request.form.get('leave_from')
        leave_to_str=request.form.get('leave_to')
        leave_type=request.form.get('leave_type')
        if (leave_from_str=='') or (leave_to_str=='') or (leave_type=='Choose...'):
            flash('Please Select Format Correctly','danger')
            return redirect(url_for('employees.modify_user_leavepost_errorD',leave_post_id=leave_post_id,username=username,sheet_inx=sheet_inx))
        leave_from = datetime.datetime.strptime(leave_from_str,'%d/%m/%Y')
        leave_to = datetime.datetime.strptime(leave_to_str,'%d/%m/%Y')
        leave_days_total = (leave_to -leave_from) + datetime.timedelta(1)
        leave_days=leave_days_total.days
        if leave_days<0:
            flash('End Day of leave cannot be ahead than Start Day of leave','danger')
            return redirect(url_for('employees.modify_user_leavepost_errorD',leave_post_id=leave_post_id,username=username,sheet_inx=sheet_inx))
        leave_posts = LeavePost.query.get_or_404(leave_post_id)
        if leave_posts.user_status_leave=='Rejected':
            leave_posts.user_request_leave='request_approval'
            leave_posts.user_status_leave='Submited'
        leave_posts.leave_from=leave_from
        leave_posts.leave_to=leave_to
        leave_posts.leave_days=leave_days
        leave_posts.leave_type=leave_type
        db.session.commit()
        flash('Leave request has been Modified','success')
        return redirect(url_for('employees.leave_userlogin',username=username,sheet_inx=sheet_inx))
    return render_template('/users/modify_user_leavepostD1.html',post_data=leave_posts,username=username,sheet_inx=sheet_inx)
#######USER MODE RECTIFY LEAVE###############
@employees.route("/<username>/<sheet_inx>/<int:leave_post_id>/modify_user_leavepost_errorD",methods=['GET','POST'])
@login_required
def modify_user_leavepost_errorD(username,sheet_inx,leave_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    #################CANNOT MODIFY OR DELETE ##################
    leave_posts = LeavePost.query.get_or_404(leave_post_id)
    if leave_posts.user_status_leave=='Approved':
        flash('You cannot modify or delete leave request once approved','danger')
        return redirect(url_for('employees.leave_userlogin',username=user.username,sheet_inx=sheet_inx))
    ##########################################################
    return render_template('/users/modify_user_leavepostD1.html',post_data=leave_posts,username=username,sheet_inx=sheet_inx)

###########INVOICE DOWNLOAD#############
@employees.route("/<username>/<sheet_inx>/<int:invoice_post_id>/invoice_downloadD",methods=['POST'])
@login_required
def invoice_downloadD(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    file_data_invoice=InvoicePost.query.get_or_404(invoice_post_id)
    try:
        return send_file((file_data_invoice.imgsrc),mimetype='application/octet-stream',attachment_filename=file_data_invoice.image,as_attachment=True)
    except:
        flash('No attachment or file not supported format','danger')
        return redirect(url_for('employees.invoice_userlogin',username=username,sheet_inx=sheet_inx))
#######USER MODE RECTIFY###############
###########INVOICE##################
@employees.route("/<username>/<sheet_inx>/<int:invoice_post_id>/modify_user_invoicepostDashD",methods=['GET','POST'])
@login_required
def modify_user_invoicepostDashD(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    #################CANNOT MODIFY OR DELETE ##################
    if invoice_posts.user_status_invoice=='Approved':
        flash('You cannot modify or delete invoice request once approved','danger')
        return redirect(url_for('employees.invoice_userlogin',username=user.username,sheet_inx=sheet_inx))
    ##########################################################
    invoice_all=Invoice_Add.query.all()
    return render_template('/users/modify_user_invoicepostD1.html',post_data=invoice_posts,invoice_all=invoice_all,
                                                                    username=username,sheet_inx=sheet_inx)
#####################LEAVE MODIFY FROM ADMIN##############
@employees.route("/<username>/<sheet_inx>/<int:invoice_post_id>/modify_user_invoicepostD", methods=['GET','POST'])
@login_required
def modify_user_invoicepostD(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    #################CANNOT MODIFY OR DELETE ##################
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    if invoice_posts.user_status_invoice=='Approved':
        flash('You cannot modify or delete invoice request once approved','danger')
        return redirect(url_for('employees.invoice_userlogin',username=user.username,sheet_inx=sheet_inx))
    ##########################################################
    if request.method=='POST':
        #Default Values
        invoice_date_str=request.form.get('invoice_date')
        invoice_supplier=request.form.get('invoice_supplier')
        invoice_Total=request.form.get('invoice_Total')
        invoice_category=request.form.get('invoice_category')
        if (invoice_date_str=='') or (invoice_category=='Choose...'):
            flash('Please Select Format Correctly','danger')
            invoice_all=Invoice_Add.query.all()
            return redirect(url_for('employees.modify_user_invoicepost_errorD',invoice_post_id=invoice_post_id,invoice_all=invoice_all,
                                                                                username=username,sheet_inx=sheet_inx))
        invoice_from = datetime.datetime.strptime(invoice_date_str,'%d/%m/%Y')
        invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
        if invoice_posts.user_status_invoice=='Rejected':
            invoice_posts.user_request_invoice='request_approval'
            invoice_posts.user_status_invoice='Submited'
        invoice_posts.invoice_from=invoice_from
        invoice_posts.invoice_supplier=invoice_supplier
        invoice_posts.invoice_Total=invoice_Total
        invoice_posts.invoice_category=invoice_category
        db.session.commit()
        flash('Reimbursement request has been Modified','success')
        return redirect(url_for('employees.invoice_userlogin',username=username,sheet_inx=sheet_inx))
    return render_template('/users/modify_user_invoicepostD1.html',post_data=invoice_posts,username=username,sheet_inx=sheet_inx)
#######USER MODE RECTIFY LEAVE###############
@employees.route("/<username>/<sheet_inx>/<int:invoice_post_id>/modify_user_invoicepost_errorD",methods=['GET','POST'])
@login_required
def modify_user_invoicepost_errorD(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    #################CANNOT MODIFY OR DELETE ##################
    if invoice_posts.user_status_invoice=='Approved':
        flash('You cannot modify or delete invoice request once approved','danger')
        return redirect(url_for('employees.invoice_userlogin',username=user.username,sheet_inx=sheet_inx))
    ##########################################################
    invoice_all=Invoice_Add.query.all()
    return render_template('/users/modify_user_invoicepostD1.html',post_data=invoice_posts,invoice_all=invoice_all,
                                                                    username=username,sheet_inx=sheet_inx)

#########REIMBURSEMENT REJECT FROM USER###############
@employees.route("/<username>/<sheet_inx>/<int:invoice_post_id>/reject_user_invoicepostD", methods=['POST'])
@login_required
def reject_user_invoicepostD(username,sheet_inx,invoice_post_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    invoice_posts = InvoicePost.query.get_or_404(invoice_post_id)
    #################CANNOT MODIFY OR DELETE ##################
    if invoice_posts.user_status_invoice=='Approved':
        flash('You cannot modify or delete invoice request once approved','danger')
        return redirect(url_for('employees.invoice_userlogin',username=user.username,sheet_inx=sheet_inx))
    ##########################################################
    db.session.delete(invoice_posts)
    db.session.commit()
    flash('Reimbursement request has been Deleted','danger')
    return redirect(url_for('employees.invoice_userlogin',username=username,sheet_inx=sheet_inx))
################USER SEND REQUEST FOR APPROVAL#################################
@employees.route("/<username>/<sheet_inx>/timesheet_user_request", methods=['POST'])
@login_required
def timesheet_user_request(username,sheet_inx):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
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
            end_time=start_time + datetime.timedelta(7)
            #end_time=today_date + datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
        clock_post = TimeSheetPost.query.filter(TimeSheetPost.author==user,TimeSheetPost.day_clock.between(start_time,end_time))\
                                            .filter(TimeSheetPost.admin_request_timesheet=='').order_by(TimeSheetPost.day_clock.asc())
        for clock_in in clock_post:
            if clock_in.user_status_timesheet!='Approved':
                clock_in.user_request_timesheet='request_approval'
                clock_in.user_check_timesheet='checked'
                clock_in.user_status_timesheet='Submited'
                db.session.commit()
        flash('TimeSheet has been send for approval process','success')
        return redirect(url_for('employees.timesheet_userlogin',username=username,sheet_inx=sheet_inx))
    return redirect(url_for('employees.timesheet_userlogin',username=username,sheet_inx=sheet_inx))
####################################################################################
################USER SEND REQUEST FOR APPROVAL FOR LEAVE REQUEST#################################
@employees.route("/<username>/<sheet_inx>/leave_user_request", methods=['POST'])
@login_required
def leave_user_request(username,sheet_inx):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
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
        elif sheet_inx=='this_week':
            start_time=today_date - datetime.timedelta(idx_week)
        elif sheet_inx=='this_month':
            start_time=today_date- datetime.timedelta(21+idx_week)
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
        end_time=today_date + datetime.timedelta(365)
        leave_post = LeavePost.query.filter(LeavePost.author==user,LeavePost.leave_from.between(start_time,end_time))\
                                        .filter(LeavePost.admin_request_leave=='').order_by(LeavePost.leave_from.asc())
        for leave_in in leave_post:
            leave_in.user_request_leave='request_approval'
            leave_in.user_status_leave='Submited'
            db.session.commit()
        flash('Leave request has been send for approval process','success')
        return redirect(url_for('employees.leave_userlogin',username=username,sheet_inx=sheet_inx))
    return redirect(url_for('employees.leave_userlogin',username=username,sheet_inx=sheet_inx))
####################################################################################
################USER SEND REQUEST FOR APPROVAL FOR LEAVE REQUEST#################################
@employees.route("/<username>/<sheet_inx>/invoice_user_request", methods=['POST'])
@login_required
def invoice_user_request(username,sheet_inx):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
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
            end_time=today_date + datetime.timedelta(idx_week)
        else:
            start_time=today_date- datetime.timedelta(7+idx_week)
            end_time=today_date - datetime.timedelta(idx_week)
        invoice_post = InvoicePost.query.filter(InvoicePost.author==user,InvoicePost.invoice_from.between(start_time,end_time))\
                                            .filter(InvoicePost.admin_request_invoice=='').order_by(InvoicePost.invoice_from.asc())
        for invoice_in in invoice_post:
            invoice_in.user_request_invoice='request_approval'
            invoice_in.user_status_invoice='Submited'
            db.session.commit()
        flash('Invoice request has been send for approval process','success')
        return redirect(url_for('employees.invoice_userlogin',username=username,sheet_inx=sheet_inx))
    return redirect(url_for('employees.invoice_userlogin',username=username,sheet_inx=sheet_inx))
####################################################################################
######################MESSAGE READ######################
@employees.route("/<username>/<int:mes_post_id>/message_read_user")
@login_required
def message_read_user(username,mes_post_id):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    mesg=Message.query.get(mes_post_id)
    if mesg!=None:
        mesg.body_status='read'
        db.session.commit()
        #######Check condition for redirect#######
        if mesg.body_trans=='timesheet':
            return redirect(url_for('employees.timesheet_userlogin',username=user.username,sheet_inx=mesg.body_sheet))
        elif mesg.body_trans=='leave_request':
            return redirect(url_for('employees.leave_userlogin',username=user.username,sheet_inx=mesg.body_sheet))
        elif mesg.body_trans=='invoice_request':
            return redirect(url_for('employees.invoice_userlogin',username=user.username,sheet_inx=mesg.body_sheet))
        elif mesg.body_trans=='inventory_request':
            barcode_post=BarcodePost.query.get(mesg.body_id)
            if barcode_post!=None:
                rem_post=Remainder_Barcode.query.filter(and_(Remainder_Barcode.remainder_id==barcode_post.id,\
                                                                Remainder_Barcode.remainder_date==mesg.body_date)).first()
                if rem_post.remainder_status=='posting':
                    return redirect(url_for('barcode.qrcode_user_approval',username=user.username,post_rem_id=rem_post.id,post_id=mesg.body_id))
                elif rem_post.remainder_status=='reject':
                    flash('Send another request','danger')
                    return redirect(url_for('barcode.history_qrcode_user',post_id=mesg.body_id))
                elif rem_post.remainder_status=='approve':
                    return redirect(url_for('employees.dashboard'))
                else:
                    return redirect(url_for('employees.dashboard'))
            return redirect(url_for('employees.dashboard'))
        elif mesg.body_trans=='inventory_request_ack':
            barcode_post=BarcodePost.query.get(mesg.body_id)
            if barcode_post!=None:
                rem_post=Remainder_Barcode.query.filter(and_(Remainder_Barcode.remainder_id==barcode_post.id,\
                                                                Remainder_Barcode.remainder_date==mesg.body_date)).first()
                if rem_post.remainder_status=='approve':
                    return redirect(url_for('barcode.indpost_qrcode_ack',username=user.username,post_rem_id=rem_post.id,post_id=mesg.body_id))
                else:
                    return redirect(url_for('employees.dashboard'))
            return redirect(url_for('employees.dashboard'))
        elif mesg.body_trans=='report_item_condition':
            barcode_post=BarcodePost.query.get(mesg.body_id)
            if barcode_post!=None:
                rem_post=Remainder_Itemcondition.query.filter(and_(Remainder_Itemcondition.remainder_id==barcode_post.id,\
                                                                    Remainder_Itemcondition.remainder_date==mesg.body_date)).first()
                return redirect(url_for('barcode.report_condition_approval',username=user.username,post_rem_id=rem_post.id,post_id=mesg.body_id))
            return redirect(url_for('employees.dashboard'))
        else:
            return redirect(url_for('employees.dashboard'))
######################MESSAGE UNREAD######################
@employees.route("/<username>/<int:mes_post_id>/message_unread_user")
@login_required
def message_unread_user(username,mes_post_id):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    mesg=Message.query.get_or_404(mes_post_id)
    mesg.body_status='unread'
    db.session.commit()
    return redirect(url_for('employees.dashboard'))
######################MESSAGE TRASH######################
@employees.route("/<username>/<int:mes_post_id>/message_trash_user")
@login_required
def message_trash_user(username,mes_post_id):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    mesg=Message.query.get_or_404(mes_post_id)
    db.session.delete(mesg)
    db.session.commit()
    return redirect(url_for('employees.dashboard'))
################Task Schedule Calendar View#############
@employees.route("/<username>/task_read_user")
@login_required
def task_read_user(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    count_user=0
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    for post in user_all:
        count_user=count_user+1
    color_all=[]
    color_choice=['red','blue','green','pink','orange','brown','purple']
    for random_count in range(count_user):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    today_date=datetime.date.today()
    idx_week=(today_date.weekday()+1)%7
    start_time=datetime.time()
    start_time=today_date
    end_time=start_time+datetime.timedelta(1)
    schedule_post = Task_Schedule.query.filter(Task_Schedule.recipient==user,Task_Schedule.sch_day.between(start_time,end_time))
    return render_template("/users/task_schedule_user.html",schedule_post=schedule_post,color_all=color_all,start_time=start_time)

@employees.route("/<username>/task_selection",methods=['GET','POST'])
@login_required
def task_selection(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    if request.method=='POST':
        task_date_str=request.form.get('task_date')
        task_date = datetime.datetime.strptime(task_date_str,'%d/%m/%Y')
        #task_date = datetime.datetime.strptime(task_date_str,'%Y-%m-%d')
        start_time=datetime.time()
        start_time=task_date
        end_time=start_time
        count_user=0
        user_all=User.query.filter(User.user_status=='active').order_by(User.username)
        for post in user_all:
            count_user=count_user+1
        color_all=[]
        color_choice=['red','blue','green','pink','orange','brown','purple']
        for random_count in range(count_user):
            color_r=random.choice(color_choice)
            color_all.append(color_r)
        schedule_post = Task_Schedule.query.filter(Task_Schedule.recipient==user,Task_Schedule.sch_day.between(start_time,end_time))
        return render_template("/users/task_schedule_user.html",schedule_post=schedule_post,color_all=color_all,start_time=start_time)
    return redirect(url_for('employees.task_read_user',username=user.username))

################Task Weekly View#########################
@employees.route("/<username>/weekly_view_task_user")
@login_required
def weekly_view_task_user(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
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
    project_all=Project_Add.query.all()
    week_taskall={}
    end_day=start_time+datetime.timedelta(6)
    delta = datetime.timedelta(days=1)
    d_in=start_time
    week_taskall[user.username]={'user_name':user.username}
    schedule_post = Task_Schedule.query.filter(Task_Schedule.recipient==user,Task_Schedule.sch_day.between(start_time,end_day))\
                                            .order_by(Task_Schedule.sch_day.asc())
    day_inc=0
    day_week=[]
    user_count_all=0
    week_task={}
    while d_in <= end_day:
        day_inc=day_inc+1
        inx_day=d_in.strftime('%A')
        count_din=0
        for sch_task in schedule_post:
            d_check=sch_task.sch_day
            if d_check.date()==d_in:
                count_din=count_din+1
                user_count_all=user_count_all+1
                nw_task=sch_task.sch_project
                nw_comment=sch_task.sch_comment
                nw_start=sch_task.sch_from.strftime('%H:%M')
                nw_end=sch_task.sch_to.strftime('%H:%M')
        if count_din==0:
            append_empty=''
            nw_task=append_empty
            nw_comment=append_empty
            nw_start=append_empty
            nw_end=append_empty
        day_week.append(d_in)
        week_task[d_in]={'day_week':d_in,'tk_project':nw_task,'tk_comment':nw_comment,
                                'tk_start':nw_start,'tk_end':nw_end}
        d_in = d_in + delta
    week_taskall[user.username].update(week_task)
    color_all=[]
    color_choice=['red','blue','green','pink','orange','brown','purple']
    for random_count in range(2*user_count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template("/users/viewtask_weekly_user.html",day_week=day_week,color_all=color_all,
                                                                week_taskall=week_taskall,start_time=start_time,
                                                                end_time=end_day,)

################Task Increment or Decrement Weekly View#########################
@employees.route("/<username>/weekly_view_task_incuser",methods=['POST','GET'])
@login_required
def weekly_view_task_incuser(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    #Default Initialization
    if request.method=='POST':
        task_date_str=request.form.get('task_date')
        task_date = datetime.datetime.strptime(task_date_str,'%d/%m/%Y')
        #task_date = datetime.datetime.strptime(task_date_str,'%Y-%m-%d')
        idx_week=(task_date.weekday()+1)%7
        start_time=datetime.time()
        end_time=datetime.time()
        start_time=task_date - datetime.timedelta(idx_week)
        #end_time=task_date + datetime.timedelta(idx_week)
        end_time=start_time+datetime.timedelta(7)
        end_day=start_time+datetime.timedelta(6)
        project_all=Project_Add.query.all()
        week_taskall={}
        delta = datetime.timedelta(days=1)
        d_in=start_time
        week_taskall[user.username]={'user_name':user.username}
        schedule_post = Task_Schedule.query.filter(Task_Schedule.recipient==user,Task_Schedule.sch_day.between(start_time,end_time))\
                                            .order_by(Task_Schedule.sch_day.asc())
        day_inc=0
        day_week=[]
        week_task={}
        user_count_all=0
        while d_in <= end_day:
            day_inc=day_inc+1
            inx_day=d_in.strftime('%A')
            count_din=0
            for sch_task in schedule_post:
                d_check=sch_task.sch_day
                if d_check==d_in:
                #if d_check.date()==d_in:
                    count_din=count_din+1
                    user_count_all=user_count_all+1
                    nw_task=sch_task.sch_project
                    nw_comment=sch_task.sch_comment
                    nw_start=sch_task.sch_from.strftime('%H:%M')
                    nw_end=sch_task.sch_to.strftime('%H:%M')
            if count_din==0:
                append_empty=''
                nw_task=append_empty
                nw_comment=append_empty
                nw_start=append_empty
                nw_end=append_empty
            day_week.append(d_in)
            week_task[d_in]={'day_week':d_in,'tk_project':nw_task,'tk_comment':nw_comment,
                            'tk_start':nw_start,'tk_end':nw_end}
            d_in = d_in + delta
        week_taskall[user.username].update(week_task)
        color_all=[]
        color_choice=['red','blue','green','pink','orange','brown','purple']
        for random_count in range(2*user_count_all):
            color_r=random.choice(color_choice)
            color_all.append(color_r)
        return render_template("/users/viewtask_weekly_user.html",day_week=day_week,color_all=color_all,week_taskall=week_taskall)
    return redirect(url_for('employees.weekly_view_task_user',username=user.username))
    #return render_template("/users/viewtask_weekly_user.html",day_week=day_week,color_all=color_all,week_taskall=week_taskall)
#########################################################
#####Error Report Enquiry#########
@employees.route('/enquiry_post_user',methods=['GET','POST'])
@login_required
def enquiry_post_user():
    user_all=User.query.filter(and_(User.is_author==True,User.user_status=='active'))
    if request.method=='POST':
        request_type=request.form.get('request_type')
        summary=request.form.get('summary')
        details=request.form.get('details')
        receipt_user=request.form.getlist('receipt_user')
        if receipt_user==[]:
            flash('Please select email address','danger')
            return redirect(url_for('employees.enquiry_post_user'))
        if request_type=='Choose...':
            flash('Please select request type','danger')
            return redirect(url_for('employees.enquiry_post_user'))
        if 'inputFile' not in request.files:
            flash('Please upload the image','danger')
            return redirect(url_for('employees.enquiry_post_user'))
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
        flash('Enquiry has been successfully send the error report','success')
        return redirect(url_for('employees.dashboard'))
    return render_template('/users/enquiry_post_user.html',user_all=user_all)

#########Project User View::Only Assigned User View ##########################
#######VIEW PROJECT #################
@employees.route('/view_allproject_user')
@login_required
def view_allproject_user():
    user=User.query.filter_by(username=current_user.username).first()
    if user.is_author!=True and user.permission_project!=True:
        abort(403)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
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
    return render_template('users/view_projectall_user.html',project_all=project_all,
                                                        ongoing_hr=ongoing_hr,
                                                        overdue_hr=overdue_hr)

@employees.route('/search_project_default_user')
@login_required
def search_project_default_user():
    user=User.query.filter_by(username=current_user.username).first()
    if user.is_author!=True and user.permission_project!=True:
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
        return redirect(url_for('adminDash.view_allproject_user'))
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
    return render_template('users/view_projectall_user.html',project_all=project_all,ongoing_hr=ongoing_hr,
                                                        overdue_hr=overdue_hr)

@employees.route('/view_allproject_selection_user',methods=['POST','GET'])
@login_required
def view_allproject_selection_user():
    user=User.query.filter_by(username=current_user.username).first()
    if user.is_author!=True and user.permission_project!=True:
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
        return render_template('users/view_projectall_user.html',project_all=project_all,ongoing_hr=ongoing_hr,
                                                            overdue_hr=overdue_hr)
    return render_template('users/view_projectall_user.html',project_all=project_all,ongoing_hr=ongoing_hr,
                                                        overdue_hr=overdue_hr)

@employees.route('/<int:project_post_id>/view_ind_project_user')
@login_required
def view_ind_project_user(project_post_id):
    user=User.query.filter_by(username=current_user.username).first()
    if user.is_author!=True and user.permission_project!=True:
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
    return render_template('/users/view_ind_project_user.html',H_All=H_All,H_All_T=H_All_T,Task_All_T=Task_All_T,
                                                        User_All=User_All,start_time=start_time_project,end_time=end_time,
                                                        project_posts=project_posts,Hour_All=cumu_all)

@employees.route('/<int:project_post_id>/view_month_project_user',methods=['POST','GET'])
@login_required
def view_month_project_user(project_post_id):
    user=User.query.filter_by(username=current_user.username).first()
    if user.is_author!=True and user.permission_project!=True:
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
    return render_template('/users/view_ind_project_user.html',H_All=H_All,H_All_T=H_All_T,Task_All_T=Task_All_T,
                                                        User_All=User_All,project_posts=project_posts,
                                                        start_time=start_time,end_time=end_time,Hour_All=cumu_all)

########View Archieve Project All###################
#######VIEW PROJECT #################
@employees.route('/view_archive_project_user')
@login_required
def view_archive_project_user():
    user=User.query.filter_by(username=current_user.username).first()
    if user.is_author!=True and user.permission_project!=True:
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
    return render_template('users/view_archive_project_user.html',project_all=project_all,ongoing_hr=ongoing_hr,
                                                            overdue_hr=overdue_hr)

@employees.route('/search_archive_project_user')
@login_required
def search_archive_project_user():
    user=User.query.filter_by(username=current_user.username).first()
    if user.is_author!=True and user.permission_project!=True:
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
        return redirect(url_for('employees.view_archive_project_user'))
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
    return render_template('users/view_archive_project_user.html',project_all=project_all,ongoing_hr=ongoing_hr,
                                                            overdue_hr=overdue_hr)

@employees.route('/<int:project_post_id>/view_indA_project_user')
@login_required
def view_indA_project_user(project_post_id):
    user=User.query.filter_by(username=current_user.username).first()
    if user.is_author!=True and user.permission_project!=True:
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
    return render_template('/users/view_indA_project_user.html',H_All=H_All,User_All=User_All,project_posts=project_posts,
                                                            start_time=start_time,end_time=end_time,Hour_All=cumu_all)

@employees.route('/<int:project_post_id>/view_monthA_project_user',methods=['POST','GET'])
@login_required
def view_monthA_project_user(project_post_id):
    user=User.query.filter_by(username=current_user.username).first()
    if user.is_author!=True and user.permission_project!=True:
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
    return render_template('/users/view_indA_project_user.html',H_All=H_All,User_All=User_All,
                                                           project_posts=project_posts,start_time=start_time,
                                                           end_time=end_time,Hour_All=cumu_all)

@employees.route('/create_project_user', methods=['GET', 'POST'])
@login_required
def create_project_user():
    user=User.query.filter_by(username=current_user.username).first()
    if user.is_author!=True and user.permission_project!=True:
        abort(403)
    form = Project_UserForm()
    post_allowance=Allowance_Add.query.all()
    if form.validate_on_submit():
        project_init=Project_Add.query.filter_by(project_add=form.project_add.data).first()
        if project_init is not None:
            flash('Project has already been added! Add new Project!','danger')
            return redirect(url_for('employees.create_project_user'))
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
        return redirect(url_for('employees.view_allproject_user'))
    return render_template('users/create_project_user.html', form=form,allowance_all=post_allowance)
