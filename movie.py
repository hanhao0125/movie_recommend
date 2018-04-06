from flask import render_template, jsonify, request, redirect, url_for
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
    current_page = int(request.args.get('curr_page'))
    movies = models.Movie.query.order_by(db.desc(models.Movie.add_date)).limit(PAGE_SIZE).offset(
        (current_page - 1) * PAGE_SIZE)
    # movies = models.Movie.query.order_by(models.Movie.views)\
    # .paginate(current_page, per_page=PAGE_SIZE, error_out = False).items
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
         }
    )


@app.route('/movie_comments')
def get_all_movie_comments():
    movie_id = request.args.get('movie_id')
    comments = models.MovieEva.query.order_by(db.desc(models.MovieEva.eva_date)).filter(models.MovieEva.movie_id == movie_id).all()
    res = [{
        'id': c.id,
        'eva_date': str(c.eva_date),
        'comment': c.comment,
        'score': c.score,
        'username': c.user.username}
        for c in comments]
    return jsonify(res)


@app.route('/pub_comment', methods=['POST'])
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
