import datetime
import json
import os

from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from werkzeug.utils import secure_filename
from config import *
from settings import db
from utils import admin_required
from apriori import apriori
import models

b = Blueprint('back', __name__, template_folder='templates')


@b.route('/b')
def show():
    return 'hello'


@b.route('/user_manage')
@admin_required()
def user_manage():
    return render_template('user_manage.html')


@b.route('/users')
@admin_required()
def get_all_users():
    curr_page = request.args.get('curr_page')
    curr_page = 1 if curr_page is None else int(curr_page)
    users = models.User.query.limit(PAGE_SIZE).offset(
        (curr_page - 1) * PAGE_SIZE)
    res = []
    for i in users:
        res.append({'id': i.id, 'username': i.username, 'account': i.account,
                    'email': i.email, 'register_date': str(i.register_date),
                    'is_admin': i.is_admin, 'phone': i.phone, 'is_freeze': i.is_freeze})
    return jsonify(res)


@b.route('/give_admin', methods=['GET'])
@admin_required()
def give_admin():
    id = request.args.get('id')
    user = models.User.query.get(id)
    if user is None:
        return jsonify('user not exists')
    user.is_admin = True
    db.session.commit()
    return jsonify('success')


@b.route('/update_user', methods=['POST'])
@admin_required()
def update_user():
    email = request.form['email']
    phone = request.form['phone']
    username = request.form['username']
    password = request.form['password']
    id = request.form['id']
    if id is None:
        return 'id is none'

    user = models.User.query.get(id)
    if user is None:
        return jsonify('user not exists')

    user.email = email if email is not None else user.email
    user.phone = phone if phone is not None else user.phone
    user.password = user.hash_password(password) if password is not None else user.password
    user.username = username if username is not None else user.username
    db.session.commit()
    return jsonify('success')


@b.route('/del_user')
@admin_required()
def delete_user():
    account = request.args.get('account')

    u = models.User.query.filter(account == models.User.account).first()

    if u is None:
        return 'true'

    db.session.delete(u)
    db.session.commit()
    return 'true'


@b.route('/freeze_user')
@admin_required()
def freeze_user():
    _id = request.args.get('id')
    u = models.User.query.get(_id)

    if u is None:
        return 'user_not_exists'
    u.is_freeze = True
    db.session.commit()
    return 'success'


@b.route('/release_freeze')
@admin_required()
def release_freeze():
    _id = request.args.get('id')
    u = models.User.query.get(_id)

    if u is None:
        return 'success'
    u.is_freeze = False
    db.session.commit()
    return 'success'


@b.route('/pub_news', methods=['POST'])
@admin_required()
def publish_news():
    title = request.form['title']
    content = request.form['content']
    if title is None:
        return 'title is empty'
    n = models.News(title, content)
    n.user_id = current_user.id
    db.session.add(n)
    db.session.commit()
    return 'success'


@b.route('/del_news', methods=['GET'])
@admin_required()
def delete_news():
    _id = request.args.get('id')
    if _id is None:
        return 'id is empty'

    n = models.News.query.get(_id)
    db.session.delete(n)
    db.session.commit()
    return 'success'


@b.route('/update_movie', methods=['POST'])
@admin_required()
def update_movie():
    name = request.form['name']
    _id = request.form['id']
    actor = request.form['actor']
    director = request.form['director']
    genre = request.form['genre']

    movie = models.Movie.query.get(int(_id))
    if movie is None:
        return jsonify('success')

    movie.name = name if name is not None else movie.name
    movie.actor = actor if actor is not None else movie.actor
    movie.director = director if director is not None else movie.director
    movie.genre = genre if genre is not None else movie.genre

    db.session.commit()

    return jsonify('success')


@b.route('/del_movie')
@admin_required()
def del_movie():
    _id = request.args.get('id')
    movie = models.Movie.query.get(_id)
    if movie is None:
        return jsonify('success')

    try:
        # 删除电影，同时删除电影之下的评论，收藏下的电影，movie_cat_re,movie_eva,user_collection
        # 删除评论
        evas = models.MovieEva.query.filter(models.MovieEva.movie_id == id).all()
        for i in evas:
            db.session.delete(i)
        # 删除包含该分类的电影
        cat = models.MovieCatRe.query.filter(models.MovieCatRe.movie_id == id).all()
        for c in cat:
            db.session.delete(c)

        # 删除用户收藏的电影
        uc = models.UserCollection.query.filter(models.UserCollection.movie_id == id).all()
        for u in uc:
            db.session.delete(u)
        # 删除电影本身
        db.session.delete(movie)

        db.session.commit()

    except:
        return jsonify('error')
    return jsonify('success')


@b.route('/del_guest', methods=['GET'])
@admin_required()
def del_guest():
    _id = request.args.get('id')
    g = models.GuestBook.query.filter(_id == models.GuestBook.id).first()
    if g is None:
        return jsonify('success')
    db.session.delete(g)
    db.session.commit()
    return jsonify('success')


@b.route('/movie_manage')
@admin_required()
def movie_manage():
    return render_template('movieManage.html')


@b.route('/movie_category')
@admin_required()
def get_all_category():
    c = models.MovieCategory.query.order_by(db.desc(models.MovieCategory.create_date)).all()
    res = [{'id': i.id, 'create_date': str(i.create_date),
            'category': i.category, 'desc': i.desc} for i in c]
    return jsonify(res)


@b.route('/create_category', methods=['POST'])
@admin_required()
def create_category():
    c = request.form['category']
    desc = request.form['desc']
    category = models.MovieCategory(c, desc)
    db.session.add(category)
    db.session.commit()
    return jsonify('success')


@b.route('/movies_from_category')
@admin_required()
def get_movies_from_category():
    category_id = request.args.get('id')
    movies = models.MovieCatRe.query.filter(models.MovieCatRe.movie_cat_id == category_id).all()
    res = [{'id': i.movie.id, 'name': i.movie.name,
            'genre': i.movie.genre,
            'actor': i.movie.actor,
            'director': i.movie.director,
            'score': i.movie.score,
            'views': i.movie.views,
            're_id': i.id} for i in movies]
    return jsonify(res)


@b.route('/add_movie', methods=['POST'])
@admin_required()
def add_movie():
    name = request.form['name']
    director = request.form['director']
    actor = request.form['actor']
    genre = request.form['genre']
    movie = models.Movie(name)
    movie.director = director
    movie.actor = actor
    movie.genre = genre
    db.session.add(movie)
    db.session.commit()
    return jsonify('success')


@b.route('/movies_not_from_category')
@admin_required()
def get_movies_not_from_category():
    category_id = request.args.get('id')
    movies = models.MovieCatRe.query.filter(models.MovieCatRe.movie_cat_id == category_id).all()
    ids = [i.movie.id for i in movies]
    movies = models.Movie.query.filter(~ models.Movie.id.in_(ids)).all()
    res = [{'id': i.id,
            'name': i.name,
            'director': i.director,
            } for i in movies]
    return jsonify(res)


@b.route('/add_movie_to_category', methods=['POST'])
@admin_required()
def add_movie_to_category():
    category_id = request.form['category_id']
    ids = request.form['ids']
    ids = json.loads(ids)
    ids = list(set(ids))
    for i in ids:
        m = models.MovieCatRe(i, category_id)
        db.session.add(m)
    db.session.commit()
    return jsonify('success')


@b.route('/del_movie_from_category', methods=['POST'])
@admin_required()
def del_movie_from_category():
    _id = request.form['id']
    m = models.MovieCatRe.query.filter(models.MovieCatRe.id == _id).first()

    if m is not None:
        db.session.delete(m)
        db.session.commit()

    return jsonify('success')


@b.route('/update_category', methods=['POST'])
@admin_required()
def update_category():
    _id = request.form['id']
    name = request.form['name']
    desc = request.form['desc']

    c = models.MovieCategory.query.get(int(_id))
    if c is None:
        return jsonify('error')
    c.category = name
    c.desc = desc
    db.session.commit()
    return jsonify('success')


@b.route('/del_category')
@admin_required()
def delete_category():
    _id = request.args.get('id')

    c = models.MovieCategory.query.get(int(_id))

    if c is None:
        return jsonify('error')
    # 先删除下面收录的电影

    re = models.MovieCatRe.query.filter(models.MovieCatRe.movie_cat_id == id).all()
    for r in re:
        db.session.delete(r)
    # 再删除该类别
    db.session.delete(c)
    db.session.commit()
    return jsonify('success')


@b.route('/upload_video/<movie_id>', methods=['POST', 'GET'])
@admin_required()
def upload(movie_id):
    if movie_id is None:
        return jsonify('error')
    movie = models.Movie.query.get(int(movie_id))
    if movie is None:
        return jsonify('error')

    f = request.files['file']
    basepath = os.path.dirname(__file__)  # 当前文件所在路径
    filename = str(datetime.datetime.now()) + f.filename
    upload_path = os.path.join(basepath, 'static/video', secure_filename(filename))  # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
    f.save(upload_path)

    movie.video_path = '/static/video/' + secure_filename(filename)

    db.session.commit()
    return jsonify({'res': 'success', 'video_path': movie.video_path})


@b.route('/update_movie_front/<movie_id>', methods=['POST', 'GET'])
@admin_required()
def update_movie_front(movie_id):
    if movie_id is None:
        return jsonify('error')
    movie = models.Movie.query.get(int(movie_id))
    if movie is None:
        return jsonify('error')

    f = request.files['file']
    basepath = os.path.dirname(__file__)  # 当前文件所在路径
    filename = str(datetime.datetime.now()) + f.filename
    upload_path = os.path.join(basepath, 'static/img', secure_filename(filename))  # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
    f.save(upload_path)

    movie.img_path = '/static/img/' + secure_filename(filename)

    db.session.commit()
    return jsonify({'res': 'success', 'img_path': movie.img_path})


@b.route('/upload_img', methods=['POST', 'GET'])
@admin_required()
def upload_news_img():
    f = request.files['files']
    basepath = os.path.dirname(__file__)  # 当前文件所在路径
    filename = str(datetime.datetime.now()) + f.filename
    upload_path = os.path.join(basepath, 'static/news-img', secure_filename(filename))  # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
    f.save(upload_path)
    res = "/static/news-img/" + secure_filename(filename)
    return res


@b.route('/training_apriori')
@admin_required()
def training():
    support = float(request.args.get('support'))
    confidence = float(request.args.get('confidence'))
    global MODEL_PATH
    # try:
    MODEL_PATH = apriori.generate_rules(min_support=support, min_confidence=confidence)
    # except Exception as e:
    #     print(e)
    #     return jsonify({
    #         'message': 'error'
    #     })
    sampels_rules, rules_num = apriori.samples_of_rules(MODEL_PATH)
    return jsonify({
        'rules': sampels_rules,
        'num': rules_num,
        'message': 'success'
    })


@b.route('/re_setting')
@admin_required()
def re_setting():
    return render_template('recommend_setting.html')
