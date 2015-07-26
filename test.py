__author__ = 'Sylvanus'

import pre
import init
import search
import recommend

pre.prepare()

(hashtable, similarity) = init.loadData()
scores = init.login(2297)

text = ['小说', '十字']
booklist = search.doSearch(text, hashtable)
print('list: ', booklist)

recommender = recommend.recommend(booklist, similarity, scores)
print('recommender: ', recommender)
