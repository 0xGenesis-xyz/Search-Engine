"""Convert inverted indexes to a matrix for computation."""

from collections import defaultdict, Counter
import heapq
from functools import wraps
from itertools import islice
import itertools
import os.path
import pickle
import sqlite3

import numpy as np
from numpy import linalg as LA
from scipy import sparse
from sklearn.preprocessing import normalize

try:
    from search.parser import Parser
    from search.crawler import Crawler
except ImportError:
    from parser import Parser
    from crawler import Crawler

class Matrix(object):
    k1, k2, b = 1.5, 1.5, 0.75    # Parameters
    modified = {'dictionary': False, 'higher_tier_dictionary': False}    # Member vars modified mark
    dirname = os.path.dirname(os.path.realpath(__file__))
    def __init__(self):
        self.parser = Parser()
        self.bids = Crawler().finished_set

        if os.path.exists(os.path.join(Matrix.dirname, 'dictionary.pkl')):
            self.dictionary = None
        else:
            self.dictionary = self.load_dictionary()

        if os.path.exists(os.path.join(Matrix.dirname, 'higher_tier_dictionary.pkl')):
            self.higher_tier_dictionary = None
        else:
            self.load_higher_tier_dictionary()

        self.term_to_row = self.load_term_to_row()
        self.bid_to_col = self.load_bid_to_col()

        self.N = len(self.bid_to_col)    # Total number of documents
        self.M = len(self.term_to_row)    # Total number of terms

        self.col_to_bid = self.load_col_to_bid()
        self.row_to_term = self.load_row_to_term()    # Used in similar search
        self.term_bid_matrix = self.load_term_bid_matrix()
        self.title_term_bid_matrix = self.load_title_term_bid_matrix()
        # Csr sparse matrix sed for slice term rows
        self.term_bid_matrix_csr = self.term_bid_matrix.tocsr()
        self.title_term_bid_matrix_csr = self.title_term_bid_matrix.tocsr()
        self.stop_words = self.load_stop_words()

        # Tiers, tier[0] is the lowest tier
        self.mats_csc = (self.term_bid_matrix,
                         self.title_term_bid_matrix)
        self.mats_csr = (self.term_bid_matrix_csr,
                         self.title_term_bid_matrix_csr)

    def __del__(self):
        self.save_dictionary()
        self.save_higher_tier_dictionary()
        self.save_term_to_row()
        self.save_bid_to_col()
        self.save_term_bid_matrix()
        self.save_title_term_bid_matrix()
        self.save_row_to_term()
        self.save_col_to_bid()
        self.save_stop_words()

    def saving(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            stuff = func.__name__[5:]
            if Matrix.modified[stuff]:
                filename = os.path.join(Matrix.dirname, stuff + '.pkl')
                print('Saving {} ...'.format(stuff))
                with open(filename, 'rb') as f:
                    pickle.dump(getattr(self, stuff), f)
                print('{} saved.'.format(stuff))
        return wrapper

    def loading(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            stuff = func.__name__[5:]
            filename = os.path.join(Matrix.dirname, stuff + '.pkl')
            if os.path.exists(filename):
                print('Loading {} ...'.format(stuff))
                with open(filename, 'rb') as f:
                    Matrix.modified[stuff] = False
                    r = pickle.load(f)
                print('{} loaded.'.format(stuff))
            else:
                print('Building {} ...'.format(stuff))
                r = func(*args, **kwargs)
                Matrix.modified[stuff] = True
                print('{} built.'.format(stuff))
            return r
        return wrapper

    @loading
    def load_dictionary(self):
        dictionary = defaultdict(Counter)    # {term -> {bid -> frequency}}
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

        return dictionary

    @loading
    def load_higher_tier_dictionary(self):
        higher_tier_dictionary = defaultdict(Counter)
        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        c.execute('SELECT bid, title, author, tags FROM books')
        while True:
            record = c.fetchone()
            if record:
                bid, title, author, tags = record
                text = '{} {} {}'.format(title, author, tags)
                for token in self.parser.parse(text):
                    higher_tier_dictionary[token][str(bid)] += 1
            else:
                break
        conn.close()

        return higher_tier_dictionary

    @loading
    def load_term_to_row(self):
        return {term: row for row, term in enumerate(self.dictionary)}

    @loading
    def load_bid_to_col(self):
        return {bid: col for col, bid in enumerate(self.bids)}

    @loading
    def load_term_bid_matrix(self):
        return self._dict_to_matrix(self.dictionary)

    @loading
    def load_title_term_bid_matrix(self):
        return self._dict_to_matrix(self.higher_tier_dictionary)

    @loading
    def load_row_to_term(self):
        return {row: term for term, row in self.term_to_row.items()}

    @loading
    def load_col_to_bid(self):
        return {col: bid for bid, col in self.bid_to_col.items()}

    @loading
    def load_stop_words(self, N=25000):
        """Return a boolean vector in which True entries stand for lower occurence words,
        while False entries stand for higher occurence words.
        N is the threshold values that how many stop words will be selected"""
        def df(term):
            return len(self.dictionary[term])
        def nlargest_df(N):
            return heapq.nlargest(N, ((df(term), term) for term in self.dictionary))
        v = np.ones((self.M, 1), dtype=bool)    # High occurence words (stop words) vector
        for df, term in nlargest_df(N):
            v[self.term_to_row[term], 0] = False
        return v

    def _dict_to_matrix(self, dictionary):
        """Get term/bid matrix."""
        m = sparse.dok_matrix((self.M, self.N), dtype=int)
        for term, bids in dictionary.items():
            row = self.term_to_row[term]
            for bid, freq in bids.items():
                col = self.bid_to_col[bid]
                m[row, col] = freq
        return m.tocsc()

    @saving
    def save_term_bid_matrix(self):
        pass

    @saving
    def save_title_term_bid_matrix(self):
        pass

    @saving
    def save_term_to_row(self):
        pass

    @saving
    def save_bid_to_col(self):
        pass

    @saving
    def save_dictionary(self):
        pass

    @saving
    def save_higher_tier_dictionary(self):
        pass

    @saving
    def save_row_to_term(self):
        pass

    @saving
    def save_col_to_bid(self):
        pass

    @saving
    def save_stop_words(self):
        pass

    def tf(self, freq):
        return 1 + np.log10(freq)

    def idf(self, term, tier=0):
        matrix = self.mats_csr[tier]
        def df(term):
            row_num = self.term_to_row[term]
            row = matrix.getrow(row_num)
            return row.nnz
        return np.log10(self.N / df(term))

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
        When tier is 'l', search the lower tier, and if tier is 'h' search the higher tier.
        Return the column indices of matched books."""
        matrix = self.mats_csr[tier]
        docs = np.zeros(self.N, dtype=bool)    # Get union of docs containing query
        for term in query_terms:
            row = self.term_to_row.get(term)
            if row is None:
                continue
            else:
                np.logical_or(docs, matrix.getrow(row).toarray()[0], docs)
        return docs.nonzero()[0]

    def make_matched_matrix(self, cols, tier):
        matrix = self.mats_csc[tier]
        # Pick matched columns
        m = matrix[:,cols]
        m.data = self.tf(m.data)
        m = normalize(m.T, axis=1, copy=False).T    # No copy to make faster
        return m

    def tiered_search(self, query, K=50):
        query_terms = self.parser.parse_query(query)

        # Higher tier
        try:
            hres = heapq.nlargest(K, self.cos_sim_search(query_terms, tier=1))
        except:    # Terms don't occur in titles, continue to search the lower tier
            hres = []
        lres = []
        if len(hres) < K:    # Lower tier
            try:
                hres_bids = [r[1] for r in hres]
                # Docs that hasn't been retrieve
                lres = heapq.nlargest(K - len(hres),    # Find at most K docs
                                      filter(lambda pair: pair[0] not in hres_bids,
                                             self.cos_sim_search(query_terms, tier=0)))
            except:    # Term don't occur in all docs, return nothing
                return ()
        return (int(r[1]) for r in itertools.chain(hres, lres))    # Return K highest ranked bids

    def cos_sim_search(self, query_terms, tier=0):
        """Return an unsorted iterator of (similarity, bid) tuples given the query terms.
        If qv is not provided, it will be computed.
        Default tier is 0"""
        qv = self.make_query_vector(query_terms, tier)
        cols = self.boolean_search(query_terms, tier)
        m = self.make_matched_matrix(cols, tier)
        cos_sims = qv.dot(m).toarray()[0]
        bids = (self.col_to_bid[col] for col in cols)
        return zip(cos_sims, bids)

    def find_most_similar(self, bids, K_sim=14):
        """Return the bid of the most similar book to parameter bid except the given bid."""
        termv = sparse.csc_matrix((self.M, 1), dtype=int)
        for bid in bids:
            col_num = self.bid_to_col.get(str(bid))
            if col_num is not None:
                termv = termv + self.term_bid_matrix.getcol(col_num)
        if termv.nnz == 0:
            return ()
        termva = termv.toarray()    # Generate a vector for terms
        stop_words_removed = np.logical_and(termva, self.stop_words)
        nonzero = stop_words_removed.nonzero()[0]    # Nonzero indices
        rest_term_rows = self.term_bid_matrix_csr[nonzero]
        docs = np.zeros(self.N, dtype=bool)
        for row in rest_term_rows:
            np.logical_or(docs, row.toarray()[0], docs)
        cols = docs.nonzero()[0]
        matched_matrix = self.term_bid_matrix[:,cols]
        termv.data = self.tf(termv.data) * np.array([self.idf(self.row_to_term[row])
                                                     for row in termv.indices])
        termv = normalize(termv.T, axis=1, copy=False)
        matched_matrix.data = self.tf(matched_matrix.data)
        matched_matrix = normalize(matched_matrix.T, axis=1, copy=False).T
        cos_sims = termv.dot(matched_matrix).toarray()[0]
        found_bids = (self.col_to_bid[col] for col in cols)
        return islice((int(r[1])
                       for r in heapq.nlargest(K_sim, zip(cos_sims, found_bids))
                       if int(r[1]) not in bids),
                       9)

    def find_most_similar_tags(self, bid, K_sim=10):
        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        c.execute('SELECT tags FROM books WHERE bid = ?', (int(bid),))
        query_terms = self.parser.parse_query(c.fetchone()[0])
        return (int(r[1]) for r in heapq.nlargest(K_sim, self.cos_sim_search(query_terms)))

    def bm25_search(self, query):
        pass

def test():
    m = Matrix()

    def search(query):
        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        #for bid in m.tiered_search(query):
        for bid in m.find_most_similar(query):
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
