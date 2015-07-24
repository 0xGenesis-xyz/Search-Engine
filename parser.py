"""Parse a document or a query. Return a inverted index."""

import string
import pickle
from collections import defaultdict, Counter
from functools import partial
import os
import os.path
import jieba
from nltk import stem
import bookid

class Parser(object):
    def __init__(self):
        self.stemmer = stem.LancasterStemmer()
        self.bids = bookid.get_all_bookid()
        self.parsed_set = self.load_parsed_set()
        self.unparsed_set = self.bids - self.parsed_set
        self.dictionary = self.load_dictionary()

        chinese_punc = '！“”￥‘’（），—。、：；《》？【】…　·．／・―'
        self.delset = string.punctuation + string.whitespace + chinese_punc

    def run(self):
        try:
            for bid in self.unparsed_set:
                self.parse_doc(bid)
        except KeyboardInterrupt:
            pass
        finally:
            self.save_dictionary(self.dictionary)
            self.save_parsed_set(self.parsed_set)

    @staticmethod
    def load_dictionary():
        if os.path.exists('dictionary.pkl'):
            with open('dictionary.pkl', 'rb') as f:
                return pickle.load(f)
        else:
            # {term -> {bid -> frequency}}
            return defaultdict(Counter)

    @staticmethod
    def load_parsed_set():
        if os.path.exists('parsed_set.pkl'):
            with open('parsed_set.pkl', 'rb') as f:
                return pickle.load(f)
        else:
            return set()

    @staticmethod
    def save_dictionary(dictionary):
        with open('dictionary.pkl', 'wb') as f:
            pickle.dump(dictionary, f)

    @staticmethod
    def save_parsed_set(parsed_set):
        with open('parsed_set.pkl', 'wb') as f:
            pickle.dump(parsed_set, f)

    def parse_doc(self, bid):
        if bid in self.parsed_set:
            return
        path = os.path.join('text', bid + '.txt')
        try:
            with open(path, 'r') as f:
                text = f.read()
        except FileNotFoundError as E:
            with open('parser.log', 'a') as f:
                f.write('{}\n'.format(E))

        for token in jieba.cut_for_search(text):
            if token in self.delset:
                continue
            if token.isalpha():
                token = self.stemmer.stem(token)
            self.dictionary[token][bid] += 1

        self.parsed_set.add(bid)

    def parse_query(self, query):
        terms = Counter()
        for token in jieba.cut_for_search(query):
            if token in self.delset:
                continue
            if token.isalpha():
                token = self.stemmer.stem(token)
            terms[token] += 1
        return terms

    def test_parse(self, path):
        try:
            with open(path, 'r') as f:
                text = f.read()
        except FileNotFoundError as E:
            pass

        words = []
        for token in jieba.cut_for_search(text):
            if token in self.delset:
                continue
            if token.isalpha():
                token = self.stemmer.stem(token)
            words.append(token)
        return ' '.join(words)

    def test(self):
        with open('test.txt', 'w') as out:
            files = os.listdir('text')
            for i, file_name in enumerate(files):
                if i < 10:
                    continue
                if i > 13000:
                    break
                if i % 500 == 0:
                    print(i)
                bid = file_name[:-4]
                self.parse_doc(bid)
                #s = self.test_parse(os.path.join('text', file_name))
                #out.write(s + '\n')
        self.save_dictionary(self.dictionary)

if __name__ == '__main__':
    parser = Parser()
    parser.test()
