import datetime
import os
import time
import json
import pyzbar.pyzbar as pyzbar
import numpy as np
from PIL import Image
import re
import io
from io import BytesIO
import base64, json
import random
import qrcode
from flask import render_template,url_for,flash, redirect,request,jsonify,Blueprint,abort,session,send_file, make_response,current_app,send_from_directory
from flask_login import current_user,login_required
from TimesheetApp import db
from TimesheetApp.models import Asset_Add,Vendor_Add,Item_Add,Condition_Add,Project_Add,KeyGen_Add,BarcodePost,Message,User,Remainder_Barcode,History_Barcode,Remainder_Itemcondition
from TimesheetApp.barcode.forms import AssetForm,VendorForm, ItemForm,ConditionForm
from sqlalchemy import and_
###Mail Services#########
import uuid
from TimesheetApp.utilities.common import email


barcode=Blueprint('barcode',__name__)

user_barcode_data = {}
user_barcode_data_reader = {}
user_codedata={}
user_codedata_reader={}

#########Admin Dashboard##########
@barcode.route('/create_asset', methods=['GET', 'POST'])
@login_required
def create_asset():
    if session.get('is_author')!=True:
        abort(403)
    form = AssetForm()
    if form.validate_on_submit():
        form.asset_add.data=form.asset_add.data.lower()
        asset_init=Asset_Add.query.filter_by(asset_add=form.asset_add.data).first()
        if asset_init is not None:
            flash('Asset has already been added! Add new asset!','danger')
            return redirect(url_for('barcode.create_asset'))
        asset_create = Asset_Add(asset_add=form.asset_add.data)
        db.session.add(asset_create)
        db.session.commit()
        flash('Asset has been successfully created!','success')
        return redirect(url_for('barcode.view_asset'))
    return render_template('barcode/create_asset.html', form=form)

@barcode.route('/view_asset')
@login_required
def view_asset():
    if session.get('is_author')!=True:
        abort(403)
    post_data=Asset_Add.query.all()
    return render_template('barcode/view_asset.html',post_data=post_data)

@barcode.route('/<int:post_id>/delete_asset')
@login_required
def delete_asset(post_id):
    if session.get('is_author')!=True:
        abort(403)
    post_data= Asset_Add.query.get_or_404(post_id)
    db.session.delete(post_data)
    db.session.commit()
    flash('Asset has been deleted!','danger')
    return redirect(url_for('barcode.view_asset'))

@barcode.route('/create_vendor', methods=['GET', 'POST'])
@login_required
def create_vendor():
    if session.get('is_author')!=True:
        abort(403)
    form = VendorForm()
    if form.validate_on_submit():
        form.vendor_add.data=form.vendor_add.data.lower()
        vendor_init=Vendor_Add.query.filter_by(vendor_add=form.vendor_add.data).first()
        if vendor_init is not None:
            flash('Vendor has already been added! Add new vendor!','danger')
            return redirect(url_for('barcode.create_vendor'))
        vendor_create = Vendor_Add(vendor_add=form.vendor_add.data)
        db.session.add(vendor_create)
        db.session.commit()
        flash('Vendor has been successfully created!','success')
        return redirect(url_for('barcode.view_vendor'))
    return render_template('barcode/create_vendor.html', form=form)

@barcode.route('/view_vendor')
@login_required
def view_vendor():
    if session.get('is_author')!=True:
        abort(403)
    post_data=Vendor_Add.query.all()
    return render_template('barcode/view_vendor.html',post_data=post_data)

@barcode.route('/<int:post_id>/delete_vendor')
@login_required
def delete_vendor(post_id):
    if session.get('is_author')!=True:
        abort(403)
    post_data= Vendor_Add.query.get_or_404(post_id)
    db.session.delete(post_data)
    db.session.commit()
    flash('Vendor has been deleted!','danger')
    return redirect(url_for('barcode.view_vendor'))

@barcode.route('/create_itemname', methods=['GET', 'POST'])
@login_required
def create_itemname():
    if session.get('is_author')!=True:
        abort(403)
    form = ItemForm()
    if form.validate_on_submit():
        form.item_add.data=form.item_add.data.lower()
        item_init=Item_Add.query.filter_by(item_add=form.item_add.data).first()
        if item_init is not None:
            flash('Item has already been added! Add new item!','danger')
            return redirect(url_for('barcode.create_itemname'))
        item_create = Item_Add(item_add=form.item_add.data,
                               item_key_gen=int(0))
        db.session.add(item_create)
        db.session.commit()
        flash('Item has been successfully created!','success')
        return redirect(url_for('barcode.view_itemname'))
    return render_template('barcode/create_itemname.html', form=form)

@barcode.route('/view_itemname')
@login_required
def view_itemname():
    if session.get('is_author')!=True:
        abort(403)
    post_data=Item_Add.query.all()
    return render_template('barcode/view_itemname.html',post_data=post_data)

@barcode.route('/<int:post_id>/delete_itemname')
@login_required
def delete_itemname(post_id):
    if session.get('is_author')!=True:
        abort(403)
    post_data= Item_Add.query.get_or_404(post_id)
    db.session.delete(post_data)
    db.session.commit()
    flash('Item has been deleted!','danger')
    return redirect(url_for('barcode.view_itemname'))

@barcode.route('/create_condition', methods=['GET', 'POST'])
@login_required
def create_condition():
    if session.get('is_author')!=True:
        abort(403)
    form = ConditionForm()
    if form.validate_on_submit():
        form.condition_add.data=form.condition_add.data.lower()
        condition_init=Condition_Add.query.filter_by(condition_add=form.condition_add.data).first()
        if condition_init is not None:
            flash('Item condition has already been added! Add new condition!','danger')
            return redirect(url_for('barcode.create_condition'))
        condition_create = Condition_Add(condition_add=form.condition_add.data)
        db.session.add(condition_create)
        db.session.commit()
        flash('Item condition has been successfully created!','success')
        return redirect(url_for('barcode.view_condition'))
    return render_template('barcode/create_condition.html', form=form)

@barcode.route('/view_condition')
@login_required
def view_condition():
    if session.get('is_author')!=True:
        abort(403)
    post_data=Condition_Add.query.all()
    return render_template('barcode/view_condition.html',post_data=post_data)

@barcode.route('/<int:post_id>/delete_condition')
@login_required
def delete_condition(post_id):
    if session.get('is_author')!=True:
        abort(403)
    post_data= Condition_Add.query.get_or_404(post_id)
    db.session.delete(post_data)
    db.session.commit()
    flash('Item condition has been deleted!','danger')
    return redirect(url_for('barcode.view_condition'))

@barcode.route('/history_view_all_admin')
@login_required
def history_view_all_admin():
    if session.get('is_author')!=True:
        abort(403)
    user_all=User.query.order_by(User.username).all()
    page = request.args.get('page', 1, type=int)
    post_submit=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    post_history=History_Barcode.query.order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
    post_barcode=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    post_history_count=History_Barcode.query.order_by(History_Barcode.date.desc())
    #####Random Color Generation#########
    count_h=0
    for post_init_h in post_history_count:
        count_h=count_h+1
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_h):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
        #r = lambda: random.randint(0,255)
        #color_r = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
    return render_template('/barcode/history_view_all_admin.html',post_data=post_submit,project_all=project_all,
                                                              color_all=color_all,user_all=user_all,
                                                              post_history=post_history,post_barcode=post_barcode)
##############Inventory Selection #####################################
@barcode.route('/view_inventory_history_all_selection_admin',methods=['POST','GET'])
@login_required
def view_inventory_history_all_selection_admin():
    if request.method=='POST':
        user_get=request.form.get('user_select')
        model_select=request.form.get('model_select')
        desp_select=request.form.get('desp_select')
        page = request.args.get('page', 1, type=int)
        if user_get!='':
            post_submit=History_Barcode.query.filter(History_Barcode.user_update==user_get)\
                                                .order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
        elif model_select!='':
            post_submit=History_Barcode.query.filter(History_Barcode.update_location==model_select)\
                                                .order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
        elif desp_select!='':
            post_submit=History_Barcode.query.filter(History_Barcode.update_serialnum==desp_select)\
                                                .order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
        else:
            post_submit=History_Barcode.query.order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
    if request.method=='GET':
        page = request.args.get('page', 1, type=int)
        post_submit=History_Barcode.query.order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
    user_all=User.query.order_by(User.username).all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    post_default=History_Barcode.query.order_by(History_Barcode.date.desc())
    post_barcode=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    #########################
    count_all=0
    for post_init in post_default:
        count_all=count_all+1
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/barcode/history_view_all_admin.html',post_history=post_submit,project_all=project_all,
                                                            post_barcode=post_barcode,
                                                            color_all=color_all,user_all=user_all)

@barcode.route('/view_inventory_all_admin')
@login_required
def view_inventory_all_admin():
    if session.get('is_author')!=True:
        abort(403)
    user_all=User.query.order_by(User.username).all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    item_all=Item_Add.query.all()
    page = request.args.get('page', 1, type=int)
    post_submit=BarcodePost.query.order_by(BarcodePost.date.desc()).paginate(page=page, per_page=25)
    post_count=BarcodePost.query.order_by(BarcodePost.date.desc())
    count_all=0
    count_miss=0
    count_dam=0
    type_nav='default'
    for post_init in post_count:
        count_all=count_all+1
        if post_init.item_condition=='missing':
            count_miss=count_miss+1
        if post_init.item_condition=='damaged':
            count_dam=count_dam+1
    #####Random Color Generation#########
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
        #r = lambda: random.randint(0,255)
        #color_r = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
    return render_template('/barcode/inventory_view_all_admin.html',post_data=post_submit,project_all=project_all,
                                                              color_all=color_all,user_all=user_all,
                                                              item_all=item_all,
                                                              count_all=count_all,count_miss=count_miss,
                                                              count_dam=count_dam,type_nav=type_nav)
##########Delete Inventory########
@barcode.route('/<int:post_id>/delete_inventory_admin')
@login_required
def delete_inventory_admin(post_id):
    if session.get('is_author')!=True:
        abort(403)
    post_data= BarcodePost.query.get_or_404(post_id)
    db.session.delete(post_data)
    db.session.commit()
    flash('Item has been deleted!','danger')
    return redirect(url_for('barcode.view_inventory_all_admin'))

@barcode.route('/<int:post_id>/modify_inventory_admin',methods=['GET','POST'])
@login_required
def modify_inventory_admin(post_id):
    if session.get('is_author')!=True:
        abort(403)
    post_data=BarcodePost.query.get_or_404(post_id)
    user_all=User.query.filter(User.user_status=='active').order_by(User.username)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default').order_by(Project_Add.project_add)
    item_con_all=Condition_Add.query.all()
    if request.method=='POST':
        post_data.created_by=request.form.get('user_add')
        post_data.item_condition=request.form.get('status_item')
        post_data.location_item=request.form.get('location_add')
        post_data.item_desp=request.form.get('desp_add')
        date_issue_str=request.form.get('date_issue')
        date_issuef=datetime.datetime.strptime(date_issue_str,'%d/%m/%Y')
        post_data.date_created=date_issuef
        db.session.commit()
        return redirect(url_for('barcode.view_inventory_all_admin'))
    return render_template('/barcode/modify_inventory_admin.html',post_data=post_data,user_all=user_all,
                                                                  item_con_all=item_con_all,project_all=project_all)
#######Inventory of Navigation Bar##############
@barcode.route('/<nav_bar>/view_inventory_nav_admin')
@login_required
def view_inventory_nav_admin(nav_bar):
    page = request.args.get('page', 1, type=int)
    if nav_bar=='miss':
        post_submit=BarcodePost.query.filter(BarcodePost.item_condition=='missing')\
                                        .order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        type_nav='miss'
    elif nav_bar=='dam':
        post_submit=BarcodePost.query.filter(BarcodePost.item_condition=='damaged')\
                                        .order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        type_nav='dam'
    else:
        post_submit=BarcodePost.query.order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        type_nav='default'
    user_all=User.query.order_by(User.username).all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    item_all=Item_Add.query.all()
    post_default=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    count_all=0
    count_miss=0
    count_dam=0
    for post_init in post_default:
        count_all=count_all+1
        if post_init.item_condition=='missing':
            count_miss=count_miss+1
        if post_init.item_condition=='damaged':
            count_dam=count_dam+1
    #########################
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/barcode/inventory_view_all_admin.html',post_data=post_submit,project_all=project_all,
                                                              color_all=color_all,user_all=user_all,
                                                              item_all=item_all,
                                                              count_all=count_all,count_miss=count_miss,
                                                              count_dam=count_dam,type_nav=type_nav)
##############Inventory Selection #####################################
@barcode.route('/view_inventory_all_selection_admin',methods=['POST','GET'])
@login_required
def view_inventory_all_selection_admin():
    if request.method=='POST':
        page = request.args.get('page', 1, type=int)
        user_get=request.form.get('user_select')
        model_select=request.form.get('model_select')
        desp_select=request.form.get('desp_select')
        if user_get!='':
            post_submit=BarcodePost.query.filter(BarcodePost.created_by==user_get)\
                                            .order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        elif model_select!='':
            post_submit=BarcodePost.query.filter(BarcodePost.location_item==model_select)\
                                            .order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        elif desp_select!='':
            post_submit=BarcodePost.query.filter(BarcodePost.item_add==desp_select)\
                                            .order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        else:
            post_submit=BarcodePost.query.order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
    if request.method=='GET':
        page = request.args.get('page', 1, type=int)
        post_submit=BarcodePost.query.order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
    type_nav='default'
    user_all=User.query.order_by(User.username).all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    item_all=Item_Add.query.all()
    post_default=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    count_all=0
    count_miss=0
    count_dam=0
    for post_init in post_default:
        count_all=count_all+1
        if post_init.item_condition=='missing':
            count_miss=count_miss+1
        if post_init.item_condition=='damaged':
            count_dam=count_dam+1
    #########################
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/barcode/inventory_view_all_admin.html',post_data=post_submit,project_all=project_all,
                                                              color_all=color_all,user_all=user_all,
                                                              item_all=item_all,
                                                              count_all=count_all,count_miss=count_miss,
                                                              count_dam=count_dam,type_nav=type_nav)
#####################################################################################################
##############Inventory Selection #####################################
@barcode.route('/<int:post_log_id>/view_inventory_logstatus_selection_admin')
@login_required
def view_inventory_logstatus_selection_admin(post_log_id):
    post_check=History_Barcode.query.get_or_404(post_log_id)
    page = request.args.get('page', 1, type=int)
    post_submit=History_Barcode.query.filter(History_Barcode.update_serialnum==post_check.update_serialnum)\
                                        .order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
    user_all=User.query.order_by(User.username).all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    post_default=History_Barcode.query.order_by(History_Barcode.date.desc())
    post_barcode=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    count_all=0
    for post_init in post_default:
        count_all=count_all+1
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/barcode/history_view_all_admin.html',post_history=post_submit,project_all=project_all,
                                                            post_barcode=post_barcode,
                                                            color_all=color_all,user_all=user_all)

@barcode.route('/<int:post_id>/history_qrcode_user_admin')
@login_required
def history_qrcode_user_admin(post_id):
    barcode_post=BarcodePost.query.get_or_404(post_id)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    qrgen_code = qrcode.QRCode(version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,border=0,)

    qrgen_code.add_data(barcode_post.item_serial_num)
    qrgen_code.make(fit=True)
    pil_img = qrgen_code.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    test_img=pil_img
    img_io.seek(0)
    img_str = base64.b64encode(img_io.getvalue())
    image_bytes = io.BytesIO(base64.b64decode(img_str))
    im = Image.open(image_bytes)
    decodedObjects = pyzbar.decode(im)
    encode_barcodedata = []
    for obj in decodedObjects:
        #print('Type : ', obj.type)
        #print('Data : ', obj.data, '\n')
        encode_barcodedata.append({"code":obj.data.decode('utf-8') ,
                                    "type": obj.type})

    result = base64.b64encode(img_io.getvalue()).decode('ascii')
    #contents=img_io.getvalue().encode("base64")
    #return send_file(img_io, mimetype='image/jpeg')
    return render_template('/barcode/indpost_qrcode_admin.html',result=result,
                                                        post_data=barcode_post,
                                                        project_all=project_all)
#########User Dashboard########################################################
###############################################################################
@barcode.route('/<username>/create_inventory_step1',methods=['GET','POST'])
@login_required
def create_inventory_step1(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    percent_job=round(((1/2)*100),1)
    asset_all=Asset_Add.query.all()
    item_all=Item_Add.query.all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    condition_all=Condition_Add.query.all()
    if request.method=='POST':
        item_add_init=request.form.get('item_add')
        item_other=request.form.get('item_other')
        asset_add=request.form.get('asset_add')
        asset_other=request.form.get('asset_other')
        item_condition=request.form.get('condition_item')
        location_item=request.form.get('location_item')
        asset_other=asset_other.lower()
        item_other=item_other.lower()
        #####Check Form Validation#########
        if location_item=='' or item_condition is None:
            flash('Please select the choices','danger')
            return redirect(url_for('barcode.create_inventory_step1',username=user.username))
        if (item_add_init=='' and item_other=='') or (item_add_init!='' and item_other!=''):
            flash('Please select only one item choices','danger')
            return redirect(url_for('barcode.create_inventory_step1',username=user.username))
        if (asset_add=='' and asset_other=='') or (asset_add!='' and asset_other!=''):
            flash('Please select item choices','danger')
            return redirect(url_for('barcode.create_inventory_step1',username=user.username))
        #################################################
        if item_other!='':
            product_init=Item_Add.query.filter(Item_Add.item_add==item_other).first()
            if product_init is not None:
                flash('Item has been already added','danger')
                return redirect(url_for('barcode.create_inventory_step1',username=user.username))
            item_add_init=item_other
            item_create = Item_Add(item_add=item_add_init,item_key_gen=int(0))
            db.session.add(item_create)
            db.session.commit()
        if asset_other!='':
            asset_init=Asset_Add.query.filter(Asset_Add.asset_add==asset_other).first()
            if asset_init is not None:
                flash('Asset has been already added','danger')
                return redirect(url_for('barcode.create_inventory_step1',username=user.username))
            asset_add=asset_other
            asset_create = Asset_Add(asset_add=asset_add)
            db.session.add(asset_create)
            db.session.commit()
        ###################################
        created_by=user.username
        user_barcode_data[user.username]={'item_add':item_add_init,
                                          'item_condition':item_condition,
                                          'asset_add':asset_add,
                                          'location_item':location_item,
                                          'created_by':created_by}
        return redirect(url_for('barcode.create_inventory_step2',username=user.username))
    return render_template('barcode/create_inventory_step1.html',percent_job=percent_job,
                                                                   item_all=item_all,
                                                                   project_all=project_all,
                                                                   asset_all=asset_all,
                                                                   condition_all=condition_all)

@barcode.route('/<username>/create_inventory_step2',methods=['GET','POST'])
@login_required
def create_inventory_step2(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    percent_job=round(((2/2)*100),1)
    vendor_all=Vendor_Add.query.all()
    if request.method=='POST':
        vendor_add=request.form.get('vendor_add')
        vendor_other=request.form.get('vendor_other')
        vendor_other=vendor_other.lower()
        part_number=request.form.get('part_number')
        item_desp=request.form.get('item_desp')
        user_id=current_user.id
        if (vendor_add=='' and vendor_other=='') or (vendor_add!='' and vendor_other!=''):
            flash('Please select only one vendor choices','danger')
            return redirect(url_for('barcode.create_inventory_step2',username=user.username))
        if vendor_other!='':
            vendor_init=Vendor_Add.query.filter(Vendor_Add.vendor_add==vendor_other).first()
            if vendor_init is not None:
                flash('Vendor has been already added','danger')
                return redirect(url_for('barcode.create_inventory_step2',username=user.username))
            vendor_add=vendor_other
            vendor_create = Vendor_Add(vendor_add=vendor_add)
            db.session.add(vendor_create)
            db.session.commit()
        item_add=user_barcode_data[user.username]['item_add']
        item_condition=user_barcode_data[user.username]['item_condition']
        asset_add=user_barcode_data[user.username]['asset_add']
        location_item=user_barcode_data[user.username]['location_item']
        created_by=user_barcode_data[user.username]['created_by']
        date_created=datetime.datetime.today()
        #####Key Generation#############################################
        if  item_add.count(' ')==0 or item_add.count(' ')==1:
            item_code_add_serial=item_add[:3].upper()
            item_code_add=item_code_add_serial[:2]

        else:
            item_code_add_serial = ''.join([s[:1].upper() for s in item_add.split(' ')])
            item_code_add=item_code_add_serial[:2]
        #item_key_init=KeyGen_Add.query.get(1)
        item_key_init=Item_Add.query.filter(Item_Add.item_add==item_add).first()
        if item_key_init is not None:
            item_key=item_key_init.item_key_gen+int(1)
            item_key_init.item_key_gen=item_key
            db.session.commit()
        else:
            item_key=KeyGen_Add(key_gen=int(1))
            db.session.add(item_key)
            db.session.commit()
        keygen_item=str(item_key).zfill(4)
        item_serial_num=item_code_add_serial + '-' + keygen_item
        date_requested_update=date_created-datetime.timedelta(365)
        ################################################################
        barcode_data=BarcodePost(item_add=item_add,item_condition=item_condition,
                                item_serial_num=item_serial_num,date_created=date_created,
                                asset_add=asset_add,location_item=location_item,user_id=user_id,
                                created_by=created_by,vendor_add=vendor_add,
                                part_number=part_number,item_desp=item_desp,
                                item_code_add=item_code_add,unique_qrcode=item_serial_num)
        db.session.add(barcode_data)
        db.session.commit()
        ########################################
        item_post_id=BarcodePost.query.filter(BarcodePost.item_serial_num==item_serial_num).first()
        ###############History Add####################################
        if item_post_id is not None:
            history_data=History_Barcode(date_update=date_created,user_update=created_by,
                                        update_status='Issue',barcode_id=item_post_id.id,
                                        update_location=location_item,update_serialnum=item_serial_num,
                                        update_item=item_add,update_cond=item_condition,
                                        update_item_code=item_code_add)
            db.session.add(history_data)
            db.session.commit()
        return redirect(url_for('barcode.view_inventory_all',username=user.username))
    return render_template('/barcode/create_inventory_step2.html',percent_job=percent_job,
                                                                  vendor_all=vendor_all)

@barcode.route('/<username>/view_inventory_user')
@login_required
def view_inventory_user(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    post_submit=BarcodePost.query.order_by(BarcodePost.date_created.asc())
    #########Random Generator########
    count_all=0
    for post_init in post_submit:
        count_all=count_all+1
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/barcode/view_inventory_user.html',post_submit=post_submit,color_all=color_all)
###Inventory of ALl#####
@barcode.route('/<username>/view_inventory_all')
@login_required
def view_inventory_all(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    user_all=User.query.order_by(User.username).all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    item_all=Item_Add.query.all()
    page = request.args.get('page', 1, type=int)
    post_submit=BarcodePost.query.order_by(BarcodePost.date.desc()).paginate(page=page, per_page=25)
    post_count=BarcodePost.query.order_by(BarcodePost.date.desc())
    count_all=0
    count_miss=0
    count_dam=0
    type_nav='default'
    for post_init in post_count:
        count_all=count_all+1
        if post_init.item_condition=='missing':
            count_miss=count_miss+1
        if post_init.item_condition=='damaged':
            count_dam=count_dam+1
    #####Random Color Generation#########
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
        #r = lambda: random.randint(0,255)
        #color_r = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
    return render_template('/barcode/inventory_view_all.html',post_data=post_submit,project_all=project_all,
                                                              color_all=color_all,user_all=user_all,
                                                              item_all=item_all,
                                                              count_all=count_all,count_miss=count_miss,
                                                              count_dam=count_dam,type_nav=type_nav)
#######Inventory of Navigation Bar##############
@barcode.route('/<nav_bar>/view_inventory_nav')
@login_required
def view_inventory_nav(nav_bar):
    page = request.args.get('page', 1, type=int)
    if nav_bar=='miss':
        post_submit=BarcodePost.query.filter(BarcodePost.item_condition=='missing')\
                                        .order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        type_nav='miss'
    elif nav_bar=='dam':
        post_submit=BarcodePost.query.filter(BarcodePost.item_condition=='damaged')\
                                        .order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        type_nav='dam'
    else:
        post_submit=BarcodePost.query.order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        type_nav='default'
    user_all=User.query.order_by(User.username).all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    item_all=Item_Add.query.all()
    post_default=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    count_all=0
    count_miss=0
    count_dam=0
    for post_init in post_default:
        count_all=count_all+1
        if post_init.item_condition=='missing':
            count_miss=count_miss+1
        if post_init.item_condition=='damaged':
            count_dam=count_dam+1
    #########################
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/barcode/inventory_view_all.html',post_data=post_submit,project_all=project_all,
                                                              color_all=color_all,user_all=user_all,
                                                              item_all=item_all,
                                                              count_all=count_all,count_miss=count_miss,
                                                              count_dam=count_dam,type_nav=type_nav)
##############Inventory Selection #####################################
@barcode.route('/view_inventory_all_selection',methods=['POST','GET'])
@login_required
def view_inventory_all_selection():

    if request.method=='POST':
        page = request.args.get('page', 1, type=int)
        user_get=request.form.get('user_select')
        model_select=request.form.get('model_select')
        desp_select=request.form.get('desp_select')
        if user_get!='':
            post_submit=BarcodePost.query.filter(BarcodePost.created_by==user_get)\
                                            .order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        elif model_select!='':
            post_submit=BarcodePost.query.filter(BarcodePost.location_item==model_select)\
                                            .order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        elif desp_select!='':
            post_submit=BarcodePost.query.filter(BarcodePost.item_add==desp_select)\
                                            .order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
        else:
            post_submit=BarcodePost.query.order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)
    if request.method=='GET':
        page = request.args.get('page', 1, type=int)
        post_submit=BarcodePost.query.order_by(BarcodePost.date_created.desc()).paginate(page=page, per_page=25)


    type_nav='default'
    user_all=User.query.order_by(User.username).all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    item_all=Item_Add.query.all()
    post_default=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    count_all=0
    count_miss=0
    count_dam=0
    for post_init in post_default:
        count_all=count_all+1
        if post_init.item_condition=='missing':
            count_miss=count_miss+1
        if post_init.item_condition=='damaged':
            count_dam=count_dam+1
    #########################
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/barcode/inventory_view_all.html',post_data=post_submit,project_all=project_all,
                                                              color_all=color_all,user_all=user_all,
                                                              item_all=item_all,
                                                              count_all=count_all,count_miss=count_miss,
                                                              count_dam=count_dam,type_nav=type_nav)

############History of Qrcode of User##########################################
@barcode.route('/<int:post_id>/history_qrcode_user')
@login_required
def history_qrcode_user(post_id):
    barcode_post=BarcodePost.query.get_or_404(post_id)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    qrgen_code = qrcode.QRCode(version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,border=0,)

    qrgen_code.add_data(barcode_post.item_serial_num)
    qrgen_code.make(fit=True)
    pil_img = qrgen_code.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    test_img=pil_img
    img_io.seek(0)
    img_str = base64.b64encode(img_io.getvalue())
    image_bytes = io.BytesIO(base64.b64decode(img_str))
    im = Image.open(image_bytes)
    decodedObjects = pyzbar.decode(im)
    encode_barcodedata = []
    for obj in decodedObjects:
        #print('Type : ', obj.type)
        #print('Data : ', obj.data, '\n')
        encode_barcodedata.append({"code":obj.data.decode('utf-8') ,
                                    "type": obj.type})

    result = base64.b64encode(img_io.getvalue()).decode('ascii')
    #contents=img_io.getvalue().encode("base64")
    #return send_file(img_io, mimetype='image/jpeg')
    return render_template('/barcode/indpost_qrcode.html',result=result,
                                                        post_data=barcode_post,
                                                        project_all=project_all)
#################Inventory User Request########################################
@barcode.route('/<int:post_id>/inventory_user_request',methods=['GET','POST'])
@login_required
def inventory_user_request(post_id):
    barcode_post=BarcodePost.query.get_or_404(post_id)
    user=User.query.filter(User.username==barcode_post.created_by).first()
    if request.method=='POST':
        inv_request_date=request.form.get('inv_request_date')
        location_item=request.form.get('location_item')
        ##########Check Validation#####################
        if inv_request_date=='':
            flash('Request date for item cannot be blank','danger')
            return redirect(url_for('barcode.history_qrcode_user',post_id=barcode_post.id))
        ######Check if Qrcode is already taken by other user######
        date_request_in=datetime.datetime.strptime(inv_request_date,'%d/%m/%Y')
        rem_post=Remainder_Barcode.query.filter(and_(Remainder_Barcode.remainder_date==date_request_in,\
                                                        Remainder_Barcode.remainder_id==barcode_post.id))
        count_rem=0
        for rem_in in rem_post:
            count_rem=count_rem+1
        if count_rem >=1:
            flash('Item has been already assigned or cannot be used on that day! Please choose other date','danger')
            return redirect(url_for('barcode.history_qrcode_user',post_id=post_id))
        ########Update qrcode status###########
        rem_date_request=datetime.datetime.strptime(inv_request_date,'%d/%m/%Y')
        rem_qrcode=Remainder_Barcode(remainder_date=rem_date_request,
                                     remainder_user=current_user.username,
                                     remainder_id=barcode_post.id,
                                     remainder_status='posting',
                                     remainder_location=location_item)
        db.session.add(rem_qrcode)
        db.session.commit()
        ##########History Login Status#############
        history_data=History_Barcode(date_update=rem_date_request,user_update=current_user.username,
                                    update_status='Request',barcode_id=barcode_post.id,
                                    update_location=location_item,update_serialnum=barcode_post.item_serial_num,
                                    update_item=barcode_post.item_add,update_cond=barcode_post.item_condition,
                                    update_item_code=barcode_post.item_code_add)
        db.session.add(history_data)
        db.session.commit()
        #########Delete Barcode############################
        ######################################
        user_message_ap='Hi {}! {} is requesting for {} with serial number {} for {} on {}.'.format(user.firstname,current_user.firstname,\
                                                                                                    barcode_post.item_add,barcode_post.item_serial_num,
                                                                                                    location_item,inv_request_date)
        user_status_ap='unread'
        user_flag_ap=''
        user_title_ap='{} Request'.format(barcode_post.item_add)
        msg = Message(author=current_user, recipient=user,
                        body_message=user_message_ap,
                        body_title=user_title_ap,
                        body_flag=user_flag_ap,
                        body_trans='inventory_request',
                        body_date=rem_date_request,
                        body_id=barcode_post.id,
                        body_sheet='default',
                        body_status=user_status_ap)
        db.session.add(msg)
        db.session.commit()
        ######send email to user for verification###########
        barcode_post_email=BarcodePost.query.get(barcode_post.id)
        if barcode_post_email!=None:
            rem_post_email=Remainder_Barcode.query.filter(and_(Remainder_Barcode.remainder_id==barcode_post.id,\
                                                                        Remainder_Barcode.remainder_date==rem_date_request)).first()
            message_email='{} is requesting for {} with serial number {} for {} on {}'.format(current_user.firstname,barcode_post.item_add,\
                                                                                            barcode_post.item_serial_num,location_item,inv_request_date)
            body_html=render_template('mail/user/inventory_request_reminder.html',user=user,message_email=message_email,
                                                                                    post_rem_id=rem_post_email.id,post_id=barcode_post.id)
            body_text=render_template('mail/user/inventory_request_reminder.txt',user=user,message_email=message_email,
                                                                                post_rem_id=rem_post_email.id,post_id=barcode_post.id)
            body_title='{} Request'.format(barcode_post.item_add)
            email(user.email,body_title,body_html,body_text)
            ######send email to user for verification###########
            flash('Your request has been delivered to {}!'.format(user.firstname),'success')
    return redirect(url_for('barcode.history_qrcode_user',post_id=post_id))
#############Report Item Condition##########################
@barcode.route('/<int:post_id>/report_item_condition',methods=['GET','POST'])
@login_required
def report_item_condition(post_id):
    barcode_post=BarcodePost.query.get_or_404(post_id)
    user=User.query.filter(User.username==barcode_post.created_by).first()
    if request.method=='POST':
        user_select=request.form.get('user_select')
        item_condition=request.form.get('item_condition')
        user_report=User.query.filter(User.username==user_select).first()
        ########Update qrcode status###########
        rem_qrcode_item=Remainder_Itemcondition(remainder_date=datetime.date.today(),
                                     remainder_user=current_user.username,
                                     remainder_id=barcode_post.id,
                                     item_status='report',
                                     item_condition=item_condition)
        db.session.add(rem_qrcode_item)
        db.session.commit()
        ##########History Login Status#############
        history_data=History_Barcode(date_update=datetime.date.today(),user_update=current_user.username,
                                    update_status='Report',barcode_id=barcode_post.id,
                                    update_location=barcode_post.location_item,update_serialnum=barcode_post.item_serial_num,
                                    update_item=barcode_post.item_add,update_cond=barcode_post.item_condition,
                                    update_item_code=barcode_post.item_code_add)
        db.session.add(history_data)
        db.session.commit()
        #########Delete Barcode############################
        ######################################
        user_message_ap='Hi {}! {} is reporting the item {} with serial number {} {}.Do you accept the condition?'.format(user_report.firstname,current_user.firstname,
                                                                                                    barcode_post.item_add,barcode_post.item_serial_num,
                                                                                                    barcode_post.item_condition)
        user_status_ap='unread'
        user_flag_ap=''
        user_title_ap='Report {} Condition'.format(barcode_post.item_add)
        msg = Message(author=current_user, recipient=user_report,
                        body_message=user_message_ap,
                        body_title=user_title_ap,
                        body_flag=user_flag_ap,
                        body_trans='report_item_condition',
                        body_date=datetime.date.today(),
                        body_id=barcode_post.id,
                        body_sheet='default',
                        body_status=user_status_ap)
        db.session.add(msg)
        db.session.commit()
        ######send email to user for verification###########
        message_email='{} is reporting the item {} with serial number {} {}.Do you accept the condition?'.format(current_user.firstname,barcode_post.item_add,\
                                                                                            barcode_post.item_serial_num,barcode_post.item_condition)
        body_html=render_template('mail/user/reminder.html',user=user_report,message_email=message_email)
        body_text=render_template('mail/user/reminder.txt',user=user_report,message_email=message_email)
        body_title='Report {} Condition'.format(barcode_post.item_add)
        email(user_report.email,body_title,body_html,body_text)
        ######send email to user for verification###########
        flash('Your request has been delivered to {}!'.format(user_report.firstname),'success')
        return redirect(url_for('barcode.barcode_decode_user'))

@barcode.route('/<username>/<int:post_id>/<int:post_rem_id>/report_condition_approval')
@login_required
def report_condition_approval(username,post_id,post_rem_id):
    user=User.query.filter_by(username=username).first_or_404()
    if session.get('is_author')!=True:
        abort(403)
    barcode_post=BarcodePost.query.get_or_404(post_id)
    rem_post=Remainder_Itemcondition.query.get_or_404(post_rem_id)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    qrgen_code = qrcode.QRCode(version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,border=0,)
    qrgen_code.add_data(barcode_post.item_serial_num)
    qrgen_code.make(fit=True)
    pil_img = qrgen_code.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    test_img=pil_img
    img_io.seek(0)
    img_str = base64.b64encode(img_io.getvalue())
    image_bytes = io.BytesIO(base64.b64decode(img_str))
    im = Image.open(image_bytes)
    decodedObjects = pyzbar.decode(im)
    encode_barcodedata = []
    for obj in decodedObjects:
        encode_barcodedata.append({"code":obj.data.decode('utf-8') ,
                                    "type": obj.type})
    result = base64.b64encode(img_io.getvalue()).decode('ascii')
    return render_template('/barcode/report_condition_approval.html',result=result,
                                                        post_data=barcode_post,
                                                        rem_post=rem_post,
                                                        project_all=project_all)

@barcode.route('/<username>/<int:post_id>/<int:rem_post_id>/approve_report_condition')
@login_required
def approve_report_condition(username,post_id,rem_post_id):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)

    barcode_post=BarcodePost.query.get_or_404(post_id)
    remainder_post=Remainder_Itemcondition.query.get_or_404(rem_post_id)
    user_request=User.query.filter_by(username=remainder_post.remainder_user).first_or_404()
    barcode_post.item_condition=remainder_post.item_condition
    barcode_post.date_created=remainder_post.remainder_date
    barcode_post.created_by=user_request.username
    db.session.commit()
    flash('You have successfully approve the item condition','success')
    return redirect(url_for('barcode.history_qrcode_user',post_id=barcode_post.id))

@barcode.route('/<username>/<int:post_id>/<int:rem_post_id>/report_condition_decline',methods=['GET','POST'])
@login_required
def report_condition_decline(username,post_id,rem_post_id):
    user_init=User.query.filter_by(username=username).first_or_404()
    if user_init != current_user:
        abort(403)
    barcode_post=BarcodePost.query.get_or_404(post_id)
    remainder_post=Remainder_Itemcondition.query.get_or_404(rem_post_id)
    receipt_user=User.query.filter(User.username==remainder_post.remainder_user).first()
    if request.method=='POST':
        user_message_ap=request.form.get('txt_message')
        if user_message_ap=='':
            flash('Please type the reason for rejection','danger')
            return redirect(url_for('barcode.report_condition_approval',username=user_init.username,
                                                                   post_id=barcode_post.id,
                                                                   post_rem_id=remainder_post.id))
        ########Message########################################
        user_status_ap='unread'
        user_flag_ap=''
        user_title_ap='{} Item Condition Request Decline'.format(barcode_post.item_add)
        msg = Message(author=current_user, recipient=receipt_user,
                        body_message=user_message_ap,
                        body_title=user_title_ap,
                        body_flag=user_flag_ap,
                        body_trans='default',
                        body_date=remainder_post.remainder_date,
                        body_id=barcode_post.id,
                        body_sheet='default',
                        body_status=user_status_ap)
        db.session.add(msg)
        db.session.commit()
        ######send email to user for verification###########
        message_email=request.form.get('txt_message')
        body_html=render_template('mail/user/reminder.html',user=receipt_user,message_email=message_email)
        body_text=render_template('mail/user/reminder.txt',user=receipt_user,message_email=message_email)
        body_title='{} Item Condition Request Decline'.format(barcode_post.item_add)
        email(receipt_user.email,body_title,body_html,body_text)
        ######send email to user for verification###########
        flash('You have successfully decline the item condition ammendment','success')
        return redirect(url_for('barcode.history_qrcode_user',post_id=barcode_post.id))
    return redirect(url_for('barcode.history_qrcode_user',post_id=barcode_post.id))
#########################################################################################
@barcode.route('/<username>/<int:post_id>/<int:post_rem_id>/inventory_user_request_ack',methods=['GET','POST'])
@login_required
def inventory_user_request_ack(username,post_id,post_rem_id):
    user_default=User.query.filter_by(username=username).first_or_404()
    if user_default != current_user:
        abort(403)
    barcode_post=BarcodePost.query.get_or_404(post_id)
    rem_post=Remainder_Barcode.query.get_or_404(post_rem_id)
    user=User.query.filter(User.username==barcode_post.created_by).first()
    if request.method=='POST':
        inv_request_date_ack=request.form.get('inv_request_date_ack')
        condition_item=request.form.get('condition_item')
        if inv_request_date_ack=='' or condition_item=='':
            flash('Select the form correctly','danger')
            return redirect(url_for('barcode.indpost_qrcode_ack',username=current_user.username,
                                                                post_id=barcode_post.id,
                                                                post_rem_id=rem_post.id))
        date_request_in=datetime.datetime.strptime(inv_request_date_ack,'%d/%m/%Y')
        ########Update qrcode status###########
        barcode_post.date_created = datetime.datetime.strptime(inv_request_date_ack,'%d/%m/%Y')
        barcode_post.location_item=rem_post.remainder_location
        barcode_post.created_by=rem_post.remainder_user
        barcode_post.item_condition=condition_item
        db.session.commit()
    ##########History Login Status#############
        history_data=History_Barcode(date_update=datetime.datetime.today(),user_update=current_user.username,
                                    update_status='Issue',barcode_id=barcode_post.id,
                                    update_location=barcode_post.location_item,
                                    update_serialnum=barcode_post.item_serial_num,
                                    update_item=barcode_post.item_add,
                                    update_cond=barcode_post.item_condition,
                                    update_item_code=barcode_post.item_code_add)
        db.session.add(history_data)
        db.session.commit()
        ######Remainder Status#######
        rem_post.remainder_status='null'
        db.session.commit()
        ######################################
        flash('You have successfully declare the item borrowed','success')
        return redirect(url_for('barcode.history_qrcode_user',post_id=post_id))

@barcode.route('/<username>/<int:post_id>/<int:rem_post_id>/approve_inventory_transfer')
@login_required
def approve_inventory_transfer(username,post_id,rem_post_id):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    barcode_post=BarcodePost.query.get_or_404(post_id)
    remainder_post=Remainder_Barcode.query.get_or_404(rem_post_id)
    user_request=User.query.filter_by(username=remainder_post.remainder_user).first_or_404()
    remainder_post.remainder_status='approve'
    db.session.commit()
    ##########History Login Status#############
    history_data=History_Barcode(date_update=datetime.datetime.today(),user_update=current_user.username,
                                update_status='Approve',barcode_id=barcode_post.id,
                                update_location=remainder_post.remainder_location,
                                update_serialnum=barcode_post.item_serial_num,
                                update_item=barcode_post.item_add,
                                update_cond=barcode_post.item_condition,
                                update_item_code=barcode_post.item_code_add)
    db.session.add(history_data)
    db.session.commit()
    #######Message#####################
    user_message_ap='Hi {}! Your request for {} item has been accepted on {}. Please issue item on time'.format(user_request.firstname,
                                                                                                                 barcode_post.item_serial_num,
                                                                                                                 remainder_post.remainder_date.strftime('%d/%m/%Y'))
    user_status_ap='unread'
    user_flag_ap=''
    user_title_ap='{} Request Accepted'.format(barcode_post.item_add)
    msg = Message(author=current_user, recipient=user_request,
                    body_message=user_message_ap,
                    body_title=user_title_ap,
                    body_flag=user_flag_ap,
                    body_trans='inventory_request',
                    body_id=barcode_post.id,
                    body_date=remainder_post.remainder_date,
                    body_sheet='default',
                    body_status=user_status_ap)
    db.session.add(msg)
    db.session.commit()
    ######send email to user for verification###########
    message_email='Your request for {} item has been accepted on {}. Please issue item on time.'.format(barcode_post.item_serial_num,
                                                                                                    remainder_post.remainder_date.strftime('%d/%m/%Y'))
    body_html=render_template('mail/user/reminder.html',user=user_request,message_email=message_email)
    body_text=render_template('mail/user/reminder.txt',user=user_request,message_email=message_email)
    body_title='{} Request Accepted'.format(barcode_post.item_add)
    email(user_request.email,body_title,body_html,body_text)
    ######send email to user for verification###########
    flash('You have successfully approve the item transfer','success')
    return redirect(url_for('employees.dashboard'))

@barcode.route('/<username>/<int:post_id>/<int:rem_post_id>/inventory_user_decline',methods=['GET','POST'])
@login_required
def inventory_user_decline(username,post_id,rem_post_id):
    user_init=User.query.filter_by(username=username).first_or_404()
    if user_init != current_user:
        abort(403)
    barcode_post=BarcodePost.query.get_or_404(post_id)
    remainder_post=Remainder_Barcode.query.get_or_404(rem_post_id)
    remainder_post.remainder_status='reject'
    db.session.commit()
    receipt_user=User.query.filter(User.username==remainder_post.remainder_user).first()
    if request.method=='POST':
        user_message_ap=request.form.get('txt_message')
        if user_message_ap=='':
            flash('Please type the reason for rejection','danger')
            return redirect(url_for('barcode.qrcode_user_approval',username=user_init.username,
                                                                   post_id=barcode_post.id,
                                                                   post_rem_id=remainder_post.id))
        ##########History Login Status#############
        history_data=History_Barcode(date_update=datetime.datetime.today(),user_update=current_user.username,
                                    update_status='Reject',barcode_id=barcode_post.id,
                                    update_location=remainder_post.remainder_location,update_serialnum=barcode_post.item_serial_num,
                                    update_item=barcode_post.item_add,update_cond=barcode_post.item_condition,
                                    update_item_code=barcode_post.item_code_add)
        db.session.add(history_data)
        db.session.commit()
        ########Message########################################
        user_status_ap='unread'
        user_flag_ap=''
        user_title_ap='{} Request Decline'.format(barcode_post.item_add)
        msg = Message(author=current_user, recipient=receipt_user,
                        body_message=user_message_ap,
                        body_title=user_title_ap,
                        body_flag=user_flag_ap,
                        body_trans='inventory_request',
                        body_date=remainder_post.remainder_date,
                        body_id=barcode_post.id,
                        body_sheet='default',
                        body_status=user_status_ap)
        db.session.add(msg)
        db.session.commit()
        ######send email to user for verification###########
        message_email=user_message_ap
        body_html=render_template('mail/user/reminder.html',user=receipt_user,message_email=message_email)
        body_text=render_template('mail/user/reminder.txt',user=receipt_user,message_email=message_email)
        body_title='{} Request Decline'.format(barcode_post.item_add)
        email(receipt_user.email,body_title,body_html,body_text)
        ######send email to user for verification###########
        flash('You have successfully decline the item transfer','success')
        return redirect(url_for('employees.dashboard'))
    return redirect(url_for('employees.dashboard'))

######Sending request for accept or reject to the user####################
@barcode.route('/<username>/<int:post_id>/<int:post_rem_id>/qrcode_user_approval')
@login_required
def qrcode_user_approval(username,post_id,post_rem_id):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    barcode_post=BarcodePost.query.get_or_404(post_id)
    rem_post=Remainder_Barcode.query.get_or_404(post_rem_id)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    qrgen_code = qrcode.QRCode(version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,border=0,)
    qrgen_code.add_data(barcode_post.item_serial_num)
    qrgen_code.make(fit=True)
    pil_img = qrgen_code.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    test_img=pil_img
    img_io.seek(0)
    img_str = base64.b64encode(img_io.getvalue())
    image_bytes = io.BytesIO(base64.b64decode(img_str))
    im = Image.open(image_bytes)
    decodedObjects = pyzbar.decode(im)
    encode_barcodedata = []
    for obj in decodedObjects:
        encode_barcodedata.append({"code":obj.data.decode('utf-8') ,
                                    "type": obj.type})
    result = base64.b64encode(img_io.getvalue()).decode('ascii')
    return render_template('/barcode/qrcode_user_approval.html',result=result,
                                                        post_data=barcode_post,
                                                        rem_post=rem_post,
                                                        project_all=project_all)

@barcode.route('/<username>/<int:post_id>/<int:post_rem_id>/indpost_qrcode_ack')
@login_required
def indpost_qrcode_ack(username,post_id,post_rem_id):
    user_default=User.query.filter_by(username=username).first_or_404()
    if user_default != current_user:
        abort(403)
    barcode_post=BarcodePost.query.get_or_404(post_id)
    rem_post=Remainder_Barcode.query.get_or_404(post_rem_id)
    condition_all=Condition_Add.query.all()
    qrgen_code = qrcode.QRCode(version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,border=0,)
    qrgen_code.add_data(barcode_post.item_serial_num)
    qrgen_code.make(fit=True)
    pil_img = qrgen_code.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    test_img=pil_img
    img_io.seek(0)
    img_str = base64.b64encode(img_io.getvalue())
    image_bytes = io.BytesIO(base64.b64decode(img_str))
    im = Image.open(image_bytes)
    decodedObjects = pyzbar.decode(im)
    encode_barcodedata = []
    for obj in decodedObjects:
        encode_barcodedata.append({"code":obj.data.decode('utf-8') ,
                                    "type": obj.type})
    result = base64.b64encode(img_io.getvalue()).decode('ascii')
    return render_template('/barcode/indpost_qrcode_ack.html',result=result,
                                                        post_data=barcode_post,
                                                        rem_post=rem_post,
                                                        condition_all=condition_all)
@barcode.route('/decode',methods=['POST','GET'])
@login_required
def decode():
    if request.method=='POST':
        input_decode=request.form['imgBase64']
        imgstr = re.search(r'base64,(.*)', input_decode).group(1)
        image_bytes = io.BytesIO(base64.b64decode(imgstr))
        im = Image.open(image_bytes)
        arr = np.array(im)[:, :, 0]
        decodedObjects = pyzbar.decode(arr)
        decode_barcodedata = []
        for obj in decodedObjects:
            #print('Type : ', obj.type)
            #print('Data : ', obj.data, '\n')
            decode_barcodedata.append({
                "code":obj.data.decode('utf-8')})
        #if decode_barcodedata:
        #    return jsonify(decode_barcodedata)
        if decode_barcodedata:
            user_codedata[current_user.username]={'decode_codedata':decode_barcodedata}
            return redirect(url_for('barcode.extract_qcode',username=current_user.username))
        return  jsonify({"code":'NO BarCode Found'})

@barcode.route('/barcode_decode_user')
@login_required
def barcode_decode_user():
    return render_template('/barcode/barcode_decode_user.html')

@barcode.route('/<username>/extract_qcode')
@login_required
def extract_qcode(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    condition_all=Condition_Add.query.all()
    user_all=User.query.filter(User.user_status=='active').filter(User.is_author==True).order_by(User.username)
    code_data=user_codedata[user.username]['decode_codedata']
    qcode_extract=str(code_data[0]['code'])
    post_data=BarcodePost.query.filter(BarcodePost.unique_qrcode==qcode_extract).first()
    if post_data is None:
        flash('Please try again','danger')
        return redirect(url_for('barcode.barcode_decode_user'))
    #####Qrgeneration Code##############################
    qrgen_code = qrcode.QRCode(version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,border=0,)

    qrgen_code.add_data(post_data.unique_qrcode)
    qrgen_code.make(fit=True)
    pil_img = qrgen_code.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    test_img=pil_img
    img_io.seek(0)
    result = base64.b64encode(img_io.getvalue()).decode('ascii')
    return render_template('/barcode/extract_qcode.html',post_data=post_data,project_all=project_all,
                                                         result=result,user_all=user_all,
                                                         condition_all=condition_all)

@barcode.route('/<username>/history_view_all')
@login_required
def history_view_all(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    user_all=User.query.order_by(User.username).all()
    page = request.args.get('page', 1, type=int)
    post_submit=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    post_history=History_Barcode.query.order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
    post_barcode=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    post_history_count=History_Barcode.query.order_by(History_Barcode.date.desc())
    #####Random Color Generation#########
    count_h=0
    for post_init_h in post_history_count:
        count_h=count_h+1
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_h):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
        #r = lambda: random.randint(0,255)
        #color_r = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
    return render_template('/barcode/history_view_all.html',post_data=post_submit,project_all=project_all,
                                                              color_all=color_all,user_all=user_all,
                                                              post_history=post_history,post_barcode=post_barcode)
##############Inventory Selection #####################################
@barcode.route('/view_inventory_history_all_selection',methods=['POST','GET'])
@login_required
def view_inventory_history_all_selection():
    if request.method=='POST':
        user_get=request.form.get('user_select')
        model_select=request.form.get('model_select')
        desp_select=request.form.get('desp_select')
        page = request.args.get('page', 1, type=int)
        if user_get!='':
            post_submit=History_Barcode.query.filter(History_Barcode.user_update==user_get)\
                                                .order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
        elif model_select!='':
            post_submit=History_Barcode.query.filter(History_Barcode.update_location==model_select)\
                                                .order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
        elif desp_select!='':
            post_submit=History_Barcode.query.filter(History_Barcode.update_serialnum==desp_select)\
                                                .order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
        else:
            post_submit=History_Barcode.query.order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
    if request.method=='GET':
        page = request.args.get('page', 1, type=int)
        post_submit=History_Barcode.query.order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
    user_all=User.query.order_by(User.username).all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    post_default=History_Barcode.query.order_by(History_Barcode.date.desc())
    post_barcode=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    #########################
    count_all=0
    for post_init in post_default:
        count_all=count_all+1
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/barcode/history_view_all.html',post_history=post_submit,project_all=project_all,
                                                            post_barcode=post_barcode,
                                                            color_all=color_all,user_all=user_all)
#####################################################################################################
##############Inventory Selection #####################################
@barcode.route('/<int:post_log_id>/view_inventory_logstatus_selection')
@login_required
def view_inventory_logstatus_selection(post_log_id):
    post_check=History_Barcode.query.get_or_404(post_log_id)
    page = request.args.get('page', 1, type=int)
    post_submit=History_Barcode.query.filter(History_Barcode.update_serialnum==post_check.update_serialnum)\
                                        .order_by(History_Barcode.date.desc()).paginate(page=page, per_page=25)
    user_all=User.query.order_by(User.username).all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    post_default=History_Barcode.query.order_by(History_Barcode.date.desc())
    post_barcode=BarcodePost.query.order_by(BarcodePost.date_created.desc())
    count_all=0
    for post_init in post_default:
        count_all=count_all+1
    color_all=[]
    color_choice=['red','yellow','blue','green','pink','orange','brown','purple']
    for random_count in range(count_all):
        color_r=random.choice(color_choice)
        color_all.append(color_r)
    return render_template('/barcode/history_view_all.html',post_history=post_submit,project_all=project_all,
                                                            post_barcode=post_barcode,
                                                            color_all=color_all,user_all=user_all)
####################################################################################################

############Barcode Inventory from Existing Barcode Reader##########################################
@barcode.route('/create_inventory_qrcodereader')
@login_required
def create_inventory_qrcodereader():
    return render_template('/barcode/create_inventory_qrcodereader.html')

@barcode.route('/decode_inventory_reader',methods=['POST','GET'])
@login_required
def decode_inventory_reader():
    if request.method=='POST':
        input_decode=request.form['imgBase64']
        imgstr = re.search(r'base64,(.*)', input_decode).group(1)
        image_bytes = io.BytesIO(base64.b64decode(imgstr))
        im = Image.open(image_bytes)
        arr = np.array(im)[:, :, 0]
        decodedObjects = pyzbar.decode(arr)
        decode_barcodedata = []
        for obj in decodedObjects:
            #print('Type : ', obj.type)
            #print('Data : ', obj.data, '\n')
            decode_barcodedata.append({
                "code":obj.data.decode('utf-8')})
        #if decode_barcodedata:
        #    return jsonify(decode_barcodedata)
        if decode_barcodedata:
            user_codedata_reader[current_user.username]={'decode_codedata':decode_barcodedata}
            return redirect(url_for('barcode.extract_qcode_reader',username=current_user.username))
        return  jsonify({"code":'NO BarCode Found'})

@barcode.route('/<username>/extract_qcode_reader')
@login_required
def extract_qcode_reader(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)

    code_data=user_codedata_reader[user.username]['decode_codedata']
    qcode_extract=str(code_data[0]['code'])
    qrgen_code = qrcode.QRCode(version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,border=0,)

    qrgen_code.add_data(code_data)
    qrgen_code.make(fit=True)
    pil_img = qrgen_code.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    test_img=pil_img
    img_io.seek(0)
    result = base64.b64encode(img_io.getvalue()).decode('ascii')
    return render_template('/barcode/extract_qcode_reader.html',result=result)

@barcode.route('/<username>/create_inventory_reader_step1',methods=['GET','POST'])
@login_required
def create_inventory_reader_step1(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    #######Check if Qrcode Already Exists in the Database############
    code_data=user_codedata_reader[user.username]['decode_codedata']
    qcode_extract=str(code_data[0]['code'])
    post_check_unique=BarcodePost.query.filter(BarcodePost.unique_qrcode==qcode_extract).first()
    if post_check_unique is not None:
        flash('Inventory already exists with item serial no. {} with the following Qrcode code. Scan another Qrcode'.format(post_check_unique.item_serial_num),'danger')
        return redirect(url_for('barcode.create_inventory_qrcodereader'))
    percent_job=round(((1/2)*100),1)
    asset_all=Asset_Add.query.all()
    item_all=Item_Add.query.all()
    project_all=Project_Add.query.filter(Project_Add.project_archieve=='default')
    condition_all=Condition_Add.query.all()
    if request.method=='POST':
        item_add_init=request.form.get('item_add')
        item_other=request.form.get('item_other')
        asset_add=request.form.get('asset_add')
        asset_other=request.form.get('asset_other')
        item_condition=request.form.get('condition_item')
        location_item=request.form.get('location_item')
        asset_other=asset_other.lower()
        item_other=item_other.lower()
        #####Check Form Validation#########
        if location_item=='' or item_condition is None:
            flash('Please select the choices','danger')
            return redirect(url_for('barcode.create_inventory_step1',username=user.username))
        if (item_add_init=='' and item_other=='') or (item_add_init!='' and item_other!=''):
            flash('Please select only one item choices','danger')
            return redirect(url_for('barcode.create_inventory_step1',username=user.username))
        if (asset_add=='' and asset_other=='') or (asset_add!='' and asset_other!=''):
            flash('Please select item choices','danger')
            return redirect(url_for('barcode.create_inventory_step1',username=user.username))
        #################################################
        if item_other!='':
            product_init=Item_Add.query.filter(Item_Add.item_add==item_other).first()
            if product_init is not None:
                flash('Item has been already added','danger')
                return redirect(url_for('barcode.create_inventory_step1',username=user.username))
            item_add_init=item_other
            item_create = Item_Add(item_add=item_add_init,item_key_gen=int(0))
            db.session.add(item_create)
            db.session.commit()
        if asset_other!='':
            asset_init=Asset_Add.query.filter(Asset_Add.asset_add==asset_other).first()
            if asset_init is not None:
                flash('Asset has been already added','danger')
                return redirect(url_for('barcode.create_inventory_step1',username=user.username))
            asset_add=asset_other
            asset_create = Asset_Add(asset_add=asset_add)
            db.session.add(asset_create)
            db.session.commit()
        ###################################
        created_by=user.username
        user_barcode_data_reader[user.username]={'item_add':item_add_init,
                                          'item_condition':item_condition,
                                          'asset_add':asset_add,
                                          'location_item':location_item,
                                          'created_by':created_by,
                                          'unique_qrcode':qcode_extract
                                          }
        return redirect(url_for('barcode.create_inventory_reader_step2',username=user.username))
    return render_template('barcode/create_inventory_reader_step1.html',percent_job=percent_job,
                                                                   item_all=item_all,
                                                                   project_all=project_all,
                                                                   asset_all=asset_all,
                                                                   condition_all=condition_all)
@barcode.route('/<username>/create_inventory_reader_step2',methods=['GET','POST'])
@login_required
def create_inventory_reader_step2(username):
    user=User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    percent_job=round(((2/2)*100),1)
    vendor_all=Vendor_Add.query.all()
    if request.method=='POST':
        vendor_add=request.form.get('vendor_add')
        vendor_other=request.form.get('vendor_other')
        vendor_other=vendor_other.lower()
        part_number=request.form.get('part_number')
        item_desp=request.form.get('item_desp')
        user_id=current_user.id
        if (vendor_add=='' and vendor_other=='') or (vendor_add!='' and vendor_other!=''):
            flash('Please select only one vendor choices','danger')
            return redirect(url_for('barcode.create_inventory_step2',username=user.username))
        if vendor_other!='':
            vendor_init=Vendor_Add.query.filter(Vendor_Add.vendor_add==vendor_other).first()
            if vendor_init is not None:
                flash('Vendor has been already added','danger')
                return redirect(url_for('barcode.create_inventory_step2',username=user.username))
            vendor_add=vendor_other
            vendor_create = Vendor_Add(vendor_add=vendor_add)
            db.session.add(vendor_create)
            db.session.commit()
        item_add=user_barcode_data_reader[user.username]['item_add']
        item_condition=user_barcode_data_reader[user.username]['item_condition']
        asset_add=user_barcode_data_reader[user.username]['asset_add']
        location_item=user_barcode_data_reader[user.username]['location_item']
        created_by=user_barcode_data_reader[user.username]['created_by']
        unique_qrcode=user_barcode_data_reader[user.username]['unique_qrcode']
        date_created=datetime.datetime.today()
        #####Key Generation#############################################
        if  item_add.count(' ')==0 or item_add.count(' ')==1:
            item_code_add_serial=item_add[:3].upper()
            item_code_add=item_code_add_serial[:3]

        else:
            item_code_add_serial = ''.join([s[:1].upper() for s in item_add.split(' ')])
            item_code_add=item_code_add_serial[:3]
        #item_key_init=KeyGen_Add.query.get(1)
        item_key_init=Item_Add.query.filter(Item_Add.item_add==item_add).first()
        if item_key_init is not None:
            item_key=item_key_init.item_key_gen+int(1)
            item_key_init.item_key_gen=item_key
            db.session.commit()
        else:
            item_key=KeyGen_Add(key_gen=int(1))
            db.session.add(item_key)
            db.session.commit()
        keygen_item=str(item_key).zfill(4)
        item_serial_num=item_code_add_serial + '-' + keygen_item
        date_requested_update=date_created-datetime.timedelta(365)
        ################################################################
        barcode_data=BarcodePost(item_add=item_add,item_condition=item_condition,
                                item_serial_num=item_serial_num,date_created=date_created,
                                asset_add=asset_add,location_item=location_item,user_id=user_id,
                                created_by=created_by,vendor_add=vendor_add,
                                part_number=part_number,item_desp=item_desp,
                                item_code_add=item_code_add,unique_qrcode=unique_qrcode)
        db.session.add(barcode_data)
        db.session.commit()
        ########################################
        item_post_id=BarcodePost.query.filter(and_(BarcodePost.item_serial_num==item_serial_num,BarcodePost.date_created==date_created)).first()
        ###############History Add####################################
        history_data=History_Barcode(date_update=date_created,user_update=created_by,
                                    update_status='Issue',barcode_id=item_post_id.id,
                                    update_location=location_item,update_serialnum=item_serial_num,
                                    update_item=item_add,update_cond=item_condition,
                                    update_item_code=item_code_add)
        db.session.add(history_data)
        db.session.commit()
        return redirect(url_for('barcode.view_inventory_all',username=user.username))
    return render_template('/barcode/create_inventory_reader_step2.html',percent_job=percent_job,
                                                                  vendor_all=vendor_all)
###########################################################################


@barcode.route('/test_site_site')
def test_site_site():
    return render_template('/barcode/test6.html')
