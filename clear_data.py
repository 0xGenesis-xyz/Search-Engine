import sqlite3
import shutil
import os

if __name__ == '__main__':
    shutil.rmtree('img')
    shutil.rmtree('text')
    os.mkdir('img')
    os.mkdir('text')
    os.remove('finished_set.pkl')
    open('crawler.log', 'w').close()

    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('DELETE FROM books')
    conn.commit()
    conn.close()
