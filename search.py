__author__ = 'Sylvanus'

from init import hashtable
from collections import Counter
import numpy as np
import math

def doSearch(text):
    wordfre = Counter(text)
    wordlist = list(wordfre.keys())
    indexlist = search(wordlist)
    Mweight = makeMatrix(wordlist, indexlist)
    Qweight = queryWeight(wordlist, wordfre)
    weight = np.dot(Qweight, Mweight)
    res = [(i, v) for i, v in enumerate(weight)]
    sorted(res, key=lambda item: item[1])
    return [i[0] for i in res]

def search(wordlist):
    indexlist = hashtable[wordlist[0]][0]
    for word in wordlist:
        indexlist = indexlist & hashtable[word][0]
    return indexlist

def makeMatrix(wordlist, indexlist):
    matrix = np.zeros((len(wordlist), len(indexlist)))
    i, j = 0, 0
    for word in wordlist:
        for index in indexlist:
            matrix[i][j] = hashtable[word][1][index]
            j += 1
        i += 1
    return matrix

def queryWeight(wordlist, wordfre):
    weight = np.array(len(wordlist))
    i = 0
    for word in wordlist:
        weight[i] = (1 + math.log10(wordfre[word])) * hashtable[word][2]
        i += 1
    return weight
