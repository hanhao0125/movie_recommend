import random

from settings import db
from datetime import datetime
import xlrd
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_login import UserMixin
import json
import uuid
from sqlalchemy.sql import func


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120))
    genre = db.Column(db.String(120))
    actor = db.Column(db.String(120))
    director = db.Column(db.String(120))
    views = db.Column(db.Integer)
    country = db.Column(db.String(20))
    score = db.Column(db.Float)
    add_date = db.Column(db.DateTime)
    video_path = db.Column(db.String(200))

    def __init__(self, name):
        self.name = name
        self.add_date = datetime.utcnow()

    def __repr__(self):
        return 'Movie name=%s' % self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32))
    account = db.Column(db.String(32), unique=True)
    password = db.Column(db.String(128))
    register_date = db.Column(db.DateTime)
    email = db.Column(db.String(32))
    phone = db.Column(db.String(32))
    is_admin = db.Column(db.Boolean)

    def __init__(self, account):
        self.username = account
        self.account = account
        self.register_date = datetime.utcnow()
        self.is_admin = False

    def hash_password(self, password):
        self.password = generate_password_hash(password)
        return self.password

    def verify_password(self, password):
        password_hash = generate_password_hash(password)
        if password_hash is None:
            return False
        return check_password_hash(self.password, password)

    def admin(self):
        return self.is_admin

    def __repr__(self):
        return 'User name=%s' % self.username


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pub_date = db.Column(db.DateTime)
    content = db.Column(db.String(4000))
    title = db.Column(db.String(120))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('users', lazy='dynamic'))

    def __init__(self, title, content, pub_date=None):
        self.title = title
        self.content = content
        if pub_date is None:
            self.pub_date = datetime.utcnow()

    def __repr__(self):
        return 'News content=%s' % self.content


class MovieEva(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    eva_date = db.Column(db.DateTime)
    comment = db.Column(db.String(120))
    score = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # user = db.relationship('User', backref=db.backref('users', lazy='dynamic'))

    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    movie = db.relationship('Movie', backref=db.backref('movies', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('eva_user', lazy='dynamic'))

    def __init__(self, comment, eva_date=None):
        self.comment = comment
        if eva_date is None:
            self.eva_date = datetime.utcnow()

    def __repr__(self):
        return 'Movie_eva content=%s' % self.comment


class MovieCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    create_date = db.Column(db.DateTime)
    category = db.Column(db.String(20))
    desc = db.Column(db.String(800))

    def __init__(self, category, desc, create_date=None):
        self.category = category
        self.desc = desc
        if create_date is None:
            self.create_date = datetime.utcnow()

    def __repr__(self):
        return 'Movie category=%s' % self.category


class GuestBook(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pub_date = db.Column(db.DateTime)
    content = db.Column(db.String(400))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    user = db.relationship('User', backref=db.backref('g_users', lazy='dynamic'))

    def __init__(self, content, pub_date=None):
        self.content = content
        if pub_date is None:
            self.pub_date = datetime.utcnow()

    def __repr__(self):
        return 'Guest_book content=%s' % self.content


class MovieCatRe(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    movie_cat_id = db.Column(db.Integer, db.ForeignKey('movie_category.id'))

    movie = db.relationship('Movie', backref='movie_cat_re')
    movie_category = db.relationship('MovieCategory', backref='movie_cat_re')

    def __init__(self, movie_id, movie_cat_id):
        self.movie_id = movie_id
        self.movie_cat_id = movie_cat_id

    def __repr__(self):
        return 'movie_cat_re id=%d' % self.id


class UserCollection(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    mark = db.Column(db.String(300))
    collect_date = db.Column(db.DateTime)
    movie = db.relationship('Movie', backref='user_collection')
    user = db.relationship('User', backref='user_collection')

    def __init__(self, movie_id, user_id):
        self.movie_id = movie_id
        self.user_id = user_id
        self.collect_date = datetime.utcnow()

    def __repr__(self):
        return 'movie_cat_re id=%d' % self.id


class Qa(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sex = db.Column(db.String(5))
    favorite_genre = db.Column(db.String(5))
    score = db.Column(db.Integer)
    from_where = db.Column(db.String(10))
    suggest = db.Column(db.String(300))
    submit_date = db.Column(db.DateTime)

    def __init__(self, sex, favorite_genre, score, from_where, suggest):
        self.sex = sex
        self.favorite_genre = favorite_genre
        self.score = score
        self.from_where = from_where
        self.suggest = suggest
        self.submit_date = datetime.utcnow()


def import_user():
    for i in range(1000, 3000, 3):
        user = User('jobs' + str(i) + '@gmail.com')
        user.hash_password('1')
        user.email = 'jobs' + str(i) + '@gmail.com'
        user.phone = '1786678' + str(i)

        db.session.add(user)
    db.session.commit()


def import_movie():
    data = xlrd.open_workbook('data/movie_data.xlsx')
    table = data.sheets()[0]
    rows = table.nrows
    print(rows)
    for i in range(1, rows):
        value = table.row_values(i)
        movie = Movie(name=value[0])
        movie.genre = value[15]
        movie.director = value[13]
        movie.actor = value[14]
        db.session.add(movie)
    db.session.commit()


def generate_movie_comments():
    movies = Movie.query.all()
    reviews = ['不好看', '非诚精彩', '满分', '期望过高']
    user_ids = User.query.all()
    user_ids = [u.id for u in user_ids]
    for i in movies:
        i.views = random.randint(1000, 100000)
        for j in range(30):
            r = reviews[random.randint(0, 2)]
            score = random.randint(3, 10)
            user_id = user_ids[random.randint(1, 400)]
            me = MovieEva(r)
            me.user_id = user_id
            me.score = score
            me.movie_id = i.id
            db.session.add(me)
    db.session.commit()


def generate_qa():
    from_where = ['朋友介绍', '百度搜索电影', '商业推荐', '无意发现']
    g = ['科幻', '爱情', '动作', '喜剧', '纪实']
    sex = ['男', '女']
    for i in range(1000):
        q = Qa(sex[random.randint(0, 1)], g[random.randint(0, len(g) - 1)], random.randint(1, 5)
               , from_where[random.randint(0, len(from_where) - 1)], suggest='无')
        db.session.add(q)
    db.session.commit()


def update_movie_score():
    movies = Movie.query.all()
    for m in movies:
        m.score = a[0]
        print(m.score)
    db.session.commit()


if __name__ == '__main__':
    # db.drop_all()
    # db.create_all()
    # db.session.commit()
    # import_user()
    # import_movie()
    # generate_movie_comments()
    generate_qa()
