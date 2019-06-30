import import_parent
from application.recommend_models import models, cluster
import unittest
from pprint import pprint as pp


class TestRecommendModels():
    def __init__(self):
        self.m = models.RecommendModel(model_name="svd")
        # return super().__init__(methodName)
    # def test_surprise_model(self,):
    # models.svd()

    def test_get_movies_by_id(self):
        p = models.get_movie_ids_by_uid(1, mode='all')
        assert len(p) == 27278

    def test_verify_rating(self):
        self.m.verify_ratings(1)

    def test_check_uid(self,):
        assert self.m._check_uid_exist(1)
        assert self.m._check_mid_exist(131072)
        assert self.m._check_uid_and_mid_exist(1, 131072)

    def test_get_movie_object_by_id(self):
        a = models.get_movie_object_by_id(1)
        pp(a)

    def test_recommend_movies_by_predict_ratings(self):
        p = self.m.recommend_movies_by_predict_ratings(1, n=-1)
        pp(p)

    def test_recommend_by_similar_movie(self):
        a = self.m.recommend_movies_by_similar_movie(1)
        pp(a)

    def test_recommend_movies_by_similar_user(self,):
        a = self.m.recommend_movies_by_similar_user(1)
        pp(a)


class TestCluster():
    def __init__(self):
        self.c = cluster.Cluster()

    def test_cluster(self):
        self.c.cluster()

    def test_visualization(self):
        self.c.visualization()


if __name__ == "__main__":
    t = TestCluster()
    t.test_visualization()
    # t = TestRecommendModels()
    # t.test_check_uid()
    # t.test_verify_rating()
    # t.test_recommend_movies_by_predict_ratings()
    # t.test_recommend_movies_by_similar_user()
    # t.test_recommend_by_uid()
    # t.test_recommend_by_similar_movie()
    # t.test_get_movie_object_by_id()
    # unittest.main()
    # models.knn()
