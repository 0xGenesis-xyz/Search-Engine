import sqlite3
import shutil
import os

if __name__ == '__main__':
    os.remove('dictionary.pkl')
    os.remove('term_to_row.pkl')
    os.remove('bid_to_col.pkl')
