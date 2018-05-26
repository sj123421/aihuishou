#!/usr/bin/python
# -*- coding:utf-8 -*-
# author:joel 18-5-18

'''
https://www.aihuishou.com/   首页
https://www.aihuishou.com/shouji?all=True  手机
https://www.aihuishou.com/shouji/b9  手机/华为
https://www.aihuishou.com/shouji/b9?all=False  手机/华为/第一页
https://www.aihuishou.com/shouji/b9-p8?all=False  手机/华为/第八页
https://www.aihuishou.com/pc/index.html#/inquiry/1564507921190264205  对应选项选择完后的具体价格信息
https://www.aihuishou.com/userinquiry/create  免费查询按钮
'''
import os
import random
import aliyunyzm
import pytesser
import requests
import time
import pymongo
import re
import lxml
from pytesser import *
from lxml import etree
from bs4 import BeautifulSoup
from pytesseract import pytesseract
from selenium import webdriver
from PIL import Image,ImageEnhance


class Spider():
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
        }
        self.phoneType = 'https://www.aihuishou.com/shouji/b9?all=False'
        self.aihuishou = 'https://www.aihuishou.com'
        self.submit = 'http://www.aihuishou.com/userinquiry/create'
        self.dataApi = 'https://www.aihuishou.com/portal-api/inquiry/'
        #在此处创建MongoDB，接下来只要用self.info.insert()就可以逐条插入数据
        self.client = pymongo.MongoClient(host='localhost', port=27017)
        self.db = self.client['aihuishou']
        self.info = self.db['shuju']

    def getHtml(self):
        r = requests.get(self.phoneType,headers = self.headers)  #爬取华为的第一页
        requests.adapters.DEFAULT_RETRIES = 5
        html = r.text
        return html

    def getDetailUrl(self):
        html = self.getHtml()
        soup = BeautifulSoup(html,'lxml')
        all_href = soup.find('div',class_ = 'product-list-wrapper').find_all('a')
        #print len(all_href)
        #all_title = soup.find('div',class_ = 'product-list-wrapper').find_all('title')
        url = []
        for i in all_href:
            infourl = self.aihuishou+i['href']
            url.append(infourl)
        #print url
        for j in url:
            r = requests.get(j)
            html = etree.HTML(r.text)
            now_url = j
            print now_url
            base_id_list = html.xpath('//*[@id="group-property"]/@data-sku-property-value-ids[1]')[0]
            #print base_id_list
            href = html.xpath('//*[@id="submit"]/@href')[0]
            #print href
            pid = html.xpath('//*[@id="submit"]/@data-pid')[0]
            #print pid
            try:
                mid = html.xpath('//*[@id="submit"]/@data-mid')[0]
            except Exception as e:
                mid = ''
                print e

            #获取前3~4个随机选择的list
            pattern1 = re.compile('\d{4}',re.S)
            pattern2 = re.compile('\[\[(.*?)\]',re.S)
            first_little_list = re.findall(pattern2,base_id_list)
            number_of_alist = re.findall(pattern1,first_little_list[0])
            #print number_of_alist
            num = len(number_of_alist)
            base_id_list = re.findall(pattern1,base_id_list)
            three_id_list = []
            for i in range(0,len(base_id_list),num):
                three = base_id_list[i:i+num]
                three_id_list.append(three)
            #print three_id_list #列出前3-4个随机选项列表组合
            #获取各个选项的ID及描述
            beiban = html.xpath('//*[@id="group-property"]/div[2]/div[3]/dl[1]/dd/ul/li/@data-id')
            beiban_describ = html.xpath('//*[@id="group-property"]/div[2]/div[3]/dl[1]/dd/ul/li/div[1]')

            waiguan = html.xpath('//*[@id="group-property"]/div[2]/div[3]/dl[2]/dd/ul/li/@data-id')
            waiguan_describ = html.xpath('//*[@id="group-property"]/div[2]/div[3]/dl[2]/dd/ul/li/div[1]')

            xianshi = html.xpath('//*[@id="group-property"]/div[2]/div[3]/dl[3]/dd/ul/li/@data-id')
            xianshi_describ = html.xpath('//*[@id="group-property"]/div[2]/div[3]/dl[3]/dd/ul/li/div[1]')

            weixiu = html.xpath('//*[@id="group-property"]/div[2]/div[3]/dl[4]/dd/ul/li/@data-id')
            weixiu_miaoshu = html.xpath('//*[@id="group-property"]/div[2]/div[3]/dl[4]/dd/ul/li/div')

            mima = html.xpath('//*[@id="group-property"]/div[2]/div[3]/dl[5]/dd/ul/li/@data-id')
            mima_describ = html.xpath('//*[@id="group-property"]/div[2]/div[3]/dl[5]/dd/ul/li/div')

            wenti_id = html.xpath('//*[@id="group-property"]/div[2]/div[4]/dl/dd/ul/li/@data-id')
            wenti_default = html.xpath('//*[@id="group-property"]/div[2]/div[4]/dl/dd/ul/li/@data-default')
            wenti_describ = html.xpath('//*[@id="group-property"]/div[2]/div[4]/dl/dd/ul/li/span[2]')

            price_units = []
            str = ';'#以；分割列表
            #for循环构造可能的priceUnits
            for i in three_id_list:
                for j in beiban:
                    for k in waiguan:
                        for l in xianshi:
                            for m in weixiu:
                                for o in range(0,len(wenti_id)):
                                    wenti_default_save = wenti_default
                                    wenti_default[o] = wenti_id[o]
                                    price = str.join(i)+';'+j+';'+k+';'+l+';'+m+';;'+str.join(wenti_default)
                                    wenti_default = wenti_default_save
                                    price_units.append(price)

            break #先爬取一个华为型号的手机
        return pid,mid,price_units,now_url

    def getData(self):
        pid,mid,price_units,now_url= self.getDetailUrl()
        num = 0    #用来标记验证码图片号
        for price in price_units:
            print price
            data1 = {
                'AuctionProductId':pid,
                'ProductModelId':mid,
                'PriceUnits':price
            }
            #建立一个session连接，当后面出现验证码的时候可再次post
            ses = requests.Session()
            #点击按钮向其post
            r1 = ses.post(self.submit,data =data1,headers = self.headers)
            time.sleep(random.randint(2, 8))
            r1.encoding = 'utf-8'
            print r1.text #得到返回
            rjson =  r1.json()
            result= r1.text
            if rjson['code'] == 0:  #如果没有验证码，则向api发送请求
                self.getRealData(result)
            else:
                r2 = self.yanzhengma(rjson, num, ses, pid, mid, price)
                result2 = r2.text
                r2json = r2.json()
                if r2json['code'] != 0:
                    r3 = self.yanzhengma(r2json, num, ses, pid, mid, price)
                    result3 = r3.text
                    self.getRealData(result3)
                else:
                    self.getRealData(result2)
                #图片编号加一
                num += 1

    def yanzhengma(self,rjson,num,ses,pid,mid,price):
        # 若有验证码，则先获取验证码的url再通过selenium+phantomjs自动测试识别验证码
        rjson = rjson
        captchaUrl = rjson['data']['captchaUrl']
        # print captchaUrl  验证码的网址
        # 本来用Chrome（）测试，后用phantomJS无界面浏览器，就不会弹出界面
        # chromedriver = "C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe"
        # os.environ["webdriver.chrome.driver"] = chromedriver
        driver = webdriver.PhantomJS()  # 将下载下来的phantomJS放在python的script目录下，若出现selenium抛弃phantomJS的报错，本项目中采用降低selenium的颁发--selenium2.48.0
        driver.get(captchaUrl)  # 要登陆的验证码网站
        imgElement = driver.find_element_by_xpath('/html/body/img')

        driver.save_screenshot('D:/Python/aihuishou_yzm/{}.png'.format(num))  # 截取登录页面
        imgSize = imgElement.size  # 获取验证码图片的大小
        imgLocation = imgElement.location  # 获取验证码元素坐标
        rangle = (int(imgLocation['x']), int(imgLocation['y']), int(imgLocation['x'] + imgSize['width']),
                  int(imgLocation['y'] + imgSize['height']))  # 计算验证码整体坐标
        login = Image.open("D:/Python/aihuishou_yzm/{}.png".format(num))
        frame4 = login.crop(rangle)  # 截取验证码图片
        # 保存到...
        frame4.save('D:/Python/aihuishou_yzm/{}text.png'.format(num))

        authcodeImg = Image.open('D:/Python/aihuishou_yzm/{}text.png'.format(num))
        imgry = authcodeImg.convert('L')  # 图像加强，二值化
        sharpness = ImageEnhance.Contrast(imgry)  # 对比度增强
        sharp_img = sharpness.enhance(2.0)
        sharp_img.save('D:/Python/aihuishou_yzm/{}code.png'.format(num))
        time.sleep(1)

        # tessdata_dir_config = '--tessdata-dir "C:/Program Files (x86)/Tesseract-OCR/tessdata"'
        # authCodeText = pytesser.image_file_to_string('D:/Python/aihuishou_yzm/{}code.png'.format(num)).strip()
        # print authCodeText
        # 无法准确识别验证码，第三方验证码工具或者找到网上的验证码分割算法,该网站验证码为黏连验证码
        # 用阿里云验证码识别识别已经处理过的验证码截图
        codeText = aliyunyzm.aliyun_yzm(num)  # 调用阿里云的识别验证码接口，识别成功但是对于（1和7难以区分）
        print codeText
        #将验证码post进去
        data2 = {
            'AuctionProductId': pid,
            'ProductModelId': mid,
            'PriceUnits': price,
            'imgCaptcha': codeText
        }
        # 将识别出来的验证码
        # #利用session维持会话
        r2 = ses.post(self.submit, data=data2, headers=self.headers)
        time.sleep(random.randint(2, 8))
        r2.encoding = 'utf-8'
        print r2.text
        result = r2.text
        return r2

    def getRealData(self, result):
        tag = result.split('/')[4][:-3]
        js_url = self.dataApi + tag
        r = requests.get(js_url, headers=self.headers)
        rjson = r.json()
        time.sleep(random.randint(2, 8))
        print r.text  # 得到真实数据
        self.info.insert(rjson)
        print u'已存入一条数据...'
        print '\n--------------------\n'
        # return rjson


spider = Spider()
spider.getData()
