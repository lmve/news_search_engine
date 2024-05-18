# -*- coding: utf-8 -*-
'''
Created on 2023.12.8
@author: lucky_ma
@description:主控制程序、前端是基于 Flask 框架开发
@Version 0.0
@CopyRight:CQUT
'''
# render_template   ----->    用于模板显示界面
from flask import Flask, render_template, request
from search_engine import SearchEngine
import xml.etree.ElementTree as ET
import sqlite3
import configparser
import jieba
import switch

#创建一个 Flask 对象
app = Flask(__name__)
doc_dir_path = ''
db_path = ''
global page
global keys

'''
   搜索模块
'''
def searching(key):
    global page
    global doc_id
    se = SearchEngine('../config.ini', 'utf-8') #创建一个搜索对象
    #id_scores 记录文档id 与其对应的得分
    flag, id_scores = se.search(key)  #搜索结果
    # 提取结果文档 id
    doc_id = [i for i, s in id_scores]
    #分页，每个网页 5 条数据
    page = []
    for i in range(1, (len(doc_id) // 5 + 2)):
        page.append(i)
    return flag,page
'''
   结果分页
'''
def cut_page(page, no):# 分页
    docs = find(doc_id[no*5:page[no]*5])
    return docs
'''
   从数据库中查找最接近的k条数据
'''
def get_k_nearest(db_path, docid, k=5):
    conn = sqlite3.connect(db_path)    #使用 sqlite3 库连接到位于 db_path 的SQLite数据库。
    c = conn.cursor()                  #创建一个游标对象，用于执行SQL查询。
    c.execute("SELECT * FROM knearest WHERE id=?", (docid,))
    docs = c.fetchone()
    #print(docs)
    conn.close()
    return docs[1: 1 + (k if k < 5 else 5)]  # max = 5
'''
   创建根路由，这是搜索界面
   基于html模板的显示界面
'''
@app.route('/')
def main():
    init()
    return render_template('search.html', error=True)  #返回一个 html 的模板显示

# 读取表单数据，获得doc_ID
'''
   定义了一个路由（'/search/'）和一个对应的方法（search）。
   这个方法处理一个 POST 请求，
   获取前端搜索框的数据进行搜索，
   然后将搜索结果返回给前端。
'''
@app.route('/search/', methods=['POST'])
def search():
    try:
        global keys     #获取前端搜索框的数据
        global checked
        checked = ['checked="true"', '', '']
        keys = request.form['key_word']

        print(keys,checked)  #测试
        # 判断搜索词是否为拼音
        key = keys
        is_pin,newkey = switch.pinyin_switch_hanzi(keys)
        if is_pin:
            keys = newkey
            print("收到一段拼音",key,newkey)

        if keys not in ['']:# 检查搜索词是否为空
            # flag 表明是否找到  page表示结果有几页
            flag,page = searching(keys)
            # print(flag) #测试
            # flag = 0 查询失败
            if flag==0:
                return render_template('result.html', error=False)
            docs = cut_page(page, 0)#结果文档
            return render_template('result.html', checked=checked, key=keys, docs=docs, page=page,
                                   error=True)
        else:
            return render_template('result.html', error=False)

    except:
        print('search error')

'''
   将需要的数据以字典形式打包传递给search函数
   将要展示的页面信息提取出来
   url：文档的URL
   title：文档的标题
   body：文档的正文内容
   snippet：文档的前120个字符（后加省略号）
   datetime：文档的日期时间
   time：文档的时间部分（从datetime中提取）
'''
def find(docid, extra=False):#传入结果文档编号
    docs = []
    global dir_path, db_path
    for id in docid:  #找到对应文档编号的内容按照HTML格式提取出来
        root = ET.parse(dir_path + '%s.xml' % id).getroot()
        url = root.find('url').text
        title = root.find('title').text
        body = root.find('body').text
        snippet = root.find('body').text[0:120] + '……'
        time = root.find('datetime').text.split(' ')[0]
        datetime = root.find('datetime').text
        doc = {'url': url, 'title': title, 'snippet': snippet, 'datetime': datetime, 'time': time, 'body': body,
               'id': id, 'extra': []}
        # 是否需要额外的数据
        if extra:
            temp_doc = get_k_nearest(db_path, id)
            for i in temp_doc:
                root = ET.parse(dir_path + '%s.xml' % i).getroot()
                title = root.find('title').text
                doc['extra'].append({'id': i, 'title': title})
        docs.append(doc)
    return docs

'''
   切换页面路由
'''
@app.route('/search/page/<page_no>/', methods=['GET'])
def next_page(page_no):
    try:
        page_no = int(page_no)
        docs = cut_page(page, (page_no-1))
        return render_template('result.html', checked=checked, key=keys, docs=docs, page=page,
                               error=True)
    except:
        print('next error')



'''
   内容展示界面
'''
@app.route('/search/<id>/', methods=['GET', 'POST'])
def content(id):
    try:
        doc = find([id], extra=True)
        return render_template('page.html', doc=doc[0])
    except:
        print('content error')

#config 文件中包含了各项基本参数，读取该文件来配置相关参数
def init():
    config = configparser.ConfigParser()
    config.read('../config.ini', 'utf-8')
    global dir_path, db_path
    dir_path = config['DEFAULT']['doc_dir_path']
    db_path = config['DEFAULT']['db_path']

if __name__ == '__main__':
    jieba.initialize()  # 手动初始化（可选）
    # app.run(host="0.0.0.0", port=5000, debug=True) # 部署到服务器上，外网可通过服务器IP和端口访问
    app.run(debug=True)
