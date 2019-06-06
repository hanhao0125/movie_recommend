import datetime
import json
import os
from functools import wraps

from flask import (
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
    abort)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user)
from sqlalchemy import func
from werkzeug.utils import secure_filename

import models
from apriori import apriori
from config import *
from settings import app, db

ACCESS_IP = {}
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app=app)


@login_manager.user_loader
def load_user(_id):
    try:
        return models.User.query.get(int(_id))
    except:
        return None


def admin_required():
    def decorator(_func):
        @wraps(_func)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.is_admin:
                return _func(*args, **kwargs)
            else:
                abort(403)

        return decorated_function

    return decorator


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = request.form['account']
        password = request.form['password']
        user = models.User.query.filter(models.User.account == account).first()
        if user is not None:
            if user.is_freeze:
                return jsonify('账号被冻结，请联系管理员解封')
            if user.verify_password(password):
                # user = models.User(account)
                login_user(user)
                return jsonify('success')
            else:
                return jsonify('密码不正确！')
        else:
            return jsonify('账号不存在')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        account = request.form['account']
        password = request.form['password']
        user = models.User.query.filter(models.User.account == account).first()
        if user is not None:
            return jsonify('用户名已存在！')
        else:
            user = models.User(account)
            user.hash_password(password)
            db.session.add(user)
            db.session.commit()
        return jsonify('success')
    else:
        return render_template('register.html')


@app.route('/')
@app.route('/main')
def main():
    return render_template(
        'movieIndex.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/users')
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


@app.route('/give_admin', methods=['GET'])
@admin_required()
def give_admin():
    id = request.args.get('id')
    user = models.User.query.get(id)
    if user is None:
        return jsonify('user not exists')
    user.is_admin = True
    db.session.commit()
    return jsonify('success')


@app.route('/update_user', methods=['POST'])
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


@app.route('/news')
def get_all_news():
    news = models.News.query.order_by(db.desc(models.News.pub_date)).all()
    res = []
    for i in news:
        res.append(
            {'title': i.title, 'content': i.content, 'id': i.id, 'pub_date': str(i.pub_date),
             'username': i.user.username})
    return jsonify(res)


@app.route('/news/<_id>', methods=['GET'])
def get_news(_id):
    i = models.News.get(_id)
    return jsonify(
        {'title': i.title, 'content': i.content, 'id': i.id, 'pub_date': str(i.pub_date), 'username': i.user.username})


@app.route('/del_user')
@admin_required()
def delete_user():
    account = request.args.get('account')

    u = models.User.query.filter(account == models.User.account).first()

    if u is None:
        return 'true'

    db.session.delete(u)
    db.session.commit()
    return 'true'


@app.route('/freeze_user')
@admin_required()
def freeze_user():
    _id = request.args.get('id')
    u = models.User.query.get(_id)

    if u is None:
        return 'user_not_exists'
    u.is_freeze = True
    db.session.commit()
    return 'success'


@app.route('/release_freeze')
@admin_required()
def release_freeze():
    _id = request.args.get('id')
    u = models.User.query.get(_id)

    if u is None:
        return 'success'
    u.is_freeze = False
    db.session.commit()
    return 'success'


@app.route('/pub_news', methods=['POST'])
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


@app.route('/del_news', methods=['GET'])
@admin_required()
def delete_news():
    _id = request.args.get('id')
    if _id is None:
        return 'id is empty'

    n = models.News.query.get(id)
    db.session.delete(n)
    db.session.commit()
    return 'success'


@app.route('/movies')
def get_all_movies():
    movies = models.Movie.query.all()
    res = []
    for m in movies:
        res.append({
            'name': m.name,
            'genre': m.genre,
            'actor': m.actor,
            'director': m.director,
            'score': m.score,
            'views': m.views
        })
    return jsonify(res)


@app.route('/update_movie', methods=['POST'])
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


@app.route('/movies_count')
def get_movies_count():
    count = models.Movie.query.count()
    return jsonify(count)


@app.route('/del_movie')
@admin_required()
def del_movie():
    id = request.args.get('id')
    movie = models.Movie.query.get(id)
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


@app.route('/page_movies')
def get_page_movie():
    s = {
        'name': models.Movie.name,
        'views': models.Movie.views,
        'score': models.Movie.score,
        'add_date': models.Movie.add_date,
        'id': models.Movie.id

    }
    current_page = int(request.args.get('curr_page'))
    sort_key = request.args.get('sort_key')

    search_words = str(request.args.get('search_words'))
    if search_words != '_none':
        movies = models.Movie.query.order_by(db.desc(s.get(sort_key, 'id'))) \
            .filter(models.Movie.name.like(''.join(['%', search_words, '%']))).all()
    else:
        movies = models.Movie.query.order_by(db.desc(s.get(sort_key, 'id'))).limit(PAGE_SIZE).offset(
            (current_page - 1) * PAGE_SIZE)

    # movies = models.Movie.query.order_by(models.Movie.views)\
    # .paginate(current_page, per_page=PAGE_SIZE, error_out = False).items

    res = [{
        'id': m.id,
        'name': m.name,
        'genre': m.genre,
        'actor': m.actor,
        'director': m.director,
        'score': m.score,
        'views': m.views,
        'video_path': m.video_path,
        'img_path': m.img_path
    } for m in movies]
    return jsonify(res)


@app.route('/search_movies')
def search_movies():
    s = request.args.get('search_words')
    if s is None:
        return jsonify([])
    movies = models.Movie.query.order_by(db.desc(models.Movie.name)) \
        .filter(models.Movie.name.like(''.join(['%', s, '%']))).all()
    res = [{
        'id': m.id,
        'name': m.name,
        'genre': m.genre,
        'actor': m.actor,
        'director': m.director,
        'score': str(m.score),
        'views': str(m.views),
        'video_path': m.video_path
    } for m in movies]
    return jsonify(res)


@app.route('/guests')
def get_all_guests():
    guests = models.GuestBook.query.order_by(db.desc(models.GuestBook.pub_date)).all()
    res = []
    for i in guests:
        res.append({
            'id': i.id,
            'username': i.user.username,
            'content': i.content,
            'pub_date': str(i.pub_date)
        })
    return jsonify(res)


@app.route('/del_guest', methods=['GET'])
@admin_required()
def del_guest():
    id = request.args.get('id')
    g = models.GuestBook.query.filter(id == models.GuestBook.id).first()
    if g is None:
        return jsonify('success')
    db.session.delete(g)
    db.session.commit()
    return jsonify('success')


@app.route('/leave_message', methods=['POST'])
@login_required
def leave_message():
    content = request.form['content']
    user_id = current_user.id
    g = models.GuestBook(content)
    g.user_id = user_id
    db.session.add(g)
    db.session.commit()
    return jsonify('success')


@app.route('/movie_manage')
@admin_required()
def movie_manage():
    return render_template('movieManage.html')


@app.route('/movie_category')
@admin_required()
def get_all_category():
    c = models.MovieCategory.query.order_by(db.desc(models.MovieCategory.create_date)).all()
    res = [{'id': i.id, 'create_date': str(i.create_date),
            'category': i.category, 'desc': i.desc} for i in c]
    return jsonify(res)


@app.route('/create_category', methods=['POST'])
@admin_required()
def create_category():
    c = request.form['category']
    desc = request.form['desc']
    category = models.MovieCategory(c, desc)
    db.session.add(category)
    db.session.commit()
    return jsonify('success')


@app.route('/movies_from_category')
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


@app.route('/add_movie', methods=['POST'])
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


@app.route('/movies_not_from_category')
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


@app.route('/add_movie_to_category', methods=['POST'])
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


@app.route('/del_movie_from_category', methods=['POST'])
@admin_required()
def del_movie_from_category():
    _id = request.form['id']
    m = models.MovieCatRe.query.filter(models.MovieCatRe.id == _id).first()

    if m is not None:
        db.session.delete(m)
        db.session.commit()

    return jsonify('success')


@app.route('/update_category', methods=['POST'])
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


@app.route('/del_category')
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


@app.route('/movie_details_page/<movie_id>', methods=['GET'])
def movie_details_page(movie_id):
    movie = models.Movie.query.get(int(movie_id))
    # 更新访问次数
    global ACCESS_IP
    try:
        now = datetime.datetime.now()
        ACCESS_IP = {k: v for k, v in ACCESS_IP.items() if (now - k).seconds < 60}
        ips = set(ACCESS_IP.values())
        if request.remote_addr not in ips:
            movie.views += 1
            ACCESS_IP[datetime.datetime.now()] = request.remote_addr
        db.session.commit()
    except:
        return render_template('movieDetail.html', movie=movie)
    return render_template('movieDetail.html', movie=movie)


@app.route('/movie_details')
def movie_details():
    movie_id = request.args.get('movie_id')
    movie = models.Movie.query.get(int(movie_id))
    return jsonify(
        {'id': movie.id,
         'name': movie.name,
         'genre': movie.genre,
         'actor': movie.actor,
         'director': movie.director,
         'score': movie.score,
         'views': movie.views,
         'video_path': movie.video_path,
         'collect_num': movie.collect_num,
         'eva_num': movie.eva_num,
         'img_path': movie.img_path
         }
    )


@app.route('/movie_video/<movie_id>')
@login_required
def get_movie_video(movie_id):
    movie = models.Movie.query.get(int(movie_id))
    if movie is not None:
        return send_file(movie.video_path[1:], as_attachment=True)
    else:
        return 'error'


# 分页
@app.route('/movie_comments')
def get_all_movie_comments():
    movie_id = request.args.get('movie_id')
    curr_page = int(request.args.get('curr_page'))
    curr_page = 1 if curr_page is None else curr_page
    comments = models.MovieEva.query.order_by(db.desc(models.MovieEva.eva_date)).filter(
        models.MovieEva.movie_id == movie_id).limit(COMMENT_PAGE_SIZE).offset(
        (curr_page - 1) * COMMENT_PAGE_SIZE)

    res = [{
        'id': c.id,
        'eva_date': str(c.eva_date),
        'comment': c.comment,
        'score': c.score,
        'username': c.user.username}
        for c in comments]
    return jsonify(res)


@app.route('/pub_comment', methods=['POST'])
@login_required
def add_new_comments():
    comment = request.form['comment']
    score = request.form['score']
    movie_id = request.form['movie_id']

    curr_user_id = current_user.id

    me = models.MovieEva(comment)
    me.score = score
    me.movie_id = movie_id
    me.user_id = curr_user_id

    db.session.add(me)
    db.session.commit()
    # 更新 movie 表中的平均得分
    avg_score = db.session.query(func.avg(models.MovieEva.score)
                                 .label('average')).filter(models.MovieEva.movie_id == movie_id).first()[0]
    movie = models.Movie.query.get(movie_id)
    if movie is not None:
        movie.score = avg_score
        movie.eva_num += 1

    db.session.commit()

    return jsonify({'res': 'success', 'score': avg_score})


@app.route('/questionnaire')
@login_required
def questionnaire_page():
    return render_template('questionnaire.html')


@app.route('/submit_qa', methods=['POST'])
@login_required
def add_qa():
    user_id = current_user.id
    q = models.Qa.query.filter(models.Qa.user_id == user_id).first()
    if q is not None:
        return jsonify({'res': '该问卷只能填写一次'})
    sex = request.form['sex']
    favorite_genre = request.form['favorite_genre']
    score = request.form['score']
    from_where = request.form['from_where']
    suggest = request.form['suggest']

    qa = models.Qa(sex, favorite_genre, score, from_where, suggest)
    qa.user_id = user_id
    db.session.add(qa)
    db.session.commit()
    return jsonify({'res': 'success'})


@app.route('/st_page')
def st_page():
    return render_template('infoStatistics.html')


@app.route('/statistics')
def get_statistics():
    movie_count = models.Movie.query.count()
    user_count = models.User.query.count()
    eva_count = models.MovieEva.query.count()
    qa_count = models.Qa.query.count()
    guest_count = models.GuestBook.query.count()
    score = db.session.query(func.avg(models.Qa.score).label('average')).first()[0]
    from_where = db.session.query(models.Qa.from_where, func.count('*')) \
        .group_by(models.Qa.from_where).all()
    from_where = {i[0]: i[1] for i in from_where}

    favorite_genre = db.session.query(models.Qa.favorite_genre, func.count('*')) \
        .group_by(models.Qa.favorite_genre).all()
    favorite_genre = {i[0]: i[1] for i in favorite_genre}
    res = {
        'movie_count': movie_count,
        'user_count': user_count,
        'eva_count': eva_count,
        'qa_count': qa_count,
        'guest_count': guest_count,
        'score': str(score),
        'from_where': from_where,
        'favorite_genre': favorite_genre
    }
    return jsonify(res)


@app.route('/qa')
def get_all_qa():
    qa = models.Qa.query.order_by(db.desc(models.Qa.submit_date)).limit(50)
    return jsonify([{'score': i.score, 'submit_date': str(i.submit_date),
                     'favorite_genre': i.favorite_genre,
                     'sex': i.sex, 'from_where': i.from_where} for i in qa])


@app.route('/collect_movie', methods=['POST'])
@login_required
def collect_movie():
    movie_id = request.form['movie_id']
    mark = request.form['mark']

    user_id = current_user.id

    is_exist = models.UserCollection.query.filter(movie_id == models.UserCollection.movie_id,
                                                  user_id == models.UserCollection.user_id).all()

    # 已经存在，直接返回
    if len(is_exist) != 0:
        return jsonify('collected')

    # 更新 movie 表中 collect_num 字段
    m = models.Movie.query.get(int(movie_id))
    if m is not None:
        m.collect_num += 1
    c = models.UserCollection(movie_id, user_id)
    c.mark = mark
    db.session.add(c)
    db.session.commit()
    return jsonify('success')


@app.route('/personal_collect')
@login_required
def get_all_my_collections():
    user = current_user
    c = models.UserCollection.query.order_by(db.desc(models.UserCollection.collect_date)).filter(
        models.UserCollection.user_id == user.id).all()
    res = [{
        'id': i.id,
        'movie_id': i.movie.id,
        'movie_name': i.movie.name,
        'collect_date': str(i.collect_date),
        'mark': i.mark}
        for i in c
    ]
    return jsonify(res)


@app.route('/del_collection')
@admin_required()
def del_collection():
    _id = request.args.get('id')
    if id is None:
        return 'error'
    c = models.UserCollection.query.get(int(_id))
    if c is None:
        return 'success'
    db.session.delete(c)

    db.session.commit()
    return jsonify('success')


@app.route('/upload_video/<movie_id>', methods=['POST', 'GET'])
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


@app.route('/update_movie_front/<movie_id>', methods=['POST', 'GET'])
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


@app.route('/upload_img', methods=['POST', 'GET'])
@admin_required()
def upload_news_img():
    f = request.files['files']
    basepath = os.path.dirname(__file__)  # 当前文件所在路径
    filename = str(datetime.datetime.now()) + f.filename
    upload_path = os.path.join(basepath, 'static/news-img', secure_filename(filename))  # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
    f.save(upload_path)
    res = "/static/news-img/" + secure_filename(filename)
    return res


@app.route('/news_details/<_id>')
def nd(_id):
    news = models.News.query.get(int(_id))
    return jsonify({
        'pub_date': str(news.pub_date),
        'title': news.title,
        'content': news.content,
        'user': news.user.username
    })


@app.route('/recommend_movies')
@login_required
def recommend_movies():
    user_id = current_user.id
    res = apriori.recommend_by_user_id(user_id, model_path=MODEL_PATH)
    return jsonify(res)


@app.route('/training_apriori')
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


@app.route('/update_user_info', methods=['POST'])
@login_required
def uu_info():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    phone = request.form['phone']
    user_id = current_user.id
    user = models.User.query.get(int(user_id))

    if password:
        user.password = user.hash_password(password)
    if username:
        user.username = username
    if email:
        user.email = email
    if phone:
        user.phone = phone
    db.session.commit()
    return jsonify('success')


@app.route('/news_detail/<_id>')
def news_details(_id):
    news = models.News.query.get(int(_id))
    return render_template('newsDetail.html', news=news)


@app.route('/guest')
def guest_page():
    return render_template('guestBook.html')


@app.route('/movie_index')
def movie_index():
    return render_template('movieIndex.html')


@app.route('/news_page')
def news_page():
    return render_template('news.html')


@app.route('/user_manage')
@admin_required()
def user_manage():
    return render_template('user_manage.html')


@app.route('/my_collection')
@login_required
def collection_page():
    return render_template('myCollection.html')


@app.route('/test')
def just_test():
    return render_template('test.html')


@app.route('/re_setting')
@admin_required()
def re_setting():
    return render_template('recommend_setting.html')


@app.route('/my_recommend')
@login_required
def my_recommed_page():
    return render_template('my_recommend.html')


@app.route('/user_info')
def user_info():
    return render_template('userInfo.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
