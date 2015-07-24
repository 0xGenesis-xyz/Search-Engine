__author__ = 'Sylvanus'

import pre
import init
import search

pre.prepare()

init.loadData()
init.login(2297)

print('hashtable', init.hashtable)

text = ['小说']
booklist = search.doSearch(text)
print(booklist)