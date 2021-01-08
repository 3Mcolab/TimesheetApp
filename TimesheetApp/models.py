#models.py
from TimesheetApp import db,login_manager
from extensions import uploaded_images
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin
from datetime import datetime
#from TimesheetApp import app
from TimesheetApp.search import add_to_index, remove_from_index, query_index

class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(db.Model,UserMixin):

    __tablename__ = 'users'

    id = db.Column(db.Integer,primary_key=True)
    is_author=db.Column(db.Boolean)
    profile_image = db.Column(db.String(64),nullable=False,default='default_profile.png')
    email = db.Column(db.String(64),unique=True,index=True)
    username = db.Column(db.String(64),unique=True,index=True)
    password_hash = db.Column(db.String(128))
    firstname = db.Column(db.String(128))
    lastname = db.Column(db.String(128))
    position = db.Column(db.String(128))
    birthday = db.Column(db.DateTime,default=datetime.utcnow)
    last_seen=db.Column(db.DateTime,default=datetime.utcnow)
    user_status=db.Column(db.String(64))

    ####Mail Services############################
    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    confirmation_code = db.Column(db.String(128))
    confirmation_email=db.Column(db.String(128))
    password_reset_code=db.Column(db.String(128))
    ######Mail Services##########################
    ######Permission User Project################
    permission_project=db.Column(db.Boolean, default=False, nullable=False)
    #####Permission User Project#################
    posts = db.relationship('TimeSheetPost',backref='author',lazy=True)
    leave_posts = db.relationship('LeavePost',backref='author',lazy=True)
    enquiry_posts = db.relationship('EnquiryPost',backref='author',lazy=True)
    invoice_posts = db.relationship('InvoicePost',backref='author',lazy=True)
    barcode_posts = db.relationship('BarcodePost',backref='author',lazy=True)

    messages_sent = db.relationship('Message',foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    schedule_sent = db.relationship('Task_Schedule',foreign_keys='Task_Schedule.sender_id',
                                    backref='author', lazy='dynamic')
    schedule_received = db.relationship('Task_Schedule',foreign_keys='Task_Schedule.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)

    def __init__(self, email, username, password,user_status,is_author=False):
        self.email = email
        self.username = username
        self.is_author=is_author
        self.user_status=user_status
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

    def __repr__(self):
        return f"Username {self.username} {self.is_author}"

    @staticmethod
    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.date > last_read_time).count()
#Timesheet from the User
class TimeSheetPost(db.Model):

    users = db.relationship(User)

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)

    date = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    timesheet_status = db.Column(db.Boolean, default=False, nullable=False)
    timesheet_flag = db.Column(db.String(64))
    accept_flag=db.Column(db.String(64))
    reject_flag=db.Column(db.String(64))
    user_request_timesheet= db.Column(db.String(64))
    user_check_timesheet=db.Column(db.String(64))
    admin_request_timesheet= db.Column(db.String(64))
    user_status_timesheet=db.Column(db.String(64))
    day_clock = db.Column(db.DateTime,nullable=False)
    project = db.Column(db.String(64))
    job_num=db.Column(db.String(64))
    task = db.Column(db.String(64))
    status_clock = db.Column(db.String(64))
    remainder = db.Column(db.String(64))
    meal_allowance = db.Column(db.String(64))
    meal_rate_day=db.Column(db.Float)
    meal_type = db.Column(db.String(64))
    OverTime_15=db.Column(db.Float)
    OverTime_2=db.Column(db.Float)
    OverTime_25=db.Column(db.Float)
    NormalTime=db.Column(db.Float)
    Launch_Break=db.Column(db.Float)
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_out = db.Column(db.DateTime, nullable=False)
    travel_choice = db.Column(db.String(64))
    distance = db.Column(db.String(64))
    location = db.Column(db.String(64))
    comment = db.Column(db.Text, nullable=False)

    def __init__(self,timesheet_status,meal_allowance,meal_type,meal_rate_day,accept_flag,reject_flag,remainder,job_num,user_status_timesheet,user_request_timesheet,user_check_timesheet,admin_request_timesheet,timesheet_flag,day_clock,OverTime_15,OverTime_2,OverTime_25,NormalTime,Launch_Break,project,task,clock_in,clock_out,travel_choice,distance,location,comment,user_id):
        self.day_clock = day_clock
        self.timesheet_status=timesheet_status
        self.accept_flag=accept_flag
        self.reject_flag=reject_flag
        self.remainder=remainder
        self.job_num=job_num
        self.meal_allowance=meal_allowance
        self.meal_type=meal_type
        self.meal_rate_day=meal_rate_day
        self.user_request_timesheet=user_request_timesheet
        self.admin_request_timesheet=admin_request_timesheet
        self.user_check_timesheet=user_check_timesheet
        self.user_status_timesheet=user_status_timesheet
        self.timesheet_flag=timesheet_flag
        self.OverTime_25=OverTime_25
        self.OverTime_15=OverTime_15
        self.OverTime_2=OverTime_2
        self.NormalTime=NormalTime
        self.Launch_Break=Launch_Break
        self.project = project
        self.task = task
        self.clock_in = clock_in
        self.clock_out = clock_out
        self.travel_choice=travel_choice
        self.distance=distance
        self.location=location
        self.comment=comment
        self.user_id = user_id

    def __repr__(self):
        return f"Post ID: {self.id} --- Project{self.project} Day --{self.day_clock},,User_ID:{self.user_id}"

##Leave from the Users
class LeavePost(db.Model):
    users = db.relationship(User)

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)

    date = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    leave_status = db.Column(db.Boolean, default=False, nullable=False)
    leave_flag = db.Column(db.String(64))
    accept_flag=db.Column(db.String(64))
    reject_flag=db.Column(db.String(64))
    user_request_leave= db.Column(db.String(64))
    admin_request_leave= db.Column(db.String(64))
    user_check_leave=db.Column(db.String(64))
    user_status_leave=db.Column(db.String(64))
    leave_from = db.Column(db.DateTime,nullable=False)
    leave_to = db.Column(db.DateTime,nullable=False)
    leave_type = db.Column(db.String(64))
    leave_note = db.Column(db.Text, nullable=False)
    leave_days = db.Column(db.Integer,nullable=False)
    ####File Handling############
    image=db.Column(db.String())

    @property
    def imgsrc(self):
        return uploaded_images.url(self.image)
    def __init__(self,accept_flag,reject_flag,leave_status,image,user_status_leave,leave_flag,user_request_leave,admin_request_leave,user_check_leave,leave_from,leave_note,leave_to,leave_type,leave_days,user_id):
        self.leave_from = leave_from
        self.leave_status=leave_status
        self.accept_flag=accept_flag
        self.reject_flag=reject_flag
        self.leave_flag=leave_flag
        self.user_request_leave=user_request_leave
        self.admin_request_leave=admin_request_leave
        self.user_check_leave=user_check_leave
        self.user_status_leave=user_status_leave
        self.leave_to=leave_to
        self.leave_type=leave_type
        self.leave_note=leave_note
        self.leave_days=leave_days
        self.image=image
        self.user_id = user_id

    def __repr__(self):
        return f"Post ID: {self.id} --- Leave Type{self.leave_type} Leave From --{self.leave_from},User_ID:{self.user_id}"

##Invoice from the Users
class InvoicePost(db.Model):
    users = db.relationship(User)

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)

    date = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    invoice_status = db.Column(db.Boolean, default=False, nullable=False)
    invoice_flag = db.Column(db.String(64))
    accept_flag=db.Column(db.String(64))
    reject_flag=db.Column(db.String(64))
    user_request_invoice= db.Column(db.String(64))
    admin_request_invoice= db.Column(db.String(64))
    user_check_invoice=db.Column(db.String(64))
    user_status_invoice=db.Column(db.String(64))
    invoice_from = db.Column(db.DateTime,nullable=False)
    invoice_supplier = db.Column(db.String(64))
    invoice_Total=db.Column(db.Float)
    invoice_category = db.Column(db.String(64))
    admin_approve_flag=db.Column(db.String(64))
    admin_reject_flag=db.Column(db.String(64))
    invoice_description = db.Column(db.Text, nullable=False)
    ####File Handling############
    image=db.Column(db.String())

    @property
    def imgsrc(self):
        return uploaded_images.url(self.image)
    def __init__(self,accept_flag,reject_flag,invoice_status,image,admin_approve_flag,admin_reject_flag,user_status_invoice,invoice_flag,user_check_invoice,admin_request_invoice,user_request_invoice,invoice_from,invoice_Total,invoice_supplier,invoice_category,invoice_description,user_id):
        self.invoice_from = invoice_from
        self.invoice_status=invoice_status
        self.invoice_flag=invoice_flag
        self.accept_flag=accept_flag
        self.reject_flag=reject_flag
        self.user_request_invoice=user_request_invoice
        self.admin_request_invoice=admin_request_invoice
        self.user_status_invoice=user_status_invoice
        self.user_check_invoice=user_check_invoice
        self.invoice_Total=invoice_Total
        self.invoice_supplier=invoice_supplier
        self.invoice_category=invoice_category
        self.invoice_description=invoice_description
        self.admin_approve_flag=admin_approve_flag
        self.admin_reject_flag=admin_reject_flag
        self.image=image
        self.user_id = user_id


    def __repr__(self):
        return f"Post ID: {self.id} --- Leave Type{self.invoice_supplier} Leave From --{self.invoice_from},User_ID:{self.user_id}"

#Project
class Project_Add(SearchableMixin,db.Model):

    __searchable__ = ['project_add']
    id = db.Column(db.Integer,primary_key=True)
    date = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    project_add = db.Column(db.String(64))
    job_add = db.Column(db.String(64))
    allocate_project=db.Column(db.Float)
    allowance_id = db.Column(db.String(128))
    project_archieve=db.Column(db.String(64))
    ##########################
    def __init__(self,project_add,job_add,allocate_project,project_archieve,allowance_id):
        self.project_add = project_add
        self.job_add = job_add
        self.allocate_project = allocate_project
        self.project_archieve=project_archieve
        self.allowance_id=allowance_id

    def __repr__(self):
        return f"{self.project_add} {self.allocate_project}"

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)
#Task
class Task_Add(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    task_add = db.Column(db.String(64))
    def __init__(self,task_add):
        self.task_add = task_add

    def __repr__(self):
        return f"{self.task_add}"

class BirthDay_Add(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    daybirth = db.Column(db.Integer,nullable=False)
    def __init__(self,daybirth):
        self.daybirth = daybirth

    def __repr__(self):
        return f"{self.daybirth}"

class LeaveRem_Add(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    leaveDash = db.Column(db.Integer,nullable=False)
    def __init__(self,leaveDash):
        self.leaveDash = leaveDash

    def __repr__(self):
        return f"{self.leaveDash}"

#Invoice Type Add
class Invoice_Add(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    invoice_add = db.Column(db.String(64))
    def __init__(self,invoice_add):
        self.invoice_add = invoice_add

    def __repr__(self):
        return f"{self.invoice_add}"
###########Public Holiday#######
class Public_Holiday(db.Model):
    id = db.Column(db.Integer,primary_key=True)

    day_clock = db.Column(db.DateTime,nullable=False)
    holiday_type = db.Column(db.String(64))
    def __init__(self,day_clock,holiday_type):
        self.day_clock = day_clock
        self.holiday_type=holiday_type

    def __repr__(self):
        return f"{self.holiday_type}"

###########All Purposes Allowance########
class Allowance_Add(db.Model):

    id = db.Column(db.Integer,primary_key=True)

    allowance_add = db.Column(db.String(64))
    allocate_rate = db.Column(db.Float)
    allocate_unit=db.Column(db.String(64))

    def __init__(self,allowance_add,allocate_rate,allocate_unit):

        self.allowance_add = allowance_add
        self.allocate_rate = allocate_rate
        self.allocate_unit=allocate_unit
    def __repr__(self):
        return f"{self.allowance_add} {self.allocate_rate}"
#######Message Notification##########
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    body_message = db.Column(db.Text)
    body_status = db.Column(db.Text)
    body_title = db.Column(db.String(140))
    body_flag = db.Column(db.String(140))
    body_trans = db.Column(db.String(140))
    body_sheet=db.Column(db.String(140))
    body_id = db.Column(db.Integer) ##Qrcode Generator Id
    body_date=db.Column(db.DateTime,nullable=False)######Qrcode Generator Id
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body_message)
#######Task Schedule Notification##########
class Task_Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sch_comment = db.Column(db.String(140))
    sch_day = db.Column(db.DateTime,nullable=False)
    sch_project = db.Column(db.String(64))
    sch_from = db.Column(db.DateTime, nullable=False)
    sch_to = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<Task Scheduel {}>'.format(self.sch_project)
################################################
class Asset_Add(db.Model):
    id = db.Column(db.Integer,primary_key=True)

    asset_add = db.Column(db.String(128))
    def __init__(self,asset_add):
        self.asset_add = asset_add
    def __repr__(self):
        return f"{self.asset_add}"

class Vendor_Add(db.Model):
    id = db.Column(db.Integer,primary_key=True)

    vendor_add = db.Column(db.String(128))
    def __init__(self,vendor_add):
        self.vendor_add = vendor_add
    def __repr__(self):
        return f"{self.vendor_add}"

class Item_Add(db.Model):
    id = db.Column(db.Integer,primary_key=True)

    item_add = db.Column(db.String(128))
    item_key_gen = db.Column(db.Integer,nullable=False)
    def __init__(self,item_add,item_key_gen):
        self.item_add = item_add
        self.item_key_gen=item_key_gen
    def __repr__(self):
        return f"{self.item_add}"

class Condition_Add(db.Model):
    id = db.Column(db.Integer,primary_key=True)

    condition_add = db.Column(db.String(128))
    def __init__(self,condition_add):
        self.condition_add = condition_add
    def __repr__(self):
        return f"{self.condition_add}"

class KeyGen_Add(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    key_gen = db.Column(db.Integer,nullable=False)
    def __init__(self,key_gen):
        self.key_gen = key_gen

    def __repr__(self):
        return f"{self.key_gen}"

class BarcodePost(db.Model):
    users = db.relationship(User)
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)

    date = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    item_add = db.Column(db.String(128))
    item_condition=db.Column(db.String(64))
    item_code_add=db.Column(db.String(64))
    created_by=db.Column(db.String(64))
    item_serial_num=db.Column(db.String(64))
    unique_qrcode=db.Column(db.String(64))
    asset_add=db.Column(db.String(64))
    location_item=db.Column(db.String(64))
    vendor_add=db.Column(db.String(64))
    part_number=db.Column(db.String(64))
    item_desp=db.Column(db.String(128))
    date_created=db.Column(db.DateTime,nullable=False)
    def __init__(self,item_add,item_condition,item_code_add,unique_qrcode,created_by,item_serial_num,asset_add,location_item,vendor_add,part_number,item_desp,date_created,user_id):
        self.item_add = item_add
        self.item_condition=item_condition
        self.item_code_add=item_code_add
        self.unique_qrcode=unique_qrcode
        self.created_by=created_by
        self.item_serial_num=item_serial_num
        self.asset_add=asset_add
        self.location_item=location_item
        self.vendor_add=vendor_add
        self.part_number=part_number
        self.item_desp=item_desp
        self.date_created=date_created
        self.user_id = user_id

    def __repr__(self):
        return f"Post ID: {self.id} --- Item Add{self.item_add} ,User_ID:{self.user_id}"

class Remainder_Barcode(db.Model):
    id = db.Column(db.Integer,primary_key=True)

    date = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    remainder_date=db.Column(db.DateTime,nullable=False)
    remainder_user=db.Column(db.String(64))
    remainder_id = db.Column(db.Integer,nullable=False)
    remainder_status=db.Column(db.String(64))
    remainder_location=db.Column(db.String(64))

    def __init__(self,remainder_date,remainder_user,remainder_id,remainder_status,remainder_location):
        self.remainder_date = remainder_date
        self.remainder_user=remainder_user
        self.remainder_id=remainder_id
        self.remainder_status=remainder_status
        self.remainder_location=remainder_location

    def __repr__(self):
        return f"Post ID: {self.id} --- User{self.remainder_user}"

class Remainder_Itemcondition(db.Model):
    id = db.Column(db.Integer,primary_key=True)

    date = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    remainder_date=db.Column(db.DateTime,nullable=False)
    remainder_user=db.Column(db.String(64))
    remainder_id = db.Column(db.Integer,nullable=False)
    item_status=db.Column(db.String(64))
    item_condition=db.Column(db.String(64))

    def __init__(self,remainder_date,remainder_user,remainder_id,item_status,item_condition):
        self.remainder_date = remainder_date
        self.remainder_user=remainder_user
        self.remainder_id=remainder_id
        self.item_status=item_status
        self.item_condition=item_condition

    def __repr__(self):
        return f"Post ID: {self.id} --- User{self.remainder_user}"

class History_Barcode(db.Model):
    id = db.Column(db.Integer,primary_key=True)

    date = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    date_update=db.Column(db.DateTime,nullable=False)
    user_update=db.Column(db.String(64))
    barcode_id = db.Column(db.Integer,nullable=False)
    update_status=db.Column(db.String(64))
    update_location=db.Column(db.String(64))
    update_serialnum=db.Column(db.String(64))
    update_item=db.Column(db.String(64))
    update_cond=db.Column(db.String(64))
    update_item_code=db.Column(db.String(64))

    def __init__(self,date_update,user_update,barcode_id,update_status,update_location,update_serialnum,update_item,update_cond,update_item_code):
        self.date_update = date_update
        self.user_update=user_update
        self.barcode_id=barcode_id
        self.update_status=update_status
        self.update_location=update_location
        self.update_serialnum=update_serialnum
        self.update_item=update_item
        self.update_cond=update_cond
        self.update_item_code=update_item_code

    def __repr__(self):
        return f"Post ID: {self.id} --- User{self.user_update}"


class EnquiryPost(db.Model):
    users = db.relationship(User)

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    date = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)

    request_type=db.Column(db.String(64))
    summary = db.Column(db.String(128))
    details = db.Column(db.Text, nullable=False)
    receipt_email=db.Column(db.String(64))
    image=db.Column(db.String(128))

    @property
    def imgsrc(self):
        return uploaded_images.url(self.image)

    def __init__(self,user_id,request_type,summary,details,receipt_email,image):
        self.request_type = request_type
        self.summary=summary
        self.details=details
        self.receipt_email=receipt_email
        self.image=image
        self.user_id=user_id

    def __repr__(self):
        return f"Post ID: {self.id} --- Enquiry{self.request_type}"
