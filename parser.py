import string
import pickle
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

        chinese_punc = '！“”￥‘’（），—。、：；《》？【】…　'
        self.delset = string.punctuation + string.whitespace + chinese_punc

    def load_dictionary(self):
        if os.path.exists('dictionary.pkl'):
            with open('dictionary.pkl', 'rb') as f:
                return pickle.load(f)
        else:
            return {}

    def load_parsed_set(self):
        if os.path.exists('parsed_set.pkl'):
            with open('parsed_set.pkl', 'rb') as f:
                return pickle.load(f)
        else:
            return set()

    def save_dictionary(self):
        with open('dictionary.pkl', 'wb') as f:
            pickle.dump(self.dictionary, f)

    def save_parsed_set(self):
        with open('parsed_set.pkl', 'wb') as f:
            pickle.dump(self.dictionary, f)

    def parse(self, bid):
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
                pass
            if token.isalpha():
                token = self.stemmer.stem(token)

            if token not in self.dictionary:
                self.dictionary[token] = {}
            index = self.dictionary[token]
            index[bid] = index.get(bid, 0) + 1

        self.parsed_set.add(bid)

    def run(self):
        try:
            for bid in self.unparsed_set:
                self.parse(bid)
        except KeyboardInterrupt:
            pass
        finally:
            self.save_dictionary()
            self.save_parsed_set()
