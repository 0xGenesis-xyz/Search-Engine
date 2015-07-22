import csv
import os.path

def get_all_bookid():
    path = os.path.join('.', 'data', 'userbook.csv')
    with open(path, 'r') as csvf:
        book_infos = csv.reader(csvf)
        next(book_infos)
        bids = set((book_info[1] for book_info in book_infos))

    return sorted(bids)
