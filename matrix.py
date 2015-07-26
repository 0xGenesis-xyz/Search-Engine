"""Convert inverted indexes to a matrix for computation."""

from collections import defaultdict, Counter
import heapq
from functools import reduce, wraps
import os.path
import pickle
import sqlite3

import numpy as np
from numpy import linalg as LA
from scipy import sparse
from sklearn.preprocessing import normalize

from parser import Parser
from crawler import Crawler

class Matrix(object):
    k1, k2, b = 1.5, 1.5, 0.75    # Parameters
    def __init__(self):
        self.parser = Parser()
        self.bids = Crawler().finished_set
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

        # Tiers, tier[0] is the lowest tier
        self.dicts = (self.dictionary,
                      self.higher_tier_dictionary)
        self.mats = (self.term_bid_matrix,
                     self.title_term_bid_matrix)

    def __del__(self):
        self.save_dictionary()
        self.save_higher_tier_dictionary()
        self.save_term_to_row()
        self.save_bid_to_col()
        self.save_term_bid_matrix()
        self.save_title_term_bid_matrix()

    def processing(text):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                stuff = f.__name__[5:]
                print('{}ing {} ... \t\t'.format(text.title(), stuff))
                r = f(*args, **kwargs)
                print('{} {}ed!'.format(stuff, text))
                return r
            return wrapper
        return decorator

    @processing('load')
    def load_dictionary(self):
        if os.path.exists('dictionary.pkl'):
            with open('dictionary.pkl', 'rb') as f:
                return pickle.load(f)

        dictionary = defaultdict(Counter)    # {term -> {bid -> frequency}}
        count = 0
        for bid in self.bids:
            path = os.path.join('text', bid + '.txt')
            try:
                with open(path, 'r') as f:
                    text = f.read()
            except FileNotFoundError as E:
                with open('parser.log', 'a') as f:
                    f.write('{}\n'.format(E))

            for token in self.parser.parse(text):
                dictionary[token][bid] += 1

            count += 1
            if count % 10000 == 0:
                print(count)

        return dictionary

    @processing('load')
    def load_higher_tier_dictionary(self):
        if os.path.exists('higher_tier_dictionary.pkl'):
            with open('higher_tier_dictionary.pkl', 'rb') as f:
                return pickle.load(f)

        higher_tier_dictionary = defaultdict(Counter)
        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        c.execute('SELECT bid, title FROM books')
        count = 0
        while True:
            record = c.fetchone()
            if record:
                bid, title = record
                for token in self.parser.parse(title):
                    higher_tier_dictionary[token][str(bid)] += 1
            else:
                break

            count += 1
            if count % 10000 == 0:
                print(count)
        conn.close()
        return higher_tier_dictionary

    @processing('load')
    def load_term_to_row(self):
        if os.path.exists('term_to_row.pkl'):
            with open('term_to_row.pkl', 'rb') as f:
                return pickle.load(f)
        return {term: row for row, term in enumerate(self.dictionary)}

    @processing('load')
    def load_bid_to_col(self):
        if os.path.exists('bid_to_col.pkl'):
            with open('bid_to_col.pkl', 'rb') as f:
                return pickle.load(f)
        return {bid: col for col, bid in enumerate(self.bids)}

    @processing('load')
    def load_term_bid_matrix(self):
        if os.path.exists('term_bid_matrix.pkl'):
            with open('term_bid_matrix.pkl', 'rb') as f:
                return pickle.load(f)
        return self._dict_to_matrix(self.dictionary)

    @processing('load')
    def load_title_term_bid_matrix(self):
        if os.path.exists('title_term_bid_matrix.pkl'):
            with open('title_term_bid_matrix.pkl', 'rb') as f:
                return pickle.load(f)
        return self._dict_to_matrix(self.higher_tier_dictionary)

    def _dict_to_matrix(self, dictionary):
        """Get term/bid matrix."""
        m = sparse.dok_matrix((len(self.term_to_row), len(self.bid_to_col)), dtype=int)
        for term, bids in dictionary.items():
            row = self.term_to_row[term]
            for bid, freq in bids.items():
                col = self.bid_to_col[bid]
                m[row, col] = freq
        return m.tocsc()

    @processing('sav')
    def save_term_bid_matrix(self):
        with open('term_bid_matrix.pkl', 'wb') as f:
            pickle.dump(self.term_bid_matrix, f)

    @processing('sav')
    def save_title_term_bid_matrix(self):
        with open('title_term_bid_matrix.pkl', 'wb') as f:
            pickle.dump(self.title_term_bid_matrix, f)

    @processing('sav')
    def save_term_to_row(self):
        with open('term_to_row.pkl', 'wb') as f:
            pickle.dump(self.term_to_row, f)

    @processing('sav')
    def save_bid_to_col(self):
        with open('bid_to_col.pkl', 'wb') as f:
            pickle.dump(self.bid_to_col, f)

    @processing('sav')
    def save_dictionary(self):
        with open('dictionary.pkl', 'wb') as f:
            pickle.dump(self.dictionary, f)

    @processing('sav')
    def save_higher_tier_dictionary(self):
        with open('higher_tier_dictionary.pkl', 'wb') as f:
            pickle.dump(self.higher_tier_dictionary, f)

    def tf(self, freq):
        return 1 + np.log10(freq)

    def idf(self, term, tier):
        dictionary = self.dicts[tier]
        return np.log10(self.N / len(dictionary[term]))

    def make_query_vector(self, query_terms, tier):
        """Generator a query tf-idf vector according to terms counter.
        Parameter query_terms is a Counter data structure."""
        q = sparse.dok_matrix((1, self.M))    # 1 * #term_num# vector
        # Build query tf-idf vector
        for term, freq in query_terms.items():
            q[0,self.term_to_row[term]] = self.tf(freq) * self.idf(term, tier)
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

        # Higher tier
        try:
            res = list(self.cos_sim_search(query_terms, tier=1))
        except KeyError:    # Terms don't occur in titles, continue to search the lower tier
            res = ()
        if len(res) < K:    # Lower tier
            try:
                res = list(self.cos_sim_search(query_terms, tier=0))
            except KeyError:    # Term don't occur in all docs, return nothing
                return ()
        return (int(r[1]) for r in heapq.nlargest(K, res))    # Return K highest ranked bids

    def cos_sim_search(self, query_terms, tier=0):
        """Return an unsorted iterator of (similarity, bid) tuples given the query terms.
        If qv is not provided, it will be computed.
        Default tier is 0"""
        qv = self.make_query_vector(query_terms, tier)
        bids = self.boolean_search(query_terms, tier)
        m = self.make_matched_matrix(bids, tier)
        cos_sims = qv.dot(m).toarray()[0]
        return zip(cos_sims, bids)

    def bm25_search(self, query):
        pass

def test():
    m = Matrix()

    def search(query):
        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        for bid in m.tiered_search(query):
            c.execute('SELECT title, author, summary FROM books WHERE bid = ?', (bid,))
            title, author, summary = c.fetchone()
            print(title, author, summary, '\n')
        conn.close()

    print('Start search')
    while True:
        query = input()
        if query != '':
            search(query)
        else:
            break

if __name__ == '__main__':
    test()
