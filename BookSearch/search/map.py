__author__ = 'Sylvanus'

import pickle
import scipy.io as sio

data = sio.loadmat('data.mat')

itemmap = {}
book = 0
for bid in data['itemhashInv'][0]:
    itemmap[bid] = book
    book += 1

with open('itemmap.pkl', 'wb') as pkl_file:
    pickle._dump(itemmap, pkl_file)

usermap = {}
user = 0
for uid in data['userhashInv'][0]:
    usermap[uid] = user
    user += 1

with open('usermap.pkl', 'wb') as pkl_file:
    pickle._dump(usermap, pkl_file)

print(len(itemmap))