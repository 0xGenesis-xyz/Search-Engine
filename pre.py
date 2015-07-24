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
    print('bookNum:', bookNum)
    d = {}
    bid = 0
    for book in data:
        for word in book:
            if word in d.keys():
                d[word][0].add(bid)
                d[word][1][bid] += 1
            else:
                d[word] = (set([bid]), [0]*bookNum)
                d[word][1][bid] = 1
        bid += 1
    idf = {}
    for word in d.keys():
        idf[word] = math.log10(bookNum/len(d[word][0]))
    dic = {}
    for word in d.keys():
        print(word, ': ', d[word])
        dic[word] = (d[word][0], list(map(lambda x: (1+math.log10(x))*idf[word] if x>0 else 0,  d[word][1])), idf[word])
        print(word, ': ', dic[word])
    norm = [0]*bookNum
    for word in d.keys():
        norm = [x+y*y for x, y in zip(norm, dic[word][1])]
    for word in d.keys():
        dic[word] = (d[word][0], [x/y for x, y in zip(dic[word][1], norm)], idf[word])
    with open('data.pkl', 'wb') as pkl_file:
        pickle._dump(dic, pkl_file)
    mat = np.array([value[1] for value in dic.values()])
#    for word in d.keys():
#        mat = np.vstack([mat, d[word][1]])
    print('mat:')
    print(mat)
    sim = np.dot(mat.T, mat)
    top = [[None]*bookNum for i in range(3)]
    print('sim:')
    print(sim)
    for i in range(bookNum):
        for j in range(3):
            top[i][j] = sim[i].argmax()
            sim[i, top[i][j]] = 0
    print('top:')
    print(top)
    with open('similarity.pkl', 'wb') as pkl_file:
        pickle._dump(top, pkl_file)
