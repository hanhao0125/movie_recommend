import random

from settings import db
from datetime import datetime
import xlrd
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_login import UserMixin
import pandas as pd
import json
import uuid
from sqlalchemy.sql import func


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120))
    genre = db.Column(db.String(120))
    actor = db.Column(db.String(120))
    director = db.Column(db.String(120))
    views = db.Column(db.Integer, default=0)
    country = db.Column(db.String(20))
    score = db.Column(db.Float, default=0)
    add_date = db.Column(db.DateTime)
    video_path = db.Column(db.String(200))
    collect_num = db.Column(db.Integer, default=0)
    eva_num = db.Column(db.Integer, default=0)
    img_path = db.Column(db.String(200), default='/static/img/front.jpg')

    def __init__(self, name):
        self.name = name
        self.add_date = datetime.now()
        self.views = 0
        self.score = 0
        self.video_path = '/static/video/test.mp4'
        self.collect_num = 0
        self.eva_num = 0

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
    is_freeze = db.Column(db.Boolean)

    def __init__(self, account):
        self.username = account
        self.account = account
        self.register_date = datetime.now()
        self.is_admin = False
        self.is_freeze = False

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

    def freeze(self):
        return self.is_freeze

    def __repr__(self):
        return 'User name=%s' % self.username


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pub_date = db.Column(db.DateTime)
    content = db.Column(db.String(4000))
    title = db.Column(db.String(120))
    user_id = db.Column(db.Integer)

    def __init__(self, title, content, pub_date=None):
        self.title = title
        self.content = content
        if pub_date is None:
            self.pub_date = datetime.now()

    def __repr__(self):
        return 'News content=%s' % self.content


class MovieEva(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    eva_date = db.Column(db.DateTime)
    comment = db.Column(db.String(120))
    score = db.Column(db.Float)

    user_id = db.Column(db.Integer)
    movie_id = db.Column(db.Integer)

    def __init__(self, comment, eva_date=None):
        self.comment = comment
        if eva_date is None:
            self.eva_date = datetime.now()

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
            self.create_date = datetime.now()

    def __repr__(self):
        return 'Movie category=%s' % self.category


class GuestBook(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pub_date = db.Column(db.DateTime)
    content = db.Column(db.String(400))
    user_id = db.Column(db.Integer)

    def __init__(self, content, pub_date=None):
        self.content = content
        if pub_date is None:
            self.pub_date = datetime.now()

    def __repr__(self):
        return 'Guest_book content=%s' % self.content


class MovieCatRe(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    movie_id = db.Column(db.Integer)
    movie_cat_id = db.Column(db.Integer)

    def __init__(self, movie_id, movie_cat_id):
        self.movie_id = movie_id
        self.movie_cat_id = movie_cat_id

    def __repr__(self):
        return 'movie_cat_re id=%d' % self.id


class UserCollection(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    movie_id = db.Column(db.Integer)
    mark = db.Column(db.String(300))
    collect_date = db.Column(db.DateTime)

    def __init__(self, movie_id, user_id):
        self.movie_id = movie_id
        self.user_id = user_id
        self.collect_date = datetime.now()

    def __repr__(self):
        return 'user_collection id=%d' % self.id


class Qa(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sex = db.Column(db.String(5))
    favorite_genre = db.Column(db.String(5))
    score = db.Column(db.Integer)
    from_where = db.Column(db.String(10))
    suggest = db.Column(db.String(300))
    submit_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer)

    def __init__(self, sex, favorite_genre, score, from_where, suggest):
        self.sex = sex
        self.favorite_genre = favorite_genre
        self.score = score
        self.from_where = from_where
        self.suggest = suggest
        self.submit_date = datetime.now()

    def __repr__(self):
        return str(self.user_id)


def import_user():
    for i in range(1000, 3000, 3):
        user = User('jobs' + str(i) + '@gmail.com')
        user.hash_password('1')
        user.email = 'jobs' + str(i) + '@gmail.com'
        user.phone = '1786678' + str(i)

        db.session.add(user)
    db.session.commit()


def import_user2():
    d = pd.read_csv('apriori/ml-100k/u.data',
                    delimiter="\t", header=None, encoding="mac-roman",
                    names=["UserID", "MovieID", "Rating", "DateTime"])
    for i in d['UserID'].unique():
        u = User.query.get(int(i))
        if u is None:
            j = str(i)
            user = User(j + str(random.randint(1, 100000)))
            user.username = j
            user.hash_password(j)
            user.email = str(j)
            user.id = int(i)
            print(i)
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


def import_movie2():
    movie_name_data = pd.read_csv('apriori/ml-100k/u.item', delimiter="|", header=None, encoding="mac-roman")
    movie_name_data.columns = ["MovieID", "Title", "Release Date", "Video Release", "IMDB", "<UNK>", "Action",
                               "Adventure", "Animation", "Children's", "Comedy", "Crime", "Documentary", "Drama",
                               "Fantasy", "Film-Noir", "Horror", "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller",
                               "War", "Western"]
    for i in movie_name_data.loc[:, ['MovieID', 'Title']].values:
        movie = Movie.query.get(int(i[0]))
        if movie is None:
            movie = Movie(name=i[1])
            movie.id = int(i[0])
            movie.genre = '动作'
            movie.director = 'unknown'
            movie.actor = 'unknown'
            db.session.add(movie)
    db.session.commit()


def import_movie_comments():
    d = pd.read_csv('apriori/ml-100k/u.data',
                    delimiter="\t", header=None, encoding="mac-roman",
                    names=["UserID", "MovieID", "Rating", "DateTime"])
    for i in d.values:
        print(i)
        k = MovieEva('好')
        k.movie_id = int(i[1])
        k.user_id = int(i[0])
        k.score = 2 * int(i[2])
        db.session.add(k)
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
        m.video_path = '/static/video/test.mp4'

        avg_score = db.session.query(func.avg(MovieEva.score)
                                     .label('average')).filter(MovieEva.movie_id == m.id).first()[0]
        m.score = avg_score
    db.session.commit()


def update_movie_eva():
    m = MovieEva.query.all()
    for i in m:
        i.user_id = 668
        if i.user is None:
            i.user_id = 668
    db.session.commit()


def update_movie_num():
    movies = Movie.query.all()
    for m in movies:
        cn = UserCollection.query.filter(UserCollection.movie_id == m.id).all()
        m.collect_num = len(cn)
        en = MovieEva.query.filter(MovieEva.movie_id == m.id).all()
        m.eva_num = len(en)
    db.session.commit()


def init_db():
    db.drop_all()
    db.create_all()
    db.session.commit()
    import_user()
    import_movie()
    generate_movie_comments()
    generate_qa()
    update_movie_score()


def import_user_collection():
    for i in range(300, 500):
        uc = UserCollection(i, 668)
        db.session.add(uc)
    db.session.commit()


if __name__ == '__main__':
    # import_user2()
    # import_movie2()
    # update_movie_eva()
    init_db()
    # pass
