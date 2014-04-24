import hashlib
import sqlite3

SALT = 'foobar'

# utility functions
def flatten(lt):
    return [i for t in lt for i in t]

def uniHash(s):
    return hashlib.sha256((s + SALT).encode()).hexdigest()

class rssDatabase:
    def __init__(self, db, mode='a'):
        if mode != 'a' and mode !='w':
            raise Exception('invalid mode')

        #touch db
        open(db,mode).close() 
        self.__conn = sqlite3.connect(db)
        self.__dbc = self.__conn.cursor()
        if mode == 'w':    
            self.__dbc.execute('''
                            CREATE TABLE users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT NOT NULL UNIQUE,
                                pass TEXT NOT NULL
                            )''')
            self.__dbc.execute('''
                            CREATE TABLE feeds (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                userid INTEGER,
                                url TEXT NOT NULL,
                                FOREIGN KEY(userid) REFERENCES users(id)
                            )''')   
            self.__dbc.execute('''
                            CREATE TABLE posts (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                feedid INTEGER NOT NULL,
                                url TEXT NOT NULL,
                                FOREIGN KEY(feedid) REFERENCES feeds(id)
                            )''')
            self.__conn.commit()

    def addUser(self, name, passwd):
        t = (name, )
        self.__dbc.execute('''SELECT count(*) FROM users WHERE name=?''', t)
        r = flatten(self.__dbc.fetchall())
        if (r == [0]):
            t = (None, name, uniHash(passwd), )
            self.__dbc.execute('''INSERT INTO users VALUES (?,?,?)''', t)
            self.__conn.commit()
            return 0
        elif (r == [1]):
            return 1
        else:
            raise Exception('users curropted')

    def login(self, name, passwd): #returns userID
        t = (name, uniHash(passwd), )
        self.__dbc.execute('''SELECT count(*) FROM users WHERE name=? AND pass=?''', t)
        r = flatten(self.__dbc.fetchall())
        if (r == [1]):
            self.__dbc.execute('''SELECT id FROM users WHERE name=? AND pass=?''', t)
            return flatten(self.__dbc.fetchall())[0]
        elif (r == [0]):
            return None
        else:
            raise Exception('users curropted')
    
    def addFeed(self, userid, url):
        t = (userid, )
        self.__dbc.execute('''SELECT count(*) FROM users WHERE id=?''', t)
        r = flatten(self.__dbc.fetchall())
        if (r == [1]):
            t = (userid, url, )
            self.__dbc.execute('''SELECT count(*) FROM feeds WHERE userid=? AND url=?''', t)
            r = flatten(self.__dbc.fetchall())
            if (r == [0]):
                t = (None, userid, url, )
                self.__dbc.execute('''INSERT INTO feeds VALUES (?,?,?)''', t)
                self.__conn.commit()
                return 0
            elif (r ==[1]):
                return 1
            else:
                raise Exception('feeds curropted')
        elif (r == [0]):
            raise Exception('invalid userid')
        else: 
            raise Exception('users curropted')
            
    def getFeeds(self, userid):
        t = (userid, )
        self.__dbc.execute('''select count(*) from users where id=?''', t)
        r = flatten(self.__dbc.fetchall())
        if (r == [1]):
            self.__dbc.execute('''SELECT id,url FROM feeds WHERE userid=?''', t)
            r = self.__dbc.fetchall()
            feeds = []
            for result in r:
                feeds.append(dict(feedid=result[0],url=result[1],))
            return feeds
        elif (r == [0]):
            raise Exception('invalid userid')
        else: 
            raise Exception('users curropted')

    def delFeed(self, userid, feedid):
        t = (userid, feedid, )
        self.__dbc.execute('''select count(*) FROM feeds WHERE userid=? AND id=?''', t)
        r = flatten(self.__dbc.fetchall())
        if (r == [1]):
            self.__dbc.execute('''DELETE FROM posts WHERE feedid=?''', t)
            self.__dbc.execute('''DELETE FROM feeds WHERE id=?''', t)
            conn.commit()
            return 0
        elif (r == [0]): 
            raise Exception('invalid feedid')
        else: 
            raise Exception('feeds curropted')

    def getPosts(self, userid, feedid, n=0):
        t = (userid, feedid, )
        self.__dbc.execute('''select count(*) FROM feeds WHERE userid=? AND id=?''', t)
        r = flatten(self.__dbc.fetchall()) 
        if (r == [1]):
            if (n == 0):
                t = (feedid, )
                self.__dbc.execute('''SELECT url FROM posts WHERE feedid=?''', t)
            else:
                t = (feedid, n, )
                self.__dbc.execute('''SELECT url FROM posts WHERE feedid=? ORDER BY id DESC LIMIT ? ''', t)
            r = flatten(self.__dbc.fetchall())
            return r
        elif (r == [0]): 
            raise Exception('invalid feedid')
        else: 
            raise Exception('feeds curropted')
    
    def markRead(self, userid, feedid, url):
        t = (userid, feedid, )
        self.__dbc.execute('''select count(*) FROM feeds WHERE userid=? AND id=?''', t)
        r = flatten(self.__dbc.fetchall()) 
        if (r == [1]):
            t = (feedid, url, )
            self.__dbc.execute('''SELECT count(*) FROM posts WHERE feedid=? AND url=?''', t)
            r = flatten(self.__dbc.fetchall())
            if (r == [0]):
                t = (None, feedid, url, )
                self.__dbc.execute('''INSERT INTO posts VALUES (?,?,?)''', t)
                self.__conn.commit()
                return 0
            elif (r == [1]):
                return 1
            else:
                raise Exception("posts curropted")
        elif (r == [0]): 
            raise Exception('invalid feedid')
        else: 
            raise Exception('feeds curropted')

