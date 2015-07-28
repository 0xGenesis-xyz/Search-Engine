__author__ = 'Sylvanus'

import pickle
import scipy.io as sio

#hashtable = None
#similarity = None
#scores = None

def loadData():
#    global hashtable
#    global similarity
    with open('data.pkl', 'rb') as pkl_file:
        hashtable = pickle.load(pkl_file)
    with open('similarity.pkl', 'rb') as pkl_file:
        similarity = pickle.load(pkl_file)
    print('hashtable:', hashtable)
    return (hashtable, similarity)

def login(uid):
    data = sio.loadmat('data.mat')
    user = 0
    for id in data['userhashInv'][0]:
        if id==uid:
            break
        user += 1
    scores = data['pred'][user]
    return scores
#    with open('score.txt', 'rb') as f:
#        u = 0
#        line = f.readline()
#        while line:
#            if u==user:
#                break
#            else:
#                u += 1
#            line = f.readline()
#    scores = [float(score) for score in line.split()]
