from flask import render_template, jsonify, request, redirect, url_for, Response
from sqlalchemy import func

import models
from forms import LoginForm
from settings import app, db
from flask_login import login_user, login_required
from flask_login import LoginManager, current_user
from flask_login import logout_user
from flask_wtf.csrf import CsrfProtect
import os
import json
from flask import send_from_directory

PAGE_SIZE = 10
# app.secret_key = os.urandom(24)

# use login manager to manage session
login_manager = LoginManager()
# login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app=app)


# csrf protection
# csrf = CsrfProtect()
# csrf.init_app(app)


@login_manager.user_loader
def load_user(id):
    try:
        return models.User.query.get(int(id))
    except:
        return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = request.form['account']
        password = request.form['password']
        user = models.User.query.filter(models.User.account == account).first()
        if user is not None:
            if user.verify_password(password):
                # user = models.User(account)
                login_user(user)
                return jsonify('success')
            else:
                return jsonify('密码不正确！')
        else:
            return jsonify('账号不存在')
    return render_template('login.html')


# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        account = request.form['account']
        password = request.form['password']
        print(account, password)
        user = models.User.query.filter(models.User.account == account).first()
        if user is not None:
            return jsonify('用户名已存在！')
        else:
            user = models.User(account)
            user.hash_password(password)
            db.session.add(user)
            db.session.commit()
            print(user)
        return jsonify('success')
    else:
        return render_template('register.html')


@app.route('/')
@app.route('/main')
@login_required
def main():
    return render_template(
        'main.html')


# ...
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/users')
def get_all_users():
    users = models.User.query.limit(50)
    res = []
    for i in users:
        res.append({'id': i.id, 'username': i.username, 'account': i.account,
                    'email': i.email, 'register_date': str(i.register_date),
                    'is_admin': i.is_admin, 'phone': i.phone})
    return jsonify(res)


@app.route('/give_admin', methods=['GET'])
@login_required
def give_admin():
    id = request.args.get('id')
    print(id)
    user = models.User.query.get(id)
    if user is None:
        return jsonify('user not exists')
    user.is_admin = True
    db.session.commit()
    return jsonify('success')


@app.route('/update_user', methods=['POST'])
@login_required
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


@app.route('/news/<id>', methods=['GET'])
def get_news(id):
    i = models.News.get(id)
    return jsonify(
        {'title': i.title, 'content': i.content, 'id': i.id, 'pub_date': str(i.pub_date), 'username': i.user.username})


@app.route('/del_user')
@login_required
def delete_user():
    account = request.args.get('account')

    u = models.User.query.filter(account == models.User.account).first()

    if u is None:
        return 'true'

    db.session.delete(u)
    db.session.commit()
    return 'true'


@app.route('/pub_news', methods=['POST'])
@login_required
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
@login_required
def delete_news():
    id = request.args.get('id')
    if id is None:
        return 'id is empty'

    n = models.News.query.get(id)
    db.session.delete(n)
    db.session.commit()
    return 'success'


@app.route('/movies')
def get_all_movies():
    movies = models.Movie.query.all()
    res = []
    count = models.Movie.query.count()
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


@app.route('/movies_count')
def get_movies_count():
    count = models.Movie.query.count()
    return jsonify(count)


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

    search_words = request.args.get('search_words')

    if search_words is not None:
        print(search_words)
        movies = models.Movie.query.order_by(db.desc(s.get(sort_key, 'id'))) \
            .filter(models.Movie.name.like(''.join(['%', search_words, '%']))).limit(PAGE_SIZE).offset(
            (current_page - 1) * PAGE_SIZE)
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
@login_required
def del_guest():
    id = request.args.get('id')
    g = models.GuestBook.query.filter(id == models.GuestBook.id).first()
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
def movie_manage():
    return render_template('movieManage.html')


@app.route('/movie_category')
def get_all_category():
    c = models.MovieCategory.query.order_by(db.desc(models.MovieCategory.create_date)).all()
    res = [{'id': i.id, 'create_date': str(i.create_date),
            'category': i.category, 'desc': i.desc} for i in c]
    return jsonify(res)


@app.route('/create_category', methods=['POST'])
def create_category():
    c = request.form['category']
    desc = request.form['desc']
    category = models.MovieCategory(c, desc)
    db.session.add(category)
    db.session.commit()
    return jsonify('success')


@app.route('/movies_from_category')
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
def del_movie_from_category():
    _id = request.form['id']
    m = models.MovieCatRe.query.filter(models.MovieCatRe.id == _id).first()

    if m is not None:
        db.session.delete(m)
        db.session.commit()

    return jsonify('success')


@app.route('/movie_details_page/<movie_id>', methods=['GET'])
def movie_details_page(movie_id):
    movie = models.Movie.query.get(int(movie_id))
    # 更新访问次数
    # todo 同一 ip 相近时间段内重复访问应该记做一次
    movie.views += 1
    db.session.commit()
    return render_template('movieDetail.html', movie=movie)


@app.route('/movie_details/<movie_id>')
def movie_details(movie_id):
    movie = models.Movie.query.get(int(movie_id))
    return jsonify(
        {'id': movie.id,
         'name': movie.name,
         'genre': movie.genre,
         'actor': movie.actor,
         'director': movie.director,
         'score': movie.score,
         'views': movie.views,
         'video_path': movie.video_path
         }
    )


@app.route('/movie_comments')
def get_all_movie_comments():
    movie_id = request.args.get('movie_id')
    comments = models.MovieEva.query.order_by(db.desc(models.MovieEva.eva_date)).filter(
        models.MovieEva.movie_id == movie_id).all()
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
    # 更新 movie 表中的平均得分
    avg_score = db.session.query(func.avg(models.MovieEva.score)
                                 .label('average')).filter(models.MovieEva.movie_id == movie_id).first()[0]
    movie = models.Movie.query.get(movie_id)
    if movie is not None:
        movie.score = avg_score

    db.session.add(me)
    db.session.commit()

    return jsonify('success')


@app.route('/questionnaire')
def questionnaire_page():
    return render_template('questionnaire.html')


@app.route('/submit_qa', methods=['POST'])
def add_qa():
    sex = request.form['sex']
    favorite_genre = request.form['favorite_genre']
    score = request.form['score']
    from_where = request.form['from_where']
    suggest = request.form['suggest']

    qa = models.Qa(sex, favorite_genre, score, from_where, suggest)
    db.session.add(qa)
    db.session.commit()
    return jsonify('success')


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
    favorite_genre = db.session.query(models.Qa.favorite_genre, func.count('*')) \
        .group_by(models.Qa.favorite_genre).all()
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
    qa = models.Qa.query.order_by(db.desc(models.Qa.submit_date)).all()
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
        return jsonify('success')

    c = models.UserCollection(movie_id, user_id)
    c.mark = mark
    db.session.add(c)
    db.session.commit()
    return jsonify('success')


@app.route('/my_collections')
@login_required
def collections_page():
    return render_template('myCollection.html')


@app.route('/guest')
@login_required
def guest_page():
    return render_template('guestBook.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
