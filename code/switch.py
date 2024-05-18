'''
Created on 2023.12.13
@author: lucky_ma
@description:  拼音转汉字模块，将搜索词中的拼音转成汉字
@Version 0.0
@CopyRight:CQUT
'''

from Pinyin2Hanzi import DefaultDagParams
from Pinyin2Hanzi import dag


def pinyin_2_hanzi(pinyinList):

    dagParams = DefaultDagParams()
    # 10个候选值
    result = dag(dagParams, pinyinList, path_num=1, log=True)
    # dict = {}
    for item in result:
        socre = item.score # 得分
        res = item.path # 转换结果
    #     dict[socre] = res
    # result = sorted(dict.items(),key=lambda d:d[1],reverse=True)
    # print(result)
    return res
def pinyin_or_word(string,pinyinLib):
    '''
    judge a string is a pinyin or not.
    pinyinLib comes from a txt file.
    最大逆向匹配
    '''
    max_len = 6   # 拼音最长为6
    string = string.lower()
    stringlen = len(string)
    result = []
    while True:
        matched = 0
        matched_word = ''
        if stringlen < max_len:
            max_len = stringlen
        for i in range(max_len, 0, -1):
            s = string[(stringlen-i):stringlen]
            if s in pinyinLib:
                matched_word = s
                matched = i
                break
        if len(matched_word) == 0:
            break
        else:
            result.append(s)
            string = string[:(stringlen-matched)]
            stringlen = len(string)
            if stringlen == 0:
                break
    if len(result) == 0:
        return False,result
    return True,result

def get_pinyin_lib():
    with open("../data/pinyin.txt",encoding='UTF-8') as f:
        pinyinlib = f.read().split('\n')
    return pinyinlib
'''
   拼音转汉字
   输入：前端搜索词
   输出：拼音标志，汉字
'''
def pinyin_switch_hanzi(pinyin):
    pinyinLib = get_pinyin_lib()
    flag,list = pinyin_or_word(pinyin,pinyinLib)
    key = ''
    if flag:  # True 表示 该字符串为拼音
        result = pinyin_2_hanzi(list[::-1])
        for item in result:
            key += item
    return flag,key #返回字符串结果


if __name__ == '__main__':
    # lists = ['jin', 'tian', 'tian', 'qi', 'zhen', 'hao', 'a']
    # pinyin_2_hanzi(lists)
    # print(get_pinyin_lib())
    pinyinLib = get_pinyin_lib()
    # print(pinyin_or_word("nihao jintiantianqiruhe", pinyinLib))
    flag,list = pinyin_or_word("今天天气真好啊",pinyinLib)
    if flag:
        print(pinyin_2_hanzi(list[::-1]))