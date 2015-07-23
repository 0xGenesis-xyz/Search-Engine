__author__ = 'Sylvanus'

import pickle

hashtable = None
similarity = None
scores = None

def loadData():
    with open('data.pkl', 'rb') as pkl_file:
        hashtable = pickle.load(pkl_file)
    with open('similarity.pkl', 'rb') as pkl_file:
        similarity = pickle.load(pkl_file)

def login(uid):
    user = uid
    with open('score.txt', 'r') as f:
        u = 0
        line = f.readline()
        while line:
            if u==user:
                break
            else:
                u += 1
            line = f.readline()
    scores = [float(score) for score in line.split()]
