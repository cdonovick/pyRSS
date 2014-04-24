import bottle
from bottle import run, template, request, hook, route, view, redirect
import beaker.middleware
from db import rssDatabase
import feedparser
import base64

# Set up a way to keep session variables
session_opts = {
        'session.type': 'file',
        'session.data_dir': './session/',
        'session.auto': True,
        }
app = beaker.middleware.SessionMiddleware(bottle.app(), session_opts)

rdb = rssDatabase('bar.db', 'a')

# ignore trailing '/' decorator
def iRoute(path, **pargs):    
    if path[-1] == '/':
        paths=[path[:-1], path]
    else:
        paths=[path, path + '/']
    def wrapper(func):
        for p in paths:
            func = route(p, **pargs)(func)
        return func
    return wrapper

# auth decorator
def reqAuth(func):
    def wrapper(*args, **kwargs):
        if ('userid' in request.session and request.session['userid']):
            return func(*args, **kwargs)
        else:
            return redirect('login')
    return wrapper

# Session variables can be found at request.sessiont
@hook('before_request')
def setup_request():
    request.session = request.environ['beaker.session']

# index
@iRoute('/')
@view('index')
def index():
    return dict()

# register
@iRoute('/register', method='GET')
@view('register')
def register():
    return dict(error=None)

@iRoute('/register', method='POST')
def register():
    name = request.forms.get('name')    
    passwd = request.forms.get('passwd')
    if (rdb.addUser(name,passwd) == 0):
        #success
        redirect('/login')
    else:
        #fail
        return template('register', error='username taken')

# login
@iRoute('/login', method='GET')
@view('login')
def login():
    return dict()

@iRoute('/login', method='POST')
def login():
    name = request.forms.get('name')
    passwd = request.forms.get('passwd')
    userid = rdb.login(name,passwd)
    if userid:
        request.session['name'] = name
        request.session['userid'] = userid
        redirect('/home')
    else:
        return template('login')

# home
@iRoute('/home', method='GET')
@reqAuth
@view('home')
def home():
    rawFeeds=rdb.getFeeds(request.session['userid'])
    feeds=[]
    for f in rawFeeds:
        d = feedparser.parse(f['url'])
        #unread posts
        readPosts = rdb.getPosts(request.session['userid'], f['feedid'], len(d.entries))
        posts = [x for x in d.entries if x.link not in readPosts] if 'entries' in d else [] 
        #feeds = [dict(feedid=feedid, title=feed.title, posts=(bas64(post.url), post.title))]
        feeds.append(dict(
            feedid=f['feedid'],
            title=d.feed['title'] if 'title' in d.feed else "", 
            posts=[(base64.urlsafe_b64encode(x.link.encode()), x.title) for x in posts],))
    return dict(name=request.session['name'],feeds=feeds)

# add feed
@iRoute('/add', method='POST')
@reqAuth
def add():
    userid = request.session['userid']
    feedurl = request.forms.get('url')
    rdb.addFeed(userid,feedurl)
    redirect('/home')

# open feed
@iRoute('/out/<feedid:int>/<url>', method='GET')
@reqAuth
def out(feedid, url):
    url = base64.urlsafe_b64decode(url).decode('utf-8')
    rdb.markRead(request.session['userid'], feedid, url)
    redirect(url)

# log out
@iRoute('/logout')
def logout():
    request.session.delete()
    redirect('/')

# Start the server
run(app, host='localhost', port=8080)
