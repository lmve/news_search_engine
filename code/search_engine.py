# -*- coding: utf-8 -*-
'''
Created on 2023.12.10
@author: lucky_ma
@description: SearchEngine类 使用基于概率的BM25模型来检索。
@Version 0.0
@CopyRight:CQUT
'''

import jieba
import math
import operator
import sqlite3
import configparser
from datetime import *
'''
   SearchEngine 类
   数据域中K1、B、N、AVG_L、HOT_K1、HOT_K2
   这些变量用于存储BM25算法的参数
   BM25score(Q,d)=∑t∈Qw(t,d)
   w(t,d)=qtfk3+qtf×k1×tftf+k1(1−b+b×ld/avg_l)×log2N−df+0.5df+0.5
   qtf --> 查询中的词频
   tf  --> 文档中的词频
   avl --> 平均文档长度
   df  --> 文档频率
   N   --> 文档数量
   ld  --> 文档长度
   search(self, sentence): #sentence 搜索词 
   fetch_from_db(self, term): #查询文档相关信息
   clean(self, seg_list):#去停用词
   resultBM25(self, sentence):# 获得BM25分数 据此来做最终的结果排名
   首先将句子分词得到所有查询词项，然后从数据库中取出词项对应的倒排记录表，
   对记录表中的所有文档，计算其BM25得分，最后按得分高低排序作为查询结果。
'''
class SearchEngine:
    stop_words = set()
    config_path = ''
    config_encoding = ''
    K1 = 0
    B = 0
    N = 0
    AVG_L = 0
    HOT_K1 = 0
    HOT_K2 = 0
    conn = None  #用于连接数据库
    # 根据参数生成一个 Search 对象
    def __init__(self, config_path, config_encoding):
        self.config_path = config_path
        self.config_encoding = config_encoding
        config = configparser.ConfigParser()
        config.read(config_path, config_encoding)
        f = open(config['DEFAULT']['stop_words_path'], encoding = config['DEFAULT']['stop_words_encoding'])
        words = f.read()
        self.stop_words = set(words.split('\n'))
        self.conn = sqlite3.connect(config['DEFAULT']['db_path'])
        self.K1 = float(config['DEFAULT']['k1'])
        self.B = float(config['DEFAULT']['b'])
        self.N = int(config['DEFAULT']['n'])
        self.AVG_L = float(config['DEFAULT']['avg_l'])
        self.HOT_K1 = float(config['DEFAULT']['hot_k1'])
        self.HOT_K2 = float(config['DEFAULT']['hot_k2'])
    #断开数据库的连接
    def __del__(self):
        self.conn.close()

    def is_number(self, s):
        return s.isdigit()


    # sigmoid函数是一种常用的非线性激活函数，它的输出值在0和1之间。
    # 它可以将任意实数映射到(0,1)区间，可以解释为概率。
    def sigmoid(self, x):
        return 1 / (1 + math.exp(-x))

    def clean(self, seg_list):
        '''
        :param seg_list
        :return: n(它可能用于记录经过清理的列表中的非数字和非停用词的数量。)
                 cleaned_dict(另一个是包含经过清理的单词及其出现次数的字典 )。
        '''
        cleaned_dict = {}
        n = 0
        for i in seg_list:
            i = i.strip().lower()
            # 不是空字符串。
            # 不是数字（通过调用`self.is_number(i)`方法来确定）。
            #不在停用词列表中（通过检查是否存在于`self.stop_words`中来确定）。
            # 只有当一个元素满足这三个条件时，它才会被进一步处理。
            if i != '' and not self.is_number(i) and i not in self.stop_words:
                n = n + 1
                if i in cleaned_dict:
                    cleaned_dict[i] = cleaned_dict[i] + 1
                else:
                    cleaned_dict[i] = 1
        return n, cleaned_dict

    # 从数据库中查询
    def fetch_from_db(self, term):
        c = self.conn.cursor()
        c.execute('SELECT * FROM postings WHERE term=?', (term,))
        return(c.fetchone())

    # 计算BM25得分
    def resultBM25(self, sentence):# 获得BM25分数
        seg_list = jieba.lcut(sentence, cut_all=False)  #对搜索词进行分词
        n, cleaned_dict = self.clean(seg_list) #清除停用词
        BM25_scores = {}
        for term in cleaned_dict.keys():
            r = self.fetch_from_db(term)    #从数据库中获取关键词的文档频率等信息
            if r is None:
                continue

            df = r[1]                   #文档频率
            w = math.log2((self.N - df + 0.5) / (df + 0.5)) #计算权重
            docs = r[2].split('\n')
            #计算BM25得分
            for doc in docs:
                docid, date_time, tf, ld = doc.split('\t')
                docid = int(docid)
                tf = int(tf)
                ld = int(ld)
                s = (self.K1 * tf * w) / (tf + self.K1 * (1 - self.B + self.B * ld / self.AVG_L))
                if docid in BM25_scores:
                    BM25_scores[docid] = BM25_scores[docid] + s
                else:
                    BM25_scores[docid] = s
        #按评分排序
        BM25_scores = sorted(BM25_scores.items(), key = operator.itemgetter(1))
        BM25_scores.reverse()
        if len(BM25_scores) == 0:
            return 0, []
        else:
            return 1, BM25_scores

    def search(self, sentence): #sentence 搜索词
        return self.resultBM25(sentence)


if __name__ == "__main__":
    se = SearchEngine('../config.ini', 'utf-8')
    flag, rs = se.search('北京雾霾')
    print(rs[:10])