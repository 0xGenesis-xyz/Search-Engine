import csv
import os.path
import pickle

def get_all_bookid():
    if os.path.exists('bidset.pkl'):
        with open('bidset.pkl', 'rb') as f:
            return pickle.load(f)

    path = os.path.join('.', 'data', 'userbook.csv')
    with open(path, 'r') as csvf:
        book_infos = csv.reader(csvf)
        next(book_infos)
        bids = set((book_info[1] for book_info in book_infos))

    with open('bidset.pkl', 'wb') as f:
        pickle.dump(bids, f)

    return bids
