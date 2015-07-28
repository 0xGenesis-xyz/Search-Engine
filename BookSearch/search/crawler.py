"""Crawl data from douban.com."""

import requests
import re
import os.path
import pickle
import urllib.parse
import sqlite3
import time
import csv

class Crawler(object):
    def __init__(self):
        self.conn = sqlite3.connect('books.db')
        self.c = self.conn.cursor()
        self.bids = self.get_all_bookid()
        self.finished_set = self.load_set()
        self.unfinished_set = self.bids - self.finished_set
        self.continuous_error_n = 0

    def run(self):
        print("Crawling...")
        try:
            for bid in self.unfinished_set:
                self.parse_book_json(bid)
                time.sleep(1.51)
            print('Finished')
        except KeyboardInterrupt:
            pass
        finally:
            self.conn.commit()
            self.conn.close()
            self.save_set()

    def get_all_bookid(self):
        if os.path.exists('bidset.pkl'):
            with open('bidset.pkl', 'rb') as f:
                return pickle.load(f)

        path = os.path.join('..', 'data', 'userbook.csv')
        with open(path, 'r') as csvf:
            book_infos = csv.reader(csvf)
            next(book_infos)
            bids = set((book_info[1] for book_info in book_infos))

        with open('bidset.pkl', 'wb') as f:
            pickle.dump(bids, f)

        return bids

    def load_set(self):
        if os.path.exists('finished_set.pkl'):
            with open('finished_set.pkl', 'rb') as f:
                return pickle.load(f)
        else:
            return set()

    def save_set(self):
        with open('finished_set.pkl', 'wb') as f:
            pickle.dump(self.finished_set, f)

    def get_image(self, url, bid):
        r = requests.get(url)
        path = os.path.join('.', 'img', bid + '.jpg')
        with open(path, 'wb') as imgf:
            imgf.write(r.content)

    def parse_book_json(self, bid):
        if bid in self.finished_set:
            return
        apikey = '040a8bb6cf4c9f230c1fa3246de5dd69'
        api_url = 'https://api.douban.com/v2/book/{}?apikey={}'.format(bid, apikey)

        try:
            url = 'http://book.douban.com/subject/{}/'.format(bid)
            r = requests.get(api_url)
            data = r.json()
            if data.get('msg', '') == 'book_not_found':
                raise RuntimeError('Book not found')
            title = data.get('title', '')
            subtitle = data.get('subtitle', '')
            alt_title = data.get('alt_title', '')
            author = ' '.join(data.get('author', '') or [])
            translator = ' '.join(data.get('translator', []))
            publisher = data.get('publisher', '')
            pubdate = data.get('pubdate', '')
            binding = data.get('binding', '')
            summary = data.get('summary', '').replace('\n', '')
            author_intro = data.get('author_intro', '').replace('\n', '')
            catalog = data.get('catalog', '')
            rating_b = data.get('rating', '')
            if rating_b:
                rating = float(rating_b['average'])
                numRaters = int(rating_b['numRaters'])
            else:
                rating, numRaters = 0, 0
            pages = data.get('pages', '')
            price = data.get('price', '')
            isbn13 = data.get('isbn13', '')
            isbn10 = data.get('isbn10', '')
            try:
                if isbn13:
                    isbn_query = '{}-{}-{}-{}-{}'.format(isbn13[0:3], isbn13[3], isbn13[4:8], isbn13[8:12], isbn13[12])
                elif isbn10:
                    isbn_query = '{}-{}-{}-{}'.format(isbn10[0], isbn10[1:4], isbn10[4:9], isbn10[9])
                else:
                    isbn_query = ''
            except IndexError:
                isbn_query = ''
            zjulib_url = 'http://webpac.zju.edu.cn/F/-?' + urllib.parse.urlencode({"func": "find-b", "find_code": "ISB", "request": isbn_query, "local_base": "ZJU01"})
            series = data.get('series', '')
            if series:
                series = series['title']
            tags = data.get('tags', [])
            tags = ' '.join((t['name'] for t in tags))

            # Image
            img_url = data.get('image')
            if not img_url:
                raise RuntimeError('Image not found')
            self.get_image(img_url, bid)
            # Preserve data
            self.write_db(bid, url, title, subtitle, alt_title, author, translator,
                          publisher, pubdate, binding, summary, author_intro, catalog,
                          rating, numRaters, pages, price, isbn13, isbn10, series, tags,
                          zjulib_url)
            self.write_text(bid, title, subtitle, alt_title, author, translator,
                            publisher, summary, author_intro, catalog, isbn13, isbn10,
                            series, tags)

            self.finished_set.add(bid)
            #self.continuous_error_n = 0

            # print('标题：{}\n作者：{}\n译者：{}\n副标题：{}\n出版社：{}\n出版年：{}\n页数：{}\n定价：{}\n装帧：{}\nISBN：{}\n统一书号：{}\n丛书：{}\n内容简介：{}\n作者简介：{}\n评分：{}\n评价人数：{}\n目录：{}\n标签：{}\n-------------------------------------'.format(title_text, authors_text, translators_text, subheading_text, publisher_text, publish_year_text, pages_number, price_text, binding_text, isbn_text, uniform_id_text, series_text, content_intro_text, author_intro_text, rate_value, rate_people_number, catalogue_text, tags_text))
        except Exception as E:
            with open('crawler.log', 'a') as f:
                f.write('Error in {} : {}\n'.format(url, E))
            # checking whether current IP address is forbidden
            #self.continuous_error_n += 1
            #if self.continuous_error_n > 10:
            #    raise RuntimeError('Try to relogin')
            return

    def write_db(self, *args):
        self.c.execute('''INSERT INTO books VALUES
                          (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                           ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', args)

    def write_text(self, bid, *args):
        path = os.path.join('.', 'text', bid + '.txt')
        with open(path, 'w') as f:
            f.write('\n'.join(args))


if __name__ == '__main__':
    crawler = Crawler()
    crawler.run()
