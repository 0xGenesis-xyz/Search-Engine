"""Parse a document or a query. Return a inverted index."""

import string
import pickle
from collections import Counter
from functools import partial
import os
import os.path
import jieba
from nltk import stem

class Parser(object):
    def __init__(self):
        self.stemmer = stem.LancasterStemmer()
        #self.bids = bookid.get_all_bookid()
        #self.parsed_set = self.load_parsed_set()
        #self.unparsed_set = self.bids - self.parsed_set

        chinese_punc = '！“”￥‘’（），—。、：；《》？【】…　·．／・―•'
        self.delset = string.punctuation + string.whitespace + chinese_punc

        self.start_parser()

    def start_parser(self):
        # It will takes some time to start parser
        next(jieba.cut_for_search('启动'))

    def run(self):
        try:
            for bid in self.unparsed_set:
                self.parse_doc(bid)
                self.parsed_set.add(bid)
        except KeyboardInterrupt:
            pass
        """
        finally:
            self.save_dictionary(self.dictionary)
            self.save_parsed_set(self.parsed_set)
        """

    @staticmethod
    def load_parsed_set():
        if os.path.exists('parsed_set.pkl'):
            with open('parsed_set.pkl', 'rb') as f:
                return pickle.load(f)
        else:
            return set()

    @staticmethod
    def save_parsed_set(parsed_set):
        with open('parsed_set.pkl', 'wb') as f:
            pickle.dump(parsed_set, f)

    def parse(self, text):
        """A generator of tokens in the text."""
        for token in jieba.cut_for_search(text):
            if token in self.delset:
                continue
            if token.isalpha():
                token = self.stemmer.stem(token)
            yield token

    def parse_query(self, query):
        terms = Counter()
        for token in self.parse(query):
            terms[token] += 1
        return terms


if __name__ == '__main__':
    parser = Parser()
    parser.test()
