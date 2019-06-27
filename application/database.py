import random
import time
from datetime import datetime

import pandas as pd
import tqdm
from flask_login import UserMixin
from sqlalchemy.sql import func
from werkzeug.security import check_password_hash, generate_password_hash

from .settings import db


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(300))
    genres = db.Column(db.String(300))
    actors = db.Column(db.String(300))
    director = db.Column(db.String(300))
    view_nums = db.Column(db.Integer, default=0)
    country = db.Column(db.String(20))
    score = db.Column(db.Float, default=0)
    add_date = db.Column(db.DateTime)
    year = db.Column(db.String(4))
    video_path = db.Column(db.String(200))
    collect_nums = db.Column(db.Integer, default=0)
    rating_nums = db.Column(db.Integer, default=0)
    img_path = db.Column(db.String(200), default='/static/img/front.jpg')

    def __init__(self, name):
        self.name = name
        self.add_date = datetime.now()
        self.actors = 'unknown'
        self.director = 'unknown'
        self.view_nums = 0
        self.score = 0
        self.video_path = '/static/video/test.mp4'
        self.collect_nums = 0
        self.rating_nums = 0

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


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rating_date = db.Column(db.DateTime)
    comment = db.Column('_comment', db.String(120))
    rating = db.Column(db.Float)
    user_id = db.Column('userId', db.Integer)
    movie_id = db.Column('movieId', db.Integer)

    def __init__(self):
        pass

    def __repr__(self):
        return 'Rating content=%s' % self.rating


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


def import_movie_from_ml20():
    movies = pd.read_csv('/Users/hanhao/Software/ml-20m/movies.csv')
    movies['year'] = movies.title.apply(lambda x: (x[-5:-1]))

    for _, row in movies.iterrows():
        m = Movie(row['title'])
        m.genres = row['genres']
        m.id = row['movieId']
        m.year = row['year']
        db.session.add(m)
    db.session.commit()


def import_user_from_ml20():
    ratings = pd.read_csv('/Users/hanhao/Software/ml-20m/ratings.csv')
    users = ratings['userId'].unique()
    password = generate_password_hash('1')
    us = []
    for uid in tqdm.tqdm(users):
        u = User(str(uid))
        u.id = int(uid)
        u.password = password
        us.append(u)
    db.session.add_all(us)
    db.session.commit()


def import_ratings_from_ml20():
    ratings = pd.read_csv('/Users/hanhao/Software/ml-20m/ratings.csv')
    ratings['date'] = ratings.timestamp.apply(lambda x: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x)))

    ratings.drop(['timestamp'], axis=1, inplace=True)
    print('data process finished')
    ratings.to_sql('rating', db.engine, index=True, if_exists='replace', index_label='id')


def generate_comments_to_rating():
    ratings = Rating.query.all()
    comments = ['不好看', '非诚精彩', '满分', '期望过高', '还行吧', '一般般', '电影不错,值得推荐']
    for m in tqdm.tqdm(ratings):
        r = comments[random.randint(0, len(comments) - 1)]
        m.comment = r
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
            me = Rating(r)
            me.user_id = user_id
            me.score = score
            me.movie_id = i.id
            db.session.add(me)
    db.session.commit()


def generate_qa():
    from_where = ['朋友介绍', '百度搜索电影', '商业推荐', '其他']
    g = ['科幻', '爱情', '动作', '喜剧', '纪实']
    sex = ['男', '女']
    for i in range(1000):
        q = Qa(sex[random.randint(0, 1)], g[random.randint(0, len(g) - 1)], random.randint(1, 5), from_where[random.randint(0, len(from_where) - 1)], suggest='无')
        db.session.add(q)
    db.session.commit()


# movieId 加了索引快了许多
def update_movie_score():
    movies = Movie.query.all()
    for m in tqdm.tqdm(movies):
        avg_score = db.session.query(func.avg(Rating.rating)
                                     .label('average')).filter(Rating.movie_id == m.id).first()[0]
        m.score = avg_score
    db.session.commit()


def update_movie_rating_num():
    movies = Movie.query.all()
    for m in tqdm.tqdm(movies):
        rating_nums = db.session.query(func.count(Rating.rating)
                                       .label('sum')).filter(Rating.movie_id == m.id).first()[0]
        m.rating_nums = rating_nums
    db.session.commit()


def update_movie_num():
    movies = Movie.query.all()
    for m in movies:
        cn = UserCollection.query.filter(UserCollection.movie_id == m.id).all()
        m.collect_num = len(cn)
        en = Rating.query.filter(Rating.movie_id == m.id).all()
        m.eva_num = len(en)
    db.session.commit()


if __name__ == '__main__':
    # generate_comments_to_rating()
    update_movie_rating_num()
