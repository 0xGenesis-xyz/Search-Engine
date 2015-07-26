"""Convert inverted indexes to a matrix for computation."""

from collections import defaultdict
import heapq
from functools import reduce
import os.path
import pickle
import sqlite3

import parser

import numpy as np
from numpy import linalg as LA
from scipy import sparse
from sklearn.preprocessing import normalize

from parser import Parser
import bookid

class Matrix(object):
    k1, k2, b = 1.5, 1.5, 0.75    # Parameters
    def __init__(self):
        self.bids = bookid.get_all_bookid()
        self.dictionary = self.load_dictionary()
        self.higher_tier_dictionary = self.load_higher_tier_dictionary()
        self.term_to_row = self.load_term_to_row()
        self.bid_to_col = self.load_bid_to_col()
        self.N = len(self.bid_to_col)    # Total number of documents
        self.M = len(self.term_to_row)    # Total number of terms
        #self.row_to_term = {row: term for term, row in self.term_to_row.items()}
        #self.col_to_bid = {col: bid for bid, col in self.bid_to_col.items()}
        self.term_bid_matrix = self.load_term_bid_matrix()
        self.title_term_bid_matrix = self.load_title_term_bid_matrix()

        # Tiers, tier[0] is the highest tier
        self.dicts = (self.dictionary,
                      self.higher_tier_dictionary)
        self.mats = (self.term_bid_matrix,
                     self.title_term_bid_matrix)
        self.parser = Parser()

    def __del__(self):
        self.save_term_bid_matrix()
        self.save_title_term_bid_matrix()
        self.save_dictionary()
        self.save_higher_tier_dictionary()
        self.save_bid_to_col()
        self.save_term_to_row()

    def load_dictionary(self):
        if os.path.exists('dictionary.pkl'):
            with open('dictionary.pkl', 'rb') as f:
                return pickle.load(f)

        dictionary = defaultdict(Counter)    # {term -> {bid -> frequency}}
        for bid in self.bids:
            path = os.path.join('text', bid + '.txt')
            try:
                with open(path, 'r') as f:
                    text = f.read()
            except FileNotFoundError as E:
                with open('parser.log', 'a') as f:
                    f.write('{}\n'.format(E))

            for token in self.parse(text):
                dictionary[token][bid] += 1

        return dictionary

    def load_higher_tier_dictionary():
        if os.path.exist('higher_tier_dictionary.pkl'):
            with open('higher_tier_dictionary.pkl', 'rb') as f:
                return pickle.load(f)

        higher_tier_dictionary = defaultdict(Counter)
        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        c.execute('SELECT bid, title FROM books')
        while True:
            record = c.fetchone()
            if record:
                bid, title = record
                for token in self.parser.parse(title):
                    higher_tier_dictionary[token][str(bid)] += 1
            else:
                break
        conn.close()
        return higher_tier_dictionary

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
        return _dict_to_matrix(self.dictionary)

    def load_title_term_bid_matrix(self):
        if os.path.exists('title_term_bid_matrix.pkl'):
            with open('title_term_bid_matrix.pkl', 'rb') as f:
                return pickle.load(f)
        return _dict_to_matrix(self.higher_tier_dictionary)

    def _dict_to_matrix(self, dictionary):
        """Get term/bid matrix."""
        m = sparse.dok_matrix((len(self.term_to_row), len(self.bid_to_col)), dtype=int)
        for term, bids in dictionary.items():
            row = self.term_to_row[term]
            for bid, freq in bids.items():
                col = self.bid_to_col[bid]
                m[row, col] = freq
        return m.tocsc()

    def save_term_bid_matrix(self):
        with open('term_bid_matrix.pkl', 'wb') as f:
            pickle.dump(self.term_bid_matrix, f)

    def save_title_term_bid_matrix(self):
        with open('title_term_bid_matrix.pkl', 'wb') as f:
            pickle.dump(self.title_term_bid_matrix, f)

    def save_term_to_row(self):
        with open('term_to_row.pkl', 'wb') as f:
            pickle.dump(self.term_to_row, f)

    def save_bid_to_col(self):
        with open('bid_to_col.pkl', 'wb') as f:
            pickle.dump(self.bid_to_col, f)

    def save_dictionary(self):
        with open('dictionary.pkl', 'wb') as f:
            pickle.dump(self.dictionary, f)

    def save_higher_tier_dictionary(self):
        with open('higher_tier_dictionary.pkl', 'wb') as f:
            pickle.dump(self.higher_tier_dictionary, f)

    def tf(self, freq):
        return 1 + np.log10(freq)

    def idf(self, term, tier):
        dictionary = self.dicts[tier]
        return np.log10(self.N / len(dictionary[term]))

    def make_query_vector(self, query_terms):
        """Generator a query tf-idf vector according to terms counter.
        Parameter query_terms is a Counter data structure."""
        q = sparse.dok_matrix((1, self.matrix.M))    # 1 * #term_num# vector
        # Build query tf-idf vector
        for term, freq in query_terms.items():
            q[0,self.term_to_row[term]] = Search.tf(freq) * Search.idf(term)
        q = normalize(q.tocsr(), axis=1, copy=False)
        return q

    def boolean_search(self, query_terms, tier):
        """Search a query according to its ocurrence in the documents and return matched results.
        When tier is 'l', search the lower tier, and if tier is 'h' search the higher tier."""
        dictionary = self.dicts[tier]
        bids = reduce(set.union,
                      (set(dictionary.get(term, []))
                       for term in query_terms))
        return bids

    def make_matched_matrix(self, bids, tier):
        dictionary = self.dicts[tier]
        matrix = self.mats[tier]
        # Pick matched columns
        m = matrix[:,[self.bid_to_col[bid] for bid in bids]]
        m.data = self.tf(m.data)
        m = normalize(m.transpose(), axis=1, copy=False).transpose()    # No copy to make faster
        return m

    def tiered_search(self, query, K=10):
        query_terms = self.parser.parse_query(query)
        qv = self.make_query_vector(query_terms)

        # Higher tier
        res = list(self.cos_sim_search(query_terms, qv, tier=1))
        if len(res) < K:    # Lower tier
            res = list(self.cos_sim_search(query_terms, qv, 0))
        return (r[1] for r in heapq.nlargest(K, res))    # Return K highest ranked bids

    def cos_sim_search(self, query_terms, qv=None, tier=0):
        """Return an unsorted iterator of (similarity, bid) tuples given the query terms.
        If qv is not provided, it will be computed.
        Default tier is 0"""
        if qv is None:
            qv = self.make_query_vector(query_terms)
        bids = self.boolean_search(query_terms, tier)
        m = self.make_matched_matrix(bids, tier)
        cos_sims = qv.dot(m).toarray()[0]
        return zip(cos_sims, bids)

    def bm25_search(self, query):
        pass

def test():
    d2m = DictToMatrix()
    """
    for bid in d2m.boolean_search('一个中学生'):
        path = os.path.join('text', bid + '.txt')
        with open(path, 'r') as f:
            print(f.read())
    """

    def search(query):
        count = 0
        for bid in d2m.boolean_search(query):
            count += 1
            if count > 10:
                break
            path = os.path.join('text', bid + '.txt')
            with open(path, 'r') as f:
                print(f.read())

    print('Start search')
    while True:
        query = input()
        if query != '':
            search(query)
        else:
            break


if __name__ == '__main__':
    test()
