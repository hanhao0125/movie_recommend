import os
from collections import defaultdict
from pprint import pprint as pp
from typing import *

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.spatial.distance import cosine
from sklearn import metrics
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from surprise import SVD, AlgoBase, Dataset, KNNBaseline, Reader, dump
from surprise.model_selection import cross_validate

from application.config import RECOMMEND_MODEL_SAVED_PATH
from application.database import Movie, Rating, User
from application.settings import db


class Cluster:
    def __init__(self):
        self.model = dump.load(f'{RECOMMEND_MODEL_SAVED_PATH}/svd')[1]
        self.d = self.model.trainset

    def get_vector_by_user_id(self, uid: int) -> np.array:
        user_raw_idx = self.d._raw2inner_id_users[uid]
        return self.model.pu[user_raw_idx]

    def get_vector_by_movie_id(self, mid: int) -> np.array:
        """Returns the latent features of a movie in the form of a numpy array"""
        movie_row_idx = self.d._raw2inner_id_items[mid]
        return self.model.qi[movie_row_idx]

    def all_user_vectors(self):
        # first get all user vector
        user_vectors = []
        user_ids = User.query.with_entities(User.id).all()
        for uid in user_ids:
            user_vectors.append(self.get_vector_by_user_id(uid[0]))
        user_vectors = np.array(user_vectors)
        print(user_vectors.shape)
        print(user_vectors)
        return user_vectors

    def all_movie_vectors(self):
        # first get all user vector
        movie_vectors = []
        movie_ids = Movie.query.with_entities(Movie.id).all()
        for mid in movie_ids:
            movie_vectors.append(self.get_vector_by_user_id(mid[0]))
        movie_vectors = np.array(movie_vectors)
        print(movie_vectors.shape)
        return movie_vectors

    def kmeans(self):
        X = self.all_user_vectors()
        clf = KMeans(3)
        y_pred = clf.fit_predict(X)

        m = metrics.calinski_harabaz_score(X, y_pred)
        print(m)
        return X, y_pred

    def visualization(self):
        X, y_pred = self.kmeans()
        pca = PCA(n_components=2)
        new_x = pca.fit_transform(X)
        print(new_x.shape, y_pred.shape)
        plt.scatter(new_x[:, 0], new_x[:, 1], c=y_pred)
        plt.show()
