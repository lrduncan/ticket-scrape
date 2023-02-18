import logging
import sqlite3

if __name__ == '__main__':
    con = sqlite3.connect('items.db')
    cur = con.cursor()
    # cur.execute('DROP TABLE IF EXISTS items')
    cur.execute('CREATE TABLE items(url, price)')
    # Fill in the lines with the url and lowest current used price.
    # If there is no used stock, use null for price
    cur.execute('''
        INSERT INTO items VALUES
        ('', null),
        ('', null)
    ''')
    con.commit()
    res = cur.execute('select * from items')
    logging.info(res.fetchall())
