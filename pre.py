__author__ = 'Sylvanus'

import numpy as np
import math
import pickle

def prepare():
    with open('dataCreep.txt', 'r') as f:
        lines = f.readlines()
    data = []
    for line in lines:
        data.append(line.strip().split())
    bookNum = len(data)
    d = {}
    bid = 0
    for book in data:
        for word in book:
            if word in d.keys():
                d[word][0].add(bid)
                d[word][1][bid] += 1
            else:
                d[word] = (set(), [1]*bookNum)
        bid += 1
    idf = {}
    for word in d.keys():
        idf[word] = math.log10(bookNum/len(d[word][0]))
    dic = {}
    for word in d.keys():
        dic[word] = (d[word][0], list(map(lambda x: (1+math.log10(x))/idf[word], d[word][1])), idf[word])
    norm = [0]*bookNum
    for word in d.keys():
        norm = [x+y*y for x, y in zip(norm, dic[word][1])]
    for word in d.keys():
        dic[word][1] = [x/y for x, y in zip(dic[word][1], norm)]
    with open('data.pkl', 'wb') as pkl_file:
        pickle._dump(dic, pkl_file)
    mat = np.array
    for word in d.keys():
        mat = np.array([mat, d[word][1]])
    sim = np.dot(mat.T, mat)
    top = [[None]*bookNum for i in range(3)]
    for i in range(bookNum):
        for j in range(3):
            top[i][j] = sim[i].argmax()
            sim[i][top[i][j]] = 0
    with open('similarity.pkl', 'wb') as pkl_file:
        pickle._dump(top, pkl_file)
