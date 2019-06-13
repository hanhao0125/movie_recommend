from flask import Blueprint, current_app
from flask import jsonify, render_template, request, send_file
from flask_login import current_user, login_required

from apriori import apriori
from config import PAGE_SIZE, COMMENT_PAGE_SIZE, MAX_CACHE_VIEW_NUM
from models import Movie, Rating, UserCollection
from settings import db, redis_client
from sqlalchemy import func

m = Blueprint('movie', __name__, template_folder='templates')


@m.route('/')
@m.route('/main')
def main():
    return render_template('movie/movieIndex.html')


@m.route('/movies')
def get_all_movies():
    movies = Movie.query.all()
    res = []
    for movie in movies:
        res.append({
            'name': movie.name,
            'genre': movie.genres,
            'actor': movie.actors,
            'director': movie.director,
            'score': movie.score,
            'views': movie.view_nums
        })
    return jsonify(res)


@m.route('/movies_count')
def get_movies_count():
    count = Movie.query.count()
    return jsonify(count)


@m.route('/page_movies')
def get_page_movie():
    s = {
        'name': Movie.name,
        'views': Movie.view_nums,
        'score': Movie.score,
        'add_date': Movie.add_date,
        'id': Movie.id,
        'rating_nums': Movie.rating_nums
    }
    current_page = int(request.args.get('curr_page'))
    sort_key = request.args.get('sort_key')

    search_words = str(request.args.get('search_words'))
    if search_words != '_none':
        movies = Movie.query.order_by(db.desc(s.get(sort_key, 'id'))) \
            .filter(Movie.name.like(''.join(['%', search_words, '%']))).all()
    else:
        movies = Movie.query.order_by(db.desc(s.get(sort_key, 'id'))).limit(PAGE_SIZE).offset(
            (current_page - 1) * PAGE_SIZE)

    # movies = models.Movie.query.order_by(models.Movie.views)\
    # .paginate(current_page, per_page=PAGE_SIZE, error_out = False).items

    res = [{
        'id': m.id,
        'name': m.name,
        'genre': m.genres,
        'actor': m.actors,
        'director': m.director,
        'score': m.score,
        'views': m.view_nums,
        'video_path': m.video_path,
        'img_path': m.img_path
    } for m in movies]
    return jsonify(res)


@m.route('/search_movies')
def search_movies():
    s = request.args.get('search_words')
    if s is None:
        return jsonify([])
    movies = Movie.query.order_by(db.desc(Movie.name)) \
        .filter(Movie.name.like(''.join(['%', s, '%']))).all()
    res = [{
        'id': movie.id,
        'name': movie.name,
        'genre': movie.genres,
        'actor': movie.actors,
        'director': movie.director,
        'score': str(movie.score),
        'views': str(movie.view_nums),
        'video_path': movie.video_path
    } for movie in movies]
    return jsonify(res)


@m.route('/movie_details_page/<movie_id>', methods=['GET'])
def movie_details_page(movie_id):
    movie = Movie.query.get(int(movie_id))
    movie_key = 'movie:' + movie_id
    # save ip if no login
    id_or_ip = current_user.id if hasattr(current_user, 'id') else request.remote_addr
    redis_client.sadd(movie_key, id_or_ip)

    current_app.logger.info(f'{id_or_ip} '
                            f'views movie {movie.id}:{movie.name} nums:{movie.view_nums} '
                            f'redis_num:{redis_client.scard(movie_key)}')

    movie.view_nums += redis_client.scard(movie_key)

    # 超过 容量,删除重新开始. TODO 加入时间控制:时间窗口内同一用户或 ip 的多次访问算为一次.
    if redis_client.scard(movie_key) > MAX_CACHE_VIEW_NUM:
        current_app.logger.info(f'redis movie_view_nums full. update db')
        db.session.commit()
        redis_client.delete(movie_key)
        redis_client.sadd(movie_key, id_or_ip)

    return render_template('movie/movieDetail.html', movie=movie)


@m.route('/movie_details')
def movie_details():
    movie_id = request.args.get('movie_id')
    movie = Movie.query.get(int(movie_id))
    return jsonify(
        {'id': movie.id,
         'name': movie.name,
         'genres': movie.genres,
         'actors': movie.actors,
         'director': movie.director,
         'score': movie.score,
         'view_nums': movie.view_nums,
         'video_path': movie.video_path,
         'collect_nums': movie.collect_nums,
         'rating_nums': movie.rating_nums,
         'img_path': movie.img_path
         }
    )


@m.route('/movie_video/<movie_id>')
@login_required
def get_movie_video(movie_id):
    movie = Movie.query.get(int(movie_id))
    if movie is not None:
        return send_file(movie.video_path[1:], as_attachment=True)
    else:
        return 'error'


# 分页
@m.route('/movie_comments')
def get_all_movie_comments():
    movie_id = request.args.get('movie_id')
    curr_page = int(request.args.get('curr_page'))
    curr_page = 1 if curr_page is None else curr_page
    comments = Rating.query.order_by(db.desc(Rating.rating_date)).filter(
        Rating.movie_id == movie_id).limit(COMMENT_PAGE_SIZE).offset(
        (curr_page - 1) * COMMENT_PAGE_SIZE)

    res = [{
        'id': c.id,
        'eva_date': str(c.rating_date),
        'comment': c.comment,
        'score': c.rating,
        'username': c.user_id}
        for c in comments]
    return jsonify(res)


@m.route('/collect_movie', methods=['POST'])
@login_required
def collect_movie():
    movie_id = request.form['movie_id']
    mark = request.form['mark']

    user_id = current_user.id

    is_exist = UserCollection.query.filter(movie_id == UserCollection.movie_id,
                                           user_id == UserCollection.user_id).all()

    # 已经存在，直接返回
    if len(is_exist) != 0:
        return jsonify('collected')

    # 更新 movie 表中 collect_num 字段
    m = Movie.query.get(int(movie_id))
    if m is not None:
        m.collect_num += 1
    c = UserCollection(movie_id, user_id)
    c.mark = mark
    db.session.add(c)
    db.session.commit()
    return jsonify('success')


@m.route('/comment', methods=['POST'])
@login_required
def add_new_comments():
    comment = request.form['comment']
    score = request.form['score']
    movie_id = request.form['movie_id']

    curr_user_id = current_user.id

    # TODO 首先判断该用户是否已经评论打分过该电影
    me = Rating()
    me.comment = comment
    me.rating = score
    me.movie_id = movie_id
    me.user_id = curr_user_id

    db.session.add(me)
    db.session.commit()
    # 更新 movie 表中的平均得分
    avg_score = db.session.query(func.avg(Rating.score)
                                 .label('average')).filter(Rating.movie_id == movie_id).first()[0]
    movie = Movie.query.get(movie_id)
    if movie is not None:
        movie.score = avg_score
        movie.eva_num += 1

    db.session.commit()

    return jsonify({'res': 'success', 'score': avg_score})


@m.route('/personal_collect')
@login_required
def get_all_my_collections():
    user = current_user
    c = UserCollection.query.order_by(db.desc(UserCollection.collect_date)).filter(
        UserCollection.user_id == user.id).all()
    res = [{
        'id': i.id,
        'movie_id': i.movie.id,
        'movie_name': i.movie.name,
        'collect_date': str(i.collect_date),
        'mark': i.mark}
        for i in c
    ]
    return jsonify(res)


@m.route('/recommend_movies')
@login_required
def recommend_movies():
    user_id = current_user.id
    res = apriori.recommend_by_user_id(user_id)
    return jsonify(res)


@m.route('/del_collection')
@login_required
def del_collection():
    _id = request.args.get('id')
    if id is None:
        return 'error'
    c = UserCollection.query.get(int(_id))
    if c is None:
        return 'success'
    db.session.delete(c)

    db.session.commit()
    return jsonify('success')


@m.route('/movie_index')
def movie_index():
    return render_template('movie/movieIndex.html')


@m.route('/news_page')
def news_page():
    return render_template('feature/news.html')


@m.route('/my_collection')
@login_required
def collection_page():
    return render_template('user/myCollection.html')


@m.route('/my_recommend')
@login_required
def my_recommend_page():
    return render_template('user/my_recommend.html')
