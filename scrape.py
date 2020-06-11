#!/usr/bin/env python3

import requests
from selectolax.parser import HTMLParser
import sys
import re
import time
import logging
import os.path
import datetime as dt
import pandas as pd
logging.basicConfig(level=logging.INFO)

BASE_URL = "https://forum.officer.com/"

for d in ['scrape/','data/','scrape/author/']:
    try:
        os.mkdir(d)
    except OSError:
        print (f'{d} already exists')

def get_html(url, author=False):
    '''Page HTML and save to a file. If file already
    exists then do nothing'''
    if url==BASE_URL:
        path = 'scrape/_main.txt'
    else:
        if not author:
            path = parse_url(url)['filepath']
            try:
                os.makedirs(parse_url(url)['dirpath'])
            except OSError:
                print ("Creation of the directory %s failed" % parse_url(url)['dirpath'])
        else:
            path = 'scrape/author/'+parse_url(url)['title']+'.txt'
            
    if not os.path.isfile(path):
        r = requests.get(url)
        if r.ok:
            print(f'writing data to {path}')
            fh = open(path, "bw")
            fh.write(r.content)
        else:
            sys.exit()
            
def format_post_date(date):
    strings_parsed = date.replace('Yesterday',(dt.datetime.today()-dt.timedelta(1)).strftime("%m-%d-%Y")).replace('Today',(dt.datetime.today()).strftime("%m-%d-%Y"))
    formatted_date = dt.datetime.strptime(strings_parsed, '%m-%d-%Y, %I:%M %p')
    return formatted_date

def parse_url(url):
    url_data = {}
    path = url[32:]
    parts = path.split('/')
    url_data['title'] = parts[-1]
    url_data['dirpath'] = 'scrape/'+('/'.join(parts[:-1]))
    url_data['filepath'] = url_data['dirpath']+"/"+url_data['title']+'.txt'
    logging.info(f"URL data is: {url_data}")
    return url_data

def get_forum_data():
    '''Parse data for each forum present on main page'''
    html = open('scrape/_main.txt', "br").read()
    p = HTMLParser(html)
    forums = p.css("tr.forum-item")
    forum_title_list = []
    forumsdf = pd.DataFrame()

    # Process each tr node with a class name of "forum-item"
    for forum in forums:
        try:
            forum_data = {}
            forum_data['topic_count'] = int(forum.css_first("td.topics-count").text().replace(',',''))
            forum_data['posts_count'] = int(forum.css_first("td.posts-count").text().replace(',',''))
            cell_forum = forum.css_first("td.cell-forum")
            forum_title_element = cell_forum.css_first("a.forum-title")
            forum_data['title'] = forum_title_element.text()
            forum_data['url'] = forum_title_element.attrs['href']
            get_html(forum_data['url'])
            parsed_forum_url = parse_url(forum_data['url'])
            forum_title_list.append(parsed_forum_url['title'])
            cell_lastpost = forum.css_first("td.lastpost")
            lastpost_title_element = cell_lastpost.css_first("a.lastpost-title")
            forum_data['lastpost_title'] = lastpost_title_element.text()
            forum_data['lastpost_url'] = lastpost_title_element.attrs['href']
            lastpost_author_element = cell_lastpost.css_first("div.lastpost-by").css_first("a")
            forum_data['lastpost_author'] = lastpost_author_element.text()
            forum_data['lastpost_author_url'] = lastpost_author_element.attrs['href']
            lastpost_date_element = cell_lastpost.css_first("div.lastpost-date")
            lastpost_date_unformatted = lastpost_date_element.text()
            forum_data['lastpost_date'] = format_post_date(lastpost_date_unformatted)
            logging.info(f"Forum data is: {forum_data}")
            forumsdf = forumsdf.append(forum_data,ignore_index=True)
        except:
            print('error scraping forum')
        get_topic_data(forum_data['url'])
    
    forumsdf.to_csv('data/forums.csv')
        
    #return forum_title_list
        
def get_subforum_data():
    '''Parse data for each subforum list present on main page'''
    html = open("scrape/_main.txt", "br").read()
    p = HTMLParser(html)
    subforum_lists = p.css("tr.subforum-list")
    subforumsdf = pd.DataFrame()
    
    for subforum_list in subforum_lists:
        subforum_elements = subforum_list.css("div.subforum-info")
        for subforum_element in subforum_elements:
            subforum_data = {}
            subforum_title_element = subforum_element.css_first('a.subforum-title')
            subforum_data['title'] = subforum_title_element.text()
            subforum_data['url'] = subforum_title_element.attrs['href']
            subforum_title_list.append(parse_url(subforum_data['url'])['forum'])
            counts_text = subforum_element.css_first('span.counts').text()
            counts = counts_text.replace('(','').replace(')','').replace(',','').split('/')
            subforum_data['topics'] = counts[0]
            subforum_data['posts'] = counts[1]
            logging.info(f"Subforum data is: {subforum_data}")
            subforumsdf = subforumsdf.append(subforum_data,ignore_index=True)
            
    subforumsdf.to_csv('data/subforums.csv')
    
def get_topic_data(forum_url):
    local_path = parse_url(forum_url)['filepath']
    html = open(local_path, "br").read()
    p = HTMLParser(html)
    threads = p.css("tr.topic-item")
    thread_list = []
    threaddf = pd.DataFrame()
    
    for thread in threads:
        try:
            thread_data = {}
            cell_thread = thread.css_first("td.cell-topic")
            thread_title_element = cell_thread.css_first("a.topic-title")
            thread_data['title'] = thread_title_element.text()
            thread_data['url'] = thread_title_element.attrs['href']
            get_html(thread_data['url'])
            parsed_thread_url = parse_url(thread_data['url'])
            thread_list.append(parsed_thread_url['title'])
            cell_lastpost = thread.css_first("td.cell-lastpost")
            lastpost_author_element = cell_lastpost.css_first("div.lastpost-by").css_first("a")
            thread_data['lastpost_author'] = lastpost_author_element.text()
            thread_data['lastpost_author_url'] = lastpost_author_element.attrs['href']
            lastpost_date_element = cell_lastpost.css_first("span.post-date")
            lastpost_date_unformatted = lastpost_date_element.text()
            thread_data['lastpost_date'] = format_post_date(lastpost_date_unformatted)
            logging.info(f"Thread data is: {thread_data}")
            threaddf = threaddf.append(thread_data,ignore_index=True)
        except:
            print(f'error scraping thread')
        get_post_data(thread_data['url'])
        
    threaddf.to_csv('data/threads.csv')
    
def get_post_data(thread_url):
    print(f'getting post data from {thread_url}')
    local_path = parse_url(thread_url)['filepath']
    html = open(local_path, "br").read()
    p = HTMLParser(html)
    posts = p.css("li.b-post")
    postdf = pd.DataFrame()
    
    for post in posts:
        try:
            post_data = {}
            post_data['content'] = post.css_first("div.b-post__content").text()
            post_data['date'] = format_post_date(post.css_first("div.b-post__timestamp").text())
            post_data['author'] = post.css_first("div.author").text()
            post_data['author_url'] = post.css_first("div.author").css_first("a").attrs['href']
            post_data['author_title'] = post.css_first("div.usertitle").text()
            postdf = postdf.append(post_data,ignore_index=True)
        except:
            print('error scraping post')
        #get_html(post_data['author_url'],author=True)
        
    postdf.to_csv('data/posts.csv')


get_html(BASE_URL)
get_forum_data()