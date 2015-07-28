__author__ = 'Sylvanus'

#from init import hashtable
from collections import Counter
import math
import sqlite3

import numpy as np
from scipy import sparse
from sklearn.preprocessing import normalize

from matrix import Matrix

class Search(object):
    K = 10    # Only show K highest ranked results
    def __init__(self):
        self.matrix = Matrix()

    def search(self, query):
        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        for bid in self.matrix.tiered_search(self, query):
            with open('text/{}.txt'.format(bid), 'r') as f:
                print(f.read(), end='\n\n')

def doSearch(text, hashtable):
    wordfre = Counter(text)
    wordlist = list(wordfre.keys())
    print(wordlist)
    indexlist = search(wordlist, hashtable)
    print('indexlist: ', indexlist)
    Mweight = makeMatrix(wordlist, indexlist, hashtable)
    print('Mweight: ', Mweight)
    Qweight = queryWeight(wordlist, wordfre, hashtable)
    print('Qweight: ', Qweight)
    weight = np.dot(Qweight, Mweight)
    print('weight: ', weight)
    res = [(i, v) for i, v in enumerate(weight)]
    print('res:', res)
    sorted(res, key=lambda item: item[1])
    print('res:', res)
    ans = [None]*len(res)
    i = 0
    for a in indexlist:
        ans[i] = a
        i += 1
    print('ans: ', ans)
    return [ans[i[0]] for i in res]

def search(wordlist, hashtable):
    indexlist = hashtable[wordlist[0]][0]
    for word in wordlist:
        indexlist = indexlist & hashtable[word][0]
    return indexlist

def makeMatrix(wordlist, indexlist, hashtable):
    matrix = np.zeros((len(wordlist), len(indexlist)))
    i, j = 0, 0
    for word in wordlist:
        for index in indexlist:
            print(hashtable[word][1])
            matrix[i][j] = hashtable[word][1][index]
            j += 1
        i += 1
        j = 0
    return matrix

def queryWeight(wordlist, wordfre, hashtable):
    weight = np.array([None]*len(wordlist))
    i = 0
    norm = 0
    for word in wordlist:
        print('qW: ', hashtable[word])
        weight[i] = (1 + math.log10(wordfre[word])) * hashtable[word][2]
        norm += weight[i]
        i += 1
    return [x/math.sqrt(norm) for x in weight]
