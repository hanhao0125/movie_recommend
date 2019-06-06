import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules
from settings import db
import pickle
import numpy as np
import models
from config import abs_path


def get_data():
    all_ratings = pd.read_sql('select * from movie_eva where score >= 3', db.engine)
    records = [list(v.values) for k, v in all_ratings.groupby("user_id")["movie_id"]]
    print(records)
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
    return save_path.split('\\')[-1]


# top 5
def samples_of_rules(model_path='support-0.1-confidence-0.7.pkl', num=20):
    model_path = abs_path + model_path
    a = pickle.load(open(model_path, 'rb'))
    a = a.sort_values('confidence', ascending=False)
    res = []

    for i, row in a[:num].iterrows():
        r = {}
        r['antecedants'] = get_movie_name_by_id(row['antecedants'])
        r['consequents'] = get_movie_name_by_id(row['consequents'])
        r['confidence'] = row['confidence']
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
            if row['antecedants'].issubset(t):
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


# test_confidence()


def recommend_by_user_id(user_id, model_path='support-0.1-confidence-0.7.pkl'):
    model_path = abs_path + model_path
    user = models.User.query.get(int(user_id))
    if user is None:
        return False
    fav_movies = models.MovieEva.query.filter(models.MovieEva.user_id == user_id).all()
    print(fav_movies)
    movie_id = [m.movie_id for m in fav_movies if m.score >= 5]
    all_movie_id = set([m.movie_id for m in fav_movies])
    print(len(all_movie_id))
    a = pickle.load(open(model_path, 'rb'))
    t = set(movie_id)

    recommend = set()
    for i, row in a.iterrows():
        if row['antecedants'].issubset(t):
            recommend = recommend | row['consequents']

    recommend -= all_movie_id
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


# recommend_by_user_id(111)
# if __name__ == '__main__':
#     samples_of_rules()
