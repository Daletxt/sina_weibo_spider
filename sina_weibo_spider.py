# -*- coding: utf-8 -*-
import re
import os
import json
import urllib.request

import requests
from lxml import etree

#需要的设置：
#改一下 图片下载的文件夹路径
#设置要爬取的微博用户的的微博ID
id='1267050985'


#设置代理IP
proxy_addr="122.241.72.191:808"

#定义页面打开函数
def use_proxy(url,proxy_addr):
    req=urllib.request.Request(url)
    req.add_header("User-Agent","Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0")
    proxy=urllib.request.ProxyHandler({'http':proxy_addr})
    opener=urllib.request.build_opener(proxy,urllib.request.HTTPHandler)
    urllib.request.install_opener(opener)
    data=urllib.request.urlopen(req).read().decode('utf-8','ignore')
    return data

#获取微博主页的containerid，爬取微博内容时需要此id
def get_containerid(url):
    data=use_proxy(url,proxy_addr)
    content=json.loads(data).get('data')
    for data in content.get('tabsInfo').get('tabs'):
        if(data.get('tab_type')=='weibo'):
            containerid=data.get('containerid')
    return containerid

#获取微博大V账号的用户基本信息，如：微博昵称、微博地址、微博头像、关注人数、粉丝数、性别、等级等
def get_userInfo(id):
    url='https://m.weibo.cn/api/container/getIndex?type=uid&value='+id
    data=use_proxy(url,proxy_addr)
    content=json.loads(data).get('data')
    profile_image_url=content.get('userInfo').get('profile_image_url')
    description=content.get('userInfo').get('description')
    profile_url=content.get('userInfo').get('profile_url')
    verified=content.get('userInfo').get('verified')
    guanzhu=content.get('userInfo').get('follow_count')
    name=content.get('userInfo').get('screen_name')
    fensi=content.get('userInfo').get('followers_count')
    gender=content.get('userInfo').get('gender')
    urank=content.get('userInfo').get('urank')
    print("微博昵称："+name+"\n"+"微博主页地址："+profile_url+"\n"+"微博头像地址："+profile_image_url+"\n"+"是否认证："+str(verified)+"\n"+"微博说明："+description+"\n"+"关注人数："+str(guanzhu)+"\n"+"粉丝数："+str(fensi)+"\n"+"性别："+gender+"\n"+"微博等级："+str(urank)+"\n")


#获取微博内容信息,并保存到文本中，内容包括：每条微博的内容、微博详情页面地址、点赞数、评论数、转发数等
def get_weibo(id,file):
    i=1
    while True:
        url='https://m.weibo.cn/api/container/getIndex?type=uid&value='+id
        weibo_url='https://m.weibo.cn/api/container/getIndex?type=uid&value='+id+'&containerid='+get_containerid(url)+'&page='+str(i)
        try:
            data=use_proxy(weibo_url,proxy_addr)
            content=json.loads(data).get('data')
            cards=content.get('cards')
            if(len(cards)>0):
                for j in range(len(cards)):
                    print("-----正在爬取第"+str(i)+"页，第"+str(j)+"条微博------")
                    card_type=cards[j].get('card_type')
                    if(card_type==9):
                        mblog=cards[j].get('mblog')
                        attitudes_count=mblog.get('attitudes_count')
                        comments_count=mblog.get('comments_count')
                        created_at=mblog.get('created_at')
                        reposts_count=mblog.get('reposts_count')
                        scheme=cards[j].get('scheme')
                        print(scheme)
                        text=mblog.get('text')

                        r = requests.get(url=scheme)
                        try:
                            data_xpath = etree.HTML(r.text).xpath("//script/text()")[1]
                            title_temp = re.findall('\"status_title\": (.*)', data_xpath)[0]
                            # print("转发的微博标题是：", title)
                            longText = re.findall('\"longTextContent\": (.*)', data_xpath)
                            if longText:
                                longTextContent = longText[0]
                                # print("转发微博 的 正文 长文本处理", longTextContent)
                            else:
                                longText = re.findall('\"text\": (.*)', data_xpath)
                                if longText:
                                    longTextContent = longText[1]
                                    # print("转发的微博 的 正文 的内容：", longTextContent)
                                else:
                                    longTextContent = "转发的微博没有文本内容"
                        except:
                            title_temp = "标记：微博没有标题"
                            longTextContent = "标记：列表越界，就是微博详情页没拿到东西"
                        img_list = re.findall(r'"size": "large",\n                        "url": "(.+?)",\n                        "geo"',r.text)
                        # print("图片地址列表是：", img_list)
                        print("这个微博有 {} 张图片".format(len(img_list)))
                        title = title_temp.replace("\"", "").replace("\\", "").replace("?","？").replace(":","：").replace("*","").replace("<"," ").replace(">","").replace("|","")
                        # print(title, img_list)
                        #下载并保存图片
                        save_one_atlas(title,img_list)
                        with open(file,'a',encoding='utf-8') as fh:
                            fh.write("----第"+str(i)+"页，第"+str(j)+"条微博----"+"\n")
                            fh.write("微博地址："+str(scheme)+"\n"+"发布时间："+str(created_at)+"\n"+
                                     "微博内容："+text+"\n"+"点赞数："+str(attitudes_count)+"\n"+
                                     "评论数："+str(comments_count)+"\n"+"转发数："+str(reposts_count)+"\n"+
                                     "转发的微博标题是："+title+"\n"+"转发的微博的正文的内容："+longTextContent+"\n")
                i+=1
            else:
                break
        except Exception as e:
            print(e)
            pass

def save_img(title, img, count, file_path):
    #保存图片
    pic = requests.get(url=img)
    picture_name = title + str(count) + ".jpg"
    picture = file_path + "/" + picture_name
    print("图片名：", picture_name)
    with open(picture, 'wb') as f:
        f.write(pic.content)


def save_one_atlas(title, img_list):
    #图片放到对应文件夹
    if img_list:
        file_path = "D:/Python/新浪爬虫/图片/" + title + "/"
        # 打开下载图片的目录，如果不存在以转发微博标题命名的文件夹则自动创建
        if len(img_list)==1:
            file_path = "D:/Python/新浪爬虫/图片/"
        else:
            if not os.path.exists(file_path):
                os.makedirs(file_path)
        print(file_path)
        print("图集--" + title + "--开始保存")
        for i in range(0, len(img_list)):
            img_url = img_list[i]
            save_img(title, img_url, i, file_path)
            print('正在保存第' + str(i) + '张图片')
        print("图集--" + title + "保存成功")
    else:
        pass


if __name__ == "__main__":

    file=id+".txt"
    get_userInfo(id)
    get_weibo(id, file)

