import itertools
import json
import os
import re
from uuid import uuid4

from flask import Blueprint, jsonify
from flask import current_app
from flask import request
from sqlalchemy.sql.expression import func
from werkzeug.utils import secure_filename

from authorization.authorization import token_check
from authorization.models import User
from ext import db
from helpers import allowed_file
from .models import Announcement, ImagesAnnoun, Category, RecentlyViewed, TypeClose, ReasonClose, Want
from .schema import AnnouncementSchema, AnnouncementImageSchema, RecentlyViewedSchema, TypeCloseSchema, \
    ReasonCloseSchema, ClosedSchema, AllCategorySchema, WantSchema

home_api = Blueprint('api', __name__)


@home_api.route('/create_annotation', methods=['POST'])
@token_check
def create_announcement(token):
    files = request.files.getlist('files')
    data = json.loads(request.form['request'])

    image_schema = AnnouncementImageSchema()
    print(1, token)
    getted_user = User.query.filter(User.token == token).one()

    data['user'] = getted_user.id

    announ_schema = AnnouncementSchema()
    announcement = announ_schema.load(data=data)

    db.session.add(announcement)
    db.session.flush()
    id = announcement.id
    db.session.commit()

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            extension = filename.split()[-1]
            new_filename = "upload-{}.{}".format(
                uuid4(), extension
            )

            file.save(os.path.join(current_app.config['UPLOAD_FOLDER_ANNOUN'], new_filename))
            img_data = {
                "image_path": f'/images/announcement/{new_filename}',
                "announcement": id
            }
            db_image = image_schema.load(img_data)
            db.session.add(db_image)
            db.session.commit()

    return {
               "result": True
           }, 200


@home_api.route('/update_annotation/<id>', methods=['POST'])
@token_check
def update_annotation(token, id):
    files = request.files.getlist('files')
    request_data = json.loads(request.form['request'])
    image_schema = AnnouncementImageSchema()
    getted_user = User.query.filter(User.token == token).one()

    request_data['user'] = getted_user.id
    request_data['id'] = id
    announ_schema = AnnouncementSchema()
    announcement = announ_schema.load(data=request_data)
    db.session.add(announcement)
    db.session.flush()
    id = announcement.id
    db.session.commit()
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            extension = filename.split()[-1]
            new_filename = "upload-{}.{}".format(
                uuid4(), extension
            )

            file.save(os.path.join(current_app.config['UPLOAD_FOLDER_ANNOUN'], new_filename))
            img_data = {
                "image_path": f'/images/announcement/{new_filename}',
                "announcement": id
            }
            db_image = image_schema.load(img_data)
            db.session.add(db_image)
            db.session.commit()

    return {
               "result": True
           }, 200


@home_api.route('/delete_img_annotation/<id>', methods=['POST'])
@token_check
def delete_img_annotation(token, id):
    try:
        image_path = request.json['image_path']
    except KeyError:
        return {
                   "result": False
               }, 500
    db.session.query(ImagesAnnoun).filter(ImagesAnnoun.announcement == id).filter(
        ImagesAnnoun.image_path == image_path).delete()
    db.session.commit()

    full_path = current_app.config['PROJECT_HOME'] + image_path

    if os.path.exists(full_path):
        os.remove(full_path)
    else:
        print("The file does not exist")

    return {
               "result": True
           }, 200


@home_api.route('/my_announcements/all_active', methods=['GET'])
@token_check
def all_announcements(token):
    getted_user = User.query.filter(User.token == token).one()
    all_announ = Announcement.query.filter(Announcement.user == getted_user.id, Announcement.delete == False,
                                           Announcement.saled == False).all()
    announcement_schema = AnnouncementSchema()
    all = announcement_schema.dump(all_announ, many=True)

    return {
               "announcement": all}, 200


@home_api.route('/my_announcements/closed', methods=['GET'])
@token_check
def closed_announcements(token):
    getted_user = User.query.filter(User.token == token).one()
    all_announ = Announcement.query.filter(Announcement.user == getted_user.id, Announcement.delete != None).all()
    announcement_schema = AnnouncementSchema()
    all = announcement_schema.dump(all_announ, many=True)

    return {
               "announcement": all}, 200


@home_api.route('/my_announcements/saled', methods=['GET'])
@token_check
def saled_announcements(token):
    getted_user = User.query.filter(User.token == token).one()
    all_announ = Announcement.query.filter(Announcement.user == getted_user.id, Announcement.saled == True).all()
    announcement_schema = AnnouncementSchema()
    all = announcement_schema.dump(all_announ, many=True)

    return {
               "announcement": all}, 200


@home_api.route('/search_announcements', methods=['GET'])
@token_check
def search_announcements(token):
    getted_user = User.query.filter(User.token == token).one()
    filters = list()

    filter_category = Announcement.query.filter(Announcement.category == request.args.get('category'),
                                                Announcement.reason_id == None, Announcement.user != getted_user.id ).filter().subquery()
    if request.args.get('category'):
        filters.append(Announcement.category == filter_category.c.category)

    filter_exchange = Announcement.query.filter(Announcement.no_exchange == request.args.get('exchange'),
                                                Announcement.reason_id == None, Announcement.user != getted_user.id).filter().subquery()
    if request.args.get('exchange'):
        filters.append(Announcement.no_exchange == filter_exchange.c.no_exchange)

    filter_city = Announcement.query.filter(Announcement.city == request.args.get('city'),
                                            Announcement.reason_id == None, Announcement.user != getted_user.id).filter().subquery()
    if request.args.get('city'):
        filters.append(Announcement.city == filter_city.c.city)

    filter_address = Announcement.query.filter(Announcement.address == request.args.get('address'),
                                               Announcement.reason_id == None, Announcement.user != getted_user.id).filter().subquery()
    if request.args.get('address'):
        filters.append(Announcement.address == filter_address.c.address)
    description = Announcement.query.filter(Announcement.description.ilike('%' + request.args.get('query') + '%'),
                                            Announcement.reason_id == None, Announcement.user != getted_user.id, *filters).all()
    name = Announcement.query.filter(Announcement.name.ilike('%' + request.args.get('query') + '%'),
                                     Announcement.reason_id == None, Announcement.user != getted_user.id, *filters).all()
    all_announs = list(set(description + name))
    announcement_schema = AnnouncementSchema()
    all = announcement_schema.dump(all_announs, many=True)
    return {
               "announcement": all}, 200


@home_api.route('/all_categories', methods=['GET'])
def all_categories():
    query = Category.query.all()
    print(query)
    category_schema = AllCategorySchema()
    all = category_schema.dump(query, many=True)
    return {
               "category": all}, 200


@home_api.route('/get_announcement/<id>', methods=['GET'])
@token_check
def get_announcement(token, id):
    getted_user = User.query.filter(User.token == token).one()
    announ = Announcement.query.get(id)
    announcement_schema = AnnouncementSchema()
    announ_dump = announcement_schema.dump(announ)
    if getted_user.id == announ.user:
        return jsonify(announ_dump), 200
    else:
        recently = RecentlyViewed(user=getted_user.id, announcement=announ.id)
        db.session.add(recently)
        db.session.commit()
        return jsonify(announ_dump), 200


@home_api.route('/get_closed_users_announcement/<id>', methods=['GET'])
def get_closed_users_announcement(id):
    announ = Announcement.query.filter(Announcement.user == id, Announcement.reason_id != None).all()
    announcement_schema = AnnouncementSchema()
    announ_dump = announcement_schema.dump(announ, many=True)
    return { "announcement": all}, 200



@home_api.route('/get_users_announcement/<id>', methods=['GET'])
def get_users_announcement(id):
    announ = Announcement.query.filter(Announcement.user == id, Announcement.reason_id == None).all()
    announcement_schema = AnnouncementSchema()
    announ_dump = announcement_schema.dump(announ, many=True)

    return { "announcement": announ_dump}, 200


@home_api.route('/announcements_from_category/<id>', methods=['GET'])
@token_check
def announcements_from_category(token, id):
    announ = Announcement.query.filter(Announcement.category == id).filter(Announcement.saled != True).filter(
        Announcement.delete != True)
    announcement_schema = AnnouncementSchema()
    announ_dump = announcement_schema.dump(announ, many=True)
    return jsonify(announ_dump), 200


@home_api.route('/recently_viewed', methods=['GET'])
@token_check
def recently_viewed(token):
    getted_user = User.query.filter(User.token == token).one()
    announcments_disctinct = RecentlyViewed.query.filter(RecentlyViewed.user == getted_user.id).distinct(
        RecentlyViewed.announcement).subquery()
    announcments = RecentlyViewed.query.filter(RecentlyViewed.id == announcments_disctinct.c.id).order_by(
        RecentlyViewed.created.desc()).limit(10)
    announcement_schema = RecentlyViewedSchema()
    announ_dump = announcement_schema.dump(announcments, many=True)
    return jsonify(announ_dump), 200


@home_api.route('/recommendation_from_r_v', methods=['GET'])
@token_check
def recommendation_from_r_v(token):
    getted_user = User.query.filter(User.token == token).one()
    recently_viewed = RecentlyViewed.query.filter(RecentlyViewed.user == getted_user.id).distinct(
        RecentlyViewed.announcement).subquery()
    get_announcements = Announcement.query.filter(Announcement.id == recently_viewed.c.announcement).subquery()
    recommendation = Announcement.query.filter(Announcement.category == get_announcements.c.category,
                                               Announcement.user != getted_user.id).order_by(func.random()).limit(10)
    announcement_schema = AnnouncementSchema()
    announ_dump = announcement_schema.dump(recommendation, many=True)
    return jsonify(announ_dump), 200


@home_api.route('/type_close', methods=['GET'])
@token_check
def type_close(token):
    query = TypeClose.query.all()
    type_schema = TypeCloseSchema()
    type_dump = type_schema.dump(query, many=True)
    return jsonify(type_dump), 200


@home_api.route('/reason_close', methods=['GET'])
@token_check
def reason_close(token):
    query = ReasonClose.query.all()
    type_schema = ReasonCloseSchema()
    type_dump = type_schema.dump(query, many=True)
    return jsonify(type_dump), 200


@home_api.route('/close_announcement/<id>', methods=['POST'])
@token_check
def close_deal(token, id):
    try:
        announ = Announcement.query.get(id)
        request_data = request.get_json()
        schema = ClosedSchema()
        closed_schema = schema.load(data=request_data)
        db.session.add(closed_schema)
        db.session.flush()
        id = closed_schema.id

        db.session.commit()

        announ.reason_id = id
        if closed_schema.type == 1:
            announ.saled = True
        else:
            announ.delete = True
        db.session.commit()

        return {
            'result': True}
    except:
        return {
            'result': False}


@home_api.route('/edit_want/<id>', methods=['POST'])
@token_check
def edit_want(token, id):
    request_data = request.get_json()
    request_data['id'] = id
    want_schema = WantSchema()
    want = want_schema.load(data=request_data)
    db.session.add(want)
    db.session.commit()
    return jsonify({
        "result": True
    }), 200


@home_api.route('/delete_want/<id>', methods=['DELETE'])
@token_check
def delete_want(token, id):
    want = Want.query.get(id)
    db.session.delete(want)
    db.session.commit()
    return jsonify({
        "result": True
    }), 200


@home_api.route('/wants_for_user/<id>', methods=['GET'])
@token_check
def wants_for_user(token, id):
    announs_user = Announcement.query.filter(Announcement.user == id).subquery()
    wants = Want.query.filter(Want.announcement == announs_user.c.id).all()
    wants_schema = WantSchema()
    wants_dump = wants_schema.dump(wants, many=True)
    return jsonify(wants_dump), 200


@home_api.route('/wants_for_current_user', methods=['GET'])
@token_check
def wants_for_current_user(token):
    user = User.query.filter(User.token == token).subquery()
    announs_user = Announcement.query.filter(Announcement.user == user.c.id).subquery()
    wants = Want.query.filter(Want.announcement == announs_user.c.id).all()
    wants_schema = WantSchema()
    wants_dump = wants_schema.dump(wants, many=True)
    return jsonify(wants_dump), 200


@home_api.route('/recommended_for_want/<id>', methods=['GET'])
@token_check
def recommended_for_want(token, id):
    user = User.query.filter(User.token == token).one()
    for_result = list()
    announ = Announcement.query.get(id)

    str = announ.str_want
    reg = re.compile('[^-zA-Z а-яА-Я]')
    words = reg.sub('', str)
    list_of_words = words.split(' ')
    for word in list_of_words:
        descr = Announcement.query.filter(Announcement.description.ilike('%' + word + '%'),
                                          Announcement.user != user.id).all()
        name = Announcement.query.filter(Announcement.name.ilike('%' + word + '%'), Announcement.user != user.id).all()
        all_announs = list(set(descr + name))
        for_result.append(all_announs)

    for_result = list(set(itertools.chain(*for_result)))
    announcement_schema = AnnouncementSchema()
    all = announcement_schema.dump(for_result, many=True)

    return jsonify({
        "result": all
    }), 200
