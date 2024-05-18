# -*- coding: utf-8 -*-
'''
Created on 2023.12.8
@author: lucky_ma
@description:   推荐系统
@Version 0.0
@CopyRight:CQUT
'''

from os import listdir
import xml.etree.ElementTree as ET
import jieba
import jieba.analyse
import sqlite3
import configparser
from datetime import *
import math

import pandas as pd
import numpy as np

from sklearn.metrics import pairwise_distances
'''
   精选文章
   一篇文档用一个向量表示，
   先提取tfidf得分最高的25个关键词的值作为文档的向量表示。
   计算相似度
   
'''
class Selected:
    stop_words = set()
    k_nearest = []
    
    config_path = ''
    config_encoding = ''
    doc_dir_path = ''
    doc_encoding = ''
    stop_words_path = ''
    stop_words_encoding = ''
    idf_path = ''
    db_path = ''
    
    def __init__(self, config_path, config_encoding):
        self.config_path = config_path
        self.config_encoding = config_encoding
        config = configparser.ConfigParser()
        config.read(config_path, config_encoding)
        
        self.doc_dir_path = config['DEFAULT']['doc_dir_path']
        self.doc_encoding = config['DEFAULT']['doc_encoding']
        self.stop_words_path = config['DEFAULT']['stop_words_path']
        self.stop_words_encoding = config['DEFAULT']['stop_words_encoding']
        self.idf_path = config['DEFAULT']['idf_path']
        self.db_path = config['DEFAULT']['db_path']

        f = open(self.stop_words_path, encoding = self.stop_words_encoding)
        words = f.read()
        self.stop_words = set(words.split('\n'))

    '''
       向数据库中写入相关数据
    '''
    def write_select_to_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''DROP TABLE IF EXISTS knearest''')
        c.execute('''CREATE TABLE knearest
                     (id INTEGER PRIMARY KEY, first INTEGER, second INTEGER,
                     third INTEGER, fourth INTEGER, fifth INTEGER)''')
        for docid, doclist in self.k_nearest:
            c.execute("INSERT INTO knearest VALUES (?, ?, ?, ?, ?, ?)", tuple([docid] + doclist))

        conn.commit()
        conn.close()
    
    def is_number(self, s):
       return s.isdigit()
            
    #为每个文档创建一个包含这些关键词及其TF-IDF值的矩阵。
    def construct_dt_matrix(self, files, topK = 25):
        jieba.analyse.set_stop_words(self.stop_words_path)
        jieba.analyse.set_idf_path(self.idf_path)
        M = len(files)
        N = 1
        terms = {}
        dt = []
        for i in files:
            root = ET.parse(self.doc_dir_path + i).getroot()
            title = root.find('title').text
            body = root.find('body').text
            docid = int(root.find('id').text)
            tags = jieba.analyse.extract_tags(title + '。' + body, topK=topK, withWeight=True)
            #tags = jieba.analyse.extract_tags(title, topK=topK, withWeight=True)
            cleaned_dict = {}
            for word, tfidf in tags:
                word = word.strip().lower()
                if word == '' or self.is_number(word):
                    continue
                cleaned_dict[word] = tfidf
                if word not in terms:
                    terms[word] = N
                    N += 1
            dt.append([docid, cleaned_dict])
        dt_matrix = [[0 for i in range(N)] for j in range(M)]
        i =0
        for docid, t_tfidf in dt:
            dt_matrix[i][0] = docid
            for term, tfidf in t_tfidf.items():
                dt_matrix[i][terms[term]] = tfidf
            i += 1

        dt_matrix = pd.DataFrame(dt_matrix)
        dt_matrix.index = dt_matrix[0]
        print('dt_matrix shape:(%d %d)'%(dt_matrix.shape))
        return dt_matrix
    #为每个文档找到其k个最相似的文档，根据余弦相似度
    def construct_k_nearest_matrix(self, dt_matrix, k):
        tmp = np.array(1 - pairwise_distances(dt_matrix[dt_matrix.columns[1:]], metric = "cosine"))
        similarity_matrix = pd.DataFrame(tmp, index = dt_matrix.index.tolist(), columns = dt_matrix.index.tolist())
        for i in similarity_matrix.index:
            tmp = [int(i),[]]
            j = 0
            while j < k:
                max_col = similarity_matrix.loc[i].idxmax(axis = 0)
                similarity_matrix.loc[i][max_col] =  -1
                try:
                    if max_col != i:
                        tmp[1].append(int(max_col)) #max column name
                        j += 1
                except Exception as e:
                    print(max_col)
                    continue
            self.k_nearest.append(tmp)

        
    def find_k_nearest(self, k, topK):
        # self.gen_idf_file()
        files = listdir(self.doc_dir_path)
        dt_matrix = self.construct_dt_matrix(files, topK)
        self.construct_k_nearest_matrix(dt_matrix, k)
        self.write_select_to_db()
        

    