"""Convert inverted indexes to a matrix for computation."""

from collections import defaultdict
from functools import reduce
import os.path
import pickle

import parser

import numpy as np
from numpy import linalg as LA
from scipy import sparse
from sklearn.preprocessing import normalize

from parser import Parser
import bookid

class DictToMatrix(object):
    def __init__(self):
        self.dictionary = Parser.load_dictionary()
        self.bids = bookid.get_all_bookid()
        self.term_to_row = self.load_term_to_row()
        #self.row_to_term = {row: term for term, row in self.term_to_row.items()}
        self.bid_to_col = self.load_bid_to_col()
        #self.col_to_bid = {col: bid for bid, col in self.bid_to_col.items()}
        self.term_bid_matrix = self.load_term_bid_matrix()
        self.parser = Parser()

    def __del__(self):
        self.save_term_bid_matrix(self.term_bid_matrix)
        self.save_bid_to_col(self.bid_to_col)
        self.save_term_to_row(self.term_to_row)

    def load_term_to_row(self):
        if os.path.exists('term_to_row.pkl'):
            with open('term_to_row.pkl', 'rb') as f:
                return pickle.load(f)
        return {term: row for row, term in enumerate(self.dictionary)}

    def load_bid_to_col(self):
        if os.path.exists('bid_to_col.pkl'):
            with open('bid_to_col.pkl', 'rb') as f:
                return pickle.load(f)
        return {bid: col for col, bid in enumerate(self.bids)}

    def load_term_bid_matrix(self):
        if os.path.exists('term_bid_matrix.pkl'):
            with open('term_bid_matrix.pkl', 'rb') as f:
                return pickle.load(f)
        m = sparse.dok_matrix((len(self.term_to_row), len(self.bid_to_col)), dtype=int)

        # Get term/bid matrix
        for term, bids in self.dictionary.items():
            row = self.term_to_row[term]
            for bid, freq in bids.items():
                col = self.bid_to_col[bid]
                m[row, col] = freq
        return m.tocsc()

    @staticmethod
    def save_term_bid_matrix(m):
        with open('term_bid_matrix.pkl', 'wb') as f:
            pickle.dump(m, f)

    @staticmethod
    def save_term_to_row(m):
        with open('term_to_row.pkl', 'wb') as f:
            pickle.dump(m, f)

    @staticmethod
    def save_bid_to_col(m):
        with open('bid_to_col.pkl', 'wb') as f:
            pickle.dump(m, f)

    def boolean_search(self, query, _cosine=False):
        """Search a query according to its ocurrence in the documents and return matched results."""
        terms = self.parser.parse_query(query)
        result = reduce(set.union,
                        (set(self.dictionary.get(term, []))
                         for term in terms))
        if _cosine:
            return result, terms
        else:
            return result

    def cosine_similarity_search(self, query):
        """Search a query according to its relevance to the documents and return a ranked result."""
        N = len(self.bid_to_col)    # column number
        tf = lambda freq: 1 + np.log10(freq)
        idf = lambda term: np.log10(N / len(self.dictionary[term]))

        bids, terms = self.boolean_search(query, True)
        # Supposing q is a row vector
        q = sparse.dok_matrix((1, len(self.term_to_row)))
        # Build query frequency vector
        for term, freq in terms.items():
            q[0,self.term_to_row[term]] = tf(freq) * idf(term)    # Use tf-idf instead of freq

        q = normalize(q.tocsr(), axis=1, copy=False)
        matched_cols = self.term_bid_matrix[:,[self.bid_to_col[bid] for bid in bids]]
        matched_cols.data = tf(matched_cols.data)    # idf has been computed in q
        matched_cols = normalize(matched_cols.transpose(), axis=1, copy=False).transpose()
        cosine_similarity = q.dot(matched_cols)
        ranked = sorted(zip(cosine_similarity.toarray()[0], bids), reverse=True)

        return (r[1] for r in ranked)

def test():
    d2m = DictToMatrix()
    """
    for bid in d2m.boolean_search('一个中学生'):
        path = os.path.join('text', bid + '.txt')
        with open(path, 'r') as f:
            print(f.read())
    """
    count = 0
    for bid in d2m.cosine_similarity_search('陀思妥耶夫斯基 卡拉马佐夫'):
        count += 1
        if count > 10:
            break
        path = os.path.join('text', bid + '.txt')
        with open(path, 'r') as f:
            print(f.read())


if __name__ == '__main__':
    test()
