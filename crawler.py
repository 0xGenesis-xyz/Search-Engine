import requests
import re
from bs4 import BeautifulSoup
import os.path
import bookid
import pickle
import sqlite3

finished = None
c = None

def get_image(url, bid):
    r = requests.get(url)
    path = os.path.join('.', 'img', bid + '.jpg')
    with open(path, 'wb') as imgf:
        imgf.write(r.content)


#def write_db(bid, url, title_text, authors_text, translators_text, subheading_text, publisher_text, publish_year_text, pages_number, price_text, binding_text, isbn_text, uniform_id_text, series_text, content_intro_text, author_intro_text, rate_value, rate_people_number, catalogue_text, tags_text):
def write_db(*args):
    global c
    c.execute('''INSERT INTO books VALUES
                 (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', args)


def write_text(bid, *args):
    path = os.path.join('.', 'text', bid + '.txt')
    with open(path, 'w') as f:
        f.write('\n'.join(args))


def parse_book(bid):
    url = 'http://book.douban.com/subject/{}/'.format(bid)

    try:
        r = requests.get(url)
    except Exception as E:
        with open('crawler.log', 'a') as f:
            f.write('Error while crawling {}:\n'.format(url))
            f.write(str(E))
        return

    try:
        soup = BeautifulSoup(r.text)
        # Image
        img_url = soup.find('a', 'nbg').attrs['href']
        get_image(img_url, bid)

        # Title
        title_text = soup.h1.span.string

        # Author
        authors = soup.find('span', text=' 作者')
        if authors:
            authors_text = ' '.join(c.string
                                    for c in authors.parent.contents
                                    if c.name == 'a')
        else:
            authors_text = ''

        # Translator
        translators = soup.find('span', text=' 译者')
        if translators:
            translators_text = ' '.join(c.string
                                        for c in translators.parent.contents
                                        if c.name == 'a')
        else:
            translators_text = ''

        # Subheading
        subheading = soup.find('span', text='副标题:')
        if subheading:
            subheading_text = subheading.next_sibling.strip()
        else:
            subheading_text = ''

        # Publisher
        publisher = soup.find('span', text='出版社:')
        if publisher:
            publisher_text = publisher.next_sibling.strip()
        else:
            publisher_text = ''

        # Publish year
        publish_year = soup.find('span', text='出版年:')
        if publish_year:
            publish_year_text = publish_year.next_sibling.strip()
        else:
            publish_year_text = ''

        # Pages
        pages = soup.find('span', text='页数:')
        if pages:
            pages_number = int(pages.next_sibling)
        else:
            pages_number = 0

        # Price
        price = soup.find('span', text='定价:')
        if price:
            price_text = price.next_sibling.strip()
        else:
            price_text = ''

        # Binding
        binding = soup.find('span', text='装帧:')
        if binding:
            binding_text = binding.next_sibling.strip()
        else:
            binding_text = ''

        # ISBN
        isbn = soup.find('span', text='ISBN:')
        if isbn:
            isbn_text = isbn.next_sibling.strip()
        else:
            isbn_text = ''

        # Uniform id
        uniform_id = soup.find('span', text='统一书号:')
        if uniform_id:
            uniform_id_text = uniform_id.next_sibling.strip()
        else:
            uniform_id_text = ''

        # Series
        series = soup.find('span', text='丛书:')
        if series:
            series_text = series.next_sibling.next_sibling.string
        else:
            series_text = ''

        # Introduction
        #    of contents
        content_intro = soup.find('span', 'all hidden')
        # 'all hidden' without an tail space represents for introduction to the book
        if content_intro:
            content_intro_text = '\n'.join((c.string for c in content_intro.find_all('p')))
        else:
            content_intro = soup.find('span', text='内容简介')
            if content_intro:
                content_intro = content_intro.find_next('div', 'intro')
                content_intro_text = ''.join((c.string
                                                for c in content_intro.find_all('p')
                                                if c.string is not None))
            else:
                content_intro_text = ''

        #    of author
        author_intro = soup.find('span', 'all hidden ')
        # 'all hidden' with an tail space represents for introduction to the author
        if author_intro:
            author_intro_text = ''.join((c.string for c in author_intro.find_all('p')))
        else:
            author_intro = soup.find('span', text='作者简介')
            if author_intro:
                author_intro = author_intro.find_next('div', 'intro')
                author_intro_text = ''.join((c.string
                                               for c in author_intro.find_all('p')
                                               if c.string is not None))
            else:
                author_intro_text = ''

        # Rating
        rate = soup.find('strong', 'll rating_num ').string
        try:
            rate_value = float(rate)
        except ValueError:
            rate_value = 0

        # Comment people number
        rate_people = soup.find('a', href='collections').span
        if rate_people:
            rate_people_number = int(rate_people.string)
        else:
            rate_people_number = 0

        # Catalogue
        catalogue = soup.find('div', id=re.compile(r'dir.*full'))
        if catalogue:
            catalogue_text = '\n'.join(map(lambda c: str(c).strip(),
                                           catalogue.contents[:-3:2]))
        else:
            catalogue_text = ''

        # Tags
        tags = (c.string
            for c in soup.find_all('a', ' tag'))
        tags_text = ' '.join(tags)

        write_db(bid, url, title_text, authors_text, translators_text, subheading_text, publisher_text, publish_year_text, pages_number, price_text, binding_text, isbn_text, uniform_id_text, series_text, content_intro_text, author_intro_text, rate_value, rate_people_number, catalogue_text, tags_text)
        write_text(bid, title_text, authors_text, translators_text, subheading_text, publisher_text, isbn_text, series_text, content_intro_text, author_intro_text, catalogue_text, tags_text)

    except Exception as E:
        with open('crawler.log', 'a') as f:
            f.write('Error while crawling {}:\n'.format(url))
            f.write(str(E))
        return

    # print('标题：{}\n作者：{}\n译者：{}\n副标题：{}\n出版社：{}\n出版年：{}\n页数：{}\n定价：{}\n装帧：{}\nISBN：{}\n统一书号：{}\n丛书：{}\n内容简介：{}\n作者简介：{}\n评分：{}\n评价人数：{}\n目录：{}\n标签：{}\n-------------------------------------'.format(title_text, authors_text, translators_text, subheading_text, publisher_text, publish_year_text, pages_number, price_text, binding_text, isbn_text, uniform_id_text, series_text, content_intro_text, author_intro_text, rate_value, rate_people_number, catalogue_text, tags_text))


def load_set():
    if os.path.exists('finished_set.pkl'):
        with open('finished_set.pkl', 'rb') as f:
            return pickle.dump(f)
    else:
        return set()


def save_set():
    with open('finished_set.pkl', 'wb') as f:
        pickle.dump(finished)


def main():
    global c
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    bids = bookid.get_all_bookid()
    finished_set = load_set()
    try:
        for bid in bids:
            parse_book(bid)
            finished_set.add(bid)
    except KeyboardInterrupt:
        pass
    finally:
        conn.commit()
        conn.close()


if __name__ == '__main__':
    main()
