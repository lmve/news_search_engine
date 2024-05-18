# -*- coding: utf-8 -*-
'''
Created on 2023.12.8
@author: lucky_ma
@description:   做查询准备
@Version 0.0
@CopyRight:CQUT
'''

from spider import get_news_pool
from spider import crawl_news
from indexTable import IndexModule
from Selected_module import Selected
from datetime import *
import urllib.request
import configparser

def get_max_page(root):
    response = urllib.request.urlopen(root)
    html = str(response.read())
    html = html[html.find('var maxPage =') : ]
    html = html[:html.find(';')]
    max_page = int(html[html.find('=') + 1 : ])
    #print(max_page)
    return(max_page)

def crawling():
    print('-----start crawling time: %s-----'%(datetime.today()))
    config = configparser.ConfigParser()
    config.read('../config.ini', 'utf-8')
    root = 'http://news.sohu.com/1/0903/61/subject212846158'
    max_page = get_max_page(root+'.shtml')
    news_pool = get_news_pool(root, max_page, max_page - 5)
    crawl_news(news_pool, 140, config['DEFAULT']['doc_dir_path'], config['DEFAULT']['doc_encoding'])
    
if __name__ == "__main__":
    print('-----start time: %s-----'%(datetime.today()))
    
    # 抓取新闻
    # crawling()
    # 构建索引
    print('-----start indexing time: %s-----'%(datetime.today()))
    im = IndexModule('../config.ini', 'utf-8','../data/idf.txt')
    im.Create_postings_lists()

    # #推荐阅读
    print('-----start recommending time: %s-----'%(datetime.today()))
    rm = Selected('../config.ini', 'utf-8')
    rm.find_k_nearest(5, 10)
    print('-----finish time: %s-----'%(datetime.today()))