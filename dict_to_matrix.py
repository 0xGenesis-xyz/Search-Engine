from collections import defaultdict
import numpy as np
from scipy import sparse
from parser import Parser
import bookid

class DictToMatrix(object):
    def __init__(self):
        self.dictionary = Parser.load_dictionary()
        self.bids = bookid.get_all_bookid()
        self.term_to_row = {term: row for row, term in enumerate(self.dictionary)}
        self.bid_to_col = {bid: col for col, bid in enumerate(self.bids)}
        self.matrix = self.term_bid_matrix()

    def term_bid_matrix(self):
        m = sparse.dok_matrix((len(self.term_to_row), len(self.bid_to_col)), 'u')
        for term, bids in self.dictionary.items():
            row = self.term_to_row[term]
            for bid, freq in bids.items():
                col = self.bid_to_col[bid]
                m[row, col] = freq
        return m

if __name__ == '__main__':
    d2m = DictToMatrix()
