import os, sys
import pandas as pd
from collections import defaultdict
from operator import itemgetter

data_fold = "ml-100k"


# 对原始数据进行处理
def data_deal():
    ratings_filename = os.path.join(data_fold, "u.data")
    all_ratings = pd.read_csv(ratings_filename, delimiter="\t", header=None,
                              names=["UserID", "MovieID", "Rating", "DateTime"])
    all_ratings["DateTime"] = pd.to_datetime(all_ratings["DateTime"], unit="s")
    # 为了判断用户是否喜欢某一部电影，增加一个属性Favorable(打分大于3则表示喜欢)
    all_ratings["Favorable"] = all_ratings["Rating"] > 3
    return all_ratings


# 定义属性作为推荐的依据
def getFeature(ratings):
    # 筛选只包含喜欢电影的用户数据集
    favorate_ratings = ratings[ratings["Favorable"]]
    # 下面需要知道每个用户喜欢什么电影，即按照用户ID进行分组,格式为：用户ID：{电影ID集合}
    favorate_reviews_by_users = dict((k, frozenset(v.values)) for k, v in favorate_ratings.groupby("UserID")["MovieID"])
    # 定义每部电影的影迷数
    num_favorable_by_movie = ratings[["MovieID", "Favorable"]].groupby("MovieID").sum()
    # 按照影迷数进行排序
    num_favorable_by_movie = num_favorable_by_movie.sort_values("Favorable", ascending=False)
    return favorate_reviews_by_users, num_favorable_by_movie


# 生成频繁项集
def find_frequent_itemsets(favorable_reviews_by_users, k_1_itemsets, min_support):
    counts = defaultdict(int)
    for user, reviews in favorable_reviews_by_users.items():
        for itemset in k_1_itemsets:
            # 判断是否为集合的子集
            if itemset.issubset(reviews):
                # 由LK生成Ck+1
                for other_reviewed_movie in reviews - itemset:
                    current_superset = itemset | frozenset((other_reviewed_movie,))
                    counts[current_superset] += 1
    # 由CK+1生成Lk+1
    return dict([(itemset, frequency) for itemset, frequency in counts.items() if frequency >= min_support])


# 通过电影ID获取电影名称
def get_movie_name(movie_id):
    movie_name_filename = os.path.join(data_fold, "u.item")
    movie_name_data = pd.read_csv(movie_name_filename, delimiter="|", header=None, encoding="mac-roman")
    movie_name_data.columns = ["MovieID", "Title", "Release Date", "Video Release", "IMDB", "<UNK>", "Action",
                               "Adventure", "Animation", "Children's", "Comedy", "Crime", "Documentary", "Drama",
                               "Fantasy", "Film-Noir", "Horror", "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller",
                               "War", "Western"]

    title_object = movie_name_data[movie_name_data["MovieID"] == movie_id]["Title"]
    title = title_object.values[0]
    return title


# 下面将通过频繁项集来生成关联规则。
def generateRule(frequent_itemsets, favorate_reviews_by_users):
    candidate_rules = []
    for itemset_length, itemset_counts in frequent_itemsets.items():
        # itemset存放频繁项集
        for itemset in itemset_counts.keys():
            for conclusion in itemset:
                premise = itemset - set((conclusion,))
                # 这样就得到大量的规则，但还需要进一步的筛选
                candidate_rules.append((premise, conclusion))

        correct_counts = defaultdict(int)
        incorrect_counts = defaultdict(int)
        for user, reviews in favorate_reviews_by_users.items():
            for candidate_rule in candidate_rules:
                premise, conclusion = candidate_rule
                # 判断用户是否喜欢前提里的所有电影,只有都喜欢，规则才适用。
                if premise.issubset(reviews):
                    # 判断结论里所有的电影，用户是否喜欢
                    if conclusion in reviews:
                        correct_counts[candidate_rule] += 1
                    else:
                        incorrect_counts[candidate_rule] += 1

    # 计算置信度：用规则应验的次数除以前提条件出现的总次数。 格式为{规则：置信度}
    rule_confidence = {candidate_rule: correct_counts[candidate_rule] / float(
        correct_counts[candidate_rule] + incorrect_counts[candidate_rule])
                       for candidate_rule in candidate_rules}
    # 规则按照置信度大小进行排序。
    sorted_confidence = sorted(rule_confidence.items(), key=itemgetter(1), reverse=True)
    return sorted_confidence


# 按照指定的格式打印前5条规则
def print_rule_top5(sorted_confidence):
    for index in range(5):
        print("Rule #{0}".format(index + 1))
        (premise, conclusion) = sorted_confidence[index][0]
        premise_names = ", ".join(get_movie_name(idx) for idx in premise)
        conclusion_name = get_movie_name(conclusion)
        print("Rule: If a person recommends {0} they will also  recommend {1}".format(premise_names, conclusion_name))
        print(" - Confidence:{0:.3f}".format(sorted_confidence[index][1]))


def get_rule(ratings):
    frequent_itemsets = {}
    min_support = 50
    favorate_reviews_by_users, num_favorable_by_movie = getFeature(ratings)
    # 定义频繁一项集
    frequent_itemsets[1] = dict(
        (frozenset((movie_id,)), row["Favorable"]) for movie_id, row in num_favorable_by_movie.iterrows() if
        row["Favorable"] > min_support)
    # 生成频繁项集
    for k in range(2, 20):
        cur_frequent_itemsets = find_frequent_itemsets(favorate_reviews_by_users, frequent_itemsets[k - 1], min_support)
        frequent_itemsets[k] = cur_frequent_itemsets
        if len(cur_frequent_itemsets) == 0:
            sys.stdout.flush()
            break
        else:
            sys.stdout.flush()
    # 删除频繁一项集,因为频繁一项集不能生成关联规则
    del frequent_itemsets[1]
    # 生成关联规则
    sorted_confidence = generateRule(frequent_itemsets, favorate_reviews_by_users)
    return sorted_confidence


if __name__ == "__main__":
    # 获取处理后的数据
    all_ratings = data_deal()
    # 由于电脑配置问题，只选择用户ID为1到200的用户，这样出结果相对较快
    ratings_test = all_ratings[all_ratings["UserID"].isin(range(201))]
    sorted_confidence_test = get_rule(ratings_test)
    print_rule_top5(sorted_confidence_test)
