#!/usr/bin/python
# -*- coding:utf-8 -*-
# author:joel 18-5-13

import urllib, urllib2, sys
import base64

def aliyun_yzm(num):
    n = num
    host = 'http://jisuyzmsb.market.alicloudapi.com'
    path = '/captcha/recognize'
    method = 'POST'
    appcode = '532900d71a9c43848825ac8fa2328a71'
    querys = 'type=n4'
    bodys = {}
    url = host + path + '?' + querys


    # f=open(r'D:\Python\aihuishou_yzm\{}code.png'.format(n),'rb') #二进制方式打开图文件
    f = open(r'D:\Python\aihuishou_yzm\{}code.png'.format(str(n)), 'rb')  # 二进制方式打开图文件
    ls_f=base64.b64encode(f.read()) #读取文件内容，转换为base64编码
    f.close()

    bodys['pic'] = ls_f
    post_data = urllib.urlencode(bodys)
    request = urllib2.Request(url, post_data)
    request.add_header('Authorization', 'APPCODE ' + appcode)
    #根据API的要求，定义相对应的Content-Type
    request.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
    response = urllib2.urlopen(request)
    content = response.read()
    if content:
        #print content
        r = content[-7:-3]
        # print r

    return r


