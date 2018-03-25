from settings import db
from datetime import datetime
import xlrd
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_login import UserMixin
import json
import uuid


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120))
    genre = db.Column(db.String(120))
    actor = db.Column(db.String(120))
    director = db.Column(db.String(120))
    views = db.Column(db.Integer)
    country = db.Column(db.String(20))
    score = db.Column(db.Float)

    def __init__(self, name):
        self.name = name

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

    def __repr__(self):
        return 'User name=%s' % self.username


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pub_date = db.Column(db.DateTime)
    content = db.Column(db.String(4000))
    title = db.Column(db.String(120))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('users', lazy='dynamic'))

    def __init__(self, title,content, pub_date=None):
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

    def __init__(self, comment, eva_date=None):
        self.comment = comment
        if eva_date is None:
            self.eva_date = datetime.utcnow()

    def __repr__(self):
        return 'Movie_eva content=%s' % self.content


class MovieCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    create_date = db.Column(db.DateTime)
    category = db.Column(db.String(20))
    desc = db.Column(db.String(800))

    def __init__(self, category, create_date=None):
        self.category = category
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


if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    db.session.commit()
    import_user()
    import_movie()
