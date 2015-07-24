__author__ = 'Sylvanus'

import pickle
import scipy.io as sio

class Init(object):
    def __init__(self):

        self.hashtable = None
        self.similarity = None
        self.scores = None

    def loadData(self):
        with open('data.pkl', 'rb') as pkl_file:
            self.hashtable = pickle.load(pkl_file)
        with open('similarity.pkl', 'rb') as pkl_file:
            self.similarity = pickle.load(pkl_file)

    def login(self, uid):
        data = sio.loadmat('data.mat')
        user = 0
        for id in data['userhashInv'][0]:
            if id==uid:
                break
            user += 1
        self.scores = data['pred'][user]
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
