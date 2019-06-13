import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules
from settings import db, apriori_model
import pickle
import numpy as np
import models
from boxx import timeit
from config import abs_path


class Apriori:
    def __init__(self):
        pass

    def fit(self):
        pass

    def top_rules(self):
        pass

    def predict(self):
        pass


def get_data():
    all_ratings = pd.read_sql('select * from rating where movieId in (select id from movie where rating_nums > 200)',
                              db.engine)
    records = [list(v.values) for k, v in all_ratings.groupby("userId")["movieId"]]
    print(len(records))
    return records


def generate_rules(min_support=0.1, min_confidence=0.7, test=False):
    d = get_data()
    if test:
        training = int(0.8 * len(d))
        dataset = d[:training]
        pickle.dump(dataset, open('training.pkl', 'wb'))
        pickle.dump(d[training:], open('test.pkl', 'wb'))
    te = TransactionEncoder()
    te_ary = te.fit(d).transform(d)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    frequent_itemsets = apriori(df, min_support=min_support, use_colnames=True)
    print(frequent_itemsets)

    a = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
    save_path = ''.join([abs_path, 'support-', str(min_support), '-confidence-', str(min_confidence), '.pkl'])
    pickle.dump(a, open(save_path, 'wb'))
    return a


# top 5
def samples_of_rules(model, num=20):
    a = model.sort_values('confidence', ascending=False)
    res = []

    for i, row in a[:num].iterrows():
        r = {'antecedents': get_movie_name_by_id(row['antecedents']),
             'consequents': get_movie_name_by_id(row['consequents']), 'confidence': row['confidence']}
        res.append(r)
        print(r)
    return res, a.shape[0]


def test_confidence():
    # generate_rules()
    a = pickle.load(open('fuck.pkl', 'rb'))
    print(a)
    test = pickle.load(open('test.pkl', 'rb'))
    print(len(test))
    c = []
    for j, t in enumerate(test):
        t = set(t)
        _true = 0
        _false = 0
        print('for user %d' % j)
        print(t)
        for i, row in a.iterrows():
            if row['antecedents'].issubset(t):
                if _is_in(row['consequents'], t):
                    _true += 1
                else:
                    _false += 1
                # print(row['antecedants'], row['consequents'])
        con = _true / (_true + _false) if _true != 0 else 0
        print(con)
        c.append(con)
        print('---------')
    print(np.mean(c))


# a is in b
def _is_in(a, b):
    t, f = 0, 0
    for i in a:
        if i not in b:
            f += 1
        else:
            t += 1
    if t == 0:
        return False

    return t / (t + f) >= 0.5


def recommend_by_user_id(user_id):
    user = models.User.query.get(int(user_id))
    if user is None:
        return False
    fav_movies = models.Rating.query.filter(models.Rating.user_id == user_id).all()

    print(f' fav movies length: {len(fav_movies)}')

    movie_id = [m.movie_id for m in fav_movies]
    a = apriori_model

    print(a.head())
    t = set(movie_id)

    recommend = set()
    for i, row in a.iterrows():
        if row['antecedents'].issubset(t):
            recommend = recommend | row['consequents']

    recommend -= t
    return get_movie_name_by_id(recommend)


def get_movie_name_by_id(movie_id):
    m = []
    for id in movie_id:
        movie = models.Movie.query.get(int(id))
        if movie:
            m.append(movie)

    res = [{
        'id': i.id,
        'name': i.name,
        'score': i.score,
        'img_path': i.img_path
    } for i in m]
    return res


if __name__ == '__main__':
    with timeit():
        generate_rules()

