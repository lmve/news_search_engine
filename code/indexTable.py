# -*- coding: utf-8 -*-
'''
Created on 2023.12.8
@author: lucky_ma
@description:   建立倒排索引
@Version 0.0
@CopyRight:CQUT
'''
import math
from os import listdir
import xml.etree.ElementTree as ET
import jieba
import sqlite3
import configparser
'''
    文档类将倒排记录表序列化成一个长的字符串
    tf 词频
    ld 长度
'''
class Doc:
    docid = 0
    date_time = ''
    tf = 0
    ld = 0
    def __init__(self, docid, date_time, tf, ld):
        self.docid = docid
        self.date_time = date_time
        self.tf = tf
        self.ld = ld
    def __repr__(self):
        return(str(self.docid) + '\t' + self.date_time + '\t' + str(self.tf) + '\t' + str(self.ld))
    def __str__(self):
        return(str(self.docid) + '\t' + self.date_time + '\t' + str(self.tf) + '\t' + str(self.ld))

'''
   创建倒排索引
   stop_words       -->  停用词
   postings_lists   -->  倒排索引表
   
'''
class IndexModule:
    stop_words = set()
    postings_lists = {}
    
    config_path = ''
    config_encoding = ''
    
    def __init__(self, config_path, config_encoding,idf_path):
        self.config_path = config_path
        self.config_encoding = config_encoding
        self.idf_path=idf_path
        config = configparser.ConfigParser()
        config.read(config_path, config_encoding)
        f = open(config['DEFAULT']['stop_words_path'], encoding = config['DEFAULT']['stop_words_encoding'])
        words = f.read()
        self.stop_words = set(words.split('\n'))

    def is_number(self, s):
        return s.isdigit()

    #去停用词
    def clean_list(self, seg_list):
        cleaned_dict = {}
        n = 0
        for i in seg_list:
            i = i.strip().lower()
            if i != '' and not self.is_number(i) and i not in self.stop_words:
                n = n + 1
                if i in cleaned_dict:
                    cleaned_dict[i] = cleaned_dict[i] + 1
                else:
                    cleaned_dict[i] = 1
        return n, cleaned_dict

    # 将索引存在数据库中
    def write_to_db(self, db_path):
        #连接数据库
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
    #若已存在则将其删除
        c.execute('''DROP TABLE IF EXISTS postings''')
        c.execute('''CREATE TABLE postings
                     (term TEXT PRIMARY KEY, df INTEGER, docs TEXT)''')
        #key、 value、 doc_list
        for key, value in self.postings_lists.items():
            doc_list = '\n'.join(map(str,value[1]))
            t = (key, value[0], doc_list)
            c.execute("INSERT INTO postings VALUES (?, ?, ?)", t)

        conn.commit()
        conn.close()

    #构建数据库表单
    def Create_postings_lists(self):
        config = configparser.ConfigParser()
        config.read(self.config_path, self.config_encoding)
        #读取所有的相关文件
        files = listdir(config['DEFAULT']['doc_dir_path'])
        AVG_L = 0 #文档的平均长度
        idf = {}
        for i in files:
            root = ET.parse(config['DEFAULT']['doc_dir_path'] + i).getroot()
            title = root.find('title').text
            body = root.find('body').text
            docid = int(root.find('id').text)
            date_time = root.find('datetime').text
            seg_list = jieba.lcut(title + '。' + body, cut_all=False)
            #去除停用词
            ld, cleaned_dict = self.clean_list(seg_list)
            
            AVG_L = AVG_L + ld
            
            for key, value in cleaned_dict.items():
                d = Doc(docid, date_time, value, ld)   #对应的文档信息
                if key in self.postings_lists:
                    self.postings_lists[key][0] = self.postings_lists[key][0] + 1 # df++
                    self.postings_lists[key][1].append(d)
                else:
                    self.postings_lists[key] = [1, [d]] # [df, [Doc]]
        n=len(files)
        idf_file = open(self.idf_path, 'w', encoding='utf-8')
        for word in self.postings_lists:
            idf_file.write('%s %.9f\n' % (word, math.log(n / self.postings_lists[word][0])))
        idf_file.close()

        #计算文档的平均长度
        AVG_L = AVG_L / len(files)
        config.set('DEFAULT', 'N', str(len(files)))
        config.set('DEFAULT', 'avg_l', str(AVG_L))
        with open(self.config_path, 'w', encoding = self.config_encoding) as configfile:
            config.write(configfile)
        #将倒排索引信息存入数据库中
        self.write_to_db(config['DEFAULT']['db_path'])

if __name__ == "__main__":
    im = IndexModule('../config.ini', 'utf-8','../data/idf.txt')
    im.Create_postings_lists()
