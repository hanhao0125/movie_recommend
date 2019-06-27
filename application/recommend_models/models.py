import os
from collections import defaultdict

import pandas as pd
from surprise import SVD, AlgoBase, Dataset, Reader, dump, KNNBaseline
from surprise.model_selection import cross_validate

from application.config import RECOMMEND_MODEL_SAVED_PATH
from application.database import Movie, Rating
from application.settings import db, logging
from pprint import pprint as pp


def svd():
    df = pd.read_sql("select userId,movieId,rating from rating", db.engine)
    reader = Reader(rating_scale=(1, 5), line_format='user item rating')
    print(df.head())
    data = Dataset.load_from_df(df, reader)
    trainset = data.build_full_trainset()
    algo = SVD()
    algo.fit(trainset)
    cross_validate(algo, data, measures=['RMSE', 'MAE'], verbose=True)
    dump.dump(f'{RECOMMEND_MODEL_SAVED_PATH}/svd', algo=algo)


def knn():
    df = pd.read_sql("select userId,movieId,rating from rating limit 10000000", db.engine)
    reader = Reader(rating_scale=(1, 5), line_format='user item rating')
    print(df.head())
    data = Dataset.load_from_df(df, reader)
    trainset = data.build_full_trainset()
    sim_options = {'name': 'pearson_baseline', 'user_based': True}

    algo = KNNBaseline(sim_options=sim_options)
    algo.fit(trainset)
    dump.dump(f'{RECOMMEND_MODEL_SAVED_PATH}/knn', algo=algo)
    print('saved to knn')
    cross_validate(algo, data, measures=['RMSE', 'MAE'], verbose=True)


class RecommendModel(object):
    def __init__(self, model_name, load_model=True):
        self.model_name = model_name
        self.model_dict = {
            'svd': f'{RECOMMEND_MODEL_SAVED_PATH}/svd'
        }
        self.model = None
        if load_model:
            self.load_model()

    def load_model(self):
        self.model = dump.load(self.model_dict[self.model_name])[1]

    def fit(self, trainset):
        if model_name == 'svd':
            model = SVD()
        model.fit(trainset)
        dump.dump(f'{RECOMMEND_MODEL_SAVED_PATH}/svd', algo=model)

    def predict_rating(self, uid, iid):
        uid = str(uid)
        iid = str(iid)
        p = self.model.predict(uid, iid, r_ui=4, verbose=True)
        return p

    def recommend_movies_by_similar_user(self, uid):
        uid = str(uid)
        inner_user_id = self.model.trainset.to_inner_uid(uid)
        neighbor_users = self.model.get_neighbors(inner_user_id, k=10)
        print('neighbor users inner id: ', neighbor_users)
        # 可能通过to_raw_uid把内部用户id转换为真实的用户id
        neighbor_raw_uid = []
        for u in neighbor_users:
            neighbor_raw_uid.append(self.model.trainset.to_raw_uid(u))
            print('real user id: ', self.model.trainset.to_raw_uid(u))
        all_movies = []
        for _uid in neighbor_raw_uid:
            all_movies += get_movies_by_uid(_uid)
        # drop the seen movie
        seen_movies = get_movies_by_uid(uid, k=1e10)
        # drop the duplicate movie by movie_id
        filter_movie = _filter_movie_by_id(all_movies, seen_movies)
        # sort by rating
        sorted_re_movies = sorted(filter_movie, key=lambda x: x.id, reverse=False)
        return sorted_re_movies

    def recommend_movies_by_similar_movie(self, uid):
        seen_movies = get_movies_by_uid(uid, k=10)
        similar_movie_ids = set()
        for m in seen_movies:
            inner_id = self.model.trainset.to_inner_iid(m["mid"])
            neighbors = self.model.get_neighbors(inner_id, 10)
            raw_ids = [self.model.trainset.to_raw_iid(_id) for _id in neighbors]
            similar_movie_ids.update(raw_ids)

        similar_movies = get_movies_details_by_ids(similar_movie_ids)
        sorted_sm = sorted(similar_movies, key=lambda x: x.rating, reverse=True)
        return sorted_sm

    def score_unseen_movie(self, uid):
        ratings = get_rating_by_uid(uid, seen=False)
        test_set = [(str(uid), str(r["movieId"]), r["rating"]) for r in ratings]
        predictions = self.model.test(test_set)
        pp(predictions)
        top_n = get_top_n_rating_for_one_user(predictions, n=10)
        return top_n


def get_unseen_movie(uid):
    ratings = Rating.query.filter(Rating.user_id != uid, )


def trans_rating_to_dict(r):
    return {
        'movieId': r.movie_id,
        'userId': r.user_id,
        'rating': r.rating
    }


def get_rating_by_uid(uid, seen=True):
    ratings = Rating.query.filter(Rating.user_id == uid if seen else Rating.user_id != uid).all()
    return [trans_rating_to_dict(r) for r in ratings]


def get_top_n_rating(predictions, n=10):
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_n[uid].append((iid, est))

    # Then sort the predictions for each user and retrieve the k highest ones.
    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n


def get_top_n_rating_for_one_user(predictions, n=-1):
    top_n = []
    for uid, iid, true_r, est, _ in predictions:
        top_n.append((iid, est))
    print(top_n)
    # Then sort the predictions for each user and retrieve the k highest ones.
    top_n.sort(key=lambda x: x[1], reverse=True)
    if n > 0:
        top_n = top_n[:n]
    return top_n


def _get_movie_by_id(movie_id):
    m = Movie.get(movie_id)
    return {"mid": m.id,
            "name": m.name,
            "img_path": m.img_path,
            "score": m.score}


def get_movies_details_by_ids(movie_ids):
    return [_get_movie_by_id(mid) for mid in movie_ids]


def _filter_movie_by_id(movies, seen_movies):
    unique_mid = {m.id for m in seen_movies}
    ret = []
    for m in movies:
        if m.id in unique_mid:
            continue
        else:
            ret.append(m)
            unique_mid.add(m.id)
    return ret


def get_movies_by_uid(uid, k=10):
    movie_ids = Rating.query.with_entities(Rating.movie_id).filter(Rating.user_id == uid).order_by(Rating.rating.desc()).limit(k).all()
    print(movie_ids)
    movies = [Movie.query.get(m[0]) for m in movie_ids]
    movies = [{"mid": m.id,
               "name": m.name,
               "img_path": m.img_path,
               "score": m.score}
              for m in movies]
    return movies

    def predict(self, userId):
        pass
