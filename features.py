from flask import Blueprint
from flask import jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func

from models import GuestBook, Rating, Movie, User, Qa, News
from settings import db

f = Blueprint('features', __name__, template_folder='templates')


@f.route('/gb')
def guest_page():
    return render_template('guestBook.html')


@f.route('/guestbook')
def get_all_guests():
    guests = GuestBook.query.order_by(db.desc(GuestBook.pub_date)).all()
    res = []
    for i in guests:
        res.append({
            'id': i.id,
            'username': i.user.username,
            'content': i.content,
            'pub_date': str(i.pub_date)
        })
    return jsonify(res)


@f.route('/message', methods=['POST'])
@login_required
def leave_message():
    content = request.form['content']
    user_id = current_user.id
    g = GuestBook(content)
    g.user_id = user_id
    db.session.add(g)
    db.session.commit()
    return jsonify('success')


@f.route('/qa')
@login_required
def questionnaire_page():
    return render_template('questionnaire.html')


@f.route('/questionnaire', methods=['GET'])
def get_all_qa():
    qa = Qa.query.order_by(db.desc(Qa.submit_date)).limit(50)
    return jsonify([{'score': i.score, 'submit_date': str(i.submit_date),
                     'favorite_genre': i.favorite_genre,
                     'sex': i.sex, 'from_where': i.from_where} for i in qa])


@f.route('/questionnaire', methods=['POST'])
@login_required
def add_qa():
    user_id = current_user.id
    q = Qa.query.filter(Qa.user_id == user_id).first()
    if q is not None:
        return jsonify({'res': '该问卷只能填写一次'})
    sex = request.form['sex']
    favorite_genre = request.form['favorite_genre']
    score = request.form['score']
    from_where = request.form['from_where']
    suggest = request.form['suggest']

    qa = Qa(sex, favorite_genre, score, from_where, suggest)
    qa.user_id = user_id
    db.session.add(qa)
    db.session.commit()
    return jsonify({'res': 'success'})


@f.route('/st')
def st_page():
    return render_template('infoStatistics.html')


@f.route('/statistics')
def get_statistics():
    movie_count = Movie.query.count()
    user_count = User.query.count()
    eva_count = Rating.query.count()
    qa_count = Qa.query.count()
    guest_count = GuestBook.query.count()
    score = db.session.query(func.avg(Qa.score).label('average')).first()[0]
    from_where = db.session.query(Qa.from_where, func.count('*')) \
        .group_by(Qa.from_where).all()
    from_where = {i[0]: i[1] for i in from_where}

    favorite_genre = db.session.query(Qa.favorite_genre, func.count('*')) \
        .group_by(Qa.favorite_genre).all()
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


# @f.route('/news/<_id>')
# def nd(_id):
#     news = News.query.get(int(_id))
#     return jsonify({
#         'pub_date': str(news.pub_date),
#         'title': news.title,
#         'content': news.content,
#         'user': news.user.username
#     })

@f.route('nw')
def news_page(): return render_template('news.html')


@f.route('/news/<_id>')
def news_details(_id):
    news = News.query.get(int(_id))
    return render_template('newsDetail.html', news=news)


@f.route('/news', methods=['GET'])
def get_all_news():
    news = News.query.order_by(db.desc(News.pub_date)).all()
    res = [{'title': i.title,
            'content': i.content,
            'id': i.id,
            'pub_date': str(i.pub_date),
            'username': i.user.username
            } for i in news]
    return jsonify(res)


@f.route('/news/<_id>', methods=['GET'])
def get_news(_id):
    i = News.get(_id)
    return jsonify(
        {'title': i.title,
         'content': i.content,
         'id': i.id,
         'pub_date': str(i.pub_date),
         'username': i.user.username})
