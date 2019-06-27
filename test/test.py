import import_parent
from application.recommend_models import models
import unittest


class TestRecommendModels(unittest.TestCase):
    # def test_surprise_model(self,):
        # models.svd()

    def test_recommend_by_uid(self):
        m = models.RecommendModel(model_name="svd")
        print(m.score_unseen_movie(1288))


if __name__ == "__main__":
    # unittest.main()
    models.knn()
