# -*- coding: utf-8 -*-
'''
Created on 2023.12.8
@author: lucky_ma
@description:爬虫程序  爬取相关网页
@Version 0.0
@CopyRight:CQUT
'''

from bs4 import BeautifulSoup
import urllib.request
import xml.etree.ElementTree as ET
import configparser
'''
   用于爬取网页信息
   通过 bs4 从网页源代码中提取出时间、url、标题
   存储在news_pool列表
'''
def get_news_pool(root, start, end):
    news_pool = []
    for i in range(start,end,-1):
        # page_url = ''
        if i != start:
            page_url = root +'_%d.shtml'%(i)
        else:
            page_url = root + '.shtml'
        try:
            response = urllib.request.urlopen(page_url)
        except Exception as e:
            print("-----%s: %s-----"%(type(e), page_url))
            continue
        #读取网页源代码并做分析
        html = response.read()
        soup = BeautifulSoup(html,"lxml")
        td = soup.find('td', class_ = "newsblue1")
        a = td.find_all('a')
        span = td.find_all('span')
        for i in range(len(a)):
            date_time = span[i].string
            url = a[i].get('href')
            title = a[i].string
            news_info = ['2016-'+date_time[1:3]+'-'+date_time[4:-1]+':00',url,title]
            news_pool.append(news_info)
    return(news_pool)

'''
   将可爬的网页处理后存盘
   news_pool  -->  列表为可爬网页
   min_len    -->  正文最短长度
   doc_dir_path -> 存储路径
   doc_encoding -> 字符格式
'''
def crawl_news(news_pool, min_len, doc_dir_path, doc_encoding):
    #文档编号从1开始
    i = 1
    for news in news_pool:
        try:
            response = urllib.request.urlopen(news[1])
        except Exception as e:
            print("-----%s: %s-----"%(type(e), news[1]))
            continue
        html = response.read()
        soup = BeautifulSoup(html,"lxml")
        try:
            body = soup.find('div', class_ = "text clear").find('div').get_text()
        except Exception as e:
            print("-----%s: %s-----"%(type(e), news[1]))
            continue
        if '//' in body:
            body = body[:body.index('//')]
        body = body.replace(" ", "")
        if len(body) <= min_len:
            continue
        doc = ET.Element("doc")
        ET.SubElement(doc, "id").text = "%d"%(i)
        ET.SubElement(doc, "url").text = news[1]
        ET.SubElement(doc, "title").text = news[2]
        ET.SubElement(doc, "datetime").text = news[0]
        ET.SubElement(doc, "body").text = body
        tree = ET.ElementTree(doc)
        tree.write(doc_dir_path + "%d.xml"%(i), encoding = doc_encoding, xml_declaration = True)
        i += 1
    
if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('../config.ini', 'utf-8')
    root = 'http://news.sohu.com/1/0903/61/subject212846158'
    news_pool = get_news_pool(root, 854, 849)
    print(news_pool)
    # crawl_news(news_pool, 140, config['DEFAULT']['doc_dir_path'], config['DEFAULT']['doc_encoding'])
    # print('done!')