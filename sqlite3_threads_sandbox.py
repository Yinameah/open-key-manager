import sqlite3
import threading
import time


def i_write_all_the_time():
    while True:
        conn = sqlite3.connect("testbd.sqlite3")
        c = conn.cursor()
        c.execute("INSERT INTO test VALUES ('','blou')")
        conn.commit()
        conn.close()


def mee_too():
    while True:
        conn = sqlite3.connect("testbd.sqlite3")
        c = conn.cursor()
        c.execute("INSERT INTO test VALUES ('','bla')")
        conn.commit()
        conn.close()


t1 = threading.Thread(target=i_write_all_the_time)
t1.start()
t2 = threading.Thread(target=mee_too)
t2.start()
