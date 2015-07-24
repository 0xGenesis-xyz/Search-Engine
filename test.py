__author__ = 'Sylvanus'

import pre
import init
import search

pre.prepare()

(hashtable, similarity) = init.loadData()
scores = init.login(2297)

text = ['小说', '十字']
booklist = search.doSearch(text, hashtable)
print('list: ', booklist)