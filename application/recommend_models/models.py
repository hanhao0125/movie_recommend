import os
from collections import defaultdict
from pprint import pprint as pp

import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine
from surprise import SVD, AlgoBase, Dataset, KNNBaseline, Reader, dump
from surprise.model_selection import cross_validate

from application.config import RECOMMEND_MODEL_SAVED_PATH
from application.database import Movie, Rating
from application.settings import db
from typing import *
# ! surprise fucked.
# ! one should always keep the type the raw id and inner id in mind
# ! surprise default thinks the raw id is str, and docs said to_inner_uid(ruid), the ruid is str.
# ! (but my fucking data is int), and the code just trans the raw id to inner_id(int), didn't trans the raw id to str
# ! so the author think to_inner_uid is mappint str to int , but when your ruid is int , it actually turns int to int
# ! you can print the trainset._raw2inner_id_users to verify the type
# ! FUCK.


def svd():
    df = pd.read_sql("select userId,movieId,rating from rating limit 20000", db.engine)
    reader = Reader(rating_scale=(1, 5))
    print(df.tail())
    data = Dataset.load_from_df(df[['userId', 'movieId', 'rating']], reader)

    trainset = data.build_full_trainset()
    print(trainset._raw2inner_id_users)
    print(trainset.n_users, trainset.n_items, trainset.n_ratings)
    algo = SVD(n_epochs=20)
    algo.fit(trainset)
    dump.dump(f'{RECOMMEND_MODEL_SAVED_PATH}/svd_simple', algo=algo)
    cross_validate(algo, data, measures=['RMSE', 'MAE'], verbose=True)


def knn():
    df = pd.read_sql("select userId,movieId,rating from rating", db.engine)
    print('finished load data')
    reader = Reader(rating_scale=(1, 5), line_format='user item rating')
    print(df.head())
    data = Dataset.load_from_df(df, reader)
    trainset = data.build_full_trainset()
    sim_options = {'name': 'pearson_baseline', 'user_based': True}

    algo = KNNBaseline(sim_options=sim_options)
    print('start fit')
    algo.fit(trainset)
    dump.dump(f'{RECOMMEND_MODEL_SAVED_PATH}/knn', algo=algo)
    print('saved to knn')
    cross_validate(algo, data, measures=['RMSE', 'MAE'], verbose=True)


def warp_object(ids, func):
    return [func(i) for i in ids]


class RecommendModel(object):
    """
    In out system, uid and mid all int.
    So args of trainset.knows_user ,  predict and _raw2inner_id_users is int
    """

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

    def get_vector_by_user_id(self, uid: int) -> np.array:
        user_raw_idx = self.model.trainset._raw2inner_id_users[uid]
        return self.model.pu[user_raw_idx]

    def get_vector_by_movie_id(self, mid: int) -> np.array:
        """Returns the latent features of a movie in the form of a numpy array"""
        movie_row_idx = self.model.trainset._raw2inner_id_items[mid]
        return self.model.qi[movie_row_idx]

    @staticmethod
    def cosine_distance(vector_a: np.array, vector_b: np.array) -> float:
        """Returns a float indicating the similarity between two vectors"""
        return cosine(vector_a, vector_b)

    def get_top_similarities_users(self, uid: int, n=5) -> List:
        """Returns the top 5 most similar users to a specified user
        This function iterates over every possible user in MovieLens and calculates
        distance between `uid` vector and that movie's vector.
        """
        # Get the first movie vector
        user_vector: np.array = self.get_vector_by_user_id(uid)
        similarity_table = []

        # Iterate over every possible movie and calculate similarity
        for other_user_id in self.model.trainset._raw2inner_id_users.keys():
            other_user_vector = self.get_vector_by_user_id(other_user_id)

            # Get the second movie vector, and calculate distance
            similarity_score = self.cosine_distance(other_user_vector, user_vector)
            similarity_table.append((similarity_score, other_user_id))

        # sort movies by ascending similarity
        # * most similar is itself, so slice [1:n+1]
        similarity_table = sorted(similarity_table)[1:n+1]
        return similarity_table

    def get_top_similarities(self, mid: int, n=5) -> List:
        """Returns the top 5 most similar movies to a specified movie
        This function iterates over every possible movie in MovieLens and calculates
        distance between `mid` vector and that movie's vector.
        """
        # Get the first movie vector
        movie_vector: np.array = self.get_vector_by_movie_id(mid)
        similarity_table = []

        # Iterate over every possible movie and calculate similarity
        for other_movie_id in self.model.trainset._raw2inner_id_items.keys():
            other_movie_vector = self.get_vector_by_movie_id(other_movie_id)

            # Get the second movie vector, and calculate distance
            similarity_score = self.cosine_distance(other_movie_vector, movie_vector)
            similarity_table.append((similarity_score, other_movie_id))

        # sort movies by ascending similarity
        # * most similar is itself, so slice [1:n+1]
        similarity_table = sorted(similarity_table)[1:n+1]
        return similarity_table

    def recommend_movies_by_similar_user(self, uid, n=10):
        similar_users = self.get_top_similarities_users(uid)
        rm = {}
        for sm in similar_users:
            t = []
            for mid in get_liked_movies(sm[1]):
                t.append(get_movie_object_by_id(mid))
            rm[sm[1]] = t
        return rm

    def recommend_movies_by_similar_movie(self, uid: int, thres: float = 3.5):
        """
        recommend movies by similar movie. first fetch user loved movie( controll by >= thres)
        then calculate the simility.

        Arguments:
            uid {[int]}
            thres: threshold that decide weather user like a movie

        Returns:
            recommend movies.
        """
        liked_movies = get_liked_movies(uid, thres=thres, n=10)
        similar_movies = {}
        for mid in liked_movies:
            t = []
            for s in self.get_top_similarities(mid):
                m = get_movie_object_by_id(s[1])
                m['sim'] = s[0]
                t.append(m)
            similar_movies[mid] = t
        return similar_movies

    def recommend_movies_by_predict_ratings(self, uid: int, n=10, thres=3.5):
        # unseen_ratings = get_rating_by_uid(uid, seen=False)
        unseen_movie_ids = get_movie_ids_by_uid(uid)
        predict_ratings = []
        for mid in unseen_movie_ids:
            # mid must be rating
            if self._check_mid_exist(mid):
                p = self.predict_rating(uid, mid)
                d = get_movie_object_by_id(mid)
                d['est'] = p.est
                predict_ratings.append(d)

        # sort by rating and get top n
        predict_ratings.sort(key=lambda x: x["est"], reverse=True)
        if n > 0:
            return predict_ratings[:n]
        else:
            return predict_ratings

    def verify_ratings(self, uid: int):
        ratings = get_rating_by_uid(uid, seen=True)
        test_set = [(uid, r["movieId"], r["rating"]) for r in ratings]
        predictions = self.model.test(test_set)
        pp(predictions)
        top_n = get_top_n_rating_for_one_user(predictions, n=10)
        return top_n

    def score_unseen_movie(self, uid):
        ratings = get_rating_by_uid(uid, seen=False)
        test_set = [(str(uid), str(r["movieId"]), r["rating"]) for r in ratings]
        predictions = self.model.test(test_set)
        pp(predictions)
        top_n = get_top_n_rating_for_one_user(predictions, n=10)
        return top_n

    def _check_uid_exist(self, uid: int):
        return uid in self.model.trainset._raw2inner_id_users
        # return self.model.trainset.knows_user(self.model.trainset.to_inner_uid(uid))

    def _check_mid_exist(self, mid: int):
        return mid in self.model.trainset._raw2inner_id_items
        # return self.model.trainset.knows_item(self.model.trainset.to_inner_iid(mid))

    def _check_uid_and_mid_exist(self, uid, mid):
        return self._check_uid_exist(uid) and self._check_mid_exist(mid)

    def predict_rating(self, uid: int, mid: int):
        if self._check_uid_exist(uid):
            # if self._check_uid_and_mid_exist(uid, mid):
            return self.model.predict(uid, mid)
        else:
            raise KeyError(f'({uid},{mid})uid and mid not exist. make sure you have int type.')

    def get_n_ratings(self, n=10):
        r = pd.read_sql(f'select userId,movieId,rating from rating limit {n}', db.engine)
        return r


def get_liked_movies(uid, thres=3.5, n=10):
    movies = Rating.query.with_entities(Rating.movie_id).filter(
        Rating.user_id == uid and Rating.rating >= thres).order_by(Rating.rating.desc()).all()
    return [m[0] for m in movies][:n]


def trans_rating_to_dict(r):
    return {
        'movieId': r.movie_id,
        'userId': r.user_id,
        'rating': r.rating
    }


def get_movie_ids_by_uid(uid: int, mode='unseen'):
    """
    uid: user id
    model: unseen-> noe seen movie ids; seen: seen movie ids; all: all movie ids
    """
    if mode == "all":
        return [m[0] for m in Movie.query.with_entities(Movie.id).all()]
    elif mode == "seen":
        seen_movie_ids = Rating.query.with_entities(Rating.movie_id).filter(Rating.user_id == uid).all()
        seen_movie_ids = [i[0] for i in seen_movie_ids]
        return seen_movie_ids
    elif mode == "unseen":
        all_movie = [m[0] for m in Movie.query.with_entities(Movie.id).all()]
        seen_movie_ids = Rating.query.with_entities(Rating.movie_id).filter(Rating.user_id == uid).all()
        return set(all_movie) - set([i[0] for i in seen_movie_ids])


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
    # Then sort the predictions for each user and retrieve the k highest ones.
    top_n.sort(key=lambda x: x[1], reverse=True)
    if n > 0:
        top_n = top_n[:n]
    return top_n


def get_movie_object_by_id(mid: int):
    m = Movie.query.get(mid)
    if m:
        return vars(m)
    else:
        print(f'None object, please check the movie_id exist:{mid}')
        return None


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
    movie_ids = Rating.query.with_entities(Rating.movie_id).filter(
        Rating.user_id == uid).order_by(Rating.rating.desc()).limit(k).all()
    print(movie_ids)
    movies = [Movie.query.get(m[0]) for m in movie_ids]
    movies = [{"mid": m.id,
               "name": m.name,
               "img_path": m.img_path,
               "score": m.score}
              for m in movies]
    return movies
